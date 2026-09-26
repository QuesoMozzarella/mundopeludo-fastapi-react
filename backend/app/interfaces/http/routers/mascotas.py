"""Rutas de especies y mascotas."""
from __future__ import annotations

from fastapi import APIRouter, Query, status

from ....application.use_cases.mascotas import ActualizarMascotaCmd, RegistrarMascotaCmd
from ....domain.value_objects import EstadoAdopcion
from ..casos import (
    ActualizarMascotaDep,
    ConsultarMascotasDep,
    DarDeBajaMascotaDep,
    ConsultarEspeciesDep,
    CrearEspecieDep,
    EliminarEspecieDep,
    RegistrarMascotaDep,
    RenombrarEspecieDep,
)
from ..deps import AccesoDep, SoloAdmin
from ..schemas.mascotas import (
    EspecieIn,
    EspecieOut,
    MascotaActualizarIn,
    MascotaIn,
    MascotaOut,
)

router = APIRouter(prefix="/api", tags=["mascotas"])


# ------------------------------ especies ------------------------------
@router.get("/especies", response_model=list[EspecieOut], summary="Listar especies")
def listar_especies(consulta: ConsultarEspeciesDep) -> list[EspecieOut]:
    return [EspecieOut.desde(e) for e in consulta.listar()]


@router.post(
    "/especies",
    response_model=EspecieOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una especie",
    dependencies=[SoloAdmin],
)
def crear_especie(datos: EspecieIn, caso: CrearEspecieDep) -> EspecieOut:
    return EspecieOut.desde(caso.ejecutar(datos.nombre))


@router.put(
    "/especies/{especie_id}",
    response_model=EspecieOut,
    summary="Renombrar una especie",
    dependencies=[SoloAdmin],
)
def actualizar_especie(
    especie_id: int, datos: EspecieIn, caso: RenombrarEspecieDep
) -> EspecieOut:
    return EspecieOut.desde(caso.ejecutar(especie_id, datos.nombre))


@router.delete(
    "/especies/{especie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una especie",
    dependencies=[SoloAdmin],
)
def eliminar_especie(especie_id: int, caso: EliminarEspecieDep) -> None:
    caso.ejecutar(especie_id)


# ------------------------------ mascotas ------------------------------
@router.get("/mascotas", response_model=list[MascotaOut], summary="Listar mascotas")
def listar_mascotas(
    consulta: ConsultarMascotasDep,
    acceso: AccesoDep,
    cliente_id: int | None = None,
    especie_id: int | None = None,
    estado_adopcion: str | None = None,
    activo: bool | None = True,
    buscar: str | None = Query(default=None, description="Nombre o raza"),
) -> list[MascotaOut]:
    cliente_id = acceso.filtro_propio(cliente_id)
    vistas = consulta.listar(cliente_id, especie_id, estado_adopcion, activo, buscar)
    return [MascotaOut.desde(v) for v in vistas]


@router.get("/mascotas/{mascota_id}", response_model=MascotaOut, summary="Ver una mascota")
def obtener_mascota(
    mascota_id: int, consulta: ConsultarMascotasDep, acceso: AccesoDep
) -> MascotaOut:
    vista = consulta.obtener(mascota_id)
    # Las mascotas publicadas en adopción son visibles para cualquiera.
    if vista.mascota.estado_adopcion is not EstadoAdopcion.EN_ADOPCION:
        acceso.propietario(vista.mascota.cliente_id)
    return MascotaOut.desde(vista)


@router.post(
    "/mascotas",
    response_model=MascotaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una mascota",
)
def crear_mascota(
    datos: MascotaIn,
    caso: RegistrarMascotaDep,
    consulta: ConsultarMascotasDep,
    acceso: AccesoDep,
) -> MascotaOut:
    acceso.propietario(datos.cliente_id)
    estado = EstadoAdopcion.desde(
        datos.estado_adopcion, campo="estado_adopcion", por_defecto=EstadoAdopcion.NORMAL
    )
    if estado is not EstadoAdopcion.NORMAL:
        acceso.solo_personal()
    mascota = caso.ejecutar(RegistrarMascotaCmd(**datos.model_dump()))
    return MascotaOut.desde(consulta.obtener(mascota.id))


@router.put("/mascotas/{mascota_id}", response_model=MascotaOut, summary="Actualizar una mascota")
def actualizar_mascota(
    mascota_id: int,
    datos: MascotaActualizarIn,
    caso: ActualizarMascotaDep,
    consulta: ConsultarMascotasDep,
    acceso: AccesoDep,
) -> MascotaOut:
    actual = consulta.obtener(mascota_id).mascota
    acceso.propietario(actual.cliente_id)
    cambios = datos.model_dump(exclude_unset=True)
    transfiere = cambios.get("cliente_id", actual.cliente_id) != actual.cliente_id
    if transfiere or "estado_adopcion" in cambios:
        # Transferir la mascota o publicarla en adopción es tarea del personal.
        acceso.solo_personal()
    caso.ejecutar(mascota_id, ActualizarMascotaCmd(**cambios))
    return MascotaOut.desde(consulta.obtener(mascota_id))


@router.delete(
    "/mascotas/{mascota_id}",
    response_model=MascotaOut,
    summary="Dar de baja una mascota (baja lógica)",
)
def eliminar_mascota(
    mascota_id: int, caso: DarDeBajaMascotaDep, consulta: ConsultarMascotasDep, acceso: AccesoDep
) -> MascotaOut:
    acceso.propietario(consulta.obtener(mascota_id).mascota.cliente_id)
    caso.ejecutar(mascota_id)
    return MascotaOut.desde(consulta.obtener(mascota_id))
