# Estado del proyecto y pendientes

Última actualización: 26-09-2026. Punto de partida para retomar el trabajo.

## Dónde estamos

- **Backend (FastAPI + SQLite, arquitectura hexagonal):** completo. Las cuatro
  fases de hexagonal / clean code / SOLID están cerradas:
  1. Repositorios tipados con puertos; roles con enum.
  2. El dominio no lee el reloj: lo recibe por el puerto `Clock`.
  3. Casos de uso inyectados en los routers (`interfaces/http/casos.py`) y
     comandos tipados (`*Cmd`) en lugar de `dict`.
  4. Un caso de uso por intención (`Consultar*`, `Crear*`, `Eliminar*`…).
  Convenciones: [`backend/README.md`](./backend/README.md#convenciones-de-la-capa-de-aplicación).
- **Seguridad:** API cerrada por defecto (`MP_REQUIRE_AUTH=1`), permisos por
  rol y por propietario, bloqueo tras 5 logins fallidos, códigos de
  recuperación con límite de intentos, primer administrador por consola
  (`python backend/crear_superusuario.py`).
- **Correo (SMTP):** código de recuperación y avisos de cita confirmada, cita
  cancelada e historia clínica al tutor, enviados tras el commit y en segundo
  plano.
- **Frontend (React):** login con JWT; inicio, adopciones y tienda públicos;
  el resto pide sesión. Consume los datos reales de la API a través de los
  adaptadores de `src/api.ts`.
- **Pruebas:** 36 de la API (`python backend/tests/test_api.py`) y 21
  escenarios e2e con Playwright (`npm run test:e2e`).

## Pendientes

### 1. Imágenes de producto desde el inventario
El formulario de Inventario pide una **URL de imagen**, pero la API guarda las
imágenes de producto subiéndolas en base64 (`POST /api/productos/{id}/imagenes`)
y la URL se descarta. Hay que decidir:
- **a)** añadir en el formulario la subida de archivo que ya soporta la API, o
- **b)** aceptar también una URL externa, como ya hacen las mascotas (`imagen_url`).

La tienda ya muestra las imágenes subidas (`/api/imagenes/{id}`).

### 2. Precio y duración de los servicios
`Servicio` no tiene `precio` ni `duracion_min`: la migración
`0007_remove_servicio_duracion_remove_servicio_precio` del Django los eliminó y
la API respeta esa decisión. El frontend sólo los muestra si llegan, así que hoy
no aparecen. Si se quieren de vuelta, es un cambio de modelo (dominio, tabla,
migración, esquemas).

### 3. Correos en desarrollo
Con el SMTP configurado en `.env`, confirmar citas o registrar historias en local
envía correos **reales** al tutor. Las cuentas de `seed.py` (`@example.com`) no
existen y Gmail devuelve el correo a `sistema.mundopeludo@gmail.com`.
Propuesta: una variable (p. ej. `MP_EMAIL_REDIRIGIR_A`) que, fuera de
producción, mande todos los correos a una sola dirección.

### 4. Más escenarios e2e
Cubiertos: visitante, autenticación, cliente (citas, compra, adopción) y
personal (panel, confirmar cita). Faltan, por ejemplo:
- recuperación de contraseña de principio a fin (con `codigo_debug`);
- registrar una historia clínica y verla desde el cliente;
- aprobar / rechazar una solicitud de adopción (cuidado: aprobarla transfiere
  la mascota y cambia los datos que usan otras pruebas);
- crear, editar y desactivar productos en Inventario;
- registrar una mascota con descripción e imagen.

### 5. Integración continua
Nada ejecuta las pruebas automáticamente. En un servidor de CI las e2e tendrían
que ir con `headless: true` (no hay pantalla), por ejemplo con una variable que
cambie esa opción en `playwright.config.ts`.

### 6. Antes de desplegar
- `MP_ENV=produccion`: la app exige entonces `MP_SECRET_KEY` propia.
- `MP_CORS_ORIGINS` con el dominio real en lugar de `*`.
- No usar `seed.py`: sus cuentas tienen una contraseña conocida.
- Crear el administrador con `crear_superusuario.py`.
- `backend/mundopeludo.db` (la base de la versión anterior) sigue versionada;
  valorar sacarla del repositorio (`git rm --cached`).
