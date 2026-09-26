"""Casos de uso del módulo de adopciones."""
from __future__ import annotations

from ...domain.errors import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from ...domain.model.mascota import SolicitudAdopcion
from ...domain.model.sistema import ActividadSistema
from ...domain.ports.repositories import (
    ActividadSistemaRepository,
    MascotaRepository,
    SolicitudAdopcionRepository,
    UsuarioRepository,
)
from ...domain.ports.services import Clock
from ...domain.value_objects import EstadoAdopcion, EstadoSolicitud
from ..read_models import SolicitudVista


class ConsultarSolicitudesAdopcion:
    def __init__(
        self,
        solicitudes: SolicitudAdopcionRepository,
        mascotas: MascotaRepository,
        usuarios: UsuarioRepository,
    ):
        self.solicitudes = solicitudes
        self.mascotas = mascotas
        self.usuarios = usuarios

    def listar(
        self,
        cliente_id: int | None = None,
        mascota_id: int | None = None,
        estado: str | None = None,
    ) -> list[SolicitudVista]:
        estado_enum = EstadoSolicitud.desde(estado, campo="estado") if estado else None
        return [
            self._componer(s)
            for s in self.solicitudes.listar(cliente_id, mascota_id, estado_enum)
        ]

    def obtener(self, solicitud_id: int) -> SolicitudVista:
        solicitud = self.solicitudes.obtener(solicitud_id)
        if solicitud is None:
            raise NotFoundError("Solicitud de adopción", solicitud_id)
        return self._componer(solicitud)

    def _componer(self, solicitud: SolicitudAdopcion) -> SolicitudVista:
        mascota = self.mascotas.obtener(solicitud.mascota_id)
        cliente = self.usuarios.obtener(solicitud.cliente_id)
        revisor = (
            self.usuarios.obtener(solicitud.revisado_por_id)
            if solicitud.revisado_por_id
            else None
        )
        return SolicitudVista(
            solicitud=solicitud,
            mascota_nombre=mascota.nombre if mascota else "",
            cliente_nombre=cliente.nombre_completo if cliente else "",
            cliente_email=cliente.email if cliente else "",
            revisor_nombre=revisor.nombre_completo if revisor else None,
        )


class SolicitarAdopcion:
    def __init__(
        self,
        solicitudes: SolicitudAdopcionRepository,
        mascotas: MascotaRepository,
        usuarios: UsuarioRepository,
        reloj: Clock,
        actividades: ActividadSistemaRepository | None = None,
    ):
        self.solicitudes = solicitudes
        self.mascotas = mascotas
        self.usuarios = usuarios
        self.reloj = reloj
        self.actividades = actividades

    def ejecutar(
        self, mascota_id: int, cliente_id: int, notas_cliente: str = ""
    ) -> SolicitudAdopcion:
        mascota = self.mascotas.obtener(mascota_id)
        if mascota is None:
            raise NotFoundError("Mascota", mascota_id)
        cliente = self.usuarios.obtener(cliente_id)
        if cliente is None:
            raise NotFoundError("Usuario", cliente_id)
        if not cliente.es_cliente:
            raise ValidationError("Sólo un cliente puede solicitar una adopción", "cliente_id")
        if mascota.estado_adopcion is not EstadoAdopcion.EN_ADOPCION:
            raise BusinessRuleError("La mascota no está disponible para adopción")
        if mascota.cliente_id == cliente_id:
            raise BusinessRuleError("La mascota ya pertenece a este cliente")
        if self.solicitudes.existe_pendiente(mascota_id, cliente_id):
            raise ConflictError("Ya tienes una solicitud pendiente para esta mascota")

        ahora = self.reloj.ahora()
        solicitud = self.solicitudes.crear(
            SolicitudAdopcion(
                mascota_id=mascota_id,
                cliente_id=cliente_id,
                notas_cliente=notas_cliente,
                fecha_solicitud=ahora,
                fecha_actualizacion=ahora,
            )
        )
        if self.actividades:
            self.actividades.registrar(
                ActividadSistema(
                    usuario=cliente.email,
                    tipo="adopcion",
                    descripcion=f"Solicitud de adopción para {mascota.nombre}",
                    fecha=ahora,
                )
            )
        return solicitud


