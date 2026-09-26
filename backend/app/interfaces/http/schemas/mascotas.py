"""Esquemas Pydantic de especies, mascotas y adopciones."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from ....application.read_models import MascotaVista, SolicitudVista
from ....domain.model.mascota import Especie


class EspecieIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)


class EspecieOut(BaseModel):
    id: int
    nombre: str

    @classmethod
    def desde(cls, especie: Especie) -> "EspecieOut":
        return cls(id=especie.id, nombre=especie.nombre)


class MascotaIn(BaseModel):
    especie_id: int
    nombre: str = Field(min_length=2, max_length=100)
    sexo: str
    color: str = Field(min_length=2, max_length=50)
    cliente_id: int | None = None
    raza: str | None = None
    edad_anos: int = Field(default=1, ge=0, le=30)
    peso: float = Field(default=1.0, gt=0, le=100)
    esta_esterilizado: bool = False
    estado_adopcion: str = "normal"


class MascotaActualizarIn(BaseModel):
    especie_id: int | None = None
    nombre: str | None = None
    sexo: str | None = None
    color: str | None = None
    cliente_id: int | None = None
    raza: str | None = None
    edad_anos: int | None = Field(default=None, ge=0, le=30)
    peso: float | None = Field(default=None, gt=0, le=100)
    esta_esterilizado: bool | None = None
    estado_adopcion: str | None = None
    activo: bool | None = None


class MascotaOut(BaseModel):
    id: int
    nombre: str
    especie_id: int
    especie: str
    raza: str | None = None
    edad_anos: int
    sexo: str
    color: str
    peso: float
    esta_esterilizado: bool
    activo: bool
    estado_adopcion: str
    disponible_para_adopcion: bool
    fecha_registro: date
    cliente_id: int | None = None
    cliente_nombre: str | None = None
    cliente_email: str | None = None

    @classmethod
    def desde(cls, vista: MascotaVista) -> "MascotaOut":
        m = vista.mascota
        return cls(
            id=m.id,
            nombre=m.nombre,
            especie_id=m.especie_id,
            especie=vista.especie_nombre,
            raza=m.raza,
            edad_anos=m.edad_anos,
            sexo=m.sexo.value,
            color=m.color,
            peso=m.peso,
            esta_esterilizado=m.esta_esterilizado,
            activo=m.activo,
            estado_adopcion=m.estado_adopcion.value,
            disponible_para_adopcion=m.disponible_para_adopcion,
            fecha_registro=m.fecha_registro,
            cliente_id=m.cliente_id,
            cliente_nombre=vista.cliente_nombre,
            cliente_email=vista.cliente_email,
        )


class SolicitudAdopcionIn(BaseModel):
    mascota_id: int
    cliente_id: int
    notas_cliente: str = ""


class RevisionIn(BaseModel):
    revisor_id: int
    notas: str = ""


class CancelacionIn(BaseModel):
    cliente_id: int


class SolicitudAdopcionOut(BaseModel):
    id: int
    mascota_id: int
    mascota_nombre: str
    cliente_id: int
    cliente_nombre: str
    cliente_email: str
    estado: str
    fecha_solicitud: datetime
    fecha_actualizacion: datetime
    fecha_revision: datetime | None = None
    revisado_por_id: int | None = None
    revisor_nombre: str | None = None
    notas_cliente: str = ""
    notas_revisor: str = ""

    @classmethod
    def desde(cls, vista: SolicitudVista) -> "SolicitudAdopcionOut":
        s = vista.solicitud
        return cls(
            id=s.id,
            mascota_id=s.mascota_id,
            mascota_nombre=vista.mascota_nombre,
            cliente_id=s.cliente_id,
            cliente_nombre=vista.cliente_nombre,
            cliente_email=vista.cliente_email,
            estado=s.estado.value,
            fecha_solicitud=s.fecha_solicitud,
            fecha_actualizacion=s.fecha_actualizacion,
            fecha_revision=s.fecha_revision,
            revisado_por_id=s.revisado_por_id,
            revisor_nombre=vista.revisor_nombre,
            notas_cliente=s.notas_cliente,
            notas_revisor=s.notas_revisor,
        )
