"""Esquemas Pydantic de la agenda y de los historiales médicos."""
from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal

from pydantic import BaseModel, Field

from ....application.read_models import CitaVista, DisponibilidadVista, HistorialVista, ServicioVista
from ....domain.model.cita import (
    DURACION_MAXIMA,
    DURACION_MINIMA,
    DURACION_POR_DEFECTO,
    Disponibilidad,
    EstadoCita,
)


class EstadoCitaIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=50)
    descripcion: str | None = None
    orden: int = 0


class EstadoCitaOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    orden: int

    @classmethod
    def desde(cls, estado: EstadoCita) -> "EstadoCitaOut":
        return cls(
            id=estado.id,
            nombre=estado.nombre,
            descripcion=estado.descripcion,
            orden=estado.orden,
        )


class ServicioIn(BaseModel):
    nombre: str = Field(min_length=3, max_length=100)
    descripcion: str | None = None
    activo: bool = True
    precio: Decimal | None = Field(default=None, ge=0, description="Sin precio publicado: null")
    duracion_min: int = Field(
        default=DURACION_POR_DEFECTO,
        ge=DURACION_MINIMA,
        le=DURACION_MAXIMA,
        description="Minutos de agenda que ocupa cada cita del servicio",
    )
    veterinarios_ids: list[int] = Field(default_factory=list)
    especialidades_ids: list[int] = Field(default_factory=list)


class ServicioActualizarIn(BaseModel):
    """`precio: null` retira el precio publicado; `duracion_min: null` no la cambia."""

    nombre: str | None = None
    descripcion: str | None = None
    activo: bool | None = None
    precio: Decimal | None = Field(default=None, ge=0)
    duracion_min: int | None = Field(default=None, ge=DURACION_MINIMA, le=DURACION_MAXIMA)
    veterinarios_ids: list[int] | None = None
    especialidades_ids: list[int] | None = None


class ServicioOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    activo: bool
    precio: float | None = None
    duracion_min: int
    veterinarios_ids: list[int]
    veterinarios: list[str]
    especialidades_ids: list[int]
    especialidades: list[str]

    @classmethod
    def desde(cls, vista: ServicioVista) -> "ServicioOut":
        s = vista.servicio
        return cls(
            id=s.id,
            nombre=s.nombre,
            descripcion=s.descripcion,
            activo=s.activo,
            precio=s.precio,
            duracion_min=s.duracion_min,
            veterinarios_ids=s.veterinarios_ids,
            veterinarios=vista.veterinarios,
            especialidades_ids=s.especialidades_ids,
            especialidades=vista.especialidades,
        )


class DisponibilidadIn(BaseModel):
    veterinario_id: int
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: time
    hora_fin: time


class DisponibilidadOut(BaseModel):
    id: int
    veterinario_id: int
    veterinario_nombre: str
    dia_semana: int
    dia: str
    hora_inicio: time
    hora_fin: time

    @classmethod
    def desde(cls, vista: DisponibilidadVista) -> "DisponibilidadOut":
        d: Disponibilidad = vista.disponibilidad
        return cls(
            id=d.id,
            veterinario_id=d.veterinario_id,
            veterinario_nombre=vista.veterinario_nombre,
            dia_semana=d.dia_semana.value,
            dia=d.dia_etiqueta,
            hora_inicio=d.hora_inicio,
            hora_fin=d.hora_fin,
        )


class CitaIn(BaseModel):
    mascota_id: int
    veterinario_id: int
    servicio_id: int
    fecha_hora: datetime
    motivo: str = Field(min_length=3, max_length=200)
    peso: float | None = None
    notas: str | None = None
    estado: str | None = None
    estado_id: int | None = None


class CitaActualizarIn(BaseModel):
    veterinario_id: int | None = None
    servicio_id: int | None = None
    fecha_hora: datetime | None = None
    motivo: str | None = None
    peso: float | None = None
    notas: str | None = None
    estado: str | None = None
    estado_id: int | None = None


class CambioEstadoIn(BaseModel):
    estado: str | None = None
    estado_id: int | None = None


class CitaOut(BaseModel):
    id: int
    mascota_id: int
    mascota_nombre: str
    mascota_raza: str | None = None
    mascota_imagen_url: str | None = None
    cliente_id: int | None = None
    cliente_nombre: str | None = None
    cliente_email: str | None = None
    cliente_telefono: str | None = None
    veterinario_id: int
    veterinario_nombre: str
    servicio_id: int
    servicio_nombre: str
    servicio_precio: float | None = None
    servicio_duracion_min: int
    estado_id: int
    estado: str
    fecha_hora: datetime
    peso: float
    motivo: str
    notas: str | None = None
    tiene_historial: bool

    @classmethod
    def desde(cls, vista: CitaVista) -> "CitaOut":
        c = vista.cita
        return cls(
            id=c.id,
            mascota_id=c.mascota_id,
            mascota_nombre=vista.mascota_nombre,
            mascota_raza=vista.mascota_raza,
            mascota_imagen_url=vista.mascota_imagen_url,
            cliente_id=vista.cliente_id,
            cliente_nombre=vista.cliente_nombre,
            cliente_email=vista.cliente_email,
            cliente_telefono=vista.cliente_telefono,
            veterinario_id=c.veterinario_id,
            veterinario_nombre=vista.veterinario_nombre,
            servicio_id=c.servicio_id,
            servicio_nombre=vista.servicio_nombre,
            servicio_precio=vista.servicio_precio,
            servicio_duracion_min=vista.servicio_duracion_min,
            estado_id=c.estado_id,
            estado=vista.estado_nombre,
            fecha_hora=c.fecha_hora,
            peso=c.peso,
            motivo=c.motivo,
            notas=c.notas,
            tiene_historial=vista.tiene_historial,
        )


class HistorialIn(BaseModel):
    """Con `cita_id` la mascota sale de la cita; sin ella, `mascota_id` y
    `veterinario_id` son obligatorios."""

    cita_id: int | None = None
    mascota_id: int | None = None
    diagnostico: str = Field(min_length=3)
    tratamiento: str = Field(min_length=3)
    observaciones: str | None = None
    veterinario_id: int | None = None


class HistorialActualizarIn(BaseModel):
    diagnostico: str | None = None
    tratamiento: str | None = None
    observaciones: str | None = None


class HistorialOut(BaseModel):
    id: int
    cita_id: int | None = None
    mascota_id: int
    mascota_nombre: str
    mascota_raza: str | None = None
    veterinario_id: int
    veterinario_nombre: str
    diagnostico: str
    tratamiento: str
    observaciones: str | None = None
    fecha_creacion: datetime
    fecha_cita: datetime | None = None

    @classmethod
    def desde(cls, vista: HistorialVista) -> "HistorialOut":
        h = vista.historial
        return cls(
            id=h.id,
            cita_id=h.cita_id,
            mascota_id=h.mascota_id,
            mascota_nombre=vista.mascota_nombre,
            mascota_raza=vista.mascota_raza,
            veterinario_id=h.veterinario_id,
            veterinario_nombre=vista.veterinario_nombre,
            diagnostico=h.diagnostico,
            tratamiento=h.tratamiento,
            observaciones=h.observaciones,
            fecha_creacion=h.fecha_creacion,
            fecha_cita=vista.fecha_cita,
        )
