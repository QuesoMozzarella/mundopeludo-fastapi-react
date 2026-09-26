"""Modelos de lectura.

Las entidades de dominio sólo guardan identificadores (`cliente_id`,
`especie_id`, ...). Las pantallas necesitan además los nombres asociados, así
que los casos de uso de consulta devuelven estos agregados de lectura en vez de
obligar al adaptador HTTP a hacer joins por su cuenta.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from ..domain.model.cita import Cita, Disponibilidad, Servicio
from ..domain.model.historial import HistorialMedico
from ..domain.model.inventario import Carrito, CarritoItem, Producto
from ..domain.model.mascota import Mascota, SolicitudAdopcion
from ..domain.model.usuario import PerfilCliente, PerfilVeterinario, Usuario


@dataclass
class UsuarioVista:
    usuario: Usuario
    perfil_cliente: PerfilCliente | None = None
    perfil_veterinario: PerfilVeterinario | None = None
    especialidades: list[str] = field(default_factory=list)


@dataclass
class MascotaVista:
    mascota: Mascota
    especie_nombre: str = ""
    cliente_nombre: str | None = None
    cliente_email: str | None = None


@dataclass
class SolicitudVista:
    solicitud: SolicitudAdopcion
    mascota_nombre: str = ""
    cliente_nombre: str = ""
    cliente_email: str = ""
    revisor_nombre: str | None = None


@dataclass
class ServicioVista:
    servicio: Servicio
    veterinarios: list[str] = field(default_factory=list)
    especialidades: list[str] = field(default_factory=list)


@dataclass
class DisponibilidadVista:
    disponibilidad: Disponibilidad
    veterinario_nombre: str = ""


@dataclass
class CitaVista:
    cita: Cita
    mascota_nombre: str = ""
    cliente_id: int | None = None
    cliente_nombre: str | None = None
    veterinario_nombre: str = ""
    servicio_nombre: str = ""
    estado_nombre: str = ""
    tiene_historial: bool = False


@dataclass
class HistorialVista:
    historial: HistorialMedico
    mascota_id: int | None = None
    cliente_id: int | None = None
    mascota_nombre: str = ""
    veterinario_nombre: str = ""
    fecha_cita: datetime | None = None


@dataclass
class ItemCarritoVista:
    item: CarritoItem
    nombre: str = ""
    sku: str = ""
    stock: int = 0
    categoria: str = ""


@dataclass
class CarritoVista:
    carrito: Carrito
    items: list[ItemCarritoVista] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return self.carrito.total


@dataclass
class ProductoVista:
    producto: Producto
    imagenes_ids: list[int] = field(default_factory=list)


@dataclass
class EstadisticasDashboard:
    total_usuarios: int = 0
    total_clientes: int = 0
    total_veterinarios: int = 0
    total_mascotas: int = 0
    mascotas_en_adopcion: int = 0
    solicitudes_pendientes: int = 0
    citas_hoy: int = 0
    citas_totales: int = 0
    total_productos: int = 0
    productos_stock_bajo: int = 0
    productos_por_vencer: int = 0
    historiales_registrados: int = 0
    ingresos_totales: float = 0.0
