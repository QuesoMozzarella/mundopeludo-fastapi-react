"""Rutas de especies y mascotas."""
from __future__ import annotations

from fastapi import APIRouter, Query, status

from ....application.use_cases.mascotas import (
    ActualizarMascota,
    ConsultarMascotas,
    DarDeBajaMascota,
    GestionarEspecies,
    RegistrarMascota,
)
from ..deps import ReposDep, ServiciosDep, SoloAdmin
from ..schemas.mascotas import (
    EspecieIn,
    EspecieOut,
    MascotaActualizarIn,
    MascotaIn,
    MascotaOut,
)

router = APIRouter(prefix="/api", tags=["mascotas"])


def _consulta(repos: ReposDep) -> ConsultarMascotas:
    return ConsultarMascotas(repos.mascotas, repos.especies, repos.usuarios)


# ------------------------------ especies ------------------------------
@router.get("/especies", response_model=list[EspecieOut], summary="Listar especies")
def listar_especies(repos: ReposDep) -> list[EspecieOut]:
    caso = GestionarEspecies(repos.especies, repos.mascotas)
    return [EspecieOut.desde(e) for e in caso.listar()]


@router.post(
    "/especies",
    response_model=EspecieOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una especie",
    dependencies=[SoloAdmin],
)
def crear_especie(datos: EspecieIn, repos: ReposDep) -> EspecieOut:
    caso = GestionarEspecies(repos.especies, repos.mascotas)
    return EspecieOut.desde(caso.crear(datos.nombre))


@router.put(
    "/especies/{especie_id}",
    response_model=EspecieOut,
    summary="Renombrar una especie",
    dependencies=[SoloAdmin],
)
def actualizar_especie(especie_id: int, datos: EspecieIn, repos: ReposDep) -> EspecieOut:
    caso = GestionarEspecies(repos.especies, repos.mascotas)
    return EspecieOut.desde(caso.actualizar(especie_id, datos.nombre))


@router.delete(
    "/especies/{especie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una especie",
    dependencies=[SoloAdmin],
)
def eliminar_especie(especie_id: int, repos: ReposDep) -> None:
    GestionarEspecies(repos.especies, repos.mascotas).eliminar(especie_id)


# ------------------------------ mascotas ------------------------------
@router.get("/mascotas", response_model=list[MascotaOut], summary="Listar mascotas")
def listar_mascotas(
    repos: ReposDep,
    cliente_id: int | None = None,
    especie_id: int | None = None,
    estado_adopcion: str | None = None,
    activo: bool | None = True,
    buscar: str | None = Query(default=None, description="Nombre o raza"),
) -> list[MascotaOut]:
    vistas = _consulta(repos).listar(cliente_id, especie_id, estado_adopcion, activo, buscar)
    return [MascotaOut.desde(v) for v in vistas]


@router.get("/mascotas/{mascota_id}", response_model=MascotaOut, summary="Ver una mascota")
def obtener_mascota(mascota_id: int, repos: ReposDep) -> MascotaOut:
    return MascotaOut.desde(_consulta(repos).obtener(mascota_id))


@router.post(
    "/mascotas",
    response_model=MascotaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una mascota",
)
def crear_mascota(datos: MascotaIn, repos: ReposDep, servicios: ServiciosDep) -> MascotaOut:
    caso = RegistrarMascota(repos.mascotas, repos.especies, repos.usuarios, servicios.reloj)
    mascota = caso.ejecutar(datos.model_dump())
    return MascotaOut.desde(_consulta(repos).obtener(mascota.id))


@router.put("/mascotas/{mascota_id}", response_model=MascotaOut, summary="Actualizar una mascota")
def actualizar_mascota(
    mascota_id: int, datos: MascotaActualizarIn, repos: ReposDep
) -> MascotaOut:
    caso = ActualizarMascota(repos.mascotas, repos.especies, repos.usuarios)
    caso.ejecutar(mascota_id, datos.model_dump(exclude_unset=True))
    return MascotaOut.desde(_consulta(repos).obtener(mascota_id))


@router.delete(
    "/mascotas/{mascota_id}",
    response_model=MascotaOut,
    summary="Dar de baja una mascota (baja lógica)",
)
def eliminar_mascota(mascota_id: int, repos: ReposDep) -> MascotaOut:
    DarDeBajaMascota(repos.mascotas).ejecutar(mascota_id)
    return MascotaOut.desde(_consulta(repos).obtener(mascota_id))
