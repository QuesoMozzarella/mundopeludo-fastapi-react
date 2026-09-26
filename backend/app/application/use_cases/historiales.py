"""Casos de uso de historiales médicos."""
from __future__ import annotations

from dataclasses import dataclass

from ...domain.errors import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from ...domain.model.cita import Cita
from ...domain.model.historial import HistorialMedico
from ...domain.ports.repositories import (
    CitaRepository,
    EstadoCitaRepository,
    HistorialMedicoRepository,
    MascotaRepository,
    UsuarioRepository,
)
from ...domain.ports.services import Clock
from ..cambios import SIN_CAMBIO, Cambio, nuevo
from ..read_models import HistorialVista


@dataclass(frozen=True, kw_only=True)
class RegistrarHistorialCmd:
    """Con `cita_id`, mascota y veterinario salen de la cita si no se indican."""

    diagnostico: str
    tratamiento: str
    cita_id: int | None = None
    mascota_id: int | None = None
    veterinario_id: int | None = None
    observaciones: str | None = None


@dataclass(frozen=True, kw_only=True)
class ActualizarHistorialCmd:
    diagnostico: Cambio[str | None] = SIN_CAMBIO
    tratamiento: Cambio[str | None] = SIN_CAMBIO
    observaciones: Cambio[str | None] = SIN_CAMBIO


class ConsultarHistoriales:
    def __init__(
        self,
        historiales: HistorialMedicoRepository,
        citas: CitaRepository,
        mascotas: MascotaRepository,
        usuarios: UsuarioRepository,
    ):
        self.historiales = historiales
        self.citas = citas
        self.mascotas = mascotas
        self.usuarios = usuarios

    def listar(self, mascota_id=None, veterinario_id=None, cliente_id=None) -> list[HistorialVista]:
        return [
            self._componer(h)
            for h in self.historiales.listar(mascota_id, veterinario_id, cliente_id)
        ]

    def obtener(self, historial_id: int) -> HistorialVista:
        historial = self.historiales.obtener(historial_id)
        if historial is None:
            raise NotFoundError("Historial médico", historial_id)
        return self._componer(historial)

    def _componer(self, historial: HistorialMedico) -> HistorialVista:
        cita = self.citas.obtener(historial.cita_id) if historial.cita_id else None
        mascota = self.mascotas.obtener(historial.mascota_id)
        veterinario = self.usuarios.obtener(historial.veterinario_id)
        return HistorialVista(
            historial=historial,
            mascota_id=mascota.id if mascota else None,
            cliente_id=mascota.cliente_id if mascota else None,
            mascota_nombre=mascota.nombre if mascota else "",
            veterinario_nombre=veterinario.nombre_completo if veterinario else "",
            fecha_cita=cita.fecha_hora if cita else None,
        )


ESTADO_CITA_ATENDIDA = "Completada"


class RegistrarHistorial:
    """Registra la ficha clínica de una mascota, con o sin cita previa.

    Con cita, la mascota y el veterinario salen de ella (si no se indican) y
    la cita queda como `Completada`. Sin cita, hay que indicar ambos.
    """

    def __init__(
        self,
        historiales: HistorialMedicoRepository,
        citas: CitaRepository,
        mascotas: MascotaRepository,
        usuarios: UsuarioRepository,
        estados: EstadoCitaRepository,
        reloj: Clock,
    ):
        self.historiales = historiales
        self.citas = citas
        self.mascotas = mascotas
        self.usuarios = usuarios
        self.estados = estados
        self.reloj = reloj

    def ejecutar(self, cmd: RegistrarHistorialCmd) -> HistorialMedico:
        cita = self._cita(cmd.cita_id)
        mascota_id = self._mascota(cmd.mascota_id, cita)
        veterinario_id = self._veterinario(cmd.veterinario_id, cita)

        historial = self.historiales.crear(
            HistorialMedico(
                mascota_id=mascota_id,
                cita_id=cita.id if cita else None,
                veterinario_id=veterinario_id,
                diagnostico=cmd.diagnostico,
                tratamiento=cmd.tratamiento,
                observaciones=cmd.observaciones,
                fecha_creacion=self.reloj.ahora(),
            )
        )
        if cita:
            self._marcar_atendida(cita)
        return historial

    def _cita(self, cita_id: int | None) -> Cita | None:
        if not cita_id:
            return None
        cita = self.citas.obtener(cita_id)
        if cita is None:
            raise NotFoundError("Cita", cita_id)
        if self.historiales.obtener_por_cita(cita.id):
            raise ConflictError("Esa cita ya tiene un historial registrado")
        return cita

    def _mascota(self, mascota_id: int | None, cita: Cita | None) -> int:
        if cita:
            if mascota_id and mascota_id != cita.mascota_id:
                raise ValidationError("La cita indicada es de otra mascota", "mascota_id")
            return cita.mascota_id
        if not mascota_id:
            raise ValidationError("Indica la cita o la mascota del historial", "mascota_id")
        mascota = self.mascotas.obtener(mascota_id)
        if mascota is None:
            raise NotFoundError("Mascota", mascota_id)
        # Con cita se puede cerrar una consulta ya agendada aunque la mascota
        # se diera de baja después; sin cita, no se abren fichas nuevas.
        if not mascota.activo:
            raise BusinessRuleError(f"{mascota.nombre} está dada de baja")
        return mascota_id

    def _veterinario(self, veterinario_id: int | None, cita: Cita | None) -> int:
        veterinario_id = veterinario_id or (cita.veterinario_id if cita else None)
        if not veterinario_id:
            raise ValidationError(
                "Indica el veterinario que firma el historial", "veterinario_id"
            )
        veterinario = self.usuarios.obtener(veterinario_id)
        if veterinario is None:
            raise NotFoundError("Usuario", veterinario_id)
        if not veterinario.es_veterinario:
            raise ValidationError(
                "Sólo un veterinario puede firmar un historial", "veterinario_id"
            )
        return veterinario_id

    def _marcar_atendida(self, cita: Cita) -> None:
        """Como hacía la API anterior: registrar la ficha cierra la cita."""
        atendida = self.estados.obtener_por_nombre(ESTADO_CITA_ATENDIDA)
        if atendida is not None:
            cita.cambiar_estado(atendida.id)
            self.citas.actualizar(cita)


class ActualizarHistorial:
    def __init__(self, historiales: HistorialMedicoRepository):
        self.historiales = historiales

    def ejecutar(self, historial_id: int, cmd: ActualizarHistorialCmd) -> HistorialMedico:
        historial = self.historiales.obtener(historial_id)
        if historial is None:
            raise NotFoundError("Historial médico", historial_id)
        # `HistorialMedico.actualizar` ignora los None: no enviado = sin cambio.
        historial.actualizar(
            diagnostico=nuevo(cmd.diagnostico, None),
            tratamiento=nuevo(cmd.tratamiento, None),
            observaciones=nuevo(cmd.observaciones, None),
        )
        return self.historiales.actualizar(historial)


class EliminarHistorial:
    def __init__(self, historiales: HistorialMedicoRepository):
        self.historiales = historiales

    def ejecutar(self, historial_id: int) -> None:
        if self.historiales.obtener(historial_id) is None:
            raise NotFoundError("Historial médico", historial_id)
        self.historiales.eliminar(historial_id)
