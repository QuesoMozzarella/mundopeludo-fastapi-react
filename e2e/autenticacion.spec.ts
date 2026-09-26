import { expect, test } from '@playwright/test';
import { abrirLogin, cerrarSesion, CUENTAS, iniciarSesion, rellenarLogin } from './ayudas';

test.describe('Autenticación', () => {
  test('una contraseña errónea muestra un error', async ({ page }) => {
    await abrirLogin(page);
    await rellenarLogin(page, CUENTAS.contrasenaErronea, 'claveIncorrecta1');
    await expect(page.getByRole('alert')).toContainText('Correo o contraseña incorrectos');
    await expect(page.locator('#btn-user-role-menu')).toHaveCount(0);
  });

  test('inicia y cierra sesión', async ({ page }) => {
    await iniciarSesion(page, CUENTAS.cliente);
    await expect(page.locator('#btn-user-role-menu')).toContainText('María');
    await cerrarSesion(page);
    await expect(page.getByRole('heading', { name: 'Bienvenido a Mundo Peludo' })).toBeVisible();
  });

  test('la sesión sobrevive a recargar la página', async ({ page }) => {
    await iniciarSesion(page, CUENTAS.cliente);
    await page.reload();
    await expect(page.locator('#btn-user-role-menu')).toContainText('María');
  });

  test('tras iniciar sesión se abre la sección que se pidió', async ({ page }) => {
    await page.goto('/');
    await page.locator('#nav-citas').click();
    await rellenarLogin(page, CUENTAS.cliente);
    await expect(page.getByRole('heading', { name: 'Gestión de Citas Médicas' })).toBeVisible();
  });

  test('el registro crea una cuenta de cliente y entra con ella', async ({ page }) => {
    const email = `e2e-${Date.now()}@test.com`;
    await abrirLogin(page);
    await page.locator('#tab-registro').click();
    await page.locator('#reg-nombre').fill('Prueba');
    await page.locator('#reg-apellidos').fill('Automática');
    await page.locator('#reg-email').fill(email);
    await page.locator('#reg-password').fill('ClaveSegura123');
    await page.locator('#reg-confirmacion').fill('ClaveSegura123');
    await page.locator('#btn-registro').click();

    const menu = page.locator('#btn-user-role-menu');
    await expect(menu).toContainText('Prueba');
    await expect(menu).toContainText('cliente');
  });

  test('el registro avisa si las contraseñas no coinciden', async ({ page }) => {
    await abrirLogin(page);
    await page.locator('#tab-registro').click();
    await page.locator('#reg-nombre').fill('Prueba');
    await page.locator('#reg-apellidos').fill('Automática');
    await page.locator('#reg-email').fill(`e2e-mal-${Date.now()}@test.com`);
    await page.locator('#reg-password').fill('ClaveSegura123');
    await page.locator('#reg-confirmacion').fill('OtraClave1234');
    await page.locator('#btn-registro').click();
    await expect(page.getByRole('alert')).toContainText('Las contraseñas no coinciden');
  });
});
