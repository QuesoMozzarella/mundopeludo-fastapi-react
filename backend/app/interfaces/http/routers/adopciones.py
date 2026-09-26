"""Rutas del módulo de adopciones."""
from __future__ import annotations

from fastapi import APIRouter, status

from ....domain.value_objects import EstadoAdopcion
from ..casos import (
    CancelarSolicitudAdopcionDep,
    ConsultarMascotasDep,
    ConsultarSolicitudesAdopcionDep,
    PublicarMascotaEnAdopcionDep,
    ResolverSolicitudAdopcionDep,
    SolicitarAdopcionDep,
)
from ..deps import AccesoDep, SoloPersonal
from ..schemas.mascotas import (
    CancelacionIn,
    MascotaOut,
    RevisionIn,
    SolicitudAdopcionIn,
    SolicitudAdopcionOut,
)

router = APIRouter(prefix="/api/adopciones", tags=["adopciones"])


@router.get("", response_model=list[MascotaOut], summary="Mascotas publicadas en adopción")
def listar_disponibles(mascotas: ConsultarMascotasDep) -> list[MascotaOut]:
    disponibles = mascotas.listar(estado_adopcion=EstadoAdopcion.EN_ADOPCION.value)
    return [MascotaOut.desde(v) for v in disponibles]


@router.put(
    "/mascotas/{mascota_id}/publicar",
    response_model=MascotaOut,
    summary="Publicar una mascota en adopción",
    dependencies=[SoloPersonal],
)
def publicar(
    mascota_id: int, caso: PublicarMascotaEnAdopcionDep, mascotas: ConsultarMascotasDep
) -> MascotaOut:
    caso.publicar(mascota_id)
    return MascotaOut.desde(mascotas.obtener(mascota_id))


@router.put(
    "/mascotas/{mascota_id}/retirar",
    response_model=MascotaOut,
    summary="Retirar una mascota de adopción",
    dependencies=[SoloPersonal],
)
def retirar(
    mascota_id: int, caso: PublicarMascotaEnAdopcionDep, mascotas: ConsultarMascotasDep
) -> MascotaOut:
    caso.retirar(mascota_id)
    return MascotaOut.desde(mascotas.obtener(mascota_id))


@router.get(
    "/solicitudes", response_model=list[SolicitudAdopcionOut], summary="Listar solicitudes"
)
def listar_solicitudes(
    consulta: ConsultarSolicitudesAdopcionDep,
    acceso: AccesoDep,
    cliente_id: int | None = None,
    mascota_id: int | None = None,
    estado: str | None = None,
) -> list[SolicitudAdopcionOut]:
    cliente_id = acceso.filtro_propio(cliente_id)
    return [
        SolicitudAdopcionOut.desde(v) for v in consulta.listar(cliente_id, mascota_id, estado)
    ]


@router.get(
    "/solicitudes/{solicitud_id}",
    response_model=SolicitudAdopcionOut,
    summary="Ver una solicitud",
)
def obtener_solicitud(
    solicitud_id: int, consulta: ConsultarSolicitudesAdopcionDep, acceso: AccesoDep
) -> SolicitudAdopcionOut:
    vista = consulta.obtener(solicitud_id)
    acceso.propietario(vista.solicitud.cliente_id)
    return SolicitudAdopcionOut.desde(vista)


@router.post(
    "/solicitudes",
    response_model=SolicitudAdopcionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Postular a una adopción",
)
def crear_solicitud(
    datos: SolicitudAdopcionIn,
    caso: SolicitarAdopcionDep,
    consulta: ConsultarSolicitudesAdopcionDep,
    acceso: AccesoDep,
) -> SolicitudAdopcionOut:
    acceso.propietario(datos.cliente_id)
    solicitud = caso.ejecutar(datos.mascota_id, datos.cliente_id, datos.notas_cliente)
    return SolicitudAdopcionOut.desde(consulta.obtener(solicitud.id))


@router.put(
    "/solicitudes/{solicitud_id}/aprobar",
    response_model=SolicitudAdopcionOut,
    summary="Aprobar una solicitud y transferir la mascota",
    dependencies=[SoloPersonal],
)
def aprobar(
    solicitud_id: int,
    datos: RevisionIn,
    caso: ResolverSolicitudAdopcionDep,
    consulta: ConsultarSolicitudesAdopcionDep,
    acceso: AccesoDep,
) -> SolicitudAdopcionOut:
    # El revisor es quien firma: nadie revisa en nombre de otro veterinario.
    acceso.propietario(datos.revisor_id, personal=False)
    caso.aprobar(solicitud_id, datos.revisor_id, datos.notas)
    return SolicitudAdopcionOut.desde(consulta.obtener(solicitud_id))


@router.put(
    "/solicitudes/{solicitud_id}/rechazar",
    response_model=SolicitudAdopcionOut,
    summary="Rechazar una solicitud",
    dependencies=[SoloPersonal],
)
def rechazar(
    solicitud_id: int,
    datos: RevisionIn,
    caso: ResolverSolicitudAdopcionDep,
    consulta: ConsultarSolicitudesAdopcionDep,
    acceso: AccesoDep,
) -> SolicitudAdopcionOut:
    acceso.propietario(datos.revisor_id, personal=False)
    caso.rechazar(solicitud_id, datos.revisor_id, datos.notas)
    return SolicitudAdopcionOut.desde(consulta.obtener(solicitud_id))


@router.put(
    "/solicitudes/{solicitud_id}/cancelar",
    response_model=SolicitudAdopcionOut,
    summary="Cancelar la propia solicitud",
)
def cancelar(
    solicitud_id: int,
    datos: CancelacionIn,
    caso: CancelarSolicitudAdopcionDep,
    consulta: ConsultarSolicitudesAdopcionDep,
    acceso: AccesoDep,
) -> SolicitudAdopcionOut:
    acceso.propietario(datos.cliente_id)
    caso.ejecutar(solicitud_id, datos.cliente_id)
    return SolicitudAdopcionOut.desde(consulta.obtener(solicitud_id))
