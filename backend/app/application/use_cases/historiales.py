"""Casos de uso de historiales médicos."""
from __future__ import annotations

from ...domain.errors import ConflictError, NotFoundError, ValidationError
from ...domain.model.historial import HistorialMedico
from ...domain.ports.repositories import (
    CitaRepository,
    HistorialMedicoRepository,
    MascotaRepository,
    UsuarioRepository,
)
from ...domain.ports.services import Clock
from ..read_models import HistorialVista


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
        cita = self.citas.obtener(historial.cita_id)
        mascota = self.mascotas.obtener(cita.mascota_id) if cita else None
        veterinario = self.usuarios.obtener(historial.veterinario_id)
        return HistorialVista(
            historial=historial,
            mascota_id=mascota.id if mascota else None,
            mascota_nombre=mascota.nombre if mascota else "",
            veterinario_nombre=veterinario.nombre_completo if veterinario else "",
            fecha_cita=cita.fecha_hora if cita else None,
        )


class RegistrarHistorial:
    """Crea la ficha clínica de una cita (relación 1–1, como el OneToOneField)."""

    def __init__(
        self,
        historiales: HistorialMedicoRepository,
        citas: CitaRepository,
        usuarios: UsuarioRepository,
        reloj: Clock,
    ):
        self.historiales = historiales
        self.citas = citas
        self.usuarios = usuarios
        self.reloj = reloj

    def ejecutar(self, datos: dict) -> HistorialMedico:
        cita = self.citas.obtener(datos.get("cita_id"))
        if cita is None:
            raise NotFoundError("Cita", datos.get("cita_id"))
        if self.historiales.obtener_por_cita(cita.id):
            raise ConflictError("Esa cita ya tiene un historial registrado")

        veterinario_id = datos.get("veterinario_id") or cita.veterinario_id
        veterinario = self.usuarios.obtener(veterinario_id)
        if veterinario is None:
            raise NotFoundError("Usuario", veterinario_id)
        if not veterinario.es_veterinario:
            raise ValidationError(
                "Sólo un veterinario puede firmar un historial", "veterinario_id"
            )

        return self.historiales.crear(
            HistorialMedico(
                cita_id=cita.id,
                veterinario_id=veterinario_id,
                diagnostico=datos.get("diagnostico"),
                tratamiento=datos.get("tratamiento"),
                observaciones=datos.get("observaciones"),
                fecha_creacion=self.reloj.ahora(),
            )
        )


class ActualizarHistorial:
    def __init__(self, historiales: HistorialMedicoRepository):
        self.historiales = historiales

    def ejecutar(self, historial_id: int, cambios: dict) -> HistorialMedico:
        historial = self.historiales.obtener(historial_id)
        if historial is None:
            raise NotFoundError("Historial médico", historial_id)
        historial.actualizar(
            diagnostico=cambios.get("diagnostico"),
            tratamiento=cambios.get("tratamiento"),
            observaciones=cambios.get("observaciones"),
        )
        return self.historiales.actualizar(historial)

    def eliminar(self, historial_id: int) -> None:
        if self.historiales.obtener(historial_id) is None:
            raise NotFoundError("Historial médico", historial_id)
        self.historiales.eliminar(historial_id)
