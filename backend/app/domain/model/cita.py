"""Contexto `citas` - adaptacion de legacy_django/citas/models.py.

Modelos Django originales: EstadoCita, Servicio, Disponibilidad, Cita.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time

from ..errors import ValidationError
from ..value_objects import DiaSemana, hora_local


@dataclass
class EstadoCita:
    """EstadoCita: catalogo ordenable de estados (Pendiente, Confirmada, ...)."""

    nombre: str
    descripcion: str | None = None
    orden: int = 0
    id: int | None = None

    def __post_init__(self) -> None:
        nombre = (self.nombre or "").strip()
        if len(nombre) < 3:
            raise ValidationError("El nombre del estado debe tener al menos 3 caracteres", "nombre")
        if len(nombre) > 50:
            raise ValidationError("El nombre del estado no puede superar 50 caracteres", "nombre")
        self.nombre = nombre
        self.descripcion = (self.descripcion or "").strip() or None
        self.orden = max(0, int(self.orden or 0))


@dataclass
class Servicio:
    """Servicio con sus dos M2M: veterinarios habilitados y especialidades.

    Nota de fidelidad: la migracion 0007 elimino `precio` y `duracion` del
    modelo Django, asi que aqui tampoco existen.
    """

    nombre: str
    descripcion: str | None = None
    activo: bool = True
    veterinarios_ids: list[int] = field(default_factory=list)
    especialidades_ids: list[int] = field(default_factory=list)
    id: int | None = None

    def __post_init__(self) -> None:
        nombre = (self.nombre or "").strip()
        if len(nombre) < 3:
            raise ValidationError("El nombre del servicio debe tener al menos 3 caracteres", "nombre")
        if len(nombre) > 100:
            raise ValidationError("El nombre del servicio no puede superar 100 caracteres", "nombre")
        self.nombre = nombre
        self.descripcion = (self.descripcion or "").strip() or None
        self.veterinarios_ids = sorted({int(i) for i in self.veterinarios_ids})
        self.especialidades_ids = sorted({int(i) for i in self.especialidades_ids})

    def admite_veterinario(self, veterinario_id: int) -> bool:
        """Sin veterinarios asignados, el servicio lo puede prestar cualquiera."""
        return not self.veterinarios_ids or veterinario_id in self.veterinarios_ids


@dataclass
class Disponibilidad:
    """Disponibilidad: franja semanal de un veterinario.

    Unicidad (veterinario, dia_semana, hora_inicio, hora_fin), igual que el
    unique_together original.
    """

    veterinario_id: int
    dia_semana: DiaSemana
    hora_inicio: time
    hora_fin: time
    id: int | None = None

    def __post_init__(self) -> None:
        self.dia_semana = DiaSemana.desde(self.dia_semana)
        self.hora_inicio = _hora(self.hora_inicio, "hora_inicio")
        self.hora_fin = _hora(self.hora_fin, "hora_fin")
        if self.hora_inicio >= self.hora_fin:
            raise ValidationError(
                "La hora de inicio debe ser anterior a la hora de fin", "hora_inicio"
            )

    @property
    def dia_etiqueta(self) -> str:
        return self.dia_semana.etiqueta

    def cubre(self, momento: datetime) -> bool:
        if momento.weekday() != self.dia_semana.value:
            return False
        return self.hora_inicio <= momento.time() < self.hora_fin

    def se_solapa_con(self, otra: "Disponibilidad") -> bool:
        if otra.veterinario_id != self.veterinario_id:
            return False
        if otra.dia_semana is not self.dia_semana:
            return False
        return self.hora_inicio < otra.hora_fin and otra.hora_inicio < self.hora_fin


def _hora(valor, campo: str) -> time:
    if isinstance(valor, time):
        return valor.replace(second=0, microsecond=0)
    if isinstance(valor, datetime):
        return valor.time().replace(second=0, microsecond=0)
    texto = str(valor or "").strip()
    for formato in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(texto, formato).time().replace(second=0, microsecond=0)
        except ValueError:
            continue
    raise ValidationError("El campo " + campo + " debe tener formato HH:MM", campo)


@dataclass
class Cita:
    """Cita: mascota + veterinario + servicio + estado en una fecha/hora."""

    mascota_id: int
    veterinario_id: int
    estado_id: int
    servicio_id: int
    fecha_hora: datetime
    motivo: str
    peso: float = 0.0
    notas: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.fecha_hora = _fecha_hora(self.fecha_hora)
        motivo = (self.motivo or "").strip()
        if len(motivo) < 3:
            raise ValidationError("El motivo debe tener al menos 3 caracteres", "motivo")
        if len(motivo) > 200:
            raise ValidationError("El motivo no puede superar 200 caracteres", "motivo")
        self.motivo = motivo
        self.notas = (self.notas or "").strip() or None
        try:
            self.peso = float(self.peso or 0.0)
        except (TypeError, ValueError):
            raise ValidationError("El peso debe ser un numero", "peso") from None
        if self.peso < 0:
            raise ValidationError("El peso no puede ser negativo", "peso")

    def reprogramar(self, nueva_fecha: datetime) -> None:
        self.fecha_hora = _fecha_hora(nueva_fecha)

    def cambiar_estado(self, estado_id: int) -> None:
        self.estado_id = int(estado_id)

    def se_solapa_con(self, otra: "Cita", minutos: int = 30) -> bool:
        """Dos citas del mismo veterinario a menos de N minutos se pisan."""
        if otra.veterinario_id != self.veterinario_id or otra.id == self.id:
            return False
        delta = abs((otra.fecha_hora - self.fecha_hora).total_seconds())
        return delta < minutos * 60


def _fecha_hora(valor) -> datetime:
    if isinstance(valor, datetime):
        return hora_local(valor).replace(microsecond=0)
    texto = str(valor or "").strip().replace("Z", "+00:00")
    try:
        return hora_local(datetime.fromisoformat(texto)).replace(microsecond=0)
    except ValueError:
        raise ValidationError(
            "fecha_hora debe ser una fecha ISO 8601 (YYYY-MM-DDTHH:MM)", "fecha_hora"
        ) from None
