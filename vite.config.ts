import { defineConfig, Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { spawn, ChildProcess } from 'child_process';
import http from 'http';

function fastApiPlugin(): Plugin {
  let fastApiProc: ChildProcess | null = null;

  // Check if port 8001 is already running
  const checkAndStart = () => {
    const req = http.get('http://127.0.0.1:8001/api/health', (res) => {
      if (res.statusCode === 200) {
        console.log('[Vite] FastAPI is already running on port 8001.');
      }
    });

    req.on('error', () => {
      console.log('[Vite] Starting FastAPI backend on port 8001...');
      // En Windows el intérprete se llama `python`; en Linux/macOS, `python3`.
      const candidates = process.platform === 'win32'
        ? ['python', 'py', 'python3']
        : ['python3', 'python'];

      const spawnWith = (index: number) => {
        if (index >= candidates.length) {
          console.error(
            '[Vite] No se encontro Python. Instalalo o levanta el backend a mano: ' +
            'python -m uvicorn backend.main:app --reload --port 8001'
          );
          return;
        }

        const proc = spawn(candidates[index], [
          '-m', 'uvicorn',
          'backend.main:app',
          '--host', '127.0.0.1',
          '--port', '8001'
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

  checkAndStart();

  return {
    name: 'fastapi-runner',
    configureServer(server) {
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
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/docs': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/openapi.json': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/redoc': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      }
    }
  },
  preview: {
    port: 3000,
    host: '0.0.0.0',
  }
});
