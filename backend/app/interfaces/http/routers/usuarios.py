"""Rutas de usuarios, perfiles y especialidades."""
from __future__ import annotations

from fastapi import APIRouter, Query, status

from ....application.use_cases.usuarios import (
    ActualizarUsuario,
    ConsultarUsuarios,
    DesactivarUsuario,
    GestionarEspecialidades,
    GestionarPerfilCliente,
    GestionarPerfilVeterinario,
)
from ....domain.value_objects import TipoUsuario
from ..deps import AccesoDep, ReposDep, ServiciosDep, SoloAdmin, SoloPersonal
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


def _consulta(repos: ReposDep) -> ConsultarUsuarios:
    return ConsultarUsuarios(
        repos.usuarios, repos.perfiles_cliente, repos.perfiles_veterinario, repos.especialidades
    )


@router.get(
    "/users",
    response_model=list[UsuarioOut],
    summary="Listar usuarios",
    dependencies=[SoloPersonal],
)
def listar_usuarios(
    repos: ReposDep,
    tipo: str | None = None,
    activos: bool | None = None,
    buscar: str | None = Query(default=None, description="Nombre, apellidos o correo"),
) -> list[UsuarioOut]:
    return [UsuarioOut.desde(v) for v in _consulta(repos).listar(tipo, activos, buscar)]


@router.get("/veterinarios", response_model=list[UsuarioOut], summary="Listar veterinarios")
def listar_veterinarios(repos: ReposDep) -> list[UsuarioOut]:
    return [UsuarioOut.desde(v) for v in _consulta(repos).listar(TipoUsuario.VETERINARIO, True)]


@router.get(
    "/clientes",
    response_model=list[UsuarioOut],
    summary="Listar clientes",
    dependencies=[SoloPersonal],
)
def listar_clientes(repos: ReposDep) -> list[UsuarioOut]:
    return [UsuarioOut.desde(v) for v in _consulta(repos).listar(TipoUsuario.CLIENTE, True)]


@router.get("/users/{usuario_id}", response_model=UsuarioOut, summary="Ver un usuario")
def obtener_usuario(usuario_id: int, repos: ReposDep, acceso: AccesoDep) -> UsuarioOut:
    acceso.propietario(usuario_id)
    return UsuarioOut.desde(_consulta(repos).obtener(usuario_id))


@router.put("/users/{usuario_id}", response_model=UsuarioOut, summary="Actualizar un usuario")
def actualizar_usuario(
    usuario_id: int,
    datos: UsuarioActualizarIn,
    repos: ReposDep,
    servicios: ServiciosDep,
    acceso: AccesoDep,
) -> UsuarioOut:
    acceso.propietario(usuario_id)
    cambios = datos.model_dump(exclude_unset=True)
    if {"tipo", "is_active"} & cambios.keys():
        # Cambiar el rol o dar de baja una cuenta no es autoservicio.
        acceso.solo_administrador()
    caso = ActualizarUsuario(
        repos.usuarios, repos.perfiles_cliente, repos.perfiles_veterinario, servicios.reloj
    )
    caso.ejecutar(usuario_id, cambios)
    return UsuarioOut.desde(_consulta(repos).obtener(usuario_id))


@router.delete(
    "/users/{usuario_id}",
    response_model=UsuarioOut,
    summary="Desactivar un usuario (baja lógica)",
    dependencies=[SoloAdmin],
)
def desactivar_usuario(usuario_id: int, repos: ReposDep) -> UsuarioOut:
    DesactivarUsuario(repos.usuarios).ejecutar(usuario_id)
    return UsuarioOut.desde(_consulta(repos).obtener(usuario_id))


@router.put(
    "/users/{usuario_id}/perfil-cliente",
    response_model=PerfilClienteOut,
    summary="Actualizar el perfil de cliente",
)
def guardar_perfil_cliente(
    usuario_id: int,
    datos: PerfilClienteIn,
    repos: ReposDep,
    servicios: ServiciosDep,
    acceso: AccesoDep,
) -> PerfilClienteOut:
    acceso.propietario(usuario_id)
    caso = GestionarPerfilCliente(repos.usuarios, repos.perfiles_cliente, servicios.reloj)
    return PerfilClienteOut.desde(caso.guardar(usuario_id, datos.documento))


@router.put(
    "/users/{usuario_id}/perfil-veterinario",
    response_model=PerfilVeterinarioOut,
    summary="Actualizar el perfil de veterinario",
    dependencies=[SoloPersonal],
)
def guardar_perfil_veterinario(
    usuario_id: int,
    datos: PerfilVeterinarioIn,
    repos: ReposDep,
    servicios: ServiciosDep,
    acceso: AccesoDep,
) -> PerfilVeterinarioOut:
    # Un veterinario edita su propio perfil; el de otro, sólo un administrador.
    acceso.propietario(usuario_id, personal=False)
    caso = GestionarPerfilVeterinario(
        repos.usuarios, repos.perfiles_veterinario, repos.especialidades, servicios.reloj
    )
    perfil = caso.guardar(
        usuario_id,
        documento=datos.documento,
        activo=datos.activo,
        especialidades_ids=datos.especialidades_ids,
        fecha_contratacion=datos.fecha_contratacion,
    )
    return PerfilVeterinarioOut.desde(perfil)


# --------------------------- especialidades ---------------------------
@router.get("/especialidades", response_model=list[EspecialidadOut], summary="Listar especialidades")
def listar_especialidades(repos: ReposDep, solo_activas: bool = False) -> list[EspecialidadOut]:
    caso = GestionarEspecialidades(repos.especialidades)
    return [EspecialidadOut.desde(e) for e in caso.listar(solo_activas)]


@router.post(
    "/especialidades",
    response_model=EspecialidadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una especialidad",
    dependencies=[SoloAdmin],
)
def crear_especialidad(datos: EspecialidadIn, repos: ReposDep) -> EspecialidadOut:
    caso = GestionarEspecialidades(repos.especialidades)
    return EspecialidadOut.desde(
        caso.crear(datos.codigo, datos.nombre, datos.descripcion, datos.activa)
    )


@router.put(
    "/especialidades/{especialidad_id}",
    response_model=EspecialidadOut,
    summary="Actualizar una especialidad",
    dependencies=[SoloAdmin],
)
def actualizar_especialidad(
    especialidad_id: int, datos: EspecialidadActualizarIn, repos: ReposDep
) -> EspecialidadOut:
    caso = GestionarEspecialidades(repos.especialidades)
    return EspecialidadOut.desde(
        caso.actualizar(especialidad_id, datos.model_dump(exclude_unset=True))
    )


@router.delete(
    "/especialidades/{especialidad_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una especialidad",
    dependencies=[SoloAdmin],
)
def eliminar_especialidad(especialidad_id: int, repos: ReposDep) -> None:
    GestionarEspecialidades(repos.especialidades).eliminar(especialidad_id)
