"""Rutas de la agenda: estados, servicios, disponibilidad y citas."""
from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Query, status

from ....application.use_cases.citas import (
    ActualizarCita,
    AgendarCita,
    ConsultarAgendaDia,
    ConsultarCitas,
    GestionarDisponibilidad,
    GestionarEstadosCita,
    GestionarServicios,
)
from ..deps import ReposDep, ServiciosDep, SoloAdmin, SoloPersonal
from ..schemas.citas import (
    CambioEstadoIn,
    CitaActualizarIn,
    CitaIn,
    CitaOut,
    DisponibilidadIn,
    DisponibilidadOut,
    EstadoCitaIn,
    EstadoCitaOut,
    ServicioActualizarIn,
    ServicioIn,
    ServicioOut,
)

router = APIRouter(prefix="/api", tags=["citas"])


def _consulta(repos: ReposDep) -> ConsultarCitas:
    return ConsultarCitas(
        repos.citas,
        repos.mascotas,
        repos.usuarios,
        repos.servicios,
        repos.estados_cita,
        repos.historiales,
    )


def _servicios(repos: ReposDep) -> GestionarServicios:
    return GestionarServicios(repos.servicios, repos.usuarios, repos.especialidades, repos.citas)


# --------------------------- estados de cita ---------------------------
@router.get("/estados-cita", response_model=list[EstadoCitaOut], summary="Listar estados de cita")
def listar_estados(repos: ReposDep) -> list[EstadoCitaOut]:
    caso = GestionarEstadosCita(repos.estados_cita, repos.citas)
    return [EstadoCitaOut.desde(e) for e in caso.listar()]


@router.post(
    "/estados-cita",
    response_model=EstadoCitaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un estado de cita",
    dependencies=[SoloAdmin],
)
def crear_estado(datos: EstadoCitaIn, repos: ReposDep) -> EstadoCitaOut:
    caso = GestionarEstadosCita(repos.estados_cita, repos.citas)
    return EstadoCitaOut.desde(caso.crear(datos.nombre, datos.descripcion, datos.orden))


@router.delete(
    "/estados-cita/{estado_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un estado de cita",
    dependencies=[SoloAdmin],
)
def eliminar_estado(estado_id: int, repos: ReposDep) -> None:
    GestionarEstadosCita(repos.estados_cita, repos.citas).eliminar(estado_id)


# ------------------------------ servicios ------------------------------
@router.get("/servicios", response_model=list[ServicioOut], summary="Listar servicios")
def listar_servicios(
    repos: ReposDep, solo_activos: bool = False, veterinario_id: int | None = None
) -> list[ServicioOut]:
    return [ServicioOut.desde(v) for v in _servicios(repos).listar(solo_activos, veterinario_id)]


@router.get("/servicios/{servicio_id}", response_model=ServicioOut, summary="Ver un servicio")
def obtener_servicio(servicio_id: int, repos: ReposDep) -> ServicioOut:
    return ServicioOut.desde(_servicios(repos).obtener(servicio_id))


@router.post(
    "/servicios",
    response_model=ServicioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un servicio",
    dependencies=[SoloAdmin],
)
def crear_servicio(datos: ServicioIn, repos: ReposDep) -> ServicioOut:
    return ServicioOut.desde(_servicios(repos).crear(datos.model_dump()))


@router.put(
    "/servicios/{servicio_id}",
    response_model=ServicioOut,
    summary="Actualizar un servicio",
    dependencies=[SoloAdmin],
)
def actualizar_servicio(
    servicio_id: int, datos: ServicioActualizarIn, repos: ReposDep
) -> ServicioOut:
    return ServicioOut.desde(
        _servicios(repos).actualizar(servicio_id, datos.model_dump(exclude_unset=True))
    )


@router.delete(
    "/servicios/{servicio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un servicio",
    dependencies=[SoloAdmin],
)
def eliminar_servicio(servicio_id: int, repos: ReposDep) -> None:
    _servicios(repos).eliminar(servicio_id)


