import { existsSync } from 'node:fs';
import { defineConfig } from '@playwright/test';

/**
 * Navegador ya instalado en el equipo (no se descarga ninguno):
 * 1. E2E_NAVEGADOR, si se define, con la ruta al ejecutable;
 * 2. Brave o Chrome en su ruta habitual de cualquier unidad;
 * 3. si no, Microsoft Edge, que viene con Windows.
 */
function navegador() {
  if (process.env.E2E_NAVEGADOR) return { launchOptions: { executablePath: process.env.E2E_NAVEGADOR } };
  const unidades = ['C', 'D', 'P'];
  const rutas = unidades.flatMap((u) => [
    `${u}:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe`,
    `${u}:/Program Files/Google/Chrome/Application/chrome.exe`,
    `${u}:/Program Files (x86)/Google/Chrome/Application/chrome.exe`
  ]);
  const encontrado = rutas.find((ruta) => existsSync(ruta));
  return encontrado ? { launchOptions: { executablePath: encontrado } } : { channel: 'msedge' };
}

// Puertos propios de las pruebas: no chocan con el entorno de desarrollo (3000/8001).
const PUERTO_WEB = 3100;
const PUERTO_API = 8011;

export default defineConfig({
  testDir: './e2e',
  // Todas las pruebas comparten la misma base sembrada: en serie, una a una.
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  reporter: [['list']],
  use: {
    baseURL: `http://localhost:${PUERTO_WEB}`,
    headless: false,
    ...navegador(),
    viewport: { width: 1366, height: 800 },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure'
  },
  webServer: [
    {
      command: 'python e2e/backend_e2e.py',
      url: `http://127.0.0.1:${PUERTO_API}/api/health`,
      env: { E2E_PUERTO_API: String(PUERTO_API) },
      reuseExistingServer: false,
      timeout: 90_000
    },
    {
      command: `npx vite --port ${PUERTO_WEB} --strictPort`,
      url: `http://localhost:${PUERTO_WEB}`,
      // El frontend apunta al backend de pruebas y no arranca otro por su cuenta.
      env: { FASTAPI_PORT: String(PUERTO_API), FASTAPI_EXTERNO: '1' },
      reuseExistingServer: false,
      timeout: 90_000
    }
  ]
});