class ResolverSolicitudAdopcion:
    """Aprueba o rechaza una solicitud; al aprobar, transfiere la mascota."""

    def __init__(
        self,
        solicitudes: SolicitudAdopcionRepository,
        mascotas: MascotaRepository,
        usuarios: UsuarioRepository,
        reloj: Clock,
        actividades: ActividadSistemaRepository | None = None,
    ):
        self.solicitudes = solicitudes
        self.mascotas = mascotas
        self.usuarios = usuarios
        self.reloj = reloj
        self.actividades = actividades

    def aprobar(self, solicitud_id: int, revisor_id: int, notas: str = "") -> SolicitudAdopcion:
        solicitud, revisor = self._preparar(solicitud_id, revisor_id)
        solicitud.aprobar(revisor_id, self.reloj.ahora(), notas)
        self.solicitudes.actualizar(solicitud)

        mascota = self.mascotas.obtener(solicitud.mascota_id)
        if mascota is None:
            raise NotFoundError("Mascota", solicitud.mascota_id)
        mascota.transferir_a(solicitud.cliente_id)
        self.mascotas.actualizar(mascota)

        # El resto de solicitudes pendientes de esa mascota quedan sin efecto.
        for otra in self.solicitudes.listar(
            mascota_id=solicitud.mascota_id, estado=EstadoSolicitud.PENDIENTE
        ):
            if otra.id != solicitud.id:
                otra.rechazar(
                    revisor_id, self.reloj.ahora(), "La mascota fue adoptada por otro solicitante"
                )
                self.solicitudes.actualizar(otra)

        self._registrar(revisor, f"Adopción aprobada para {mascota.nombre}")
        return solicitud

    def rechazar(self, solicitud_id: int, revisor_id: int, notas: str = "") -> SolicitudAdopcion:
        solicitud, revisor = self._preparar(solicitud_id, revisor_id)
        solicitud.rechazar(revisor_id, self.reloj.ahora(), notas)
        self.solicitudes.actualizar(solicitud)
        self._registrar(revisor, f"Solicitud de adopción #{solicitud.id} rechazada")
        return solicitud

    def _preparar(self, solicitud_id: int, revisor_id: int):
        solicitud = self.solicitudes.obtener(solicitud_id)
        if solicitud is None:
            raise NotFoundError("Solicitud de adopción", solicitud_id)
        revisor = self.usuarios.obtener(revisor_id)
        if revisor is None:
            raise NotFoundError("Usuario", revisor_id)
        if not (revisor.es_administrador or revisor.es_veterinario):
            raise ValidationError(
                "Sólo un administrador o veterinario puede revisar solicitudes", "revisor_id"
            )
        return solicitud, revisor

    def _registrar(self, revisor, descripcion: str) -> None:
        if self.actividades:
            self.actividades.registrar(
                ActividadSistema(
                    usuario=revisor.email,
                    tipo="adopcion",
                    descripcion=descripcion,
                    fecha=self.reloj.ahora(),
                )
            )


class CancelarSolicitudAdopcion:
    def __init__(
        self,
        solicitudes: SolicitudAdopcionRepository,
        mascotas: MascotaRepository,
        reloj: Clock,
    ):
        self.solicitudes = solicitudes
        self.mascotas = mascotas
        self.reloj = reloj

    def ejecutar(self, solicitud_id: int, cliente_id: int) -> SolicitudAdopcion:
        solicitud = self.solicitudes.obtener(solicitud_id)
        if solicitud is None:
            raise NotFoundError("Solicitud de adopción", solicitud_id)
        if solicitud.cliente_id != cliente_id:
            raise ValidationError("La solicitud pertenece a otro cliente", "cliente_id")

        solicitud.cancelar(self.reloj.ahora())
        self.solicitudes.actualizar(solicitud)

        mascota = self.mascotas.obtener(solicitud.mascota_id)
        if mascota and mascota.estado_adopcion is EstadoAdopcion.PENDIENTE:
            mascota.publicar_en_adopcion()
            self.mascotas.actualizar(mascota)
        return solicitud


class PublicarMascotaEnAdopcion:
    def __init__(self, mascotas: MascotaRepository):
        self.mascotas = mascotas

    def publicar(self, mascota_id: int):
        mascota = self._obtener(mascota_id)
        mascota.publicar_en_adopcion()
        return self.mascotas.actualizar(mascota)

    def retirar(self, mascota_id: int):
        mascota = self._obtener(mascota_id)
        mascota.retirar_de_adopcion()
        return self.mascotas.actualizar(mascota)

    def _obtener(self, mascota_id: int):
        mascota = self.mascotas.obtener(mascota_id)
        if mascota is None:
            raise NotFoundError("Mascota", mascota_id)
        return mascota
