# Backend MundoPeludo — FastAPI + sqlite3 + arquitectura hexagonal

Migración del backend Django original (`legacy_django/`) a **FastAPI** con
persistencia en **sqlite3 sin ORM**, organizada en **puertos y adaptadores**.

```
backend/
├── main.py                     # entrada ASGI: uvicorn backend.main:app
├── seed.py                     # datos de ejemplo (usa los casos de uso)
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
│   │   └── use_cases/
│   ├── infrastructure/         #  ← ADAPTADORES DE SALIDA
│   │   ├── db/                 #    conexión y DDL de SQLite
│   │   ├── repositories/       #    implementación de los puertos con SQL
│   │   └── security/           #    pbkdf2_sha256 y JWT HS256 (stdlib)
│   └── interfaces/http/        #  ← ADAPTADOR DE ENTRADA
│       ├── deps.py             #    composition root e inyección
│       ├── errors.py           #    errores de dominio → códigos HTTP
│       ├── routers/            #    endpoints FastAPI
│       └── schemas/            #    modelos Pydantic del contrato
└── tests/                      # pruebas end-to-end sin dependencias extra
```

**Regla de dependencia**: las flechas apuntan siempre hacia dentro.
`domain/` no importa nada de las otras capas; `application/` sólo conoce
`domain/`; `infrastructure/` e `interfaces/` conocen las de dentro, y sólo
`bootstrap.py` + `deps.py` saben qué implementación concreta se usa. Cambiar
SQLite por PostgreSQL significa escribir otros repositorios y una línea en
`deps.py`: ni el dominio ni los casos de uso se enteran.

---

## Puesta en marcha

```bash
pip install -r backend/requirements.txt

python backend/seed.py                       # datos de ejemplo (opcional)
uvicorn backend.main:app --reload --port 8000
```

* Swagger: <http://localhost:8000/docs>
* ReDoc: <http://localhost:8000/redoc>

### Credenciales de ejemplo (tras `seed.py`)

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@mundopeludo.com` | `mundopeludo2025` |
| Veterinario | `vet.garcia@mundopeludo.com` | `mundopeludo2025` |
| Cliente | `maria.gonzalez@example.com` | `mundopeludo2025` |

### Configuración

| Variable | Por defecto | Para qué sirve |
|---|---|---|
| `MP_DB_PATH` | `backend/data/mundopeludo.db` | Ruta del archivo SQLite |
| `MP_SECRET_KEY` | clave de desarrollo | Firma de los JWT. **Obligatoria en producción**: la app no arranca con la de desarrollo |
| `MP_TOKEN_MINUTES` | `720` | Vigencia del token |
| `MP_CORS_ORIGINS` | `*` | Orígenes permitidos, separados por coma |
| `MP_REQUIRE_AUTH` | `0` | `1` exige token, rol y propiedad del recurso (ver *Autenticación*) |
| `MP_ENV` | `desarrollo` | En producción oculta el código de recuperación |

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
| `historiales_medicos` | `HistorialMedico` | `model/historial.py` | `historiales_medicos` |
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

* **`Servicio` no tiene `precio` ni `duracion`**: la migración
  `0007_remove_servicio_duracion_remove_servicio_precio` los eliminó del modelo
  Django, y aquí se respeta esa decisión.
* **`Producto.TAMANO_CHOICES` y `EDAD_CHOICES`** estaban declaradas en Django
  pero ningún campo las usaba; no se han portado.
* **`Pedido` / `PedidoItem` son una extensión**: no existían en Django, pero el
  endpoint `/api/checkout` de la API actual los necesita para registrar la
  compra y descontar stock.
* **Autenticación**: se sustituye la sesión con cookie + CSRF de Django por JWT
  `Bearer`. Con `MP_REQUIRE_AUTH=0` (valor por defecto) las escrituras siguen
  abiertas para no romper al cliente SPA existente, que todavía no envía la
  cabecera `Authorization`. **Ese modo es abierto**: cualquiera puede leer y
  modificar cualquier dato, así que sólo sirve para desarrollo local. Con
  `MP_REQUIRE_AUTH=1` se exigen token y rol, y además:
  * el registro público sólo crea clientes; las cuentas de veterinario y de
    administrador las crea un administrador (o `seed.py`);
  * un cliente sólo ve y modifica lo suyo: su usuario, carrito, pedidos,
    mascotas, citas, historiales y solicitudes de adopción. En los listados se
    le filtra automáticamente;
  * cambiar el rol o dar de baja una cuenta, transferir una mascota o
    publicarla en adopción, y consultar usuarios, bitácora o panel quedan
    reservados al personal;
  * quien aprueba o rechaza una adopción firma con su propio `revisor_id`.
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
disponibilidad, la generación de SKU, el control de stock, la subida de
imágenes, el carrito, la atomicidad del checkout, la autorización por rol y
por propietario, el bloqueo del código de recuperación por fuerza bruta, la
reprogramación de citas, las fechas con zona horaria, el contrato con el
cliente SPA y el panel de indicadores.
