import { expect, test, type Page } from '@playwright/test';
import { CUENTAS, elegirOpcion, iniciarSesion, laborableDentroDe, proximoDomingo, unico } from './ayudas';

async function abrirFormularioDeCita(page: Page) {
  await page.locator('#nav-citas').click();
  await page.locator('#btn-nueva-cita').click();
}

test.describe('Servicios y horarios', () => {
  test('el administrador crea un servicio, se ofrece al agendar y al desactivarlo deja de ofrecerse', async ({ page }) => {
    const nombre = unico('Ecografía e2e');
    await iniciarSesion(page, CUENTAS.admin);
    await page.locator('#nav-servicios').click();
    await page.locator('#btn-nuevo-servicio').click();

    await page.locator('#input-servicio-nombre').fill(nombre);
    await page.locator('#textarea-servicio-descripcion').fill('Ecografía abdominal');
    await page.locator('#input-servicio-precio').fill('40000');
    await page.locator('#input-servicio-duracion').fill('60');
    // Sólo lo presta Felipe (el segundo veterinario de seed.py).
    await page.locator('label', { hasText: 'Felipe' }).locator('input[type="checkbox"]').check();
    await page.locator('#btn-guardar-servicio').click();

    const fila = page.locator('tr', { hasText: nombre });
    await expect(fila).toContainText('$40.000');
    await expect(fila).toContainText('60 min');
    await expect(fila).toContainText('Felipe Martínez Soto');
    await expect(fila).toContainText('Activo');

    // Al agendar, el servicio aparece y sólo con quien lo presta.
    await abrirFormularioDeCita(page);
    await elegirOpcion(page.locator('#select-cita-servicio'), nombre);
    await expect(page.locator('#select-cita-servicio')).toContainText(`${nombre} - $40.000 (60 min)`);
    await expect(page.locator('#select-cita-veterinario option')).toHaveCount(1);
    await expect(page.locator('#select-cita-veterinario')).toContainText('Felipe');
    await page.locator('#btn-cerrar-modal-cita').click();

    // Desactivado, ya no se ofrece.
    await page.locator('#nav-servicios').click();
    await fila.locator('[id^="btn-estado-servicio-"]').click();
    await expect(fila).toContainText('Inactivo');
    await abrirFormularioDeCita(page);
    await expect(page.locator('#select-cita-servicio')).not.toContainText(nombre);
  });

  test('el horario del veterinario decide las horas del formulario de citas', async ({ page }) => {
    const domingo = proximoDomingo();
    await iniciarSesion(page, CUENTAS.admin);

    // seed.py no da horario los domingos: no hay ninguna hora.
    await abrirFormularioDeCita(page);
    await elegirOpcion(page.locator('#select-cita-servicio'), 'Consulta General');
    await elegirOpcion(page.locator('#select-cita-veterinario'), 'Andrea');
    await page.locator('#input-cita-fecha').fill(domingo);
    await expect(page.locator('#aviso-sin-horas')).toBeVisible();
    await expect(page.locator('#btn-submit-cita')).toBeDisabled();
    await page.locator('#btn-cerrar-modal-cita').click();

    // Una franja de domingo de 10:00 a 11:00 para Andrea.
    await page.locator('#nav-servicios').click();
    await elegirOpcion(page.locator('#select-horario-veterinario'), 'Andrea');
    await expect(page.locator('#dia-horario-0')).toContainText('09:00–13:00');
    await page.locator('#select-franja-dia').selectOption('6');
    await page.locator('#input-franja-inicio').fill('10:00');
    await page.locator('#input-franja-fin').fill('11:00');
    await page.locator('#btn-agregar-franja').click();
    const dia = page.locator('#dia-horario-6');
    await expect(dia).toContainText('10:00–11:00');

    // Una franja que pisa otra la rechaza la API y se explica.
    await page.locator('#input-franja-inicio').fill('10:30');
    await page.locator('#input-franja-fin').fill('12:00');
    await page.locator('#btn-agregar-franja').click();
    await expect(page.getByRole('alert')).toContainText('se solapa');

    // Ahora el formulario ofrece las horas donde cabe una consulta de 30 min...
    await abrirFormularioDeCita(page);
    await elegirOpcion(page.locator('#select-cita-servicio'), 'Consulta General');
    await elegirOpcion(page.locator('#select-cita-veterinario'), 'Andrea');
    await page.locator('#input-cita-fecha').fill(domingo);
    await expect(page.locator('#select-cita-hora option')).toHaveText(['10:00 hrs', '10:30 hrs']);
    // ...y ninguna para una cirugía, que dura 2 horas.
    await elegirOpcion(page.locator('#select-cita-servicio'), 'Cirugía');
    await expect(page.locator('#aviso-sin-horas')).toBeVisible();
    await page.locator('#btn-cerrar-modal-cita').click();

    // Se deja el horario como estaba.
    await page.locator('#nav-servicios').click();
    await elegirOpcion(page.locator('#select-horario-veterinario'), 'Andrea');
    await dia.locator('[id^="btn-quitar-franja-"]').click();
    await expect(dia).toContainText('No atiende');
  });

  test('la hora ocupada deja de ofrecerse', async ({ page }) => {
    const fecha = laborableDentroDe(10);
    await iniciarSesion(page, CUENTAS.veterinario);
    await abrirFormularioDeCita(page);
    await elegirOpcion(page.locator('#select-cita-mascota'), 'Michi');
    await elegirOpcion(page.locator('#select-cita-servicio'), 'Vacunación');
    await elegirOpcion(page.locator('#select-cita-veterinario'), 'Felipe');
    await page.locator('#input-cita-fecha').fill(fecha);
    const hora = page.locator('#select-cita-hora');
    await expect(hora.locator('option[value="09:00"]')).toHaveCount(1);
    await hora.selectOption('09:00');
    await page.locator('#input-cita-motivo').fill(unico('Refuerzo e2e'));
    await page.locator('#btn-submit-cita').click();

    await page.locator('#btn-nueva-cita').click();
    await elegirOpcion(page.locator('#select-cita-servicio'), 'Vacunación');
    await elegirOpcion(page.locator('#select-cita-veterinario'), 'Felipe');
    await page.locator('#input-cita-fecha').fill(fecha);
    await expect(hora.locator('option[value="09:30"]')).toHaveCount(1);
    await expect(hora.locator('option[value="09:00"]')).toHaveCount(0);
  });

  test('el veterinario ve los servicios sin editarlos y sólo gestiona su horario', async ({ page }) => {
    await iniciarSesion(page, CUENTAS.veterinario);
    await page.locator('#nav-servicios').click();
    await expect(page.locator('tr', { hasText: 'Consulta General' })).toContainText('$25.000');
    await expect(page.locator('#btn-nuevo-servicio')).toHaveCount(0);
    await expect(page.locator('[id^="btn-editar-servicio-"]')).toHaveCount(0);

    const selector = page.locator('#select-horario-veterinario');
    await expect(selector).toBeDisabled();
    await expect(selector).toContainText('Andrea');
    await expect(page.locator('#dia-horario-5')).toContainText('15:00–19:00');
  });

  test('un cliente no ve la sección', async ({ page }) => {
    await iniciarSesion(page, CUENTAS.cliente);
    await expect(page.locator('#nav-servicios')).toHaveCount(0);
  });
});
