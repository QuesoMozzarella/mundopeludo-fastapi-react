"""Contexto historiales_medicos - legacy_django/historiales_medicos/models.py."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..errors import ValidationError


def _requerido(valor: str, campo: str) -> str:
    limpio = (valor or "").strip()
    if len(limpio) < 3:
        raise ValidationError("El campo " + campo + " debe tener al menos 3 caracteres", campo)
    return limpio


@dataclass
class HistorialMedico:
    """HistorialMedico: ficha clinica 1-1 con una cita."""

    cita_id: int
    veterinario_id: int
    diagnostico: str
    tratamiento: str
    observaciones: str | None = None
    fecha_creacion: datetime = field(default_factory=datetime.now)
    id: int | None = None

    def __post_init__(self) -> None:
        self.diagnostico = _requerido(self.diagnostico, "diagnostico")
        self.tratamiento = _requerido(self.tratamiento, "tratamiento")
        self.observaciones = (self.observaciones or "").strip() or None
        if self.cita_id is None:
            raise ValidationError("El historial debe estar asociado a una cita", "cita_id")

    def actualizar(
        self,
        diagnostico: str | None = None,
        tratamiento: str | None = None,
        observaciones: str | None = None,
    ) -> None:
        if diagnostico is not None:
            self.diagnostico = _requerido(diagnostico, "diagnostico")
        if tratamiento is not None:
            self.tratamiento = _requerido(tratamiento, "tratamiento")
        if observaciones is not None:
            self.observaciones = observaciones.strip() or None
