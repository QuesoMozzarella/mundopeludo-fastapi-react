"""Rutas del módulo de adopciones."""
from __future__ import annotations

from fastapi import APIRouter, status

from ....application.use_cases.adopciones import (
    CancelarSolicitudAdopcion,
    ConsultarSolicitudesAdopcion,
    PublicarMascotaEnAdopcion,
    ResolverSolicitudAdopcion,
    SolicitarAdopcion,
)
from ....application.use_cases.mascotas import ConsultarMascotas
from ..deps import AccesoDep, ReposDep, ServiciosDep, SoloPersonal
from ..schemas.mascotas import (
    CancelacionIn,
    MascotaOut,
    RevisionIn,
    SolicitudAdopcionIn,
    SolicitudAdopcionOut,
)

router = APIRouter(prefix="/api/adopciones", tags=["adopciones"])


def _consulta(repos: ReposDep) -> ConsultarSolicitudesAdopcion:
    return ConsultarSolicitudesAdopcion(repos.solicitudes, repos.mascotas, repos.usuarios)


@router.get("", response_model=list[MascotaOut], summary="Mascotas publicadas en adopción")
def listar_disponibles(repos: ReposDep) -> list[MascotaOut]:
    caso = ConsultarMascotas(repos.mascotas, repos.especies, repos.usuarios)
    return [MascotaOut.desde(v) for v in caso.listar(estado_adopcion="en_adopcion")]


@router.put(
    "/mascotas/{mascota_id}/publicar",
    response_model=MascotaOut,
    summary="Publicar una mascota en adopción",
    dependencies=[SoloPersonal],
)
def publicar(mascota_id: int, repos: ReposDep) -> MascotaOut:
    PublicarMascotaEnAdopcion(repos.mascotas).publicar(mascota_id)
    consulta = ConsultarMascotas(repos.mascotas, repos.especies, repos.usuarios)
    return MascotaOut.desde(consulta.obtener(mascota_id))


@router.put(
    "/mascotas/{mascota_id}/retirar",
    response_model=MascotaOut,
    summary="Retirar una mascota de adopción",
    dependencies=[SoloPersonal],
)
def retirar(mascota_id: int, repos: ReposDep) -> MascotaOut:
    PublicarMascotaEnAdopcion(repos.mascotas).retirar(mascota_id)
    consulta = ConsultarMascotas(repos.mascotas, repos.especies, repos.usuarios)
    return MascotaOut.desde(consulta.obtener(mascota_id))


@router.get(
    "/solicitudes", response_model=list[SolicitudAdopcionOut], summary="Listar solicitudes"
)
def listar_solicitudes(
    repos: ReposDep,
    acceso: AccesoDep,
    cliente_id: int | None = None,
    mascota_id: int | None = None,
    estado: str | None = None,
) -> list[SolicitudAdopcionOut]:
    cliente_id = acceso.filtro_propio(cliente_id)
    return [
        SolicitudAdopcionOut.desde(v)
        for v in _consulta(repos).listar(cliente_id, mascota_id, estado)
    ]


@router.get(
    "/solicitudes/{solicitud_id}",
    response_model=SolicitudAdopcionOut,
    summary="Ver una solicitud",
)
def obtener_solicitud(
    solicitud_id: int, repos: ReposDep, acceso: AccesoDep
) -> SolicitudAdopcionOut:
    vista = _consulta(repos).obtener(solicitud_id)
    acceso.propietario(vista.solicitud.cliente_id)
    return SolicitudAdopcionOut.desde(vista)


@router.post(
    "/solicitudes",
    response_model=SolicitudAdopcionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Postular a una adopción",
)
def crear_solicitud(
    datos: SolicitudAdopcionIn, repos: ReposDep, servicios: ServiciosDep, acceso: AccesoDep
) -> SolicitudAdopcionOut:
    acceso.propietario(datos.cliente_id)
    caso = SolicitarAdopcion(
        repos.solicitudes, repos.mascotas, repos.usuarios, servicios.reloj, repos.actividades
    )
    solicitud = caso.ejecutar(datos.mascota_id, datos.cliente_id, datos.notas_cliente)
    return SolicitudAdopcionOut.desde(_consulta(repos).obtener(solicitud.id))


@router.put(
    "/solicitudes/{solicitud_id}/aprobar",
    response_model=SolicitudAdopcionOut,
    summary="Aprobar una solicitud y transferir la mascota",
    dependencies=[SoloPersonal],
)
def aprobar(
    solicitud_id: int,
    datos: RevisionIn,
    repos: ReposDep,
    servicios: ServiciosDep,
    acceso: AccesoDep,
) -> SolicitudAdopcionOut:
    # El revisor es quien firma: nadie revisa en nombre de otro veterinario.
    acceso.propietario(datos.revisor_id, personal=False)
    caso = ResolverSolicitudAdopcion(
        repos.solicitudes, repos.mascotas, repos.usuarios, servicios.reloj, repos.actividades
    )
    caso.aprobar(solicitud_id, datos.revisor_id, datos.notas)
    return SolicitudAdopcionOut.desde(_consulta(repos).obtener(solicitud_id))


@router.put(
    "/solicitudes/{solicitud_id}/rechazar",
    response_model=SolicitudAdopcionOut,
    summary="Rechazar una solicitud",
    dependencies=[SoloPersonal],
)
def rechazar(
    solicitud_id: int,
    datos: RevisionIn,
    repos: ReposDep,
    servicios: ServiciosDep,
    acceso: AccesoDep,
) -> SolicitudAdopcionOut:
    acceso.propietario(datos.revisor_id, personal=False)
    caso = ResolverSolicitudAdopcion(
        repos.solicitudes, repos.mascotas, repos.usuarios, servicios.reloj, repos.actividades
    )
    caso.rechazar(solicitud_id, datos.revisor_id, datos.notas)
    return SolicitudAdopcionOut.desde(_consulta(repos).obtener(solicitud_id))


@router.put(
    "/solicitudes/{solicitud_id}/cancelar",
    response_model=SolicitudAdopcionOut,
    summary="Cancelar la propia solicitud",
)
def cancelar(
    solicitud_id: int,
    datos: CancelacionIn,
    repos: ReposDep,
    servicios: ServiciosDep,
    acceso: AccesoDep,
) -> SolicitudAdopcionOut:
    acceso.propietario(datos.cliente_id)
    caso = CancelarSolicitudAdopcion(repos.solicitudes, repos.mascotas, servicios.reloj)
    caso.ejecutar(solicitud_id, datos.cliente_id)
    return SolicitudAdopcionOut.desde(_consulta(repos).obtener(solicitud_id))
