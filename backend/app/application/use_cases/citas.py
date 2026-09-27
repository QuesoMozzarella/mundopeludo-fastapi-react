"""Casos de uso de la agenda: estados, servicios, disponibilidad y citas."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from ...domain.errors import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from ...domain.model.cita import (
    DURACION_POR_DEFECTO,
    Cita,
    Disponibilidad,
    EstadoCita,
    Servicio,
    se_cruzan,
)
from ...domain.model.usuario import Usuario
from ...domain.ports.repositories import (
    CitaRepository,
    DisponibilidadRepository,
    EspecialidadRepository,
    EstadoCitaRepository,
    HistorialMedicoRepository,
    MascotaRepository,
    ServicioRepository,
    UsuarioRepository,
)
from ...domain.ports.services import AvisoCita, Clock, Notificaciones
from ...domain.value_objects import hora_local
from ..cambios import SIN_CAMBIO, Cambio, enviado, nuevo, nuevo_o_vacio
from ..read_models import CitaVista, DisponibilidadVista, ServicioVista

MINUTOS_ENTRE_CITAS = 30  # separación entre los huecos que ofrece la agenda del día
ESTADO_CONFIRMADA = "Confirmada"
ESTADO_CANCELADA = "Cancelada"


# ------------------------------- comandos -------------------------------
@dataclass(frozen=True, kw_only=True)
class CrearServicioCmd:
    nombre: str
    descripcion: str | None = None
    activo: bool = True
    precio: Decimal | None = None
    duracion_min: int = DURACION_POR_DEFECTO
    veterinarios_ids: list[int] = field(default_factory=list)
    especialidades_ids: list[int] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class ActualizarServicioCmd:
    nombre: Cambio[str | None] = SIN_CAMBIO
    descripcion: Cambio[str | None] = SIN_CAMBIO
    activo: Cambio[bool | None] = SIN_CAMBIO
    precio: Cambio[Decimal | None] = SIN_CAMBIO
    duracion_min: Cambio[int | None] = SIN_CAMBIO
    veterinarios_ids: Cambio[list[int] | None] = SIN_CAMBIO
    especialidades_ids: Cambio[list[int] | None] = SIN_CAMBIO


@dataclass(frozen=True, kw_only=True)
class AgendarCitaCmd:
    mascota_id: int
    veterinario_id: int
    servicio_id: int
    fecha_hora: datetime
    motivo: str
    peso: float | None = None
    notas: str | None = None
    estado: str | None = None
    estado_id: int | None = None


@dataclass(frozen=True, kw_only=True)
class ActualizarCitaCmd:
    veterinario_id: Cambio[int | None] = SIN_CAMBIO
    servicio_id: Cambio[int | None] = SIN_CAMBIO
    fecha_hora: Cambio[datetime | None] = SIN_CAMBIO
    motivo: Cambio[str | None] = SIN_CAMBIO
    peso: Cambio[float | None] = SIN_CAMBIO
    notas: Cambio[str | None] = SIN_CAMBIO
    estado: Cambio[str | None] = SIN_CAMBIO
    estado_id: Cambio[int | None] = SIN_CAMBIO


# --------------------------- estados de cita ---------------------------
class ConsultarEstadosCita:
    def __init__(self, estados: EstadoCitaRepository):
        self.estados = estados

    def listar(self) -> list[EstadoCita]:
        return self.estados.listar()


class CrearEstadoCita:
    def __init__(self, estados: EstadoCitaRepository):
        self.estados = estados

    def ejecutar(self, nombre: str, descripcion: str | None = None, orden: int = 0) -> EstadoCita:
        if self.estados.obtener_por_nombre(nombre):
            raise ConflictError(f"Ya existe el estado '{nombre}'")
        return self.estados.crear(EstadoCita(nombre=nombre, descripcion=descripcion, orden=orden))


class EliminarEstadoCita:
    def __init__(self, estados: EstadoCitaRepository, citas: CitaRepository):
        self.estados = estados
        self.citas = citas

    def ejecutar(self, estado_id: int) -> None:
        if self.estados.obtener(estado_id) is None:
            raise NotFoundError("Estado de cita", estado_id)
        if self.citas.listar(estado_id=estado_id):
            raise ConflictError("No se puede eliminar: hay citas en ese estado")
        self.estados.eliminar(estado_id)


# ------------------------------ servicios ------------------------------
def _servicio_o_error(servicios: ServicioRepository, servicio_id: int) -> Servicio:
    servicio = servicios.obtener(servicio_id)
    if servicio is None:
        raise NotFoundError("Servicio", servicio_id)
    return servicio


def _validar_veterinarios(usuarios: UsuarioRepository, ids: list[int]) -> list[int]:
    for veterinario_id in ids:
        usuario = usuarios.obtener(veterinario_id)
        if usuario is None:
            raise NotFoundError("Usuario", veterinario_id)
        if not usuario.es_veterinario:
            raise ValidationError(
                f"El usuario {veterinario_id} no es veterinario", "veterinarios_ids"
            )
    return list(ids)


def _validar_especialidades(especialidades: EspecialidadRepository, ids: list[int]) -> list[int]:
    conocidas = {e.id for e in especialidades.listar()}
    for especialidad_id in ids:
        if especialidad_id not in conocidas:
            raise NotFoundError("Especialidad", especialidad_id)
    return list(ids)


class ConsultarServicios:
    def __init__(
        self,
        servicios: ServicioRepository,
        usuarios: UsuarioRepository,
        especialidades: EspecialidadRepository,
    ):
        self.servicios = servicios
        self.usuarios = usuarios
        self.especialidades = especialidades

    def listar(
        self, solo_activos: bool = False, veterinario_id: int | None = None
    ) -> list[ServicioVista]:
        return [self._componer(s) for s in self.servicios.listar(solo_activos, veterinario_id)]

    def obtener(self, servicio_id: int) -> ServicioVista:
        return self._componer(_servicio_o_error(self.servicios, servicio_id))

    def _componer(self, servicio: Servicio) -> ServicioVista:
        nombres_vet = []
        for veterinario_id in servicio.veterinarios_ids:
            usuario = self.usuarios.obtener(veterinario_id)
            if usuario:
                nombres_vet.append(usuario.nombre_completo)
        catalogo = {e.id: e.nombre for e in self.especialidades.listar()}
        return ServicioVista(
            servicio=servicio,
            veterinarios=nombres_vet,
            especialidades=[catalogo[i] for i in servicio.especialidades_ids if i in catalogo],
        )


class CrearServicio:
    def __init__(
        self,
        servicios: ServicioRepository,
        usuarios: UsuarioRepository,
        especialidades: EspecialidadRepository,
    ):
        self.servicios = servicios
        self.usuarios = usuarios
        self.especialidades = especialidades

    def ejecutar(self, cmd: CrearServicioCmd) -> Servicio:
        return self.servicios.crear(
            Servicio(
                nombre=cmd.nombre,
                descripcion=cmd.descripcion,
                activo=cmd.activo,
                precio=cmd.precio,
                duracion_min=cmd.duracion_min,
                veterinarios_ids=_validar_veterinarios(self.usuarios, cmd.veterinarios_ids),
                especialidades_ids=_validar_especialidades(
                    self.especialidades, cmd.especialidades_ids
                ),
            )
        )


class ActualizarServicio:
    def __init__(
        self,
        servicios: ServicioRepository,
        usuarios: UsuarioRepository,
        especialidades: EspecialidadRepository,
    ):
        self.servicios = servicios
        self.usuarios = usuarios
        self.especialidades = especialidades

    def ejecutar(self, servicio_id: int, cmd: ActualizarServicioCmd) -> Servicio:
        actual = _servicio_o_error(self.servicios, servicio_id)
        servicio = Servicio(
            id=actual.id,
            nombre=nuevo(cmd.nombre, actual.nombre),
            descripcion=nuevo_o_vacio(cmd.descripcion, actual.descripcion),
            activo=nuevo(cmd.activo, actual.activo),
            precio=nuevo_o_vacio(cmd.precio, actual.precio),
            duracion_min=nuevo(cmd.duracion_min, actual.duracion_min),
            veterinarios_ids=(
                _validar_veterinarios(self.usuarios, cmd.veterinarios_ids)
                if enviado(cmd.veterinarios_ids)
                else actual.veterinarios_ids
            ),
            especialidades_ids=(
                _validar_especialidades(self.especialidades, cmd.especialidades_ids)
                if enviado(cmd.especialidades_ids)
                else actual.especialidades_ids
            ),
        )
        return self.servicios.actualizar(servicio)


class EliminarServicio:
    def __init__(self, servicios: ServicioRepository, citas: CitaRepository):
        self.servicios = servicios
        self.citas = citas

    def ejecutar(self, servicio_id: int) -> None:
        _servicio_o_error(self.servicios, servicio_id)
        if any(c.servicio_id == servicio_id for c in self.citas.listar()):
            raise ConflictError("No se puede eliminar: hay citas asociadas a ese servicio")
        self.servicios.eliminar(servicio_id)


# ---------------------------- disponibilidad ----------------------------
class ConsultarDisponibilidad:
    def __init__(self, disponibilidades: DisponibilidadRepository, usuarios: UsuarioRepository):
        self.disponibilidades = disponibilidades
        self.usuarios = usuarios

    def listar(self, veterinario_id=None, dia_semana=None) -> list[DisponibilidadVista]:
        return [
            self._componer(d) for d in self.disponibilidades.listar(veterinario_id, dia_semana)
        ]

    def obtener(self, disponibilidad_id: int) -> DisponibilidadVista:
        disponibilidad = self.disponibilidades.obtener(disponibilidad_id)
        if disponibilidad is None:
            raise NotFoundError("Disponibilidad", disponibilidad_id)
        return self._componer(disponibilidad)

    def _componer(self, disponibilidad: Disponibilidad) -> DisponibilidadVista:
        usuario = self.usuarios.obtener(disponibilidad.veterinario_id)
        return DisponibilidadVista(
            disponibilidad=disponibilidad,
            veterinario_nombre=usuario.nombre_completo if usuario else "",
        )


class DeclararDisponibilidad:
    def __init__(self, disponibilidades: DisponibilidadRepository, usuarios: UsuarioRepository):
        self.disponibilidades = disponibilidades
        self.usuarios = usuarios

    def ejecutar(
        self, veterinario_id: int, dia_semana: int, hora_inicio, hora_fin
    ) -> Disponibilidad:
        usuario = self.usuarios.obtener(veterinario_id)
        if usuario is None:
            raise NotFoundError("Usuario", veterinario_id)
        if not usuario.es_veterinario:
            raise ValidationError("Sólo un veterinario tiene disponibilidad", "veterinario_id")

        nueva = Disponibilidad(
            veterinario_id=veterinario_id,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
        )
        for existente in self.disponibilidades.listar(veterinario_id, nueva.dia_semana.value):
            if existente.se_solapa_con(nueva):
                raise ConflictError(
                    f"La franja se solapa con {existente.hora_inicio}-{existente.hora_fin}"
                )
        return self.disponibilidades.crear(nueva)


class EliminarDisponibilidad:
    def __init__(self, disponibilidades: DisponibilidadRepository):
        self.disponibilidades = disponibilidades

    def ejecutar(self, disponibilidad_id: int) -> None:
        if self.disponibilidades.obtener(disponibilidad_id) is None:
            raise NotFoundError("Disponibilidad", disponibilidad_id)
        self.disponibilidades.eliminar(disponibilidad_id)


# -------------------------------- citas --------------------------------
class ConsultarCitas:
    def __init__(
        self,
        citas: CitaRepository,
        mascotas: MascotaRepository,
        usuarios: UsuarioRepository,
        servicios: ServicioRepository,
        estados: EstadoCitaRepository,
        historiales: HistorialMedicoRepository,
    ):
        self.citas = citas
        self.mascotas = mascotas
        self.usuarios = usuarios
        self.servicios = servicios
        self.estados = estados
        self.historiales = historiales

    def listar(
        self,
        mascota_id=None,
        veterinario_id=None,
        cliente_id=None,
        estado: str | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[CitaVista]:
        estado_id = None
        if estado:
            encontrado = self.estados.obtener_por_nombre(estado)
            if encontrado is None:
                raise NotFoundError("Estado de cita", estado)
            estado_id = encontrado.id
        desde = hora_local(desde) if desde else None
        hasta = hora_local(hasta) if hasta else None
        citas = self.citas.listar(mascota_id, veterinario_id, cliente_id, estado_id, desde, hasta)
        return [self._componer(c) for c in citas]

    def obtener(self, cita_id: int) -> CitaVista:
        cita = self.citas.obtener(cita_id)
        if cita is None:
            raise NotFoundError("Cita", cita_id)
        return self._componer(cita)

    def _componer(self, cita: Cita) -> CitaVista:
        mascota = self.mascotas.obtener(cita.mascota_id)
        veterinario = self.usuarios.obtener(cita.veterinario_id)
        servicio = self.servicios.obtener(cita.servicio_id)
        estado = self.estados.obtener(cita.estado_id)
        cliente = (
            self.usuarios.obtener(mascota.cliente_id) if mascota and mascota.cliente_id else None
        )
        return CitaVista(
            cita=cita,
            mascota_nombre=mascota.nombre if mascota else "",
            mascota_raza=mascota.raza if mascota else None,
            mascota_imagen_url=mascota.imagen_url if mascota else None,
            cliente_id=mascota.cliente_id if mascota else None,
            cliente_nombre=cliente.nombre_completo if cliente else None,
            cliente_email=cliente.email if cliente else None,
            cliente_telefono=cliente.telefono if cliente else None,
            veterinario_nombre=veterinario.nombre_completo if veterinario else "",
            servicio_nombre=servicio.nombre if servicio else "",
            servicio_precio=servicio.precio if servicio else None,
            servicio_duracion_min=servicio.duracion_min if servicio else DURACION_POR_DEFECTO,
            estado_nombre=estado.nombre if estado else "",
            tiene_historial=self.historiales.obtener_por_cita(cita.id) is not None,
        )


class ReglasDeAgenda:
    """Reglas que una cita cumple al agendarse *y* al reprogramarse.

    Viven aparte para que `AgendarCita` y `ActualizarCita` no puedan
    divergir: antes, un PUT permitía mover una cita al pasado, encima de otra
    o a un profesional que no era veterinario.
    """

    def __init__(
        self,
        citas: CitaRepository,
        usuarios: UsuarioRepository,
        servicios: ServicioRepository,
        disponibilidades: DisponibilidadRepository,
        estados: EstadoCitaRepository,
        reloj: Clock,
    ):
        self.citas = citas
        self.usuarios = usuarios
        self.servicios = servicios
        self.disponibilidades = disponibilidades
        self.estados = estados
        self.reloj = reloj

    def veterinario(self, veterinario_id: int) -> Usuario:
        veterinario = self.usuarios.obtener(veterinario_id)
        if veterinario is None:
            raise NotFoundError("Usuario", veterinario_id)
        if not veterinario.es_veterinario:
            raise ValidationError("El profesional indicado no es veterinario", "veterinario_id")
        if not veterinario.is_active:
            raise BusinessRuleError(f"{veterinario.nombre_completo} ya no atiende en la clínica")
        return veterinario

    def servicio(self, servicio_id: int, veterinario: Usuario) -> Servicio:
        servicio = self.servicios.obtener(servicio_id)
        if servicio is None:
            raise NotFoundError("Servicio", servicio_id)
        if not servicio.activo:
            raise BusinessRuleError(f"El servicio '{servicio.nombre}' no está activo")
        if not servicio.admite_veterinario(veterinario.id):
            raise BusinessRuleError(
                f"{veterinario.nombre_completo} no presta el servicio '{servicio.nombre}'"
            )
        return servicio

    def horario(self, cita: Cita, servicio: Servicio) -> None:
        """Cada cita ocupa la duración de su servicio: no puede ser en el
        pasado, pisar otra ni salirse de las franjas del veterinario. Como en
        Django, un veterinario sin franjas declaradas no tiene horas libres."""
        if cita.fecha_hora < self.reloj.ahora():
            raise BusinessRuleError("No se puede agendar una cita en el pasado")
        self.sin_solape(cita, servicio)

        franjas = self.disponibilidades.listar(cita.veterinario_id)
        if not franjas:
            raise BusinessRuleError(
                "El veterinario no tiene horario de atención declarado"
            )
        if not any(f.cubre(cita.fecha_hora, servicio.duracion_min) for f in franjas):
            raise BusinessRuleError(
                "El horario está fuera de la disponibilidad declarada del veterinario"
                f" (el servicio dura {servicio.duracion_min} min)"
            )

    def sin_solape(self, cita: Cita, servicio: Servicio) -> None:
        """La cita no pisa ninguna otra del veterinario que siga ocupando la agenda."""
        duraciones = _Duraciones(self.servicios)
        for existente in _citas_que_ocupan(
            self.citas, self.estados, cita.veterinario_id, cita.fecha_hora.date()
        ):
            if cita.se_solapa_con(
                existente, servicio.duracion_min, duraciones.de(existente.servicio_id)
            ):
                raise ConflictError(
                    f"El veterinario ya tiene una cita a las {existente.fecha_hora:%H:%M}"
                )

    def al_reactivar(self, cita: Cita, estado_anterior_id: int) -> None:
        """Una cita cancelada que vuelve a estar activa recupera su hueco:
        sólo si mientras tanto nadie lo ha ocupado."""
        if not _es_cancelada(self.estados, estado_anterior_id):
            return
        if _es_cancelada(self.estados, cita.estado_id):
            return
        servicio = _servicio_o_error(self.servicios, cita.servicio_id)
        self.sin_solape(cita, servicio)


def _es_cancelada(estados: EstadoCitaRepository, estado_id: int | None) -> bool:
    estado = estados.obtener(estado_id) if estado_id is not None else None
    return estado is not None and estado.nombre == ESTADO_CANCELADA


def _citas_que_ocupan(
    citas: CitaRepository, estados: EstadoCitaRepository, veterinario_id: int, dia: date
) -> list[Cita]:
    """Citas del día que ocupan la agenda: todas menos las canceladas."""
    cancelada = estados.obtener_por_nombre(ESTADO_CANCELADA)
    return [
        c
        for c in citas.listar_por_veterinario_y_dia(veterinario_id, dia)
        if cancelada is None or c.estado_id != cancelada.id
    ]


class _Duraciones:
    """Duración de cada servicio, leída una sola vez por consulta."""

    def __init__(self, servicios: ServicioRepository):
        self.servicios = servicios
        self._cache: dict[int, int] = {}

    def de(self, servicio_id: int) -> int:
        if servicio_id not in self._cache:
            servicio = self.servicios.obtener(servicio_id)
            self._cache[servicio_id] = (
                servicio.duracion_min if servicio else DURACION_POR_DEFECTO
            )
        return self._cache[servicio_id]


def _resolver_estado(estados: EstadoCitaRepository, estado_id, nombre) -> EstadoCita:
    if estado_id:
        estado = estados.obtener(estado_id)
        if estado is None:
            raise NotFoundError("Estado de cita", estado_id)
        return estado
    if not nombre:
        raise ValidationError("Indica 'estado' o 'estado_id'", "estado")
    estado = estados.obtener_por_nombre(nombre)
    if estado is None:
        raise NotFoundError("Estado de cita", nombre)
    return estado


class AvisosDeCita:
    """Avisa por correo al tutor cuando una cita pasa a Confirmada o Cancelada."""

    def __init__(
        self,
        mascotas: MascotaRepository,
        usuarios: UsuarioRepository,
        servicios: ServicioRepository,
        estados: EstadoCitaRepository,
        notificaciones: Notificaciones,
    ):
        self.mascotas = mascotas
        self.usuarios = usuarios
        self.servicios = servicios
        self.estados = estados
        self.notificaciones = notificaciones

    def tras_cambio_de_estado(self, cita: Cita, estado_anterior_id: int | None) -> None:
        if cita.estado_id == estado_anterior_id:
            return
        estado = self.estados.obtener(cita.estado_id)
        if estado is None or estado.nombre not in (ESTADO_CONFIRMADA, ESTADO_CANCELADA):
            return
        aviso = self._aviso(cita)
        if aviso is None:
            return
        if estado.nombre == ESTADO_CONFIRMADA:
            self.notificaciones.cita_confirmada(aviso)
        else:
            self.notificaciones.cita_cancelada(aviso)

    def _aviso(self, cita: Cita) -> AvisoCita | None:
        """None si no hay a quién avisar (mascota sin tutor o tutor de baja)."""
        mascota = self.mascotas.obtener(cita.mascota_id)
        tutor = (
            self.usuarios.obtener(mascota.cliente_id)
            if mascota and mascota.cliente_id
            else None
        )
        if tutor is None or not tutor.is_active:
            return None
        veterinario = self.usuarios.obtener(cita.veterinario_id)
        servicio = self.servicios.obtener(cita.servicio_id)
        return AvisoCita(
            email=tutor.email,
            nombre=tutor.nombre_completo,
            mascota=mascota.nombre,
            fecha_hora=cita.fecha_hora,
            veterinario=veterinario.nombre_completo if veterinario else "",
            servicio=servicio.nombre if servicio else "",
            motivo=cita.motivo,
        )


class AgendarCita:
    """Alta de cita con las reglas que en Django vivían en formularios y señales."""

    def __init__(
        self,
        citas: CitaRepository,
        mascotas: MascotaRepository,
        estados: EstadoCitaRepository,
        reglas: ReglasDeAgenda,
        avisos: AvisosDeCita,
    ):
        self.citas = citas
        self.mascotas = mascotas
        self.estados = estados
        self.reglas = reglas
        self.avisos = avisos

    def ejecutar(self, cmd: AgendarCitaCmd) -> Cita:
        mascota = self.mascotas.obtener(cmd.mascota_id)
        if mascota is None:
            raise NotFoundError("Mascota", cmd.mascota_id)
        if not mascota.activo:
            raise BusinessRuleError(f"{mascota.nombre} está dada de baja")

        veterinario = self.reglas.veterinario(cmd.veterinario_id)
        servicio = self.reglas.servicio(cmd.servicio_id, veterinario)
        estado = _resolver_estado(self.estados, cmd.estado_id, cmd.estado or "Pendiente")

        cita = Cita(
            mascota_id=mascota.id,
            veterinario_id=veterinario.id,
            estado_id=estado.id,
            servicio_id=servicio.id,
            fecha_hora=cmd.fecha_hora,
            peso=cmd.peso or mascota.peso,
            motivo=cmd.motivo,
            notas=cmd.notas,
        )
        self.reglas.horario(cita, servicio)
        cita = self.citas.crear(cita)
        # Una cita puede nacer ya confirmada (p. ej. la agenda el personal).
        self.avisos.tras_cambio_de_estado(cita, estado_anterior_id=None)
        return cita


class ActualizarCita:
    def __init__(
        self,
        citas: CitaRepository,
        estados: EstadoCitaRepository,
        reglas: ReglasDeAgenda,
        avisos: AvisosDeCita,
    ):
        self.citas = citas
        self.estados = estados
        self.reglas = reglas
        self.avisos = avisos

    def ejecutar(self, cita_id: int, cmd: ActualizarCitaCmd) -> Cita:
        actual = _cita_o_error(self.citas, cita_id)
        estado_id = actual.estado_id
        if enviado(cmd.estado_id) or enviado(cmd.estado):
            estado_id = _resolver_estado(
                self.estados, nuevo(cmd.estado_id, None), nuevo(cmd.estado, None)
            ).id

        actualizada = Cita(
            id=actual.id,
            mascota_id=actual.mascota_id,
            veterinario_id=nuevo(cmd.veterinario_id, actual.veterinario_id),
            estado_id=estado_id,
            servicio_id=nuevo(cmd.servicio_id, actual.servicio_id),
            fecha_hora=nuevo(cmd.fecha_hora, actual.fecha_hora),
            peso=nuevo(cmd.peso, actual.peso),
            motivo=nuevo(cmd.motivo, actual.motivo),
            notas=nuevo_o_vacio(cmd.notas, actual.notas),
        )

        # Sólo se revalida la agenda si cambia cuándo, con quién o qué: así
        # se pueden seguir editando las notas de una cita ya pasada.
        if (
            actualizada.veterinario_id != actual.veterinario_id
            or actualizada.servicio_id != actual.servicio_id
            or actualizada.fecha_hora != actual.fecha_hora
        ):
            veterinario = self.reglas.veterinario(actualizada.veterinario_id)
            servicio = self.reglas.servicio(actualizada.servicio_id, veterinario)
            self.reglas.horario(actualizada, servicio)
        else:
            self.reglas.al_reactivar(actualizada, actual.estado_id)
        actualizada = self.citas.actualizar(actualizada)
        self.avisos.tras_cambio_de_estado(actualizada, actual.estado_id)
        return actualizada


class CambiarEstadoCita:
    def __init__(
        self,
        citas: CitaRepository,
        estados: EstadoCitaRepository,
        reglas: ReglasDeAgenda,
        avisos: AvisosDeCita,
    ):
        self.citas = citas
        self.estados = estados
        self.reglas = reglas
        self.avisos = avisos

    def ejecutar(self, cita_id: int, estado_id=None, estado: str | None = None) -> Cita:
        cita = _cita_o_error(self.citas, cita_id)
        anterior = cita.estado_id
        cita.cambiar_estado(_resolver_estado(self.estados, estado_id, estado).id)
        self.reglas.al_reactivar(cita, anterior)
        cita = self.citas.actualizar(cita)
        self.avisos.tras_cambio_de_estado(cita, anterior)
        return cita


class EliminarCita:
    def __init__(self, citas: CitaRepository):
        self.citas = citas

    def ejecutar(self, cita_id: int) -> None:
        _cita_o_error(self.citas, cita_id)
        self.citas.eliminar(cita_id)


def _cita_o_error(citas: CitaRepository, cita_id: int) -> Cita:
    cita = citas.obtener(cita_id)
    if cita is None:
        raise NotFoundError("Cita", cita_id)
    return cita


class ConsultarAgendaDia:
    """Horas libres de un veterinario en un día, según sus franjas.

    Un hueco está libre si todavía no ha pasado y una cita del servicio
    indicado (o de la duración por defecto) cabe entera en la franja sin pisar
    ninguna de las que ocupan la agenda (las canceladas no), con la duración
    de sus propios servicios. Son las mismas reglas que valida `horario`.
    """

    def __init__(
        self,
        citas: CitaRepository,
        disponibilidades: DisponibilidadRepository,
        usuarios: UsuarioRepository,
        servicios: ServicioRepository,
        estados: EstadoCitaRepository,
        reloj: Clock,
    ):
        self.citas = citas
        self.disponibilidades = disponibilidades
        self.usuarios = usuarios
        self.servicios = servicios
        self.estados = estados
        self.reloj = reloj

    def ejecutar(
        self, veterinario_id: int, dia: date, servicio_id: int | None = None
    ) -> list[str]:
        if self.usuarios.obtener(veterinario_id) is None:
            raise NotFoundError("Usuario", veterinario_id)
        duraciones = _Duraciones(self.servicios)
        if servicio_id is not None:
            duracion = _servicio_o_error(self.servicios, servicio_id).duracion_min
        else:
            duracion = DURACION_POR_DEFECTO
        franjas = [
            f
            for f in self.disponibilidades.listar(veterinario_id)
            if f.dia_semana.value == dia.weekday()
        ]
        agenda = _citas_que_ocupan(self.citas, self.estados, veterinario_id, dia)
        ahora = self.reloj.ahora()

        libres: list[str] = []
        for franja in franjas:
            actual = datetime.combine(dia, franja.hora_inicio)
            fin = datetime.combine(dia, franja.hora_fin)
            while actual < fin:
                cabe = franja.cubre(actual, duracion)
                pisa = any(
                    se_cruzan(actual, duracion, c.fecha_hora, duraciones.de(c.servicio_id))
                    for c in agenda
                )
                if cabe and not pisa and actual >= ahora:
                    libres.append(actual.strftime("%H:%M"))
                actual += timedelta(minutes=MINUTOS_ENTRE_CITAS)
        return sorted(set(libres))
