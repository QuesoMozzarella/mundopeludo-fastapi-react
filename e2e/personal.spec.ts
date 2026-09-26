import { expect, test } from '@playwright/test';
import { CUENTAS, elegirOpcion, fechaDentroDe, iniciarSesion, tarjetaCon, unico } from './ayudas';

test.describe('Personal de la clínica', () => {
  test('el administrador ve el panel con indicadores reales', async ({ page }) => {
    await iniciarSesion(page, CUENTAS.admin);
    await page.locator('#nav-dashboard').click();
    await expect(page.getByText(/Bienvenido\/a, Maurizio/)).toBeVisible();
    // Antes el panel decía "2 activas" fijo en el código.
    await expect(page.getByText(/\d+ activas/)).toBeVisible();
    await expect(page.locator('#nav-inventario')).toBeVisible();
  });

  test('el veterinario agenda y confirma una cita', async ({ page }) => {
    const motivo = unico('Vacuna e2e');
    await iniciarSesion(page, CUENTAS.veterinario);
    await page.locator('#nav-citas').click();
    await page.locator('#btn-nueva-cita').click();

    await elegirOpcion(page.locator('#select-cita-mascota'), 'Michi');
    await elegirOpcion(page.locator('#select-cita-servicio'), 'Vacunación');
    await elegirOpcion(page.locator('#select-cita-veterinario'), 'Andrea');
    await page.locator('#input-cita-fecha').fill(fechaDentroDe(8));
    await page.locator('#select-cita-hora').selectOption('11:15');
    await page.locator('#input-cita-motivo').fill(motivo);
    await page.locator('#btn-submit-cita').click();

    const tarjeta = tarjetaCon(page, motivo);
    await expect(tarjeta).toContainText('Pendiente');
    await tarjeta.locator('[id^="btn-confirmar-cita-"]').click();
    await expect(tarjeta).toContainText('Confirmada');
  });
});