# ---------------------------- disponibilidad ----------------------------
@router.get(
    "/disponibilidades",
    response_model=list[DisponibilidadOut],
    summary="Listar franjas de disponibilidad",
)
def listar_disponibilidades(
    repos: ReposDep, veterinario_id: int | None = None, dia_semana: int | None = None
) -> list[DisponibilidadOut]:
    caso = GestionarDisponibilidad(repos.disponibilidades, repos.usuarios)
    return [DisponibilidadOut.desde(v) for v in caso.listar(veterinario_id, dia_semana)]


@router.post(
    "/disponibilidades",
    response_model=DisponibilidadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Declarar una franja de disponibilidad",
    dependencies=[SoloPersonal],
)
def crear_disponibilidad(datos: DisponibilidadIn, repos: ReposDep) -> DisponibilidadOut:
    caso = GestionarDisponibilidad(repos.disponibilidades, repos.usuarios)
    creada = caso.crear(datos.veterinario_id, datos.dia_semana, datos.hora_inicio, datos.hora_fin)
    return [
        DisponibilidadOut.desde(v)
        for v in caso.listar(datos.veterinario_id, datos.dia_semana)
        if v.disponibilidad.id == creada.id
    ][0]


@router.delete(
    "/disponibilidades/{disponibilidad_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una franja",
    dependencies=[SoloPersonal],
)
def eliminar_disponibilidad(disponibilidad_id: int, repos: ReposDep) -> None:
    GestionarDisponibilidad(repos.disponibilidades, repos.usuarios).eliminar(disponibilidad_id)


@router.get(
    "/veterinarios/{veterinario_id}/agenda",
    response_model=list[str],
    summary="Horas libres de un veterinario en un día",
)
def agenda_dia(veterinario_id: int, repos: ReposDep, dia: date = Query(...)) -> list[str]:
    caso = ConsultarAgendaDia(repos.citas, repos.disponibilidades, repos.usuarios)
    return caso.ejecutar(veterinario_id, dia)


# -------------------------------- citas --------------------------------
@router.get("/citas", response_model=list[CitaOut], summary="Listar citas")
def listar_citas(
    repos: ReposDep,
    mascota_id: int | None = None,
    veterinario_id: int | None = None,
    cliente_id: int | None = None,
    estado: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> list[CitaOut]:
    vistas = _consulta(repos).listar(mascota_id, veterinario_id, cliente_id, estado, desde, hasta)
    return [CitaOut.desde(v) for v in vistas]


@router.get("/citas/{cita_id}", response_model=CitaOut, summary="Ver una cita")
def obtener_cita(cita_id: int, repos: ReposDep) -> CitaOut:
    return CitaOut.desde(_consulta(repos).obtener(cita_id))


@router.post(
    "/citas",
    response_model=CitaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Agendar una cita",
)
def crear_cita(datos: CitaIn, repos: ReposDep, servicios: ServiciosDep) -> CitaOut:
    caso = AgendarCita(
        repos.citas,
        repos.mascotas,
        repos.usuarios,
        repos.servicios,
        repos.estados_cita,
        repos.disponibilidades,
        servicios.reloj,
    )
    cita = caso.ejecutar(datos.model_dump())
    return CitaOut.desde(_consulta(repos).obtener(cita.id))


@router.put("/citas/{cita_id}", response_model=CitaOut, summary="Actualizar una cita")
def actualizar_cita(cita_id: int, datos: CitaActualizarIn, repos: ReposDep) -> CitaOut:
    caso = ActualizarCita(repos.citas, repos.estados_cita, repos.servicios)
    caso.ejecutar(cita_id, datos.model_dump(exclude_unset=True))
    return CitaOut.desde(_consulta(repos).obtener(cita_id))


@router.put("/citas/{cita_id}/estado", response_model=CitaOut, summary="Cambiar el estado")
def cambiar_estado(cita_id: int, datos: CambioEstadoIn, repos: ReposDep) -> CitaOut:
    caso = ActualizarCita(repos.citas, repos.estados_cita, repos.servicios)
    caso.cambiar_estado(cita_id, datos.estado_id, datos.estado)
    return CitaOut.desde(_consulta(repos).obtener(cita_id))


@router.delete(
    "/citas/{cita_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una cita",
    dependencies=[SoloPersonal],
)
def eliminar_cita(cita_id: int, repos: ReposDep) -> None:
    ActualizarCita(repos.citas, repos.estados_cita, repos.servicios).eliminar(cita_id)
