"""DDL de SQLite: traducción de las migraciones de Django a tablas planas.

Cada bloque indica de qué modelo Django proviene. Las relaciones M2M
(`ManyToManyField`) se materializan como tablas puente, igual que hacía Django.
"""

DDL = """
-- ===================== usuarios.CustomUser =====================
CREATE TABLE IF NOT EXISTS usuarios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL DEFAULT '',
    nombre          TEXT    NOT NULL,
    apellidos       TEXT    NOT NULL,
    telefono        TEXT,
    direccion       TEXT,
    tipo            TEXT    NOT NULL DEFAULT 'cliente'
                    CHECK (tipo IN ('cliente','veterinario','administrador')),
    is_active       INTEGER NOT NULL DEFAULT 1,
    is_staff        INTEGER NOT NULL DEFAULT 0,
    is_superuser    INTEGER NOT NULL DEFAULT 0,
    date_joined     TEXT    NOT NULL,
    last_login      TEXT,
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta TEXT
);
CREATE INDEX IF NOT EXISTS idx_usuarios_tipo ON usuarios(tipo);

-- ===================== usuarios.PerfilCliente =====================
CREATE TABLE IF NOT EXISTS perfiles_cliente (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id          INTEGER NOT NULL UNIQUE,
    documento           TEXT,
    fecha_actualizacion TEXT    NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- ===================== usuarios.Especialidad =====================
CREATE TABLE IF NOT EXISTS especialidades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo      TEXT    NOT NULL UNIQUE,
    nombre      TEXT    NOT NULL,
    descripcion TEXT,
    activa      INTEGER NOT NULL DEFAULT 1
);

-- ===================== usuarios.PerfilVeterinario =====================
CREATE TABLE IF NOT EXISTS perfiles_veterinario (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id          INTEGER NOT NULL UNIQUE,
    fecha_contratacion  TEXT    NOT NULL,
    documento           TEXT    UNIQUE,
    activo              INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- M2M PerfilVeterinario.especialidades
CREATE TABLE IF NOT EXISTS veterinario_especialidades (
    perfil_veterinario_id INTEGER NOT NULL,
    especialidad_id       INTEGER NOT NULL,
    PRIMARY KEY (perfil_veterinario_id, especialidad_id),
    FOREIGN KEY (perfil_veterinario_id) REFERENCES perfiles_veterinario(id) ON DELETE CASCADE,
    FOREIGN KEY (especialidad_id)       REFERENCES especialidades(id)       ON DELETE CASCADE
);

-- ===================== mascotas.Especie =====================
CREATE TABLE IF NOT EXISTS especies (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE
);

-- ===================== mascotas.Mascota =====================
CREATE TABLE IF NOT EXISTS mascotas (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id         INTEGER,
    especie_id         INTEGER NOT NULL,
    nombre             TEXT    NOT NULL,
    raza               TEXT,
    edad_anos          INTEGER NOT NULL DEFAULT 1,
    sexo               TEXT    NOT NULL CHECK (sexo IN ('Macho','Hembra')),
    color              TEXT    NOT NULL,
    peso               REAL    NOT NULL DEFAULT 1.0,
    esta_esterilizado  INTEGER NOT NULL DEFAULT 0,
    activo             INTEGER NOT NULL DEFAULT 1,
    fecha_registro     TEXT    NOT NULL,
    estado_adopcion    TEXT    NOT NULL DEFAULT 'normal'
                       CHECK (estado_adopcion IN ('normal','en_adopcion','adoptada','pendiente')),
    FOREIGN KEY (cliente_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (especie_id) REFERENCES especies(id)
);
CREATE INDEX IF NOT EXISTS idx_mascotas_cliente ON mascotas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_mascotas_adopcion ON mascotas(estado_adopcion);

-- ===================== mascotas.AdopcionSolicitud =====================
CREATE TABLE IF NOT EXISTS solicitudes_adopcion (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    mascota_id          INTEGER NOT NULL,
    cliente_id          INTEGER NOT NULL,
    fecha_solicitud     TEXT    NOT NULL,
    fecha_actualizacion TEXT    NOT NULL,
    estado              TEXT    NOT NULL DEFAULT 'pendiente'
                        CHECK (estado IN ('pendiente','aprobada','rechazada','cancelada')),
    revisado_por_id     INTEGER,
    fecha_revision      TEXT,
    notas_revisor       TEXT    NOT NULL DEFAULT '',
    notas_cliente       TEXT    NOT NULL DEFAULT '',
    FOREIGN KEY (mascota_id)      REFERENCES mascotas(id) ON DELETE CASCADE,
    FOREIGN KEY (cliente_id)      REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (revisado_por_id) REFERENCES usuarios(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_solicitudes_estado ON solicitudes_adopcion(estado);

-- ===================== citas.EstadoCita =====================
CREATE TABLE IF NOT EXISTS estados_cita (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT    NOT NULL UNIQUE,
    descripcion TEXT,
    orden       INTEGER NOT NULL DEFAULT 0
);

-- ===================== citas.Servicio =====================
CREATE TABLE IF NOT EXISTS servicios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT    NOT NULL,
    descripcion TEXT,
    activo      INTEGER NOT NULL DEFAULT 1
);

-- M2M Servicio.veterinarios
CREATE TABLE IF NOT EXISTS servicio_veterinarios (
    servicio_id    INTEGER NOT NULL,
    veterinario_id INTEGER NOT NULL,
    PRIMARY KEY (servicio_id, veterinario_id),
    FOREIGN KEY (servicio_id)    REFERENCES servicios(id) ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id)  ON DELETE CASCADE
);

-- M2M Servicio.especialidades
CREATE TABLE IF NOT EXISTS servicio_especialidades (
    servicio_id     INTEGER NOT NULL,
    especialidad_id INTEGER NOT NULL,
    PRIMARY KEY (servicio_id, especialidad_id),
    FOREIGN KEY (servicio_id)     REFERENCES servicios(id)      ON DELETE CASCADE,
    FOREIGN KEY (especialidad_id) REFERENCES especialidades(id) ON DELETE CASCADE
);

-- ===================== citas.Disponibilidad =====================
CREATE TABLE IF NOT EXISTS disponibilidades (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    veterinario_id INTEGER NOT NULL,
    dia_semana     INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    hora_inicio    TEXT    NOT NULL,
    hora_fin       TEXT    NOT NULL,
    UNIQUE (veterinario_id, dia_semana, hora_inicio, hora_fin),
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- ===================== citas.Cita =====================
CREATE TABLE IF NOT EXISTS citas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    mascota_id     INTEGER NOT NULL,
    veterinario_id INTEGER NOT NULL,
    estado_id      INTEGER NOT NULL,
    servicio_id    INTEGER NOT NULL,
    fecha_hora     TEXT    NOT NULL,
    peso           REAL    NOT NULL DEFAULT 0.0,
    motivo         TEXT    NOT NULL,
    notas          TEXT,
    FOREIGN KEY (mascota_id)     REFERENCES mascotas(id)     ON DELETE CASCADE,
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id)     ON DELETE CASCADE,
    FOREIGN KEY (estado_id)      REFERENCES estados_cita(id),
    FOREIGN KEY (servicio_id)    REFERENCES servicios(id)
);
CREATE INDEX IF NOT EXISTS idx_citas_fecha ON citas(fecha_hora);
CREATE INDEX IF NOT EXISTS idx_citas_vet ON citas(veterinario_id);

-- ===================== historiales_medicos.HistorialMedico =====================
CREATE TABLE IF NOT EXISTS historiales_medicos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    mascota_id     INTEGER NOT NULL,
    cita_id        INTEGER UNIQUE,
    veterinario_id INTEGER NOT NULL,
    diagnostico    TEXT    NOT NULL,
    tratamiento    TEXT    NOT NULL,
    observaciones  TEXT,
    fecha_creacion TEXT    NOT NULL,
    FOREIGN KEY (mascota_id)     REFERENCES mascotas(id) ON DELETE CASCADE,
    -- Borrar la cita no borra la ficha clínica: sólo pierde el vínculo.
    FOREIGN KEY (cita_id)        REFERENCES citas(id)    ON DELETE SET NULL,
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_historiales_mascota ON historiales_medicos(mascota_id);

-- ===================== inventario.Producto =====================
CREATE TABLE IF NOT EXISTS productos (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre                TEXT    NOT NULL,
    descripcion           TEXT,
    categoria             TEXT    NOT NULL,
    marca                 TEXT,
    precio                REAL    NOT NULL,
    descuento_porcentaje  REAL    NOT NULL DEFAULT 0,
    stock                 INTEGER NOT NULL DEFAULT 0,
    stock_minimo          INTEGER NOT NULL DEFAULT 5,
    total_vendidos        INTEGER NOT NULL DEFAULT 0,
    tipo_animal           TEXT    NOT NULL DEFAULT 'todos',
    unidad_medida         TEXT    NOT NULL DEFAULT 'unidad',
    peso                  REAL,
    lote                  TEXT,
    fecha_vencimiento     TEXT,
    sku                   TEXT    NOT NULL UNIQUE,
    disponible_online     INTEGER NOT NULL DEFAULT 1,
    palabras_clave        TEXT,
    activo                INTEGER NOT NULL DEFAULT 1,
    fecha_creacion        TEXT    NOT NULL,
    fecha_actualizacion   TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria);

-- ===================== inventario.ImagenProducto =====================
CREATE TABLE IF NOT EXISTS imagenes_producto (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id     INTEGER NOT NULL,
    imagen_data     BLOB,
    nombre_archivo  TEXT,
    tipo_contenido  TEXT    NOT NULL DEFAULT 'image/jpeg',
    fecha_subida    TEXT    NOT NULL,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
);

-- ===================== inventario.Carrito / CarritoItem =====================
CREATE TABLE IF NOT EXISTS carritos (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id          INTEGER NOT NULL UNIQUE,
    fecha_creacion      TEXT    NOT NULL,
    fecha_actualizacion TEXT    NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS carrito_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    carrito_id      INTEGER NOT NULL,
    producto_id     INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL DEFAULT 1,
    precio_unitario REAL    NOT NULL,
    fecha_agregado  TEXT    NOT NULL,
    UNIQUE (carrito_id, producto_id),
    FOREIGN KEY (carrito_id)  REFERENCES carritos(id)  ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
);

-- ===================== Extensión: pedidos del checkout =====================
CREATE TABLE IF NOT EXISTS pedidos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id   INTEGER NOT NULL,
    total        REAL    NOT NULL,
    metodo_pago  TEXT    NOT NULL,
    direccion    TEXT,
    estado       TEXT    NOT NULL DEFAULT 'Completado',
    fecha        TEXT    NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id       INTEGER NOT NULL,
    producto_id     INTEGER NOT NULL,
    nombre_producto TEXT    NOT NULL,
    cantidad        INTEGER NOT NULL,
    precio_unitario REAL    NOT NULL,
    FOREIGN KEY (pedido_id)   REFERENCES pedidos(id)   ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- ===================== sananimal_clinic.ActividadSistema =====================
CREATE TABLE IF NOT EXISTS actividades_sistema (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario     TEXT NOT NULL,
    tipo        TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    fecha       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_actividades_fecha ON actividades_sistema(fecha DESC);

-- ===================== sananimal_clinic.CodigoRecuperacion =====================
CREATE TABLE IF NOT EXISTS codigos_recuperacion (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id        INTEGER NOT NULL,
    codigo            TEXT    NOT NULL,
    fecha_creacion    TEXT    NOT NULL,
    fecha_expiracion  TEXT    NOT NULL,
    intentos          INTEGER NOT NULL DEFAULT 0,
    activo            INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_codigos_usuario ON codigos_recuperacion(usuario_id);
"""


