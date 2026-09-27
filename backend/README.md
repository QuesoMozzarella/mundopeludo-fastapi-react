# Backend MundoPeludo — FastAPI + sqlite3 + arquitectura hexagonal

Migración del backend Django original (`legacy_django/`) a **FastAPI** con
persistencia en **sqlite3 sin ORM**, organizada en **puertos y adaptadores**.

```
backend/
├── main.py                     # entrada ASGI: uvicorn backend.main:app
├── seed.py                     # datos de ejemplo (usa los casos de uso)
├── crear_superusuario.py       # alta de administradores por consola
├── requirements.txt
├── data/                       # la base SQLite vive aquí (ignorada por git)
├── app/
│   ├── config.py               # variables de entorno (el antiguo settings.py)
│   ├── bootstrap.py            # create_app(): monta el adaptador HTTP
│   ├── domain/                 #  ← NÚCLEO. Sin imports de FastAPI ni sqlite3
│   │   ├── errors.py           #    excepciones de negocio
│   │   ├── value_objects.py    #    enums y dinero (los *_CHOICES de Django)
│   │   ├── model/              #    entidades: usuario, mascota, cita, ...
│   │   └── ports/              #    interfaces: repositorios y servicios
│   ├── application/            #  ← CASOS DE USO. Orquestan el dominio
│   │   ├── read_models.py      #    agregados de lectura para las pantallas
│   │   ├── cambios.py          #    SIN_CAMBIO: actualizaciones parciales
│   │   └── use_cases/          #    un caso por intención + sus comandos *Cmd
│   ├── infrastructure/         #  ← ADAPTADORES DE SALIDA
│   │   ├── db/                 #    conexión, DDL y migraciones de SQLite
│   │   ├── repositories/       #    implementación de los puertos con SQL
│   │   ├── security/           #    pbkdf2_sha256 y JWT HS256 (stdlib)
│   │   └── notificaciones/     #    correo SMTP (smtplib)
│   └── interfaces/http/        #  ← ADAPTADOR DE ENTRADA
│       ├── deps.py             #    repositorios, servicios, sesión y permisos
│       ├── casos.py            #    proveedores de casos de uso (Depends)
│       ├── errors.py           #    errores de dominio → códigos HTTP
│       ├── routers/            #    endpoints FastAPI
│       └── schemas/            #    modelos Pydantic del contrato
└── tests/                      # pruebas end-to-end sin dependencias extra
```

**Regla de dependencia**: las flechas apuntan siempre hacia dentro.
`domain/` no importa nada de las otras capas; `application/` sólo conoce
`domain/`; `infrastructure/` e `interfaces/` conocen las de dentro, y sólo
`bootstrap.py`, `deps.py` y `casos.py` saben qué implementación concreta se usa. Cambiar
SQLite por PostgreSQL significa escribir otros repositorios y una línea en
`deps.py`: ni el dominio ni los casos de uso se enteran.

### Convenciones de la capa de aplicación

* **Un caso de uso por intención** (SRP): `AgendarCita`, `CambiarEstadoCita`,
  `EliminarCita`... cada uno con un único método `ejecutar(...)`. Las lecturas
  van en `Consultar*` (`listar` / `obtener`), que devuelven los modelos de
  `read_models.py`. Sólo `GestionarCarrito` agrupa varias operaciones: todas
  modifican el mismo agregado y comparten sus ayudantes.
* **Comandos tipados**: las altas y actualizaciones reciben un `*Cmd`
  (dataclass inmutable) en vez de un `dict`. En los de actualización cada
  campo vale `SIN_CAMBIO` si no se envió; `nuevo()` y `nuevo_o_vacio()`
  (`application/cambios.py`) deciden qué significa `null` en cada campo.
* **Inyección**: los routers declaran el caso que necesitan
  (`caso: AgendarCitaDep`) y `interfaces/http/casos.py` lo construye con sus
  repositorios y servicios. Un router nunca toca un repositorio.
* **Sin reloj oculto**: el dominio no llama a `datetime.now()`; las fechas le
  llegan del puerto `Clock` a través de los casos de uso.

---

## Puesta en marcha

```bash
pip install -r backend/requirements.txt

cp .env.example .env                         # y rellena los valores
python backend/crear_superusuario.py         # primer administrador
uvicorn backend.main:app --reload --port 8001
```

* Swagger: <http://localhost:8001/docs>
* ReDoc: <http://localhost:8001/redoc>

La API arranca **cerrada**: todo lo que no sea público (catálogos, productos,
mascotas en adopción, registro de clientes, login y recuperación de
contraseña) exige un token `Bearer`. Como el registro público sólo crea
clientes, el primer administrador se crea por consola, igual que
`manage.py createsuperuser`:

