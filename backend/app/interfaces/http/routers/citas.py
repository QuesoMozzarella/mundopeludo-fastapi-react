"""Rutas de la agenda: estados, servicios, disponibilidad y citas."""
from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Query, status

from ....application.use_cases.citas import (
    ActualizarCitaCmd,
    ActualizarServicioCmd,
    AgendarCitaCmd,
    CrearServicioCmd,
)
from ..casos import (
    ActualizarCitaDep,
    AgendarCitaDep,
    ConsultarAgendaDiaDep,
    ConsultarCitasDep,
    ConsultarMascotasDep,
    GestionarDisponibilidadDep,
    GestionarEstadosCitaDep,
    GestionarServiciosDep,
)
from ..deps import AccesoDep, SoloAdmin, SoloPersonal
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


# --------------------------- estados de cita ---------------------------
@router.get("/estados-cita", response_model=list[EstadoCitaOut], summary="Listar estados de cita")
def listar_estados(caso: GestionarEstadosCitaDep) -> list[EstadoCitaOut]:
    return [EstadoCitaOut.desde(e) for e in caso.listar()]


@router.post(
    "/estados-cita",
    response_model=EstadoCitaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un estado de cita",
    dependencies=[SoloAdmin],
)
def crear_estado(datos: EstadoCitaIn, caso: GestionarEstadosCitaDep) -> EstadoCitaOut:
    return EstadoCitaOut.desde(caso.crear(datos.nombre, datos.descripcion, datos.orden))


@router.delete(
    "/estados-cita/{estado_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un estado de cita",
    dependencies=[SoloAdmin],
)
def eliminar_estado(estado_id: int, caso: GestionarEstadosCitaDep) -> None:
    caso.eliminar(estado_id)


# ------------------------------ servicios ------------------------------
@router.get("/servicios", response_model=list[ServicioOut], summary="Listar servicios")
def listar_servicios(
    caso: GestionarServiciosDep, solo_activos: bool = False, veterinario_id: int | None = None
) -> list[ServicioOut]:
    return [ServicioOut.desde(v) for v in caso.listar(solo_activos, veterinario_id)]


@router.get("/servicios/{servicio_id}", response_model=ServicioOut, summary="Ver un servicio")
def obtener_servicio(servicio_id: int, caso: GestionarServiciosDep) -> ServicioOut:
    return ServicioOut.desde(caso.obtener(servicio_id))


@router.post(
    "/servicios",
    response_model=ServicioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un servicio",
    dependencies=[SoloAdmin],
)
def crear_servicio(datos: ServicioIn, caso: GestionarServiciosDep) -> ServicioOut:
    return ServicioOut.desde(caso.crear(CrearServicioCmd(**datos.model_dump())))


@router.put(
    "/servicios/{servicio_id}",
    response_model=ServicioOut,
    summary="Actualizar un servicio",
    dependencies=[SoloAdmin],
)
def actualizar_servicio(
    servicio_id: int, datos: ServicioActualizarIn, caso: GestionarServiciosDep
) -> ServicioOut:
    cmd = ActualizarServicioCmd(**datos.model_dump(exclude_unset=True))
    return ServicioOut.desde(caso.actualizar(servicio_id, cmd))


@router.delete(
    "/servicios/{servicio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un servicio",
    dependencies=[SoloAdmin],
)
def eliminar_servicio(servicio_id: int, caso: GestionarServiciosDep) -> None:
    caso.eliminar(servicio_id)


# ---------------------------- disponibilidad ----------------------------
@router.get(
    "/disponibilidades",
    response_model=list[DisponibilidadOut],
    summary="Listar franjas de disponibilidad",
)
def listar_disponibilidades(
    caso: GestionarDisponibilidadDep,
    veterinario_id: int | None = None,
    dia_semana: int | None = None,
) -> list[DisponibilidadOut]:
    return [DisponibilidadOut.desde(v) for v in caso.listar(veterinario_id, dia_semana)]


@router.post(
    "/disponibilidades",
    response_model=DisponibilidadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Declarar una franja de disponibilidad",
    dependencies=[SoloPersonal],
)
def crear_disponibilidad(
    datos: DisponibilidadIn, caso: GestionarDisponibilidadDep
) -> DisponibilidadOut:
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
def eliminar_disponibilidad(disponibilidad_id: int, caso: GestionarDisponibilidadDep) -> None:
    caso.eliminar(disponibilidad_id)


@router.get(
    "/veterinarios/{veterinario_id}/agenda",
    response_model=list[str],
    summary="Horas libres de un veterinario en un día",
)
def agenda_dia(
    veterinario_id: int, caso: ConsultarAgendaDiaDep, dia: date = Query(...)
) -> list[str]:
    return caso.ejecutar(veterinario_id, dia)


# -------------------------------- citas --------------------------------
@router.get("/citas", response_model=list[CitaOut], summary="Listar citas")
def listar_citas(
    consulta: ConsultarCitasDep,
    acceso: AccesoDep,
    mascota_id: int | None = None,
    veterinario_id: int | None = None,
    cliente_id: int | None = None,
    estado: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> list[CitaOut]:
    cliente_id = acceso.filtro_propio(cliente_id)
    vistas = consulta.listar(mascota_id, veterinario_id, cliente_id, estado, desde, hasta)
    return [CitaOut.desde(v) for v in vistas]


@router.get("/citas/{cita_id}", response_model=CitaOut, summary="Ver una cita")
def obtener_cita(cita_id: int, consulta: ConsultarCitasDep, acceso: AccesoDep) -> CitaOut:
    vista = consulta.obtener(cita_id)
    acceso.propietario(vista.cliente_id)
    return CitaOut.desde(vista)


@router.post(
    "/citas",
    response_model=CitaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Agendar una cita",
)
def crear_cita(
    datos: CitaIn,
    caso: AgendarCitaDep,
    consulta: ConsultarCitasDep,
    mascotas: ConsultarMascotasDep,
    acceso: AccesoDep,
) -> CitaOut:
    acceso.propietario(mascotas.obtener(datos.mascota_id).mascota.cliente_id)
    cita = caso.ejecutar(AgendarCitaCmd(**datos.model_dump()))
    return CitaOut.desde(consulta.obtener(cita.id))


@router.put("/citas/{cita_id}", response_model=CitaOut, summary="Actualizar una cita")
def actualizar_cita(
    cita_id: int,
    datos: CitaActualizarIn,
    caso: ActualizarCitaDep,
    consulta: ConsultarCitasDep,
    acceso: AccesoDep,
) -> CitaOut:
    acceso.propietario(consulta.obtener(cita_id).cliente_id)
    caso.ejecutar(cita_id, ActualizarCitaCmd(**datos.model_dump(exclude_unset=True)))
    return CitaOut.desde(consulta.obtener(cita_id))


@router.put("/citas/{cita_id}/estado", response_model=CitaOut, summary="Cambiar el estado")
def cambiar_estado(
    cita_id: int,
    datos: CambioEstadoIn,
    caso: ActualizarCitaDep,
    consulta: ConsultarCitasDep,
    acceso: AccesoDep,
) -> CitaOut:
    acceso.propietario(consulta.obtener(cita_id).cliente_id)
    caso.cambiar_estado(cita_id, datos.estado_id, datos.estado)
    return CitaOut.desde(consulta.obtener(cita_id))


@router.delete(
    "/citas/{cita_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una cita",
    dependencies=[SoloPersonal],
)
def eliminar_cita(cita_id: int, caso: ActualizarCitaDep) -> None:
    caso.eliminar(cita_id)