def _columnas(conn, tabla: str) -> set[str]:
    return {fila[1] for fila in conn.execute(f"PRAGMA table_info({tabla})")}


# Migraciones de bases creadas con versiones anteriores del esquema. Se
# ejecutan antes del DDL y detectan por columnas si hace falta aplicarlas, así
# que son idempotentes.
MIGRACION_HISTORIAL_SIN_CITA = """
PRAGMA foreign_keys = OFF;
BEGIN;
CREATE TABLE historiales_medicos_v2 (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    mascota_id     INTEGER NOT NULL,
    cita_id        INTEGER UNIQUE,
    veterinario_id INTEGER NOT NULL,
    diagnostico    TEXT    NOT NULL,
    tratamiento    TEXT    NOT NULL,
    observaciones  TEXT,
    fecha_creacion TEXT    NOT NULL,
    FOREIGN KEY (mascota_id)     REFERENCES mascotas(id) ON DELETE CASCADE,
    FOREIGN KEY (cita_id)        REFERENCES citas(id)    ON DELETE SET NULL,
    FOREIGN KEY (veterinario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);
INSERT INTO historiales_medicos_v2
    (id, mascota_id, cita_id, veterinario_id, diagnostico, tratamiento,
     observaciones, fecha_creacion)
SELECT h.id, c.mascota_id, h.cita_id, h.veterinario_id, h.diagnostico,
       h.tratamiento, h.observaciones, h.fecha_creacion
FROM historiales_medicos h JOIN citas c ON c.id = h.cita_id;
DROP TABLE historiales_medicos;
ALTER TABLE historiales_medicos_v2 RENAME TO historiales_medicos;
COMMIT;
PRAGMA foreign_keys = ON;
"""


