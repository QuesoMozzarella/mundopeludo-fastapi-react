"""Esquemas Pydantic del contexto usuarios (contrato HTTP).

El formato del correo lo valida la entidad `Usuario` del dominio, por eso aquí
basta con `str` y no hace falta la dependencia opcional `email-validator`.
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from ....application.read_models import UsuarioVista
from ....domain.model.usuario import Especialidad, PerfilCliente, PerfilVeterinario


class LoginIn(BaseModel):
    email: str
    password: str


class RegistroIn(BaseModel):
    email: str
    password: str = Field(min_length=8)
    nombre: str = Field(min_length=2, max_length=100)
    apellidos: str = Field(min_length=2, max_length=100)
    telefono: str | None = None
    direccion: str | None = None
    tipo: str = "cliente"
    documento: str | None = None
    especialidades_ids: list[int] = Field(default_factory=list)


class UsuarioActualizarIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str | None = None
    nombre: str | None = None
    apellidos: str | None = None
    telefono: str | None = None
    direccion: str | None = None
    tipo: str | None = None
    documento: str | None = None
    is_active: bool | None = None


class CambioPasswordIn(BaseModel):
    password_actual: str
    password_nueva: str = Field(min_length=8)


class RecuperacionIn(BaseModel):
    email: str


class RestablecerIn(BaseModel):
    email: str
    codigo: str = Field(min_length=6, max_length=6)
    password_nueva: str = Field(min_length=8)


class UsuarioOut(BaseModel):
    id: int
    email: str
    nombre: str
    apellidos: str
    nombre_completo: str
    telefono: str | None = None
    direccion: str | None = None
    tipo: str
    activo: bool
    documento: str | None = None
    especialidades: list[str] = Field(default_factory=list)
    fecha_registro: datetime | None = None
    ultimo_acceso: datetime | None = None

    @classmethod
    def desde(cls, vista: UsuarioVista) -> "UsuarioOut":
        usuario = vista.usuario
        documento = None
        if vista.perfil_cliente:
            documento = vista.perfil_cliente.documento
        elif vista.perfil_veterinario:
            documento = vista.perfil_veterinario.documento
        return cls(
            id=usuario.id,
            email=usuario.email,
            nombre=usuario.nombre,
            apellidos=usuario.apellidos,
            nombre_completo=usuario.nombre_completo,
            telefono=usuario.telefono,
            direccion=usuario.direccion,
            tipo=usuario.tipo.value,
            activo=usuario.is_active,
            documento=documento,
            especialidades=vista.especialidades,
            fecha_registro=usuario.date_joined,
            ultimo_acceso=usuario.last_login,
        )


class SesionOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en_minutos: int
    usuario: UsuarioOut


class EspecialidadIn(BaseModel):
    codigo: str = Field(min_length=2, max_length=50)
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str | None = None
    activa: bool = True


class EspecialidadActualizarIn(BaseModel):
    codigo: str | None = None
    nombre: str | None = None
    descripcion: str | None = None
    activa: bool | None = None


class EspecialidadOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    activa: bool

    @classmethod
    def desde(cls, especialidad: Especialidad) -> "EspecialidadOut":
        return cls(
            id=especialidad.id,
            codigo=especialidad.codigo,
            nombre=especialidad.nombre,
            descripcion=especialidad.descripcion,
            activa=especialidad.activa,
        )


class PerfilClienteIn(BaseModel):
    documento: str | None = None


class PerfilClienteOut(BaseModel):
    usuario_id: int
    documento: str | None = None
    fecha_actualizacion: datetime

    @classmethod
    def desde(cls, perfil: PerfilCliente) -> "PerfilClienteOut":
        return cls(
            usuario_id=perfil.usuario_id,
            documento=perfil.documento,
            fecha_actualizacion=perfil.fecha_actualizacion,
        )


class PerfilVeterinarioIn(BaseModel):
    documento: str | None = None
    activo: bool | None = None
    fecha_contratacion: date | None = None
    especialidades_ids: list[int] | None = None


class PerfilVeterinarioOut(BaseModel):
    usuario_id: int
    documento: str | None = None
    activo: bool
    fecha_contratacion: date
    especialidades_ids: list[int]

    @classmethod
    def desde(cls, perfil: PerfilVeterinario) -> "PerfilVeterinarioOut":
        return cls(
            usuario_id=perfil.usuario_id,
            documento=perfil.documento,
            activo=perfil.activo,
            fecha_contratacion=perfil.fecha_contratacion,
            especialidades_ids=perfil.especialidades_ids,
        )
