import os
import sys
import sqlite3
from typing import List, Optional
from datetime import datetime

# Permitir importaciones relativas al directorio backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from database import get_db, init_db

# Inicializar base de datos
init_db()

app = FastAPI(
    title="MundoPeludo API",
    description="API RESTful de alta velocidad desarrollada en FastAPI para la gestión integral de la Clínica Veterinaria MundoPeludo.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Permitir CORS para cualquier origen (React dev server, Node.js proxy, preview)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== PYDANTIC SCHEMAS ====================

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    nombre: str
    apellidos: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    tipo: Optional[str] = "cliente"
    documento: Optional[str] = None

class MascotaCreate(BaseModel):
    cliente_id: Optional[int] = None
    especie_id: int
    nombre: str
    raza: Optional[str] = ""
    edad_anos: int = Field(default=1, ge=0, le=30)
    sexo: str
    color: str
    peso: float = Field(default=1.0, ge=0.05, le=120.0)
    esta_esterilizado: bool = False
    estado_adopcion: Optional[str] = "normal"
    imagen_url: Optional[str] = None
    descripcion: Optional[str] = None

class MascotaUpdate(BaseModel):
    nombre: Optional[str] = None
    raza: Optional[str] = None
    edad_anos: Optional[int] = None
    sexo: Optional[str] = None
    color: Optional[str] = None
    peso: Optional[float] = None
    esta_esterilizado: Optional[bool] = None
    estado_adopcion: Optional[str] = None
    imagen_url: Optional[str] = None
    descripcion: Optional[str] = None

class CitaCreate(BaseModel):
    mascota_id: int
    veterinario_id: int
    servicio_id: int
    fecha_hora: str
    peso: Optional[float] = 0.0
    motivo: str
    notas: Optional[str] = ""

class CitaStatusUpdate(BaseModel):
    estado: str

class HistorialCreate(BaseModel):
    cita_id: Optional[int] = None
    mascota_id: int
    veterinario_id: int
    diagnostico: str
    tratamiento: str
    observaciones: Optional[str] = ""

class SolicitudAdopcionCreate(BaseModel):
    mascota_id: int
    cliente_id: int
    notas_cliente: str

class SolicitudAdopcionReview(BaseModel):
    revisor_id: int
    notas_revisor: Optional[str] = ""

class ProductoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = ""
    categoria: str
    marca: Optional[str] = ""
    precio: float
    descuento_porcentaje: Optional[float] = 0.0
    stock: int
    stock_minimo: Optional[int] = 5
    tipo_animal: Optional[str] = "todos"
    unidad_medida: Optional[str] = "unidad"
    peso: Optional[float] = 0.0
    sku: Optional[str] = None
    imagen_url: Optional[str] = None

class CarritoItemAdd(BaseModel):
    producto_id: int
    cantidad: int = 1

class CheckoutRequest(BaseModel):
    usuario_id: int
    metodo_pago: str
    direccion: str

# ==================== ENDPOINTS ====================

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "MundoPeludo FastAPI Backend",
        "timestamp": datetime.now().isoformat(),
        "database": "SQLite (Connected)"
    }

# ---------- USUARIOS & AUTENTICACIÓN ----------