def migrar(conn) -> None:
    """Pone al día una base existente antes de aplicar el DDL."""
    usuarios = _columnas(conn, "usuarios")
    if usuarios and "intentos_fallidos" not in usuarios:
        # v2 → v3: bloqueo temporal por intentos de login fallidos.
        conn.execute(
            "ALTER TABLE usuarios ADD COLUMN intentos_fallidos INTEGER NOT NULL DEFAULT 0"
        )
        conn.execute("ALTER TABLE usuarios ADD COLUMN bloqueado_hasta TEXT")
    historiales = _columnas(conn, "historiales_medicos")
    if historiales and "mascota_id" not in historiales:
        # v1 → v2: la cita del historial pasa a ser opcional.
        conn.executescript(MIGRACION_HISTORIAL_SIN_CITA)


# Catálogos imprescindibles para que la API arranque usable.
SEMILLA_MINIMA = [
    (
        "INSERT OR IGNORE INTO estados_cita (nombre, descripcion, orden) VALUES (?, ?, ?)",
        [
            ("Pendiente", "Cita agendada a la espera de confirmación", 1),
            ("Confirmada", "Cita confirmada por la clínica", 2),
            ("Completada", "Atención realizada", 3),
            ("Cancelada", "Cita anulada", 4),
        ],
    ),
    (
        "INSERT OR IGNORE INTO especies (nombre) VALUES (?)",
        [
            ("Canino (Perro)",),
            ("Felino (Gato)",),
            ("Ave",),
            ("Roedor",),
            ("Reptil",),
        ],
    ),
]
