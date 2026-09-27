# Estado del proyecto y pendientes

Última actualización: 26-09-2026. Punto de partida para retomar el trabajo.

## Hoja de ruta

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Repositorios tipados con puertos; roles con enum (SOLID) | ✅ Hecha (`c5a9f1f`) |
| 2 | El dominio recibe el reloj por el puerto `Clock` | ✅ Hecha (`4a657cf`) |
| 3 | Casos de uso inyectados (3a) y comandos tipados `*Cmd` (3b) | ✅ Hecha (`709f5ab`, `dac304e`) |
| 4 | Un caso de uso por intención | ✅ Hecha (`1edf68d`) |
| 5 | Cierre de la primera lista de pendientes: imágenes de producto por archivo, precio y duración de servicios, `MP_EMAIL_REDIRIGIR_A`, 7 escenarios e2e nuevos, CI en GitHub Actions, base antigua fuera de git | ✅ Hecha, **sin commit** |
| 6 | Agenda: citas canceladas que ocupan hueco (pendiente 2), horas reales en el formulario de citas (4), pantalla de servicios (3) | ⏳ Siguiente |
| 7 | Despliegue: primera ejecución de CI verificada (1) y lista de producción (5) | ⏳ Por hacer |

Las fases 6 y 7 son una propuesta de orden; los números entre paréntesis
remiten a la sección *Pendientes*.

## Dónde estamos

- **Backend (FastAPI + SQLite, arquitectura hexagonal):** completo. Las cuatro
  fases de hexagonal / clean code / SOLID están cerradas:
  1. Repositorios tipados con puertos; roles con enum.
  2. El dominio no lee el reloj: lo recibe por el puerto `Clock`.
  3. Casos de uso inyectados en los routers (`interfaces/http/casos.py`) y
     comandos tipados (`*Cmd`) en lugar de `dict`.
  4. Un caso de uso por intención (`Consultar*`, `Crear*`, `Eliminar*`…).
  Convenciones: [`backend/README.md`](./backend/README.md#convenciones-de-la-capa-de-aplicación).
- **Servicios con precio y duración:** se recuperaron los campos que quitó la
  migración 0007 del Django. La duración decide la agenda: cada cita ocupa lo
  que dura su servicio y no puede pisar otra ni salirse de la franja del
  veterinario. Las bases existentes se migran solas.
- **Seguridad:** API cerrada por defecto (`MP_REQUIRE_AUTH=1`), permisos por
  rol y por propietario, bloqueo tras 5 logins fallidos, códigos de
  recuperación con límite de intentos, primer administrador por consola
  (`python backend/crear_superusuario.py`).
- **Correo (SMTP):** código de recuperación y avisos de cita confirmada, cita
  cancelada e historia clínica al tutor, enviados tras el commit y en segundo
  plano. En desarrollo, `MP_EMAIL_REDIRIGIR_A` manda todos a una sola
  dirección (prohibida en producción).
- **Frontend (React):** login con JWT; inicio, adopciones y tienda públicos;
  el resto pide sesión. El inventario sube las imágenes de producto como
  archivo (con vista previa) y al cambiarla retira la anterior.
- **Pruebas:** 40 de la API (`python backend/tests/test_api.py`) y 28
  escenarios e2e con Playwright (`npm run test:e2e`; `E2E_HEADLESS=1` sin
  ventana). GitHub Actions las ejecuta en cada push a `main` y en cada PR
  (`.github/workflows/pruebas.yml`).
- **Repositorio:** `backend/mundopeludo.db` (la base anterior) ya no se versiona.

## Pendientes

### 1. Comprobar la primera ejecución de CI
El workflow está escrito pero todavía no ha corrido en GitHub. Tras el primer
push, revisar la pestaña *Actions*: si las e2e fallan allí y no en local, las
trazas quedan en el artefacto `trazas-e2e`.

### 2. Las citas canceladas siguen ocupando la agenda
`ReglasDeAgenda.horario` compara con todas las citas del día del veterinario,
también las **canceladas**, así que una cita anulada bloquea su hueco. Ya pasaba
antes; con la duración real de los servicios (una cirugía ocupa 2 horas) se nota
más. Probablemente haya que excluir el estado `Cancelada` en
`listar_por_veterinario_y_dia` o en la regla.

### 3. Gestión de servicios desde la app
Precio y duración sólo se editan por la API (`POST/PUT /api/servicios`, o desde
Swagger en `/docs`): el frontend no tiene pantalla de servicios.

### 4. Horas del formulario de citas
El formulario ofrece horas fijas (09:00, 09:45, 10:30…) en vez de preguntar a
`GET /api/veterinarios/{id}/agenda?servicio_id=`, que ya devuelve los huecos
donde cabe el servicio elegido. Requiere que los veterinarios tengan
disponibilidad declarada: `seed.py` no crea ninguna.

### 5. Antes de desplegar
- `MP_ENV=produccion`: la app exige entonces `MP_SECRET_KEY` propia y rechaza
  `MP_EMAIL_REDIRIGIR_A`.
- `MP_CORS_ORIGINS` con el dominio real en lugar de `*`.
- No usar `seed.py`: sus cuentas tienen una contraseña conocida.
- Crear el administrador con `crear_superusuario.py`.
- `backend/mundopeludo.db` salió del índice, pero sigue en el historial de git;
  si tuviera datos sensibles habría que reescribir el historial.
