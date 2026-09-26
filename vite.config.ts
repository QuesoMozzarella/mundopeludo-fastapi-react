import { defineConfig, Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { spawn, ChildProcess } from 'child_process';
import http from 'http';

// Puerto del backend FastAPI. Las pruebas e2e usan otro para no tocar el de desarrollo.
const PUERTO_API = process.env.FASTAPI_PORT || '8001';
const URL_API = `http://127.0.0.1:${PUERTO_API}`;

function fastApiPlugin(): Plugin {
  let fastApiProc: ChildProcess | null = null;

  // ¿Hay ya un backend escuchando en el puerto?
  const checkAndStart = () => {
    const req = http.get(`${URL_API}/api/health`, (res) => {
      if (res.statusCode === 200) {
        console.log(`[Vite] FastAPI is already running on port ${PUERTO_API}.`);
      }
    });

    req.on('error', () => {
      console.log(`[Vite] Starting FastAPI backend on port ${PUERTO_API}...`);
      // En Windows el intérprete se llama `python`; en Linux/macOS, `python3`.
      const candidates = process.platform === 'win32'
        ? ['python', 'py', 'python3']
        : ['python3', 'python'];

      const spawnWith = (index: number) => {
        if (index >= candidates.length) {
          console.error(
            '[Vite] No se encontro Python. Instalalo o levanta el backend a mano: ' +
            `python -m uvicorn backend.main:app --reload --port ${PUERTO_API}`
          );
          return;
        }

        const proc = spawn(candidates[index], [
          '-m', 'uvicorn',
          'backend.main:app',
          '--host', '127.0.0.1',
          '--port', PUERTO_API
        ], {
          stdio: 'inherit',
          cwd: process.cwd()
        });

        proc.on('error', () => spawnWith(index + 1));
        proc.on('exit', (code) => {
          // El stub de la Microsoft Store sale con 9009 sin ejecutar nada.
          if (fastApiProc === proc && code === 9009) spawnWith(index + 1);
        });

        fastApiProc = proc;
      };

      spawnWith(0);
    });

    req.setTimeout(500, () => {
      req.destroy(new Error('timeout'));
    });
  };

  return {
    name: 'fastapi-runner',
    // Sólo con el servidor de desarrollo: en `vite build` el proceso hijo de
    // uvicorn mantenía vivo el build y nunca terminaba.
    apply: 'serve',
    configureServer(server) {
      // FASTAPI_EXTERNO=1: alguien más gestiona el backend (p. ej. las pruebas e2e).
      if (process.env.FASTAPI_EXTERNO !== '1') checkAndStart();
      server.httpServer?.on('close', () => {
        if (fastApiProc) {
          console.log('[Vite] Terminating FastAPI backend...');
          fastApiProc.kill();
          fastApiProc = null;
        }
      });
    }
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    fastApiPlugin()
  ],
  server: {
    port: 3000,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: URL_API,
        changeOrigin: true,
      },
      '/docs': {
        target: URL_API,
        changeOrigin: true,
      },
      '/openapi.json': {
        target: URL_API,
        changeOrigin: true,
      },
      '/redoc': {
        target: URL_API,
        changeOrigin: true,
      }
    }
  },
  preview: {
    port: 3000,
    host: '0.0.0.0',
  }
});
