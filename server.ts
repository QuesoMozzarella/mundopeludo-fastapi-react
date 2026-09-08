import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn, ChildProcess } from 'child_process';
import { createProxyMiddleware } from 'http-proxy-middleware';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = 3000;
const FASTAPI_PORT = 8001;
const app = express();

let fastApiProcess: ChildProcess | null = null;

function startFastApi(): Promise<void> {
  return new Promise((resolve) => {
    console.log('[Node.js] Starting FastAPI backend on port 8000...');
    
    // Iniciar backend con python3 uvicorn
    fastApiProcess = spawn('python3', [
      '-m', 'uvicorn',
      'backend.main:app',
      '--host', '127.0.0.1',
      '--port', String(FASTAPI_PORT)
    ], {
      cwd: __dirname,
      stdio: 'inherit'
    });

    fastApiProcess.on('error', (err) => {
      console.error('[FastAPI Process Error]:', err);
    });

    fastApiProcess.on('exit', (code, signal) => {
      console.log(`[FastAPI Process Exit] code: ${code}, signal: ${signal}`);
    });

    // Pequeño retardo para asegurar que el socket esté listo
    setTimeout(() => {
      console.log('[Node.js] FastAPI process spawned.');
      resolve();
    }, 1500);
  });
}

// Proxies a FastAPI
const apiProxy = createProxyMiddleware({
  target: `http://127.0.0.1:${FASTAPI_PORT}`,
  changeOrigin: true,
  logLevel: 'warn',
  onError(err, req, res) {
    console.error('[Proxy Error to FastAPI]:', err.message);
    res.status(502).json({
      error: 'FastAPI backend connection error',
      message: err.message
    });
  }
});

app.use('/api', apiProxy);
app.use('/docs', apiProxy);
app.use('/openapi.json', apiProxy);
app.use('/redoc', apiProxy);

// Archivos estáticos del frontend React compilado
const distPath = path.join(__dirname, 'dist');

if (fs.existsSync(distPath)) {
  console.log(`[Node.js] Serving static files from ${distPath}`);
  app.use(express.static(distPath));

  // SPA fallback
  app.get('*', (req, res) => {
    res.sendFile(path.join(distPath, 'index.html'));
  });
} else {
  // En caso de que dist aún no exista, responder amigablemente
  app.get('/', (req, res) => {
    res.send(`
      <!DOCTYPE html>
      <html>
        <head><title>MundoPeludo</title></head>
        <body style="font-family: sans-serif; padding: 40px; text-align: center;">
          <h1>🐾 MundoPeludo - Servidor Iniciado</h1>
          <p>Compilando frontend de React... Por favor recarga en unos momentos.</p>
          <p><a href="/docs">Ver documentación Swagger de FastAPI</a></p>
        </body>
      </html>
    `);
  });
}

// Limpieza de procesos al salir
function cleanup() {
  if (fastApiProcess) {
    console.log('[Node.js] Terminating FastAPI backend process...');
    fastApiProcess.kill();
    fastApiProcess = null;
  }
  process.exit(0);
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
process.on('exit', cleanup);

// Iniciar servidor Node.js
async function main() {
  await startFastApi();

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`====================================================`);
    console.log(`🐾 MundoPeludo corriendo en: http://0.0.0.0:${PORT}`);
    console.log(`⚡ FastAPI Documentación: http://0.0.0.0:${PORT}/docs`);
    console.log(`====================================================`);
  });
}

main().catch((err) => {
  console.error('Error al iniciar el servidor:', err);
});
