"""Rutas de historiales médicos."""
from __future__ import annotations

from fastapi import APIRouter, status

from ....application.use_cases.historiales import (
    ActualizarHistorial,
    ConsultarHistoriales,
    RegistrarHistorial,
)
from ..deps import AccesoDep, ReposDep, ServiciosDep, SoloPersonal
from ..schemas.citas import HistorialActualizarIn, HistorialIn, HistorialOut

router = APIRouter(prefix="/api", tags=["historiales médicos"])


def _consulta(repos: ReposDep) -> ConsultarHistoriales:
    return ConsultarHistoriales(repos.historiales, repos.citas, repos.mascotas, repos.usuarios)


@router.get(
    "/historiales-medicos", response_model=list[HistorialOut], summary="Listar historiales"
)
def listar(
    repos: ReposDep,
    acceso: AccesoDep,
    mascota_id: int | None = None,
    veterinario_id: int | None = None,
    cliente_id: int | None = None,
) -> list[HistorialOut]:
    cliente_id = acceso.filtro_propio(cliente_id)
    return [
        HistorialOut.desde(v)
        for v in _consulta(repos).listar(mascota_id, veterinario_id, cliente_id)
    ]


@router.get(
    "/historiales-medicos/{historial_id}", response_model=HistorialOut, summary="Ver un historial"
)
def obtener(historial_id: int, repos: ReposDep, acceso: AccesoDep) -> HistorialOut:
    vista = _consulta(repos).obtener(historial_id)
    acceso.propietario(vista.cliente_id)
    return HistorialOut.desde(vista)


@router.post(
    "/historiales-medicos",
    response_model=HistorialOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar la ficha clínica de una cita",
    dependencies=[SoloPersonal],
)
def crear(datos: HistorialIn, repos: ReposDep, servicios: ServiciosDep) -> HistorialOut:
    caso = RegistrarHistorial(repos.historiales, repos.citas, repos.usuarios, servicios.reloj)
    historial = caso.ejecutar(datos.model_dump())
    return HistorialOut.desde(_consulta(repos).obtener(historial.id))


@router.put(
    "/historiales-medicos/{historial_id}",
    response_model=HistorialOut,
    summary="Actualizar un historial",
    dependencies=[SoloPersonal],
)
def actualizar(
    historial_id: int, datos: HistorialActualizarIn, repos: ReposDep
) -> HistorialOut:
    ActualizarHistorial(repos.historiales).ejecutar(
        historial_id, datos.model_dump(exclude_unset=True)
    )
    return HistorialOut.desde(_consulta(repos).obtener(historial_id))


@router.delete(
    "/historiales-medicos/{historial_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un historial",
    dependencies=[SoloPersonal],
)
def eliminar(historial_id: int, repos: ReposDep) -> None:
    ActualizarHistorial(repos.historiales).eliminar(historial_id)


# Alias histórico usado por el cliente actual.
@router.get(
    "/historiales", response_model=list[HistorialOut], include_in_schema=False
)
def listar_alias(
    repos: ReposDep,
    acceso: AccesoDep,
    mascota_id: int | None = None,
    veterinario_id: int | None = None,
    cliente_id: int | None = None,
) -> list[HistorialOut]:
    return listar(repos, acceso, mascota_id, veterinario_id, cliente_id)


@router.post(
    "/historiales",
    response_model=HistorialOut,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
    dependencies=[SoloPersonal],
)
def crear_alias(datos: HistorialIn, repos: ReposDep, servicios: ServiciosDep) -> HistorialOut:
    return crear(datos, repos, servicios)
