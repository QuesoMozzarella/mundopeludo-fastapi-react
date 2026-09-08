import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "mundopeludo.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            tipo TEXT CHECK(tipo IN ('cliente', 'veterinario', 'administrador')) DEFAULT 'cliente',
            documento TEXT,
            especialidad TEXT,
            activo INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Tabla de especies
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS especies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        );
        """)

        # Tabla de servicios
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS servicios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            duracion_min INTEGER DEFAULT 30,
            precio REAL DEFAULT 0.0,
            activo INTEGER DEFAULT 1
        );
        """)

        # Tabla de mascotas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mascotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            especie_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            raza TEXT,
            edad_anos INTEGER DEFAULT 1,
            sexo TEXT CHECK(sexo IN ('Macho', 'Hembra')) NOT NULL,
            color TEXT NOT NULL,
            peso REAL DEFAULT 0.0,
            esta_esterilizado INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            fecha_registro DATE DEFAULT CURRENT_DATE,
            estado_adopcion TEXT CHECK(estado_adopcion IN ('normal', 'en_adopcion', 'adoptada', 'pendiente')) DEFAULT 'normal',
            imagen_url TEXT,
            descripcion TEXT,
            FOREIGN KEY (cliente_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (especie_id) REFERENCES especies(id)
        );
        """)

        # Tabla de solicitudes de adopción
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes_adopcion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mascota_id INTEGER NOT NULL,
            cliente_id INTEGER NOT NULL,
            fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado TEXT CHECK(estado IN ('pendiente', 'aprobada', 'rechazada', 'cancelada')) DEFAULT 'pendiente',
            revisado_por INTEGER,
            fecha_revision TIMESTAMP,
            notas_revisor TEXT,
            notas_cliente TEXT,
            FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
            FOREIGN KEY (cliente_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (revisado_por) REFERENCES users(id)
        );
        """)

        # Tabla de citas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS citas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mascota_id INTEGER NOT NULL,
            veterinario_id INTEGER NOT NULL,
            servicio_id INTEGER NOT NULL,
            fecha_hora TEXT NOT NULL,
            peso REAL DEFAULT 0.0,
            motivo TEXT NOT NULL,
            notas TEXT,
            estado TEXT CHECK(estado IN ('Confirmada', 'Pendiente', 'Completada', 'Cancelada')) DEFAULT 'Pendiente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
            FOREIGN KEY (veterinario_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (servicio_id) REFERENCES servicios(id)
        );
        """)

        # Tabla de historiales médicos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS historiales_medicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cita_id INTEGER UNIQUE,
            mascota_id INTEGER NOT NULL,
            veterinario_id INTEGER NOT NULL,
            diagnostico TEXT NOT NULL,
            tratamiento TEXT NOT NULL,
            observaciones TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cita_id) REFERENCES citas(id) ON DELETE SET NULL,
            FOREIGN KEY (mascota_id) REFERENCES mascotas(id) ON DELETE CASCADE,
            FOREIGN KEY (veterinario_id) REFERENCES users(id)
        );
        """)

        # Tabla de productos (inventario / tienda)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            categoria TEXT NOT NULL,
            marca TEXT,
            precio REAL NOT NULL,
            descuento_porcentaje REAL DEFAULT 0.0,
            stock INTEGER DEFAULT 0,
            stock_minimo INTEGER DEFAULT 5,
            total_vendidos INTEGER DEFAULT 0,
            tipo_animal TEXT DEFAULT 'todos',
            unidad_medida TEXT DEFAULT 'unidad',
            peso REAL DEFAULT 0.0,
            lote TEXT,
            fecha_vencimiento DATE,
            sku TEXT UNIQUE NOT NULL,
            disponible_online INTEGER DEFAULT 1,
            activo INTEGER DEFAULT 1,
            imagen_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Tabla de carrito
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS carrito_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(usuario_id, producto_id),
            FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
        );
        """)

        # Tabla de pedidos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            total REAL NOT NULL,
            metodo_pago TEXT NOT NULL,
            direccion TEXT,
            estado TEXT DEFAULT 'Completado',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES users(id)
        );
        """)
