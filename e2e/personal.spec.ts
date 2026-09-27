import { expect, test, type Page } from '@playwright/test';
import {
  cerrarSesion,
  crearMascotaEnAdopcion,
  CUENTAS,
  elegirOpcion,
  iniciarSesion,
  laborableDentroDe,
  PNG_1PX,
  tarjetaCon,
  tokenDe,
  unico
} from './ayudas';

/** Cabecera de la solicitud de adopción: el título y su estado van juntos. */
function cabeceraSolicitud(page: Page, mascota: string) {
  return page.locator('h4', { hasText: `Postulación por ${mascota}` }).locator('..');
}

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
    await page.locator('#input-cita-fecha').fill(laborableDentroDe(8));
    await page.locator('#select-cita-hora').selectOption('11:30');
    await page.locator('#input-cita-motivo').fill(motivo);
    await page.locator('#btn-submit-cita').click();

    const tarjeta = tarjetaCon(page, motivo);
    await expect(tarjeta).toContainText('Pendiente');
    await tarjeta.locator('[id^="btn-confirmar-cita-"]').click();
    await expect(tarjeta).toContainText('Confirmada');
  });

  test('el veterinario registra una historia clínica y la tutora la ve', async ({ page }) => {
    const diagnostico = unico('Otitis externa leve e2e');
    await iniciarSesion(page, CUENTAS.veterinario);
    await page.locator('#nav-historial').click();
    await page.locator('#btn-nuevo-historial').click();

    await elegirOpcion(page.locator('#select-historial-mascota'), 'Luna');
    await page.locator('#textarea-historial-diagnostico').fill(diagnostico);
    await page.locator('#textarea-historial-tratamiento').fill('Gotas óticas cada 12 horas durante 7 días');
    await page.locator('#textarea-historial-observaciones').fill('Control en 10 días');
    await page.locator('#btn-submit-historial').click();
    await expect(page.getByText(diagnostico)).toBeVisible();
    await cerrarSesion(page);

    // Luna es de María: la ve en su historial, con el tratamiento indicado.
    await iniciarSesion(page, CUENTAS.cliente);
    await page.locator('#nav-historial').click();
    await expect(page.getByText(diagnostico)).toBeVisible();
    await expect(page.getByText('Gotas óticas cada 12 horas durante 7 días')).toBeVisible();
  });

  test('el administrador crea un producto con imagen, la cambia y lo desactiva', async ({ page }) => {
    const nombre = unico('Collar e2e');
    page.on('dialog', (dialogo) => dialogo.accept()); // confirmación de la baja
    await iniciarSesion(page, CUENTAS.admin);
    await page.locator('#nav-inventario').click();
    await page.locator('#btn-agregar-producto-inv').click();

    await page.locator('#input-prod-nombre').fill(nombre);
    await elegirOpcion(page.locator('#select-prod-categoria'), 'Accesorio');
    await page.locator('#input-prod-precio').fill('15990');

    // Un archivo que no es imagen se rechaza antes de enviarlo.
    await page.locator('#input-prod-imagen').setInputFiles({
      name: 'notas.txt', mimeType: 'text/plain', buffer: Buffer.from('hola')
    });
    await expect(page.getByText('La imagen debe ser JPG, PNG, WEBP o GIF.')).toBeVisible();

    await page.locator('#input-prod-imagen').setInputFiles({
      name: 'collar.png', mimeType: 'image/png', buffer: PNG_1PX
    });
    await expect(page.locator('#input-prod-imagen-previa')).toBeVisible();
    await page.locator('#btn-submit-nuevo-prod').click();

    const fila = page.locator('tr', { hasText: nombre });
    const miniatura = fila.getByRole('img', { name: nombre });
    await expect(miniatura).toHaveAttribute('src', /^\/api\/imagenes\/\d+$/);
    // La API sirve de verdad la imagen subida.
    await expect.poll(() => miniatura.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBe(1);
    const primera = await miniatura.getAttribute('src');

    // Editar: nuevo stock y otra imagen, que sustituye a la anterior.
    await fila.locator('[id^="btn-edit-prod-"]').click();
    await expect(page.locator('#input-edit-prod-imagen-previa')).toHaveAttribute('src', primera!);
    await page.locator('#input-edit-prod-stock').fill('3');
    await page.locator('#input-edit-prod-imagen').setInputFiles({
      name: 'collar-2.png', mimeType: 'image/png', buffer: PNG_1PX
    });
    await page.locator('#btn-submit-editar-prod').click();
    await expect(fila).toContainText('Bajo Stock');
    await expect(miniatura).not.toHaveAttribute('src', primera!);
    const anterior = await page.request.get(primera!);
    expect(anterior.status(), 'la imagen anterior se retira').toBe(404);

    // La tienda muestra la imagen nueva.
    const actual = await miniatura.getAttribute('src');
    await page.locator('#nav-tienda').click();
    await expect(page.getByRole('img', { name: nombre }).first()).toHaveAttribute('src', actual!);

    // Baja lógica: desaparece del inventario.
    await page.locator('#nav-inventario').click();
    await fila.locator('[id^="btn-delete-prod-"]').click();
    await expect(fila).toHaveCount(0);
  });

  test('aprobar una solicitud de adopción entrega la mascota a su nuevo tutor', async ({ page, request }) => {
    // Mascota propia: aprobar la de seed.py (Rocky) cambiaría los datos de otras pruebas.
    const mascota = await crearMascotaEnAdopcion(request, 'Canela');

    await iniciarSesion(page, CUENTAS.cliente);
    await page.locator('#nav-adopciones').click();
    await page.locator(`#btn-solicitar-adopcion-${mascota.id}`).click();
    await page.locator('#textarea-motivo-adopcion').fill('Vivo en casa con patio y trabajo desde casa.');
    await page.locator('#btn-enviar-solicitud-adopcion').click();
    await expect(cabeceraSolicitud(page, mascota.nombre)).toContainText('En Revisión');
    await cerrarSesion(page);

    await iniciarSesion(page, CUENTAS.admin);
    await page.locator('#nav-adopciones').click();
    await page.locator('#subtab-solicitudes-adopciones').click();
    await tarjetaCon(page, `Postulación por ${mascota.nombre}`)
      .locator('[id^="btn-aprobar-solicitud-"]')
      .click();
    await expect(cabeceraSolicitud(page, mascota.nombre)).toContainText('Aprobada');
    await page.locator('#subtab-catalogo-adopciones').click();
    await expect(page.locator(`#btn-solicitar-adopcion-${mascota.id}`)).toHaveCount(0);
    await cerrarSesion(page);

    // Ya es de María: aparece entre sus mascotas.
    await iniciarSesion(page, CUENTAS.cliente);
    await page.locator('#nav-mascotas').click();
    await expect(page.getByRole('heading', { name: mascota.nombre })).toBeVisible();
  });

  test('rechazar una solicitud de adopción deja la mascota disponible', async ({ page, request }) => {
    const mascota = await crearMascotaEnAdopcion(request, 'Pimienta');
    // La postulación se prepara por la API: la pantalla ya la cubre la prueba anterior.
    const { headers, usuario } = await tokenDe(request, CUENTAS.cliente);
    const solicitud = await request.post('/api/adopciones/solicitudes', {
      headers,
      data: { mascota_id: mascota.id, cliente_id: usuario.id, notas_cliente: 'Me encantaría adoptarla.' }
    });
    expect(solicitud.status(), await solicitud.text()).toBe(201);

    await iniciarSesion(page, CUENTAS.veterinario);
    await page.locator('#nav-adopciones').click();
    await page.locator('#subtab-solicitudes-adopciones').click();
    const tarjeta = tarjetaCon(page, `Postulación por ${mascota.nombre}`);
    await tarjeta.getByPlaceholder('Notas de revisión (opcional)...').fill('Falta visita al domicilio');
    await tarjeta.locator('[id^="btn-rechazar-solicitud-"]').click();

    await expect(cabeceraSolicitud(page, mascota.nombre)).toContainText('Rechazada');
    await expect(page.getByText('Falta visita al domicilio')).toBeVisible();
    await page.locator('#subtab-catalogo-adopciones').click();
    await expect(page.locator(`#btn-solicitar-adopcion-${mascota.id}`)).toBeVisible();
  });
});
