"""Rutas de historiales médicos."""
from __future__ import annotations

from fastapi import APIRouter, status

from ..casos import ActualizarHistorialDep, ConsultarHistorialesDep, RegistrarHistorialDep
from ..deps import AccesoDep, SoloPersonal
from ..schemas.citas import HistorialActualizarIn, HistorialIn, HistorialOut

router = APIRouter(prefix="/api", tags=["historiales médicos"])


# `/historiales` es un alias histórico que usaba el cliente anterior.
@router.get(
    "/historiales-medicos", response_model=list[HistorialOut], summary="Listar historiales"
)
@router.get("/historiales", response_model=list[HistorialOut], include_in_schema=False)
def listar(
    consulta: ConsultarHistorialesDep,
    acceso: AccesoDep,
    mascota_id: int | None = None,
    veterinario_id: int | None = None,
    cliente_id: int | None = None,
) -> list[HistorialOut]:
    cliente_id = acceso.filtro_propio(cliente_id)
    return [
        HistorialOut.desde(v) for v in consulta.listar(mascota_id, veterinario_id, cliente_id)
    ]


@router.get(
    "/historiales-medicos/{historial_id}", response_model=HistorialOut, summary="Ver un historial"
)
def obtener(
    historial_id: int, consulta: ConsultarHistorialesDep, acceso: AccesoDep
) -> HistorialOut:
    vista = consulta.obtener(historial_id)
    acceso.propietario(vista.cliente_id)
    return HistorialOut.desde(vista)


@router.post(
    "/historiales-medicos",
    response_model=HistorialOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar la ficha clínica de una mascota (con o sin cita)",
    dependencies=[SoloPersonal],
)
@router.post(
    "/historiales",
    response_model=HistorialOut,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
    dependencies=[SoloPersonal],
)
def crear(
    datos: HistorialIn,
    caso: RegistrarHistorialDep,
    consulta: ConsultarHistorialesDep,
    acceso: AccesoDep,
) -> HistorialOut:
    if datos.veterinario_id is not None:
        # Quien firma la ficha es el veterinario de la sesión (o un admin).
        acceso.propietario(datos.veterinario_id, personal=False)
    historial = caso.ejecutar(datos.model_dump())
    return HistorialOut.desde(consulta.obtener(historial.id))


@router.put(
    "/historiales-medicos/{historial_id}",
    response_model=HistorialOut,
    summary="Actualizar un historial",
    dependencies=[SoloPersonal],
)
def actualizar(
    historial_id: int,
    datos: HistorialActualizarIn,
    caso: ActualizarHistorialDep,
    consulta: ConsultarHistorialesDep,
) -> HistorialOut:
    caso.ejecutar(historial_id, datos.model_dump(exclude_unset=True))
    return HistorialOut.desde(consulta.obtener(historial_id))


@router.delete(
    "/historiales-medicos/{historial_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un historial",
    dependencies=[SoloPersonal],
)
def eliminar(historial_id: int, caso: ActualizarHistorialDep) -> None:
    caso.eliminar(historial_id)
