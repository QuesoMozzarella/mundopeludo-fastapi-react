"""Esquemas Pydantic de la bitácora y del panel de indicadores."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from ....application.read_models import EstadisticasDashboard
from ....domain.model.sistema import ActividadSistema


class ActividadIn(BaseModel):
    usuario: str
    tipo: str
    descripcion: str


class ActividadOut(BaseModel):
    id: int
    usuario: str
    tipo: str
    descripcion: str
    fecha: datetime

    @classmethod
    def desde(cls, actividad: ActividadSistema) -> "ActividadOut":
        return cls(
            id=actividad.id,
            usuario=actividad.usuario,
            tipo=actividad.tipo,
            descripcion=actividad.descripcion,
            fecha=actividad.fecha,
        )


class EstadisticasOut(BaseModel):
    total_usuarios: int
    total_clientes: int
    total_veterinarios: int
    total_mascotas: int
    mascotas_en_adopcion: int
    solicitudes_pendientes: int
    citas_hoy: int
    citas_totales: int
    total_productos: int
    productos_stock_bajo: int
    productos_por_vencer: int
    historiales_registrados: int
    ingresos_totales: float

    @classmethod
    def desde(cls, stats: EstadisticasDashboard) -> "EstadisticasOut":
        return cls(**stats.__dict__)


class SaludOut(BaseModel):
    status: str = "ok"
    servicio: str = "MundoPeludo API"
    version: str
    arquitectura: str = "hexagonal (puertos y adaptadores)"
    persistencia: str = "sqlite3"