```bash
python backend/crear_superusuario.py                     # pregunta los datos
python backend/crear_superusuario.py --email admin@mundopeludo.com --nombre Ana --apellidos Ruiz
```

Desde esa cuenta se crean los veterinarios y otros administradores con
`POST /api/auth/register` enviando el token del administrador.

`main.py`, `seed.py` y `crear_superusuario.py` leen el `.env` de la raíz del
repositorio (sin pisar variables ya definidas en el entorno). Ese archivo está
en `.gitignore`: las credenciales nunca van al repositorio.

### Credenciales de ejemplo (tras `seed.py`)

> `seed.py` crea cuentas con una contraseña conocida: úsalo sólo en desarrollo.

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@mundopeludo.com` | `mundopeludo2025` |
| Veterinario | `vet.garcia@mundopeludo.com` | `mundopeludo2025` |
| Cliente | `maria.gonzalez@example.com` | `mundopeludo2025` |

### Configuración

| Variable | Por defecto | Para qué sirve |
|---|---|---|
| `MP_DB_PATH` | `backend/data/mundopeludo.db` | Ruta del archivo SQLite |
| `DATABASE_URL` | vacío | URL de **PostgreSQL** (Heroku la define al añadir Heroku Postgres). Si está, se usa en lugar de SQLite |
| `MP_DB_POOL` | `5` | Conexiones del pool de PostgreSQL por proceso |
| `MP_FRONTEND_DIR` | `dist/` | SPA compilada que FastAPI sirve junto a la API (si existe) |
| `MP_SECRET_KEY` | clave de desarrollo | Firma de los JWT. **Obligatoria en producción**: la app no arranca con la de desarrollo |
| `MP_TOKEN_MINUTES` | `720` | Vigencia del token |
| `MP_CORS_ORIGINS` | `*` | Orígenes permitidos, separados por coma |
| `MP_REQUIRE_AUTH` | `1` | API cerrada: token, rol y propiedad del recurso (ver *Autenticación*). `0` la abre por completo |
| `MP_ENV` | `desarrollo` | `produccion` activa las comprobaciones de arranque |
| `MP_EMAIL_HOST` | vacío | Servidor SMTP (`smtp.gmail.com`). Vacío: no se envían correos |
| `MP_EMAIL_PORT` | `587` | Puerto SMTP. Con `465` se usa SSL directo |
| `MP_EMAIL_USE_TLS` | `1` | STARTTLS en puertos distintos de 465 |
| `MP_EMAIL_USER` / `MP_EMAIL_PASSWORD` | vacío | Credenciales SMTP. En Gmail, una *contraseña de aplicación* |
| `MP_EMAIL_FROM` | `MP_EMAIL_USER` | Remitente visible |
| `MP_EMAIL_REDIRIGIR_A` | vacío | **Sólo desarrollo**: todos los correos van a esta dirección y el destinatario real queda en el asunto (`[Para …]`) y en la cabecera `X-MundoPeludo-Destinatario-Original`. Con `MP_ENV=produccion` la app no arranca si está definida |

---

## Correspondencia con los modelos Django

Los **15 modelos** del proyecto original están cubiertos:

| App Django | Modelo | Entidad de dominio | Tabla SQLite |
|---|---|---|---|
| `usuarios` | `CustomUser` | `model/usuario.py: Usuario` | `usuarios` |
| `usuarios` | `PerfilCliente` | `model/usuario.py: PerfilCliente` | `perfiles_cliente` |
| `usuarios` | `Especialidad` | `model/usuario.py: Especialidad` | `especialidades` |
| `usuarios` | `PerfilVeterinario` | `model/usuario.py: PerfilVeterinario` | `perfiles_veterinario` + `veterinario_especialidades` |
| `mascotas` | `Especie` | `model/mascota.py: Especie` | `especies` |
| `mascotas` | `Mascota` | `model/mascota.py: Mascota` | `mascotas` |
| `mascotas` | `AdopcionSolicitud` | `model/mascota.py: SolicitudAdopcion` | `solicitudes_adopcion` |
| `citas` | `EstadoCita` | `model/cita.py: EstadoCita` | `estados_cita` |
| `citas` | `Servicio` | `model/cita.py: Servicio` | `servicios` + `servicio_veterinarios` + `servicio_especialidades` |
| `citas` | `Disponibilidad` | `model/cita.py: Disponibilidad` | `disponibilidades` |
| `citas` | `Cita` | `model/cita.py: Cita` | `citas` |
| `historiales_medicos` | `HistorialMedico` | `model/historial.py` (cita opcional, ver abajo) | `historiales_medicos` |
| `inventario` | `Producto` | `model/inventario.py: Producto` | `productos` |
| `inventario` | `ImagenProducto` | `model/inventario.py: ImagenProducto` | `imagenes_producto` |
| `inventario` | `Carrito` / `CarritoItem` | `model/inventario.py: Carrito`, `CarritoItem` | `carritos`, `carrito_items` |
| `sananimal_clinic` | `ActividadSistema` | `model/sistema.py` | `actividades_sistema` |
| `sananimal_clinic` | `CodigoRecuperacion` | `model/sistema.py` | `codigos_recuperacion` |

### Qué se conservó del comportamiento de Django

* `Mascota.save()` normalizaba nombre y raza con `title()` y color con
  `lower()`, y `clean()` rechazaba dígitos en nombre y color: todo eso vive
  ahora en `Mascota.__post_init__`.
* `Producto._generate_sku()` genera `ALI-ALIPRE`, `MED-AMO500`… La entidad
  calcula la base (`sku_base()`) y `GeneradorSku` resuelve la unicidad contra
  la base de datos.
* Las propiedades `precio_final`, `stock_bajo`, `proximo_a_vencer`, `vencido`,
  `Carrito.subtotal` y `CarritoItem.subtotal` son propiedades del dominio.
* `AdopcionSolicitud.aprobar()` transfiere la mascota de inmediato (sin fase
  intermedia), igual que la versión final del modelo Django. Además, las demás
  solicitudes pendientes de esa mascota se rechazan automáticamente.
* `CodigoRecuperacion` mantiene la vigencia de una hora y el contador de
  intentos; ahora el código además se consume tras usarse.
* El hash de contraseñas usa el formato `pbkdf2_sha256$iteraciones$salt$hash`
  de Django, así que los hashes exportados de la base antigua siguen validando.

### Diferencias deliberadas

* **`Servicio` recupera `precio` y `duracion_min`**, que la migración
  `0007_remove_servicio_duracion_remove_servicio_precio` había eliminado del
  modelo Django. El precio es opcional (`null`: sin precio publicado; en un
  `PUT`, `null` lo retira) y la duración va de 5 a 480 minutos, 30 por defecto.
  La duración decide la agenda, como hacía el formulario de Django antes de
  la 0007: cada cita ocupa `[inicio, inicio + duración)` de su servicio, no
  puede pisar otra ni salirse de la franja del veterinario, y
  `GET /api/veterinarios/{id}/agenda?servicio_id=` sólo ofrece los huecos donde
  cabe entera (y, si es hoy, los que no han pasado). Las bases anteriores se
  migran solas: sus servicios quedan sin precio y con 30 minutos, lo que
  ocupaba hasta ahora cada cita.
* **Reglas de agenda** (`ReglasDeAgenda`):
  * Las citas **canceladas no ocupan** la agenda. Reactivar una (cambiar su
    estado a otro que no sea *Cancelada*) sólo se permite si su hueco sigue
    libre; si no, 409.
  * Un veterinario **sin franjas declaradas no recibe citas** (antes, sin
    franjas no había restricción horaria). Es lo que hacía el Django, que sólo
    ofrecía horas a los veterinarios con `Disponibilidad`.
  * Cada veterinario declara y borra **sus** franjas; el administrador, las de
    cualquiera.
* **`Producto.TAMANO_CHOICES` y `EDAD_CHOICES`** estaban declaradas en Django
  pero ningún campo las usaba; no se han portado.
* **`Pedido` / `PedidoItem` son una extensión**: no existían en Django, pero el
  endpoint `/api/checkout` de la API actual los necesita para registrar la
  compra y descontar stock.
* **Historial médico sin cita**: en Django era 1-1 obligatorio con una cita.
  Aquí pertenece a la mascota y la cita es opcional (urgencias, visitas sin
  agendar). Con cita, la mascota y el veterinario salen de ella y la cita pasa
  a `Completada`; sin cita hay que indicar `mascota_id` y `veterinario_id`.
  Borrar una cita no borra su ficha clínica: sólo pierde el vínculo. Las bases
  creadas antes se migran solas al arrancar (`schema.migrar`).
* **Autenticación**: se sustituye la sesión con cookie + CSRF de Django por JWT
  `Bearer`. Con `MP_REQUIRE_AUTH=1` (valor por defecto) se exigen token y rol,
  y además:
  * el registro público sólo crea clientes; las cuentas de veterinario y de
    administrador las crea un administrador (el primero, con
    `crear_superusuario.py`);
  * un cliente sólo ve y modifica lo suyo: su usuario, carrito, pedidos,
    mascotas, citas, historiales y solicitudes de adopción. En los listados se
    le filtra automáticamente;
  * cambiar el rol o dar de baja una cuenta, transferir una mascota o
    publicarla en adopción, y consultar usuarios, bitácora o panel quedan
    reservados al personal;
  * quien aprueba o rechaza una adopción, o firma un historial, lo hace con
    su propio id;
  * tras 5 contraseñas erróneas seguidas la cuenta se bloquea 15 minutos
    (429 con `Retry-After`), incluso para la contraseña correcta. Un login
    correcto reinicia el contador y restablecer la contraseña por código
    desbloquea al momento.

  `MP_REQUIRE_AUTH=0` abre la API por completo (cualquiera lee y modifica
  cualquier dato); sólo sirve para desarrollo local y la app lo avisa al
  arrancar.
* **Correo**: el `EMAIL_BACKEND` SMTP de Django se sustituye por el puerto
  `Notificaciones` y su adaptador `CorreoSmtp` (`smtplib`, sin dependencias).
  Envía:
  * el **código de recuperación** de contraseña, con la plantilla de la vista de
    Django. Es síncrono: si falla, la API responde 503 y no deja un código activo;
  * al tutor de la mascota, los **avisos** de cita **confirmada**, cita
    **cancelada** e **historia clínica** registrada (`AvisosDeCita` y
    `RegistrarHistorial`). Se acumulan durante la petición y salen *después del
    commit*, en segundo plano: no retienen el cerrojo de SQLite, no se envían si
    la operación falla y un error de SMTP sólo queda en el log, sin tumbar la
    operación. Mascotas sin tutor o tutores dados de baja no generan aviso.

  Sin `MP_EMAIL_HOST` no se envía nada y, fuera de producción, el código de
  recuperación vuelve en `codigo_debug` para poder probar. `seed.py` nunca envía
  correos: sus cuentas de ejemplo son ficticias.
* **Imágenes de producto**: se suben en base64 dentro del JSON
  (`POST /api/productos/{id}/imagenes`) en vez de `multipart/form-data`, para no
  depender de `python-multipart`. Los bytes se guardan en la base, igual que el
  `BinaryField` original.
* **Dinero**: el dominio usa `Decimal` con dos decimales; la serialización a
  número JSON ocurre sólo en el borde HTTP.
* **Compatibilidad con el cliente SPA**: `POST /api/checkout` acepta `items`
  en el cuerpo (el carrito del frontend vive en el navegador) y en ese caso no
  toca el carrito guardado; la respuesta incluye `pedido_id`. La revisión de
  adopciones acepta `notas_revisor` y `GET /api/productos` acepta `search` y
  `tipo_animal`, como la API anterior.

---

## Transacciones

Cada petición abre una conexión SQLite que funciona como *unit of work*: si el
handler termina bien se hace `COMMIT`, y si lanza una excepción, `ROLLBACK`.
Por eso el checkout es atómico: si el tercer producto del carrito no tiene
stock, tampoco se descuenta el de los dos primeros (hay una prueba que lo
comprueba, `test_checkout_es_transaccional`).

Las peticiones que escriben (POST, PUT, DELETE) abren la transacción con
`BEGIN IMMEDIATE`, que toma el cerrojo de escritura antes de la primera
lectura: dos compras simultáneas de la última unidad no pueden leer el mismo
stock (`test_checkout_concurrente_no_sobrevende`). Las de sólo lectura usan
`BEGIN` y, con WAL, no esperan a nadie. Si el cerrojo tarda más de 10 s, la
API responde 503.

En las actualizaciones parciales, un `null` explícito en un campo obligatorio
(precio, stock, activo...) significa "sin cambio"; sólo los campos opcionales
(descripción, notas, teléfono...) se vacían con `null`.

La excepción son los errores marcados con `conservar_cambios`
(`IntentoFallidoError`): confirman lo escrito antes de fallar. Así un código de
recuperación erróneo suma un intento aunque la petición se rechace, y tras 5
fallos el código queda bloqueado.

## Errores

`interfaces/http/errors.py` traduce las excepciones de dominio:

| Excepción | HTTP |
|---|---|
| `ValidationError` | 422 (incluye el campo culpable) |
| `NotFoundError` | 404 |
| `ConflictError`, `BusinessRuleError` | 409 |
| `AuthenticationError` | 401 |
| `AuthorizationError` | 403 |

## Pruebas

```bash
python backend/tests/test_api.py     # sin dependencias adicionales
pytest backend/tests                 # si tienes pytest instalado
```

Cubren el registro y login, la recuperación de contraseña, las validaciones de
mascota, el flujo completo de adopción, la agenda con solapes y
disponibilidad, el precio y la duración de los servicios (y su migración), la
redirección de correos en desarrollo, la generación de SKU, el control de stock, la subida de
imágenes, el carrito, la atomicidad del checkout, la autorización por rol y
por propietario, el bloqueo del código de recuperación por fuerza bruta, la
reprogramación de citas, las fechas con zona horaria, el contrato con el
cliente SPA y el panel de indicadores.
