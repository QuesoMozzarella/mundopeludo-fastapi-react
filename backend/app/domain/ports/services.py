"""Puertos de salida: servicios técnicos que el dominio necesita pero no implementa."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime

from ..model.sistema import CodigoRecuperacion
from ..model.usuario import Usuario


class PasswordHasher(ABC):
    """Reemplaza a `user.set_password()` / `check_password()` de Django."""

    @abstractmethod
    def hash(self, password_plano: str) -> str: ...

    @abstractmethod
    def verificar(self, password_plano: str, hash_guardado: str) -> bool: ...


class TokenService(ABC):
    """Emite y valida las credenciales de sesión (JWT HS256)."""

    @abstractmethod
    def emitir(self, sujeto: int, datos: dict | None = None) -> str: ...

    @abstractmethod
    def decodificar(self, token: str) -> dict:
        """Devuelve el payload o lanza `AuthenticationError`."""

    @property
    @abstractmethod
    def minutos_vigencia(self) -> int:
        """Minutos que dura un token recién emitido."""


class Clock(ABC):
    """Reloj inyectable: hace que los casos de uso sean deterministas en tests."""

    @abstractmethod
    def ahora(self) -> datetime: ...

    def hoy(self) -> date:
        return self.ahora().date()


@dataclass(frozen=True)
class AvisoCita:
    """Lo que el tutor necesita saber de una cita, ya resuelto a textos."""

    email: str
    nombre: str
    mascota: str
    fecha_hora: datetime
    veterinario: str
    servicio: str
    motivo: str


@dataclass(frozen=True)
class AvisoHistorial:
    """Resumen de la ficha clínica que recibe el tutor de la mascota."""

    email: str
    nombre: str
    mascota: str
    fecha: datetime
    veterinario: str
    diagnostico: str
    tratamiento: str
    observaciones: str | None = None


class Notificaciones(ABC):
    """Avisos a los usuarios. Hoy salen por correo; el dominio no lo sabe.

    Si el aviso no puede entregarse, la implementación lanza
    `ServicioNoDisponibleError`.
    """

    @abstractmethod
    def codigo_recuperacion(self, usuario: Usuario, codigo: CodigoRecuperacion) -> None: ...

    @abstractmethod
    def cita_confirmada(self, aviso: AvisoCita) -> None: ...

    @abstractmethod
    def cita_cancelada(self, aviso: AvisoCita) -> None: ...

    @abstractmethod
    def historial_registrado(self, aviso: AvisoHistorial) -> None: ...


class GeneradorCodigos(ABC):
    """Genera los códigos numéricos de recuperación de contraseña."""

    @abstractmethod
    def numerico(self, longitud: int = 6) -> str: ...
