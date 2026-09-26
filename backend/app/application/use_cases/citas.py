"""Casos de uso de la agenda: estados, servicios, disponibilidad y citas."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from ...domain.errors import BusinessRuleError, ConflictError, NotFoundError, ValidationError
from ...domain.model.cita import Cita, Disponibilidad, EstadoCita, Servicio
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
from ...domain.ports.services import Clock
from ..read_models import CitaVista, DisponibilidadVista, ServicioVista

MINUTOS_ENTRE_CITAS = 30


class GestionarEstadosCita:
    def __init__(self, estados: EstadoCitaRepository, citas: CitaRepository):
        self.estados = estados
        self.citas = citas

    def listar(self) -> list[EstadoCita]:
        return self.estados.listar()

    def obtener(self, estado_id: int) -> EstadoCita:
        estado = self.estados.obtener(estado_id)
        if estado is None:
            raise NotFoundError("Estado de cita", estado_id)
        return estado

    def crear(self, nombre: str, descripcion: str | None = None, orden: int = 0) -> EstadoCita:
        if self.estados.obtener_por_nombre(nombre):
            raise ConflictError(f"Ya existe el estado '{nombre}'")
        return self.estados.crear(EstadoCita(nombre=nombre, descripcion=descripcion, orden=orden))

    def actualizar(self, estado_id: int, cambios: dict) -> EstadoCita:
        actual = self.obtener(estado_id)
        return self.estados.actualizar(
            EstadoCita(
                id=actual.id,
                nombre=cambios.get("nombre") or actual.nombre,
                descripcion=cambios.get("descripcion", actual.descripcion),
                orden=cambios.get("orden", actual.orden),
            )
        )

    def eliminar(self, estado_id: int) -> None:
        self.obtener(estado_id)
        if self.citas.listar(estado_id=estado_id):
            raise ConflictError("No se puede eliminar: hay citas en ese estado")
        self.estados.eliminar(estado_id)


class GestionarServicios:
    def __init__(
        self,
        servicios: ServicioRepository,
        usuarios: UsuarioRepository,
        especialidades: EspecialidadRepository,
        citas: CitaRepository,
    ):
        self.servicios = servicios
        self.usuarios = usuarios
        self.especialidades = especialidades
        self.citas = citas

    def listar(self, solo_activos: bool = False, veterinario_id: int | None = None) -> list[ServicioVista]:
        return [self._componer(s) for s in self.servicios.listar(solo_activos, veterinario_id)]

    def obtener(self, servicio_id: int) -> ServicioVista:
        return self._componer(self._entidad(servicio_id))

    def crear(self, datos: dict) -> ServicioVista:
        servicio = Servicio(
            nombre=datos.get("nombre"),
            descripcion=datos.get("descripcion"),
            activo=datos.get("activo", True),
            veterinarios_ids=self._validar_veterinarios(datos.get("veterinarios_ids") or []),
            especialidades_ids=self._validar_especialidades(datos.get("especialidades_ids") or []),
        )
        return self._componer(self.servicios.crear(servicio))

    def actualizar(self, servicio_id: int, cambios: dict) -> ServicioVista:
        actual = self._entidad(servicio_id)
        veterinarios = cambios.get("veterinarios_ids")
        especialidades = cambios.get("especialidades_ids")
        servicio = Servicio(
            id=actual.id,
            nombre=cambios.get("nombre") or actual.nombre,
            descripcion=cambios.get("descripcion", actual.descripcion),
            activo=cambios.get("activo", actual.activo),
            veterinarios_ids=(
                self._validar_veterinarios(veterinarios)
                if veterinarios is not None
                else actual.veterinarios_ids
            ),
            especialidades_ids=(
                self._validar_especialidades(especialidades)
                if especialidades is not None
                else actual.especialidades_ids
            ),
        )
        return self._componer(self.servicios.actualizar(servicio))

    def eliminar(self, servicio_id: int) -> None:
        self._entidad(servicio_id)
        if any(c.servicio_id == servicio_id for c in self.citas.listar()):
            raise ConflictError("No se puede eliminar: hay citas asociadas a ese servicio")
        self.servicios.eliminar(servicio_id)

    def _entidad(self, servicio_id: int) -> Servicio:
        servicio = self.servicios.obtener(servicio_id)
        if servicio is None:
            raise NotFoundError("Servicio", servicio_id)
        return servicio

    def _validar_veterinarios(self, ids: list[int]) -> list[int]:
        for veterinario_id in ids:
            usuario = self.usuarios.obtener(veterinario_id)
            if usuario is None:
                raise NotFoundError("Usuario", veterinario_id)
            if not usuario.es_veterinario:
                raise ValidationError(
                    f"El usuario {veterinario_id} no es veterinario", "veterinarios_ids"
                )
        return list(ids)

    def _validar_especialidades(self, ids: list[int]) -> list[int]:
        conocidas = {e.id for e in self.especialidades.listar()}
        for especialidad_id in ids:
            if especialidad_id not in conocidas:
                raise NotFoundError("Especialidad", especialidad_id)
        return list(ids)

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


class GestionarDisponibilidad:
    def __init__(self, disponibilidades: DisponibilidadRepository, usuarios: UsuarioRepository):
        self.disponibilidades = disponibilidades
        self.usuarios = usuarios

    def listar(self, veterinario_id=None, dia_semana=None) -> list[DisponibilidadVista]:
        resultado = []
        for disponibilidad in self.disponibilidades.listar(veterinario_id, dia_semana):
            usuario = self.usuarios.obtener(disponibilidad.veterinario_id)
            resultado.append(
                DisponibilidadVista(
                    disponibilidad=disponibilidad,
                    veterinario_nombre=usuario.nombre_completo if usuario else "",
                )
            )
        return resultado

    def crear(self, veterinario_id: int, dia_semana: int, hora_inicio, hora_fin) -> Disponibilidad:
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

    def eliminar(self, disponibilidad_id: int) -> None:
        if self.disponibilidades.obtener(disponibilidad_id) is None:
            raise NotFoundError("Disponibilidad", disponibilidad_id)
        self.disponibilidades.eliminar(disponibilidad_id)


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
            cliente_id=mascota.cliente_id if mascota else None,
            cliente_nombre=cliente.nombre_completo if cliente else None,
            veterinario_nombre=veterinario.nombre_completo if veterinario else "",
            servicio_nombre=servicio.nombre if servicio else "",
            estado_nombre=estado.nombre if estado else "",
            tiene_historial=self.historiales.obtener_por_cita(cita.id) is not None,
        )


class AgendarCita:
    """Alta de cita con las reglas que en Django vivían en formularios y señales."""

    def __init__(
        self,
        citas: CitaRepository,
        mascotas: MascotaRepository,
        usuarios: UsuarioRepository,
        servicios: ServicioRepository,
        estados: EstadoCitaRepository,
        disponibilidades: DisponibilidadRepository,
        reloj: Clock,
    ):
        self.citas = citas
        self.mascotas = mascotas
        self.usuarios = usuarios
        self.servicios = servicios
        self.estados = estados
        self.disponibilidades = disponibilidades
        self.reloj = reloj

    def ejecutar(self, datos: dict) -> Cita:
        mascota = self.mascotas.obtener(datos.get("mascota_id"))
        if mascota is None:
            raise NotFoundError("Mascota", datos.get("mascota_id"))

        veterinario = self.usuarios.obtener(datos.get("veterinario_id"))
        if veterinario is None:
            raise NotFoundError("Usuario", datos.get("veterinario_id"))
        if not veterinario.es_veterinario:
            raise ValidationError("El profesional indicado no es veterinario", "veterinario_id")

        servicio = self.servicios.obtener(datos.get("servicio_id"))
        if servicio is None:
            raise NotFoundError("Servicio", datos.get("servicio_id"))
        if not servicio.activo:
            raise BusinessRuleError(f"El servicio '{servicio.nombre}' no está activo")
        if not servicio.admite_veterinario(veterinario.id):
            raise BusinessRuleError(
                f"{veterinario.nombre_completo} no presta el servicio '{servicio.nombre}'"
            )

        estado = self._resolver_estado(datos.get("estado_id"), datos.get("estado"))

        cita = Cita(
            mascota_id=mascota.id,
            veterinario_id=veterinario.id,
            estado_id=estado.id,
            servicio_id=servicio.id,
            fecha_hora=datos.get("fecha_hora"),
            peso=datos.get("peso") or mascota.peso,
            motivo=datos.get("motivo"),
            notas=datos.get("notas"),
        )
        if cita.fecha_hora < self.reloj.ahora():
            raise BusinessRuleError("No se puede agendar una cita en el pasado")

        agenda = self.citas.listar_por_veterinario_y_dia(veterinario.id, cita.fecha_hora.date())
        for existente in agenda:
            if cita.se_solapa_con(existente, MINUTOS_ENTRE_CITAS):
                raise ConflictError(
                    f"El veterinario ya tiene una cita a las {existente.fecha_hora:%H:%M}"
                )

        franjas = self.disponibilidades.listar(veterinario.id)
        if franjas and not any(f.cubre(cita.fecha_hora) for f in franjas):
            raise BusinessRuleError(
                "El horario está fuera de la disponibilidad declarada del veterinario"
            )
        return self.citas.crear(cita)

    def _resolver_estado(self, estado_id, nombre) -> EstadoCita:
        if estado_id:
            estado = self.estados.obtener(estado_id)
            if estado is None:
                raise NotFoundError("Estado de cita", estado_id)
            return estado
        estado = self.estados.obtener_por_nombre(nombre or "Pendiente")
        if estado is None:
            raise NotFoundError("Estado de cita", nombre or "Pendiente")
        return estado


class ActualizarCita:
    def __init__(
        self,
        citas: CitaRepository,
        estados: EstadoCitaRepository,
        servicios: ServicioRepository,
    ):
        self.citas = citas
        self.estados = estados
        self.servicios = servicios

    def ejecutar(self, cita_id: int, cambios: dict) -> Cita:
        actual = self._obtener(cita_id)
        estado_id = actual.estado_id
        if cambios.get("estado_id") or cambios.get("estado"):
            estado_id = self._estado(cambios.get("estado_id"), cambios.get("estado")).id
        servicio_id = cambios.get("servicio_id", actual.servicio_id)
        if servicio_id != actual.servicio_id and self.servicios.obtener(servicio_id) is None:
            raise NotFoundError("Servicio", servicio_id)

        actualizada = Cita(
            id=actual.id,
            mascota_id=actual.mascota_id,
            veterinario_id=cambios.get("veterinario_id", actual.veterinario_id),
            estado_id=estado_id,
            servicio_id=servicio_id,
            fecha_hora=cambios.get("fecha_hora", actual.fecha_hora),
            peso=cambios.get("peso", actual.peso),
            motivo=cambios.get("motivo") or actual.motivo,
            notas=cambios.get("notas", actual.notas),
        )
        return self.citas.actualizar(actualizada)

    def cambiar_estado(self, cita_id: int, estado_id=None, estado: str | None = None) -> Cita:
        cita = self._obtener(cita_id)
        cita.cambiar_estado(self._estado(estado_id, estado).id)
        return self.citas.actualizar(cita)

    def eliminar(self, cita_id: int) -> None:
        self._obtener(cita_id)
        self.citas.eliminar(cita_id)

    def _obtener(self, cita_id: int) -> Cita:
        cita = self.citas.obtener(cita_id)
        if cita is None:
            raise NotFoundError("Cita", cita_id)
        return cita

    def _estado(self, estado_id, nombre) -> EstadoCita:
        if estado_id:
            estado = self.estados.obtener(estado_id)
            if estado is None:
                raise NotFoundError("Estado de cita", estado_id)
            return estado
        if not nombre:
            raise ValidationError("Indica 'estado' o 'estado_id'", "estado")
        estado = self.estados.obtener_por_nombre(nombre)
        if estado is None:
            raise NotFoundError("Estado de cita", nombre)
        return estado


class ConsultarAgendaDia:
    """Horas libres de un veterinario en un día, según sus franjas."""

    def __init__(
        self,
        citas: CitaRepository,
        disponibilidades: DisponibilidadRepository,
        usuarios: UsuarioRepository,
    ):
        self.citas = citas
        self.disponibilidades = disponibilidades
        self.usuarios = usuarios

    def ejecutar(self, veterinario_id: int, dia: date) -> list[str]:
        if self.usuarios.obtener(veterinario_id) is None:
            raise NotFoundError("Usuario", veterinario_id)
        franjas = [
            f
            for f in self.disponibilidades.listar(veterinario_id)
            if f.dia_semana.value == dia.weekday()
        ]
        ocupadas = {c.fecha_hora.strftime("%H:%M") for c in self.citas.listar_por_veterinario_y_dia(veterinario_id, dia)}

        libres: list[str] = []
        for franja in franjas:
            actual = datetime.combine(dia, franja.hora_inicio)
            fin = datetime.combine(dia, franja.hora_fin)
            while actual < fin:
                etiqueta = actual.strftime("%H:%M")
                if etiqueta not in ocupadas:
                    libres.append(etiqueta)
                actual += timedelta(minutes=MINUTOS_ENTRE_CITAS)
        return sorted(set(libres))
