"""Contexto `usuarios` — adaptación de `legacy_django/usuarios/models.py`.

Modelos Django originales: CustomUser, PerfilCliente, Especialidad, PerfilVeterinario.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime

from ..errors import ValidationError
from ..value_objects import TipoUsuario

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _texto(valor: str | None, *, campo: str, minimo: int = 1, maximo: int = 255,
           obligatorio: bool = True) -> str | None:
    limpio = (valor or "").strip()
    if not limpio:
        if obligatorio:
            raise ValidationError(f"El campo '{campo}' es obligatorio", campo)
        return None
    if len(limpio) < minimo:
        raise ValidationError(f"'{campo}' debe tener al menos {minimo} caracteres", campo)
    if len(limpio) > maximo:
        raise ValidationError(f"'{campo}' no puede superar {maximo} caracteres", campo)
    return limpio


@dataclass
class Usuario:
    """`CustomUser`: autenticación por email, sin username."""

    email: str
    nombre: str
    apellidos: str
    tipo: TipoUsuario = TipoUsuario.CLIENTE
    telefono: str | None = None
    direccion: str | None = None
    password_hash: str = ""
    is_active: bool = True
    is_staff: bool = False
    is_superuser: bool = False
    date_joined: datetime = field(default_factory=datetime.now)
    last_login: datetime | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.email = _texto(self.email, campo="email", maximo=254).lower()
        if not _EMAIL_RE.match(self.email):
            raise ValidationError("El correo electrónico no tiene un formato válido", "email")
        self.nombre = _texto(self.nombre, campo="nombre", minimo=2, maximo=100)
        self.apellidos = _texto(self.apellidos, campo="apellidos", minimo=2, maximo=100)
        self.telefono = _texto(self.telefono, campo="telefono", maximo=20, obligatorio=False)
        self.direccion = _texto(self.direccion, campo="direccion", maximo=255, obligatorio=False)
        self.tipo = TipoUsuario.desde(self.tipo, campo="tipo", por_defecto=TipoUsuario.CLIENTE)
        if self.tipo is TipoUsuario.ADMINISTRADOR:
            # `create_superuser` del manager original fuerza staff/superuser.
            self.is_staff = True

    @property
    def nombre_completo(self) -> str:
        """Equivalente a `CustomUser.get_full_name()`."""
        return f"{self.nombre} {self.apellidos}".strip()

    @property
    def es_cliente(self) -> bool:
        return self.tipo is TipoUsuario.CLIENTE

    @property
    def es_veterinario(self) -> bool:
        return self.tipo is TipoUsuario.VETERINARIO

    @property
    def es_administrador(self) -> bool:
        return self.tipo is TipoUsuario.ADMINISTRADOR

    def registrar_acceso(self, momento: datetime) -> None:
        self.last_login = momento

    def desactivar(self) -> None:
        """Baja lógica: Django nunca borraba usuarios, los marcaba inactivos."""
        self.is_active = False


@dataclass
class PerfilCliente:
    """`PerfilCliente`: datos extra de un usuario de tipo cliente (1–1)."""

    usuario_id: int
    documento: str | None = None
    fecha_actualizacion: datetime = field(default_factory=datetime.now)
    id: int | None = None

    def __post_init__(self) -> None:
        self.documento = _texto(self.documento, campo="documento", maximo=20, obligatorio=False)


@dataclass
class Especialidad:
    """`Especialidad`: catálogo compartido por veterinarios y servicios."""

    codigo: str
    nombre: str
    descripcion: str | None = None
    activa: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        self.codigo = _texto(self.codigo, campo="codigo", minimo=2, maximo=50).lower()
        self.nombre = _texto(self.nombre, campo="nombre", minimo=2, maximo=100)
        self.descripcion = _texto(
            self.descripcion, campo="descripcion", maximo=2000, obligatorio=False
        )


@dataclass
class PerfilVeterinario:
    """`PerfilVeterinario` (1–1 con usuario) + M2M con `Especialidad`."""

    usuario_id: int
    fecha_contratacion: date = field(default_factory=date.today)
    documento: str | None = None
    activo: bool = False
    especialidades_ids: list[int] = field(default_factory=list)
    id: int | None = None

    def __post_init__(self) -> None:
        self.documento = _texto(self.documento, campo="documento", maximo=10, obligatorio=False)
        if isinstance(self.fecha_contratacion, datetime):
            self.fecha_contratacion = self.fecha_contratacion.date()
        if self.fecha_contratacion > date.today():
            raise ValidationError(
                "La fecha de contratación no puede ser futura", "fecha_contratacion"
            )
        self.especialidades_ids = sorted({int(i) for i in self.especialidades_ids})

    def asignar_especialidades(self, ids: list[int]) -> None:
        self.especialidades_ids = sorted({int(i) for i in ids})

    def activar(self) -> None:
        self.activo = True

    def desactivar(self) -> None:
        self.activo = False
