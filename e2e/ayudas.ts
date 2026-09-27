import { expect, type APIRequestContext, type Locator, type Page } from '@playwright/test';

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

/** Acepta el diálogo de confirmación propio de la app. */
export async function confirmarDialogo(page: Page) {
  await page.locator('#btn-confirmar-dialogo').click();
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
    .locator('article, div')
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

/**
 * Primer día laborable (lunes a sábado, el horario de seed.py) a partir de
 * dentro de `dias` días.
 */
export function laborableDentroDe(dias: number): string {
  const d = new Date();
  d.setDate(d.getDate() + dias);
  return fechaDentroDe(d.getDay() === 0 ? dias + 1 : dias);
}

/** Próximo domingo (nunca hoy): seed.py no da horario ese día. */
export function proximoDomingo(): string {
  const hoy = new Date().getDay();
  return fechaDentroDe(hoy === 0 ? 7 : 7 - hoy);
}

/** Texto único por ejecución, para encontrar lo que crea cada prueba. */
export function unico(prefijo: string): string {
  return `${prefijo} ${Date.now().toString(36)}`;
}

/**
 * Como `unico`, pero sólo con letras y en formato título: el nombre de una
 * mascota no admite números y el backend lo normaliza con `title()`.
 */
export function nombreUnico(prefijo: string): string {
  const letras = Date.now()
    .toString(36)
    .replace(/\d/g, (d) => 'abcdefghij'[Number(d)]);
  return `${prefijo} ${letras[0].toUpperCase()}${letras.slice(1)}`;
}

/** Registra una cuenta de cliente desde el formulario; queda con la sesión abierta. */
export async function registrarCliente(page: Page, email: string, nombre: string, clave = 'ClaveSegura123') {
  await abrirLogin(page);
  await page.locator('#tab-registro').click();
  await page.locator('#reg-nombre').fill(nombre);
  await page.locator('#reg-apellidos').fill('Automática');
  await page.locator('#reg-email').fill(email);
  await page.locator('#reg-password').fill(clave);
  await page.locator('#reg-confirmacion').fill(clave);
  await page.locator('#btn-registro').click();
  await expect(page.locator('#btn-user-role-menu')).toContainText(nombre);
}

/** PNG de 1x1 píxel, para subir como imagen de producto. */
export const PNG_1PX = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
  'base64'
);

// ---------------------------------------------------------------------------
// Preparación por la API: deja los datos que una prueba necesita sin pasar
// por pantallas que no son las que se están probando.
// ---------------------------------------------------------------------------
export async function tokenDe(request: APIRequestContext, email: string, clave: string = CLAVE) {
  const r = await request.post('/api/auth/login', { data: { email, password: clave } });
  expect(r.ok(), await r.text()).toBeTruthy();
  const { access_token, usuario } = await r.json();
  return { headers: { Authorization: `Bearer ${access_token}` }, usuario };
}

/** Mascota nueva en adopción, sin tutor. Devuelve su id y su nombre. */
export async function crearMascotaEnAdopcion(request: APIRequestContext, prefijo = 'Canela') {
  const { headers } = await tokenDe(request, CUENTAS.admin);
  const especies = await (await request.get('/api/especies')).json();
  const nombre = nombreUnico(prefijo);
  const r = await request.post('/api/mascotas', {
    headers,
    data: {
      especie_id: especies[0].id,
      nombre,
      sexo: 'Hembra',
      color: 'canela',
      peso: 9,
      estado_adopcion: 'en_adopcion'
    }
  });
  expect(r.status(), await r.text()).toBe(201);
  return { id: (await r.json()).id as number, nombre };
}
