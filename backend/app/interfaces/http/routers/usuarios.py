"""Rutas de usuarios, perfiles y especialidades."""
from __future__ import annotations

from fastapi import APIRouter, Query, status

from ....application.use_cases.usuarios import ActualizarEspecialidadCmd, ActualizarUsuarioCmd
from ....domain.value_objects import TipoUsuario
from ..casos import (
    ActualizarEspecialidadDep,
    ActualizarUsuarioDep,
    ConsultarEspecialidadesDep,
    ConsultarUsuariosDep,
    CrearEspecialidadDep,
    DesactivarUsuarioDep,
    EliminarEspecialidadDep,
    GuardarPerfilClienteDep,
    GuardarPerfilVeterinarioDep,
)
from ..deps import AccesoDep, SoloAdmin, SoloPersonal
from ..schemas.usuarios import (
    EspecialidadActualizarIn,
    EspecialidadIn,
    EspecialidadOut,
    PerfilClienteIn,
    PerfilClienteOut,
    PerfilVeterinarioIn,
    PerfilVeterinarioOut,
    UsuarioActualizarIn,
    UsuarioOut,
)

router = APIRouter(prefix="/api", tags=["usuarios"])


@router.get(
    "/users",
    response_model=list[UsuarioOut],
    summary="Listar usuarios",
    dependencies=[SoloPersonal],
)
def listar_usuarios(
    consulta: ConsultarUsuariosDep,
    tipo: str | None = None,
    activos: bool | None = None,
    buscar: str | None = Query(default=None, description="Nombre, apellidos o correo"),
) -> list[UsuarioOut]:
    return [UsuarioOut.desde(v) for v in consulta.listar(tipo, activos, buscar)]


@router.get("/veterinarios", response_model=list[UsuarioOut], summary="Listar veterinarios")
def listar_veterinarios(consulta: ConsultarUsuariosDep) -> list[UsuarioOut]:
    return [UsuarioOut.desde(v) for v in consulta.listar(TipoUsuario.VETERINARIO, True)]


@router.get(
    "/clientes",
    response_model=list[UsuarioOut],
    summary="Listar clientes",
    dependencies=[SoloPersonal],
)
def listar_clientes(consulta: ConsultarUsuariosDep) -> list[UsuarioOut]:
    return [UsuarioOut.desde(v) for v in consulta.listar(TipoUsuario.CLIENTE, True)]


@router.get("/users/{usuario_id}", response_model=UsuarioOut, summary="Ver un usuario")
def obtener_usuario(
    usuario_id: int, consulta: ConsultarUsuariosDep, acceso: AccesoDep
) -> UsuarioOut:
    acceso.propietario(usuario_id)
    return UsuarioOut.desde(consulta.obtener(usuario_id))


@router.put("/users/{usuario_id}", response_model=UsuarioOut, summary="Actualizar un usuario")
def actualizar_usuario(
    usuario_id: int,
    datos: UsuarioActualizarIn,
    caso: ActualizarUsuarioDep,
    consulta: ConsultarUsuariosDep,
    acceso: AccesoDep,
) -> UsuarioOut:
    acceso.propietario(usuario_id)
    cambios = datos.model_dump(exclude_unset=True)
    if {"tipo", "is_active"} & cambios.keys():
        # Cambiar el rol o dar de baja una cuenta no es autoservicio.
        acceso.solo_administrador()
    caso.ejecutar(usuario_id, ActualizarUsuarioCmd(**cambios))
    return UsuarioOut.desde(consulta.obtener(usuario_id))


@router.delete(
    "/users/{usuario_id}",
    response_model=UsuarioOut,
    summary="Desactivar un usuario (baja lógica)",
    dependencies=[SoloAdmin],
)
def desactivar_usuario(
    usuario_id: int, caso: DesactivarUsuarioDep, consulta: ConsultarUsuariosDep
) -> UsuarioOut:
    caso.ejecutar(usuario_id)
    return UsuarioOut.desde(consulta.obtener(usuario_id))


@router.put(
    "/users/{usuario_id}/perfil-cliente",
    response_model=PerfilClienteOut,
    summary="Actualizar el perfil de cliente",
)
def guardar_perfil_cliente(
    usuario_id: int, datos: PerfilClienteIn, caso: GuardarPerfilClienteDep, acceso: AccesoDep
) -> PerfilClienteOut:
    acceso.propietario(usuario_id)
    return PerfilClienteOut.desde(caso.ejecutar(usuario_id, datos.documento))


@router.put(
    "/users/{usuario_id}/perfil-veterinario",
    response_model=PerfilVeterinarioOut,
    summary="Actualizar el perfil de veterinario",
    dependencies=[SoloPersonal],
)
def guardar_perfil_veterinario(
    usuario_id: int,
    datos: PerfilVeterinarioIn,
    caso: GuardarPerfilVeterinarioDep,
    acceso: AccesoDep,
) -> PerfilVeterinarioOut:
    # Un veterinario edita su propio perfil; el de otro, sólo un administrador.
    acceso.propietario(usuario_id, personal=False)
    perfil = caso.ejecutar(
        usuario_id,
        documento=datos.documento,
        activo=datos.activo,
        especialidades_ids=datos.especialidades_ids,
        fecha_contratacion=datos.fecha_contratacion,
    )
    return PerfilVeterinarioOut.desde(perfil)


# --------------------------- especialidades ---------------------------
@router.get("/especialidades", response_model=list[EspecialidadOut], summary="Listar especialidades")
def listar_especialidades(
    consulta: ConsultarEspecialidadesDep, solo_activas: bool = False
) -> list[EspecialidadOut]:
    return [EspecialidadOut.desde(e) for e in consulta.listar(solo_activas)]


@router.post(
    "/especialidades",
    response_model=EspecialidadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una especialidad",
    dependencies=[SoloAdmin],
)
def crear_especialidad(datos: EspecialidadIn, caso: CrearEspecialidadDep) -> EspecialidadOut:
    return EspecialidadOut.desde(
        caso.ejecutar(datos.codigo, datos.nombre, datos.descripcion, datos.activa)
    )


@router.put(
    "/especialidades/{especialidad_id}",
    response_model=EspecialidadOut,
    summary="Actualizar una especialidad",
    dependencies=[SoloAdmin],
)
def actualizar_especialidad(
    especialidad_id: int, datos: EspecialidadActualizarIn, caso: ActualizarEspecialidadDep
) -> EspecialidadOut:
    cmd = ActualizarEspecialidadCmd(**datos.model_dump(exclude_unset=True))
    return EspecialidadOut.desde(caso.ejecutar(especialidad_id, cmd))


@router.delete(
    "/especialidades/{especialidad_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una especialidad",
    dependencies=[SoloAdmin],
)
def eliminar_especialidad(especialidad_id: int, caso: EliminarEspecialidadDep) -> None:
    caso.ejecutar(especialidad_id)
