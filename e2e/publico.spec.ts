import { expect, test } from '@playwright/test';

// Lo que en el Django era público (index, adopciones, tienda) se ve sin sesión.
test.describe('Visitante sin sesión', () => {
  test('la página de inicio es pública y muestra datos reales', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Bienvenido a Mundo Peludo' })).toBeVisible();
    await expect(page.locator('#btn-iniciar-sesion')).toBeVisible();
    // Servicios y productos vienen de la API (sembrados por seed.py).
    await expect(page.getByText('Consulta General').first()).toBeVisible();
    await expect(page.getByText('Juguete Mordedor Hueso').first()).toBeVisible();
    // Precio y duración de los servicios (los recuperó la API; seed.py los rellena).
    await expect(page.getByText('⏱️ 120 minutos')).toBeVisible();
    await expect(page.getByText('$150.000')).toBeVisible();
  });

  test('adopciones se ven sin iniciar sesión', async ({ page }) => {
    await page.goto('/');
    await page.locator('#nav-adopciones').click();
    await expect(page.getByRole('heading', { name: /Programa de Adopciones/ })).toBeVisible();
    await expect(page.getByText('Rocky').first()).toBeVisible();
    // La gestión de solicitudes es privada.
    await expect(page.locator('#subtab-solicitudes-adopciones')).toHaveCount(0);
  });

  test('postular a una adopción pide iniciar sesión', async ({ page }) => {
    await page.goto('/');
    await page.locator('#nav-adopciones').click();
    await page.locator('[id^="btn-solicitar-adopcion-"]').first().click();
    await expect(page.locator('#login-email')).toBeVisible();
  });

  test('la tienda se ve y el carrito pide iniciar sesión para pagar', async ({ page }) => {
    await page.goto('/');
    await page.locator('#nav-tienda').click();
    await expect(page.getByRole('heading', { name: /Farmacia y Tienda/ })).toBeVisible();
    await page.locator('[id^="btn-add-cart-"]').first().click();

    await page.locator('#btn-open-cart').click();
    const pagar = page.locator('#btn-confirmar-compra');
    await expect(pagar).toHaveText(/Inicia sesión para pagar/);
    await pagar.click();
    await expect(page.locator('#login-email')).toBeVisible();
  });

  for (const seccion of ['citas', 'mascotas', 'historial', 'dashboard']) {
    test(`la sección privada "${seccion}" pide iniciar sesión`, async ({ page }) => {
      await page.goto('/');
      await page.locator(`#nav-${seccion}`).click();
      await expect(page.locator('#login-email')).toBeVisible();
      await page.locator('#btn-volver-inicio').click();
      await expect(page.getByRole('heading', { name: 'Bienvenido a Mundo Peludo' })).toBeVisible();
    });
  }
});
