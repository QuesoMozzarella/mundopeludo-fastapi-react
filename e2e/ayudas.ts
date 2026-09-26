import { expect, type Locator, type Page } from '@playwright/test';

// Cuentas que crea backend/seed.py (base de pruebas; nunca la de desarrollo).
export const CLAVE = 'mundopeludo2025';
export const CUENTAS = {
  admin: 'admin@mundopeludo.com',
  veterinario: 'vet.garcia@mundopeludo.com',
  cliente: 'maria.gonzalez@example.com',
  // Sólo la usa la prueba de contraseña errónea: así los fallos no bloquean
  // (5 intentos -> 15 min) a las cuentas que usan las demás pruebas.
  contrasenaErronea: 'carlos.ramirez@example.com'
} as const;

export async function abrirLogin(page: Page) {
  await page.goto('/');
  await page.locator('#btn-iniciar-sesion').click();
  await expect(page.locator('#login-email')).toBeVisible();
}

export async function rellenarLogin(page: Page, email: string, clave: string = CLAVE) {
  await page.locator('#login-email').fill(email);
  await page.locator('#login-password').fill(clave);
  await page.locator('#btn-login').click();
}

export async function iniciarSesion(page: Page, email: string) {
  await abrirLogin(page);
  await rellenarLogin(page, email);
  await expect(page.locator('#btn-user-role-menu')).toBeVisible();
}

export async function cerrarSesion(page: Page) {
  await page.locator('#btn-user-role-menu').click();
  await page.locator('#btn-cerrar-sesion').click();
  await expect(page.locator('#btn-iniciar-sesion')).toBeVisible();
}

/** Elige en un <select> la opción cuyo texto contiene `texto`. */
export async function elegirOpcion(select: Locator, texto: string) {
  const valor = await select.locator('option', { hasText: texto }).first().getAttribute('value');
  expect(valor, `no hay opción con "${texto}"`).not.toBeNull();
  await select.selectOption(valor!);
}

/** Tarjeta (el contenedor más interno con botones) que contiene `texto`. */
export function tarjetaCon(page: Page, texto: string): Locator {
  return page
    .locator('div')
    .filter({ has: page.getByText(texto, { exact: true }) })
    .filter({ has: page.locator('button') })
    .last();
}

/** Fecha local dentro de `dias` días, en el formato de un <input type="date">. */
export function fechaDentroDe(dias: number): string {
  const d = new Date();
  d.setDate(d.getDate() + dias);
  const dos = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${dos(d.getMonth() + 1)}-${dos(d.getDate())}`;
}

/** Texto único por ejecución, para encontrar lo que crea cada prueba. */
export function unico(prefijo: string): string {
  return `${prefijo} ${Date.now().toString(36)}`;
}
