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
      fastApiProc = spawn('python3', [
        '-m', 'uvicorn',
        'backend.main:app',
        '--host', '127.0.0.1',
        '--port', '8001'
      ], {
        stdio: 'inherit'
      });

      fastApiProc.on('error', (err) => {
        console.error('[Vite] Failed to start FastAPI process:', err);
      });
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