@app.post("/api/auth/login")
def login(req: LoginRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (req.email,))
        user = cursor.fetchone()
        if not user or user["password"] != req.password:
            raise HTTPException(status_code=401, detail="Correo electrónico o contraseña incorrectos")
        
        user_dict = dict(user)
        user_dict.pop("password")
        return {"user": user_dict, "token": f"token-{user['id']}"}

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (req.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")
        
        cursor.execute("""
            INSERT INTO users (email, password, nombre, apellidos, telefono, direccion, tipo, documento, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (req.email, req.password, req.nombre, req.apellidos, req.telefono, req.direccion, req.tipo, req.documento))
        
        user_id = cursor.lastrowid
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = dict(cursor.fetchone())
        user.pop("password")
        return {"user": user, "token": f"token-{user_id}"}

@app.get("/api/users")
def get_users(tipo: Optional[str] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        if tipo:
            cursor.execute("SELECT id, email, nombre, apellidos, telefono, direccion, tipo, especialidad, documento, activo FROM users WHERE tipo = ?", (tipo,))
        else:
            cursor.execute("SELECT id, email, nombre, apellidos, telefono, direccion, tipo, especialidad, documento, activo FROM users")
        return [dict(row) for row in cursor.fetchall()]

@app.get("/api/veterinarios")
def get_veterinarios():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, nombre, apellidos, telefono, especialidad FROM users WHERE tipo = 'veterinario' AND activo = 1")
        return [dict(row) for row in cursor.fetchall()]

# ---------- ESPECIES & SERVICIOS ----------

@app.get("/api/especies")
def get_especies():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM especies")
        return [dict(row) for row in cursor.fetchall()]

@app.get("/api/servicios")
def get_servicios():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servicios WHERE activo = 1")
        return [dict(row) for row in cursor.fetchall()]

# ---------- MASCOTAS ----------

@app.get("/api/mascotas")
def get_mascotas(
    cliente_id: Optional[int] = None,
    estado_adopcion: Optional[str] = None,
    search: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT m.*, e.nombre AS especie_nombre, 
                   u.nombre AS tutor_nombre, u.apellidos AS tutor_apellidos, u.telefono AS tutor_telefono, u.email AS tutor_email
            FROM mascotas m
            LEFT JOIN especies e ON m.especie_id = e.id
            LEFT JOIN users u ON m.cliente_id = u.id
            WHERE m.activo = 1
        """
        params = []
        if cliente_id:
            query += " AND m.cliente_id = ?"
            params.append(cliente_id)
        if estado_adopcion:
            query += " AND m.estado_adopcion = ?"
            params.append(estado_adopcion)
        if search:
            query += " AND (m.nombre LIKE ? OR m.raza LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY m.id DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

@app.get("/api/mascotas/{mascota_id}")
def get_mascota(mascota_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, e.nombre AS especie_nombre, 
                   u.nombre AS tutor_nombre, u.apellidos AS tutor_apellidos, u.telefono AS tutor_telefono, u.email AS tutor_email
            FROM mascotas m
            LEFT JOIN especies e ON m.especie_id = e.id
            LEFT JOIN users u ON m.cliente_id = u.id
            WHERE m.id = ? AND m.activo = 1
        """, (mascota_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Mascota no encontrada")
        
        mascota = dict(row)
        
        # Historiales
        cursor.execute("""
            SELECT h.*, u.nombre AS vet_nombre, u.apellidos AS vet_apellidos, c.motivo AS cita_motivo
            FROM historiales_medicos h
            LEFT JOIN users u ON h.veterinario_id = u.id
            LEFT JOIN citas c ON h.cita_id = c.id
            WHERE h.mascota_id = ?
            ORDER BY h.fecha_creacion DESC
        """, (mascota_id,))
        mascota["historial"] = [dict(h) for h in cursor.fetchall()]
        
        return mascota

@app.post("/api/mascotas", status_code=status.HTTP_201_CREATED)
def create_mascota(m: MascotaCreate):
    # Validaciones personalizadas
    if any(char.isdigit() for char in m.nombre):
        raise HTTPException(status_code=400, detail="El nombre de la mascota no puede contener números")
    
    img = m.imagen_url
    if not img:
        img = "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=600&auto=format&fit=crop&q=80" if m.especie_id == 1 else "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&auto=format&fit=crop&q=80"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO mascotas (cliente_id, especie_id, nombre, raza, edad_anos, sexo, color, peso, esta_esterilizado, estado_adopcion, imagen_url, descripcion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            m.cliente_id, m.especie_id, m.nombre.strip().title(), m.raza.strip().title() if m.raza else "",
            m.edad_anos, m.sexo, m.color.strip().lower(), m.peso, 1 if m.esta_esterilizado else 0,
            m.estado_adopcion, img, m.descripcion
        ))
        mascota_id = cursor.lastrowid
        cursor.execute("SELECT m.*, e.nombre AS especie_nombre FROM mascotas m LEFT JOIN especies e ON m.especie_id = e.id WHERE m.id = ?", (mascota_id,))
        return dict(cursor.fetchone())

@app.put("/api/mascotas/{mascota_id}")
def update_mascota(mascota_id: int, m: MascotaUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mascotas WHERE id = ?", (mascota_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Mascota no encontrada")
        
        updates = []
        params = []
        for field, value in m.dict(exclude_unset=True).items():
            if value is not None:
                if field == "esta_esterilizado":
                    value = 1 if value else 0
                updates.append(f"{field} = ?")
                params.append(value)
        
        if updates:
            params.append(mascota_id)
            cursor.execute(f"UPDATE mascotas SET {', '.join(updates)} WHERE id = ?", params)
        
        cursor.execute("SELECT m.*, e.nombre AS especie_nombre FROM mascotas m LEFT JOIN especies e ON m.especie_id = e.id WHERE m.id = ?", (mascota_id,))
        return dict(cursor.fetchone())

@app.delete("/api/mascotas/{mascota_id}")
def delete_mascota(mascota_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE mascotas SET activo = 0 WHERE id = ?", (mascota_id,))
        return {"success": True, "message": "Mascota dada de baja correctamente"}

# ---------- ADOPCIONES ----------

@app.get("/api/adopciones")
def get_adopciones():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, e.nombre AS especie_nombre
            FROM mascotas m
            LEFT JOIN especies e ON m.especie_id = e.id
            WHERE m.estado_adopcion = 'en_adopcion' AND m.activo = 1
            ORDER BY m.id DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

@app.get("/api/adopciones/solicitudes")
def get_solicitudes_adopcion(cliente_id: Optional[int] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT s.*, 
                   m.nombre AS mascota_nombre, m.raza AS mascota_raza, m.imagen_url AS mascota_imagen, m.estado_adopcion AS mascota_estado,
                   u.nombre AS cliente_nombre, u.apellidos AS cliente_apellidos, u.email AS cliente_email, u.telefono AS cliente_telefono,
                   r.nombre AS revisor_nombre, r.apellidos AS revisor_apellidos
            FROM solicitudes_adopcion s
            JOIN mascotas m ON s.mascota_id = m.id
            JOIN users u ON s.cliente_id = u.id
            LEFT JOIN users r ON s.revisado_por = r.id
        """
        params = []
        if cliente_id:
            query += " WHERE s.cliente_id = ?"
            params.append(cliente_id)
        
        query += " ORDER BY s.fecha_solicitud DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/adopciones/solicitudes", status_code=status.HTTP_201_CREATED)
def create_solicitud_adopcion(req: SolicitudAdopcionCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT estado_adopcion FROM mascotas WHERE id = ?", (req.mascota_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Mascota no encontrada")
        if row["estado_adopcion"] != "en_adopcion":
            raise HTTPException(status_code=400, detail="Esta mascota no está disponible para adopción")
        
        cursor.execute("""
            INSERT INTO solicitudes_adopcion (mascota_id, cliente_id, estado, notas_cliente)
            VALUES (?, ?, 'pendiente', ?)
        """, (req.mascota_id, req.cliente_id, req.notas_cliente))
        sol_id = cursor.lastrowid
        return {"id": sol_id, "message": "Solicitud de adopción enviada con éxito"}

@app.put("/api/adopciones/solicitudes/{solicitud_id}/aprobar")
def aprobar_solicitud(solicitud_id: int, req: SolicitudAdopcionReview):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM solicitudes_adopcion WHERE id = ?", (solicitud_id,))
        solicitud = cursor.fetchone()
        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE solicitudes_adopcion 
            SET estado = 'aprobada', revisado_por = ?, fecha_revision = ?, notas_revisor = ?
            WHERE id = ?
        """, (req.revisor_id, now, req.notas_revisor, solicitud_id))

        # Transferir mascota al cliente adoptante
        cursor.execute("""
            UPDATE mascotas 
            SET estado_adopcion = 'normal', cliente_id = ?
            WHERE id = ?
        """, (solicitud["cliente_id"], solicitud["mascota_id"]))

        return {"success": True, "message": "Solicitud aprobada y mascota transferida al tutor"}

@app.put("/api/adopciones/solicitudes/{solicitud_id}/rechazar")
def rechazar_solicitud(solicitud_id: int, req: SolicitudAdopcionReview):
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE solicitudes_adopcion 
            SET estado = 'rechazada', revisado_por = ?, fecha_revision = ?, notas_revisor = ?
            WHERE id = ?
        """, (req.revisor_id, now, req.notas_revisor, solicitud_id))
        return {"success": True, "message": "Solicitud rechazada"}

# ---------- CITAS VETERINARIAS ----------

@app.get("/api/citas")
def get_citas(
    cliente_id: Optional[int] = None,
    veterinario_id: Optional[int] = None,
    estado: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT c.*, 
                   m.nombre AS mascota_nombre, m.raza AS mascota_raza, m.imagen_url AS mascota_imagen,
                   u.nombre AS tutor_nombre, u.apellidos AS tutor_apellidos, u.telefono AS tutor_telefono, u.email AS tutor_email,
                   v.nombre AS vet_nombre, v.apellidos AS vet_apellidos, v.especialidad AS vet_especialidad,
                   s.nombre AS servicio_nombre, s.precio AS servicio_precio
            FROM citas c
            LEFT JOIN mascotas m ON c.mascota_id = m.id
            LEFT JOIN users u ON m.cliente_id = u.id
            LEFT JOIN users v ON c.veterinario_id = v.id
            LEFT JOIN servicios s ON c.servicio_id = s.id
            WHERE 1=1
        """
        params = []
        if cliente_id:
            query += " AND m.cliente_id = ?"
            params.append(cliente_id)
        if veterinario_id:
            query += " AND c.veterinario_id = ?"
            params.append(veterinario_id)
        if estado:
            query += " AND c.estado = ?"
            params.append(estado)
        
        query += " ORDER BY c.fecha_hora ASC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/citas", status_code=status.HTTP_201_CREATED)
def create_cita(c: CitaCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO citas (mascota_id, veterinario_id, servicio_id, fecha_hora, peso, motivo, notas, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Confirmada')
        """, (c.mascota_id, c.veterinario_id, c.servicio_id, c.fecha_hora, c.peso, c.motivo, c.notas))
        cita_id = cursor.lastrowid
        return {"id": cita_id, "message": "Cita programada con éxito", "estado": "Confirmada"}

@app.put("/api/citas/{cita_id}/estado")
def update_cita_status(cita_id: int, req: CitaStatusUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE citas SET estado = ? WHERE id = ?", (req.estado, cita_id))
        return {"success": True, "estado": req.estado}

# ---------- HISTORIALES MÉDICOS ----------

@app.get("/api/historiales-medicos")
def get_historiales(mascota_id: Optional[int] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT h.*, 
                   m.nombre AS mascota_nombre, m.raza AS mascota_raza,
                   v.nombre AS vet_nombre, v.apellidos AS vet_apellidos,
                   c.motivo AS cita_motivo, c.fecha_hora AS cita_fecha
            FROM historiales_medicos h
            JOIN mascotas m ON h.mascota_id = m.id
            JOIN users v ON h.veterinario_id = v.id
            LEFT JOIN citas c ON h.cita_id = c.id
        """
        params = []
        if mascota_id:
            query += " WHERE h.mascota_id = ?"
            params.append(mascota_id)
        
        query += " ORDER BY h.fecha_creacion DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

@app.post("/api/historiales-medicos", status_code=status.HTTP_201_CREATED)
def create_historial(h: HistorialCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO historiales_medicos (cita_id, mascota_id, veterinario_id, diagnostico, tratamiento, observaciones)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (h.cita_id, h.mascota_id, h.veterinario_id, h.diagnostico, h.tratamiento, h.observaciones))
        
        # Si estaba asociada a una cita, marcarla como completada
        if h.cita_id:
            cursor.execute("UPDATE citas SET estado = 'Completada' WHERE id = ?", (h.cita_id,))
        
        return {"id": cursor.lastrowid, "message": "Historial médico registrado con éxito"}

@app.get("/api/historiales")
def get_historiales_alias(mascota_id: Optional[int] = None):
    return get_historiales(mascota_id)

@app.post("/api/historiales", status_code=status.HTTP_201_CREATED)
def create_historial_alias(h: HistorialCreate):
    return create_historial(h)

# ---------- PRODUCTOS & TIENDA & INVENTARIO ----------

@app.get("/api/productos")
def get_productos(
    categoria: Optional[str] = None,
    tipo_animal: Optional[str] = None,
    search: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM productos WHERE activo = 1"
        params = []
        if categoria and categoria != "todas":
            query += " AND categoria = ?"
            params.append(categoria)
        if tipo_animal and tipo_animal != "todos":
            query += " AND (tipo_animal = ? OR tipo_animal = 'ambos' OR tipo_animal = 'todos')"
            params.append(tipo_animal)
        if search:
            query += " AND (nombre LIKE ? OR descripcion LIKE ? OR marca LIKE ? OR sku LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        result = []
        for r in rows:
            p = dict(r)
            precio = p["precio"]
            desc = p["descuento_porcentaje"] or 0
            p["precio_final"] = round(precio * (1 - desc / 100.0), 2)
            p["stock_bajo"] = p["stock"] <= p["stock_minimo"]
            result.append(p)
        return result

@app.post("/api/productos", status_code=status.HTTP_201_CREATED)
def create_producto(p: ProductoCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        sku = p.sku
        if not sku:
            prefix = p.categoria[:3].upper()
            clean_name = "".join(c for c in p.nombre[:3] if c.isalnum()).upper()
            sku = f"{prefix}-{clean_name}-{int(datetime.now().timestamp()) % 1000:03d}"
        
        img = p.imagen_url or "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=500&auto=format&fit=crop&q=80"
        cursor.execute("""
            INSERT INTO productos (nombre, descripcion, categoria, marca, precio, descuento_porcentaje, stock, stock_minimo, tipo_animal, unidad_medida, peso, sku, imagen_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (p.nombre, p.descripcion, p.categoria, p.marca, p.precio, p.descuento_porcentaje, p.stock, p.stock_minimo, p.tipo_animal, p.unidad_medida, p.peso, sku, img))
        return {"id": cursor.lastrowid, "sku": sku, "message": "Producto agregado al inventario"}

@app.put("/api/productos/{producto_id}")
def update_producto(producto_id: int, p: ProductoCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE productos 
            SET nombre = ?, descripcion = ?, categoria = ?, marca = ?, precio = ?, descuento_porcentaje = ?, stock = ?, stock_minimo = ?, tipo_animal = ?, unidad_medida = ?, peso = ?
            WHERE id = ?
        """, (p.nombre, p.descripcion, p.categoria, p.marca, p.precio, p.descuento_porcentaje, p.stock, p.stock_minimo, p.tipo_animal, p.unidad_medida, p.peso, producto_id))
        return {"success": True, "message": "Producto actualizado"}

@app.delete("/api/productos/{producto_id}")
def delete_producto(producto_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET activo = 0 WHERE id = ?", (producto_id,))
        return {"success": True, "message": "Producto eliminado del catálogo"}

# ---------- CARRITO & CHECKOUT ----------

@app.get("/api/carrito/{usuario_id}")
def get_carrito(usuario_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ci.id, ci.cantidad, p.id AS producto_id, p.nombre, p.precio, p.descuento_porcentaje, p.imagen_url, p.stock, p.sku
            FROM carrito_items ci
            JOIN productos p ON ci.producto_id = p.id
            WHERE ci.usuario_id = ?
        """, (usuario_id,))
        items = []
        total = 0.0
        for r in cursor.fetchall():
            item = dict(r)
            desc = item["descuento_porcentaje"] or 0
            unit_price = round(item["precio"] * (1 - desc / 100.0), 2)
            item["precio_final"] = unit_price
            item["subtotal"] = round(unit_price * item["cantidad"], 2)
            total += item["subtotal"]
            items.append(item)
        
        return {"items": items, "total": round(total, 2), "total_items": sum(i["cantidad"] for i in items)}

@app.post("/api/carrito/{usuario_id}")
def add_to_carrito(usuario_id: int, item: CarritoItemAdd):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, stock FROM productos WHERE id = ?", (item.producto_id,))
        p = cursor.fetchone()
        if not p or p["stock"] <= 0:
            raise HTTPException(status_code=400, detail="Producto agotado")

        cursor.execute("SELECT id, cantidad FROM carrito_items WHERE usuario_id = ? AND producto_id = ?", (usuario_id, item.producto_id))
        existing = cursor.fetchone()
        if existing:
            new_qty = existing["cantidad"] + item.cantidad
            if new_qty <= 0:
                cursor.execute("DELETE FROM carrito_items WHERE id = ?", (existing["id"],))
            else:
                cursor.execute("UPDATE carrito_items SET cantidad = ? WHERE id = ?", (new_qty, existing["id"]))
        else:
            cursor.execute("INSERT INTO carrito_items (usuario_id, producto_id, cantidad) VALUES (?, ?, ?)", (usuario_id, item.producto_id, max(1, item.cantidad)))
        
        return {"success": True}

@app.delete("/api/carrito/{usuario_id}/{producto_id}")
def remove_from_carrito(usuario_id: int, producto_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM carrito_items WHERE usuario_id = ? AND producto_id = ?", (usuario_id, producto_id))
        return {"success": True}

@app.delete("/api/carrito/{usuario_id}")
def clear_carrito(usuario_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM carrito_items WHERE usuario_id = ?", (usuario_id,))
        return {"success": True}

@app.post("/api/checkout")
def process_checkout(req: CheckoutRequest):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ci.cantidad, p.id AS producto_id, p.precio, p.descuento_porcentaje, p.stock
            FROM carrito_items ci
            JOIN productos p ON ci.producto_id = p.id
            WHERE ci.usuario_id = ?
        """, (req.usuario_id,))
        cart_items = cursor.fetchall()
        if not cart_items:
            raise HTTPException(status_code=400, detail="El carrito está vacío")
        
        total = 0.0
        for item in cart_items:
            desc = item["descuento_porcentaje"] or 0
            unit_price = round(item["precio"] * (1 - desc / 100.0), 2)
            total += unit_price * item["cantidad"]
            # Reducir stock y aumentar ventas
            new_stock = max(0, item["stock"] - item["cantidad"])
            cursor.execute("UPDATE productos SET stock = ?, total_vendidos = total_vendidos + ? WHERE id = ?", (new_stock, item["cantidad"], item["producto_id"]))
        
        # Registrar pedido
        cursor.execute("""
            INSERT INTO pedidos (usuario_id, total, metodo_pago, direccion, estado)
            VALUES (?, ?, ?, ?, 'Completado')
        """, (req.usuario_id, round(total, 2), req.metodo_pago, req.direccion))
        order_id = cursor.lastrowid
        
        # Vaciar carrito
        cursor.execute("DELETE FROM carrito_items WHERE usuario_id = ?", (req.usuario_id,))
        
        return {
            "success": True,
            "pedido_id": order_id,
            "total": round(total, 2),
            "metodo_pago": req.metodo_pago,
            "message": "¡Compra realizada con éxito! Recibirás los detalles de tu pedido por correo."
        }

# ---------- DASHBOARD & STATS ----------

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mascotas WHERE activo = 1 AND estado_adopcion = 'normal'")
        total_mascotas = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM citas")
        total_citas = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM citas WHERE estado = 'Confirmada' OR estado = 'Pendiente'")
        citas_activas = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM mascotas WHERE estado_adopcion = 'en_adopcion' AND activo = 1")
        mascotas_adopcion = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM solicitudes_adopcion WHERE estado = 'pendiente'")
        solicitudes_pendientes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM productos WHERE activo = 1")
        total_productos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM productos WHERE activo = 1 AND stock <= stock_minimo")
        stock_bajo = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos")
        ingresos_totales = cursor.fetchone()[0]

        return {
            "total_mascotas": total_mascotas,
            "total_citas": total_citas,
            "citas_activas": citas_activas,
            "mascotas_adopcion": mascotas_adopcion,
            "solicitudes_pendientes": solicitudes_pendientes,
            "total_productos": total_productos,
            "stock_bajo": stock_bajo,
            "ingresos_totales": round(ingresos_totales, 2)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
