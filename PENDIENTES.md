# Estado del proyecto y pendientes

Última actualización: 26-09-2026. Punto de partida para retomar el trabajo.

## Hoja de ruta

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Repositorios tipados con puertos; roles con enum (SOLID) | ✅ Hecha (`c5a9f1f`) |
| 2 | El dominio recibe el reloj por el puerto `Clock` | ✅ Hecha (`4a657cf`) |
| 3 | Casos de uso inyectados (3a) y comandos tipados `*Cmd` (3b) | ✅ Hecha (`709f5ab`, `dac304e`) |
| 4 | Un caso de uso por intención | ✅ Hecha (`1edf68d`) |
| 5 | Cierre de la primera lista de pendientes: imágenes de producto por archivo, precio y duración de servicios, `MP_EMAIL_REDIRIGIR_A`, 7 escenarios e2e nuevos, CI en GitHub Actions, base antigua fuera de git | ✅ Hecha (`9db066c` … `596e492`) |
| 6 | Agenda: las citas canceladas liberan su hueco, sin horario declarado no se agenda, el formulario de citas ofrece las horas libres reales y pantalla de *Servicios y horarios* | ✅ Hecha |
| 7 | Despliegue: primera ejecución de CI verificada (1) y lista de producción (2) | ⏳ Siguiente |

Los números entre paréntesis remiten a la sección *Pendientes*.

## Dónde estamos

- **Backend (FastAPI + SQLite, arquitectura hexagonal):** completo. Las cuatro
  fases de hexagonal / clean code / SOLID están cerradas:
  1. Repositorios tipados con puertos; roles con enum.
  2. El dominio no lee el reloj: lo recibe por el puerto `Clock`.
  3. Casos de uso inyectados en los routers (`interfaces/http/casos.py`) y
     comandos tipados (`*Cmd`) en lugar de `dict`.
  4. Un caso de uso por intención (`Consultar*`, `Crear*`, `Eliminar*`…).
  Convenciones: [`backend/README.md`](./backend/README.md#convenciones-de-la-capa-de-aplicación).
- **Agenda:** cada servicio tiene precio y duración (los que quitó la
  migración 0007 del Django). Una cita ocupa lo que dura su servicio, no puede
  pisar otra activa (las canceladas no cuentan) ni salirse del horario del
  veterinario, y **un veterinario sin horario declarado no recibe citas**,
  como en el Django. Reactivar una cita cancelada sólo se permite si su hueco
  sigue libre. El formulario de citas pide a la API las horas libres del
  veterinario ese día para el servicio elegido.
- **Servicios y horarios:** pantalla para el personal. El administrador crea,
  edita, activa/desactiva y elimina servicios (precio, duración, quién los
  presta) y gestiona el horario de todos; cada veterinario, sólo el suyo.
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
- **Pruebas:** 44 de la API (`python backend/tests/test_api.py`) y 33
  escenarios e2e con Playwright (`npm run test:e2e`; `E2E_HEADLESS=1` sin
  ventana). GitHub Actions las ejecuta en cada push a `main` y en cada PR
  (`.github/workflows/pruebas.yml`).
- **Repositorio:** `backend/mundopeludo.db` (la base anterior) ya no se versiona.

> **Bases existentes:** desde la fase 6, un veterinario sin franjas no tiene
> horas libres. Tras actualizar, declara el horario de cada veterinario en
> *Servicios y horarios* (o vuelve a crear la base con `seed.py`, que ya lo trae).

## Pendientes

### 1. Comprobar la primera ejecución de CI
El workflow está escrito pero todavía no ha corrido en GitHub. Tras el primer
push, revisar la pestaña *Actions*: si las e2e fallan allí y no en local, las
trazas quedan en el artefacto `trazas-e2e`.

### 2. Antes de desplegar
- `MP_ENV=produccion`: la app exige entonces `MP_SECRET_KEY` propia y rechaza
  `MP_EMAIL_REDIRIGIR_A`.
- `MP_CORS_ORIGINS` con el dominio real en lugar de `*`.
- No usar `seed.py`: sus cuentas tienen una contraseña conocida.
- Crear el administrador con `crear_superusuario.py` y declarar el horario de
  cada veterinario.
- `backend/mundopeludo.db` salió del índice, pero sigue en el historial de git;
  si tuviera datos sensibles habría que reescribir el historial.

### 3. Ideas que quedaron fuera (sin prioridad)
- Especialidades de un servicio: la API las admite, la pantalla no las edita.
- Excepciones al horario (vacaciones, festivos): hoy sólo hay franjas semanales.
- Una cita que cruza la medianoche sólo se compara con las de su propio día.
