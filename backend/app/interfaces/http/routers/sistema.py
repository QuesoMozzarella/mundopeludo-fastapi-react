"""Rutas transversales: salud, bitácora de actividad y panel de indicadores."""
from __future__ import annotations

from fastapi import APIRouter, status

from ....application.use_cases.sistema import (
    ConsultarActividad,
    ObtenerEstadisticas,
    RegistrarActividad,
)
from ..deps import ReposDep, ServiciosDep, SoloPersonal
from ..schemas.sistema import ActividadIn, ActividadOut, EstadisticasOut, SaludOut

router = APIRouter(prefix="/api", tags=["sistema"])
VERSION = "3.0.0"


@router.get("/health", response_model=SaludOut, summary="Estado del servicio")
def salud() -> SaludOut:
    return SaludOut(version=VERSION)


@router.get(
    "/actividad",
    response_model=list[ActividadOut],
    summary="Bitácora del sistema",
    dependencies=[SoloPersonal],
)
def listar_actividad(
    repos: ReposDep, limite: int = 50, tipo: str | None = None
) -> list[ActividadOut]:
    return [ActividadOut.desde(a) for a in ConsultarActividad(repos.actividades).listar(limite, tipo)]


@router.post(
    "/actividad",
    response_model=ActividadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una entrada en la bitácora",
    dependencies=[SoloPersonal],
)
def registrar_actividad(
    datos: ActividadIn, repos: ReposDep, servicios: ServiciosDep
) -> ActividadOut:
    caso = RegistrarActividad(repos.actividades, servicios.reloj)
    return ActividadOut.desde(caso.ejecutar(datos.usuario, datos.tipo, datos.descripcion))


@router.get(
    "/dashboard/stats",
    response_model=EstadisticasOut,
    summary="Indicadores del panel",
    dependencies=[SoloPersonal],
)
def estadisticas(repos: ReposDep, servicios: ServiciosDep) -> EstadisticasOut:
    caso = ObtenerEstadisticas(
        repos.usuarios,
        repos.mascotas,
        repos.solicitudes,
        repos.citas,
        repos.historiales,
        repos.productos,
        repos.pedidos,
        servicios.reloj,
    )
    return EstadisticasOut.desde(caso.ejecutar())
