"""Contexto transversal — adaptación de `legacy_django/sananimal_clinic/models.py`.

Modelos Django originales: ActividadSistema, CodigoRecuperacion.
"""
from __future__ import annotations

import hmac
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..errors import ValidationError

HORAS_VIGENCIA_CODIGO = 1
MAX_INTENTOS_CODIGO = 5


@dataclass
class ActividadSistema:
    """`ActividadSistema`: bitácora de acciones, ordenada por fecha descendente."""

    usuario: str
    tipo: str
    descripcion: str
    fecha: datetime = field(default_factory=datetime.now)
    id: int | None = None

    def __post_init__(self) -> None:
        self.usuario = (self.usuario or "sistema").strip()[:255] or "sistema"
        tipo = (self.tipo or "").strip()
        if not tipo:
            raise ValidationError("El tipo de actividad es obligatorio", "tipo")
        self.tipo = tipo[:50]
        descripcion = (self.descripcion or "").strip()
        if not descripcion:
            raise ValidationError("La descripción de la actividad es obligatoria", "descripcion")
        self.descripcion = descripcion


@dataclass
class CodigoRecuperacion:
    """`CodigoRecuperacion`: código de 6 dígitos con vigencia de una hora."""

    usuario_id: int
    codigo: str
    fecha_creacion: datetime = field(default_factory=datetime.now)
    fecha_expiracion: datetime | None = None
    intentos: int = 0
    activo: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        codigo = (self.codigo or "").strip()
        if not (codigo.isdigit() and len(codigo) == 6):
            raise ValidationError("El código debe tener exactamente 6 dígitos", "codigo")
        self.codigo = codigo
        if self.fecha_expiracion is None:
            # Mismo default que el `save()` del modelo Django.
            self.fecha_expiracion = self.fecha_creacion + timedelta(hours=HORAS_VIGENCIA_CODIGO)
        self.intentos = max(0, int(self.intentos or 0))

    def esta_expirado(self, ahora: datetime) -> bool:
        return ahora > self.fecha_expiracion

    def es_utilizable(self, ahora: datetime) -> bool:
        return self.activo and not self.esta_expirado(ahora) and self.intentos < MAX_INTENTOS_CODIGO

    def coincide(self, codigo: str) -> bool:
        """Comparación en tiempo constante: no filtra cuántos dígitos acertó."""
        return hmac.compare_digest(self.codigo, (codigo or "").strip())

    def incrementar_intento(self) -> None:
        self.intentos += 1
        if self.intentos >= MAX_INTENTOS_CODIGO:
            self.activo = False

    def consumir(self) -> None:
        """Un código sólo sirve una vez."""
        self.activo = False
