"""Contexto `citas` - adaptacion de legacy_django/citas/models.py.

Modelos Django originales: EstadoCita, Servicio, Disponibilidad, Cita.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from decimal import Decimal

from ..errors import ValidationError
from ..value_objects import DiaSemana, dinero, hora_local

DURACION_POR_DEFECTO = 30  # minutos: lo que ocupaba toda cita antes de recuperar la duracion
DURACION_MINIMA = 5
DURACION_MAXIMA = 8 * 60


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

    `precio` y `duracion_min` existian en el modelo Django hasta la migracion
    0007, que los elimino; aqui se recuperan. El precio es opcional (un
    servicio puede no tenerlo publicado) y la duracion decide cuanto tiempo de
    la agenda ocupa cada cita.
    """

    nombre: str
    descripcion: str | None = None
    activo: bool = True
    precio: Decimal | None = None
    duracion_min: int = DURACION_POR_DEFECTO
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
        if self.precio is not None:
            self.precio = dinero(self.precio, campo="precio")
            if self.precio < 0:
                raise ValidationError("El precio no puede ser negativo", "precio")
        self.duracion_min = _duracion(self.duracion_min)
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

    def cubre(self, momento: datetime, minutos: int = 0) -> bool:
        """La franja contiene `momento` y, si se indica, los `minutos` siguientes."""
        if momento.weekday() != self.dia_semana.value:
            return False
        inicio = datetime.combine(momento.date(), self.hora_inicio)
        fin = datetime.combine(momento.date(), self.hora_fin)
        if not inicio <= momento < fin:
            return False
        return momento + timedelta(minutes=minutos) <= fin

    def se_solapa_con(self, otra: "Disponibilidad") -> bool:
        if otra.veterinario_id != self.veterinario_id:
            return False
        if otra.dia_semana is not self.dia_semana:
            return False
        return self.hora_inicio < otra.hora_fin and otra.hora_inicio < self.hora_fin


def _duracion(valor) -> int:
    try:
        minutos = int(valor)
    except (TypeError, ValueError):
        raise ValidationError("La duracion debe ser un numero de minutos", "duracion_min") from None
    if not DURACION_MINIMA <= minutos <= DURACION_MAXIMA:
        raise ValidationError(
            f"La duracion debe estar entre {DURACION_MINIMA} y {DURACION_MAXIMA} minutos",
            "duracion_min",
        )
    return minutos


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

    def se_solapa_con(
        self,
        otra: "Cita",
        minutos: int = DURACION_POR_DEFECTO,
        minutos_otra: int | None = None,
    ) -> bool:
        """Dos citas del mismo veterinario se pisan si sus intervalos se cruzan.

        `minutos` es lo que dura esta cita y `minutos_otra` lo que dura la
        otra (por defecto, lo mismo): cada una ocupa [inicio, inicio + duracion).
        """
        if otra.veterinario_id != self.veterinario_id or otra.id == self.id:
            return False
        return se_cruzan(
            self.fecha_hora,
            minutos,
            otra.fecha_hora,
            minutos if minutos_otra is None else minutos_otra,
        )


def se_cruzan(inicio: datetime, minutos: int, otro_inicio: datetime, otros_minutos: int) -> bool:
    """Los intervalos [inicio, inicio + minutos) y [otro_inicio, ...) se cruzan."""
    fin = inicio + timedelta(minutes=minutos)
    otro_fin = otro_inicio + timedelta(minutes=otros_minutos)
    return inicio < otro_fin and otro_inicio < fin


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
