"""Rutas transversales: salud, bitácora de actividad y panel de indicadores."""
from __future__ import annotations

from fastapi import APIRouter, status

from ..casos import ConsultarActividadDep, ObtenerEstadisticasDep, RegistrarActividadDep
from ..deps import ConfigDep, SoloPersonal
from ..schemas.sistema import ActividadIn, ActividadOut, EstadisticasOut, SaludOut

router = APIRouter(prefix="/api", tags=["sistema"])
VERSION = "3.0.0"


@router.get("/health", response_model=SaludOut, summary="Estado del servicio")
def salud(configuracion: ConfigDep) -> SaludOut:
    return SaludOut(version=VERSION, persistencia="postgresql" if configuracion.url_bd else "sqlite3")


@router.get(
    "/actividad",
    response_model=list[ActividadOut],
    summary="Bitácora del sistema",
    dependencies=[SoloPersonal],
)
def listar_actividad(
    consulta: ConsultarActividadDep, limite: int = 50, tipo: str | None = None
) -> list[ActividadOut]:
    return [ActividadOut.desde(a) for a in consulta.listar(limite, tipo)]


@router.post(
    "/actividad",
    response_model=ActividadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una entrada en la bitácora",
    dependencies=[SoloPersonal],
)
def registrar_actividad(datos: ActividadIn, caso: RegistrarActividadDep) -> ActividadOut:
    return ActividadOut.desde(caso.ejecutar(datos.usuario, datos.tipo, datos.descripcion))


@router.get(
    "/dashboard/stats",
    response_model=EstadisticasOut,
    summary="Indicadores del panel",
    dependencies=[SoloPersonal],
)
def estadisticas(caso: ObtenerEstadisticasDep) -> EstadisticasOut:
    return EstadisticasOut.desde(caso.ejecutar())
