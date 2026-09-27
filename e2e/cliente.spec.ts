import { expect, test } from '@playwright/test';
import { CUENTAS, elegirOpcion, fechaDentroDe, iniciarSesion, nombreUnico, tarjetaCon, unico } from './ayudas';

test.describe('Cliente (María, de seed.py)', () => {
  test.beforeEach(async ({ page }) => {
    await iniciarSesion(page, CUENTAS.cliente);
  });

  test('ve sus citas con la fecha legible', async ({ page }) => {
    await page.locator('#nav-citas').click();
    await expect(page.getByText('Luna').first()).toBeVisible();
    // "lun, 28 sept 2026, 10:30 a. m." y nunca el ISO crudo de la API.
    await expect(page.getByText(/\d{4}, \d{1,2}:\d{2}\s[ap]\.\s?m\./).first()).toBeVisible();
    await expect(page.getByText(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/)).toHaveCount(0);
  });

  test('agenda una cita y aparece pendiente', async ({ page }) => {
    const motivo = unico('Control e2e');
    await page.locator('#nav-citas').click();
    await page.locator('#btn-nueva-cita').click();

    await elegirOpcion(page.locator('#select-cita-mascota'), 'Luna');
    await elegirOpcion(page.locator('#select-cita-servicio'), 'Consulta General');
    await elegirOpcion(page.locator('#select-cita-veterinario'), 'Andrea');
    await page.locator('#input-cita-fecha').fill(fechaDentroDe(6));
    await page.locator('#select-cita-hora').selectOption('10:30');
    await page.locator('#input-cita-motivo').fill(motivo);
    await page.locator('#btn-submit-cita').click();

    const tarjeta = tarjetaCon(page, motivo);
    await expect(tarjeta).toBeVisible();
    await expect(tarjeta).toContainText('Pendiente');
  });

  test('compra en la tienda y recibe el número de pedido', async ({ page }) => {
    await page.locator('#nav-tienda').click();
    await page.locator('[id^="btn-add-cart-"]').first().click();
    await page.locator('#btn-open-cart').click();
    await page.locator('#input-cart-direccion').fill('Retiro en clínica');
    await page.locator('#btn-confirmar-compra').click();

    await expect(page.getByText('¡Pedido Confirmado con Éxito!')).toBeVisible();
    await expect(page.getByText(/#PED-\d+/)).toBeVisible();
  });

  test('postula a una adopción y la solicitud muestra su teléfono', async ({ page }) => {
    await page.locator('#nav-adopciones').click();
    await page.locator('[id^="btn-solicitar-adopcion-"]').first().click();
    await page.locator('#textarea-motivo-adopcion').fill('Tengo patio grande y experiencia con perros.');
    await page.locator('#btn-enviar-solicitud-adopcion').click();

    // Antes siempre salía "Tel: No indicado": la API no enviaba el teléfono.
    await expect(page.getByText('Tel: +56 9 5432 1098').first()).toBeVisible();
  });

  test('registra una mascota con descripción e imagen y las ve en su ficha', async ({ page }) => {
    const nombre = nombreUnico('Toby');
    // Imagen servida por la propia app: no depende de internet.
    const imagen = new URL('/img/gato.jpg', page.url()).toString();
    await page.locator('#nav-mascotas').click();
    await page.locator('#btn-registrar-mascota').click();

    await page.locator('#input-mascota-nombre').fill(nombre);
    await page.locator('#input-mascota-raza').fill('Beagle');
    await page.locator('#input-mascota-color').fill('tricolor');
    await page.locator('#input-mascota-foto').fill(imagen);
    await page.locator('#textarea-mascota-descripcion').fill('Alérgico al pollo, muy sociable.');
    await page.locator('#btn-submit-mascota').click();

    await tarjetaCon(page, nombre).locator('[id^="btn-ver-ficha-"]').click();
    await expect(page.getByText('Observaciones de la Mascota: Alérgico al pollo, muy sociable.')).toBeVisible();
    await expect(page.getByRole('img', { name: nombre }).last()).toHaveAttribute('src', imagen);
  });

  test('ve precio y duración del servicio en su cita', async ({ page }) => {
    await page.locator('#nav-citas').click();
    // La cita de seed.py es una Consulta General: 30 min y $25.000.
    await expect(page.getByText(/Consulta General\s*\(30 min · \$25\.000\)/).first()).toBeVisible();
  });

  test('no ve las secciones del personal', async ({ page }) => {
    await expect(page.locator('#nav-inventario')).toHaveCount(0);
  });
});
