"""Rutas de autenticación y recuperación de contraseña."""
from __future__ import annotations

from fastapi import APIRouter, status

from ....application.use_cases.autenticacion import (
    AutenticarUsuario,
    CambiarPassword,
    RegistrarUsuario,
    RestablecerPassword,
    SolicitarCodigoRecuperacion,
)
from ....application.use_cases.usuarios import ConsultarUsuarios
from ....config import Config
from ....domain.value_objects import TipoUsuario
from ..deps import AccesoDep, ConfigDep, ReposDep, ServiciosDep, UsuarioDep
from ..schemas.usuarios import (
    CambioPasswordIn,
    LoginIn,
    RecuperacionIn,
    RegistroIn,
    RestablecerIn,
    SesionOut,
    UsuarioOut,
)

router = APIRouter(prefix="/api/auth", tags=["autenticación"])


def _vista(repos: ReposDep, usuario_id: int) -> UsuarioOut:
    consulta = ConsultarUsuarios(
        repos.usuarios, repos.perfiles_cliente, repos.perfiles_veterinario, repos.especialidades
    )
    return UsuarioOut.desde(consulta.obtener(usuario_id))


@router.post("/login", response_model=SesionOut, summary="Iniciar sesión")
def login(datos: LoginIn, repos: ReposDep, servicios: ServiciosDep) -> SesionOut:
    caso = AutenticarUsuario(
        repos.usuarios, servicios.hasher, servicios.tokens, servicios.reloj, repos.actividades
    )
    sesion = caso.ejecutar(datos.email, datos.password)
    return SesionOut(
        access_token=sesion.token,
        expira_en_minutos=sesion.expira_en_minutos,
        usuario=_vista(repos, sesion.usuario.id),
    )


@router.post(
    "/register",
    response_model=SesionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una cuenta nueva",
)
def registrar(
    datos: RegistroIn, repos: ReposDep, servicios: ServiciosDep, acceso: AccesoDep
) -> SesionOut:
    # El registro público sólo da de alta clientes; las cuentas de personal
    # (veterinario, administrador) las crea un administrador.
    tipo = TipoUsuario.desde(datos.tipo, campo="tipo", por_defecto=TipoUsuario.CLIENTE)
    if tipo is not TipoUsuario.CLIENTE:
        acceso.solo_administrador()
    caso = RegistrarUsuario(
        repos.usuarios,
        repos.perfiles_cliente,
        repos.perfiles_veterinario,
        servicios.hasher,
        servicios.reloj,
        repos.actividades,
    )
    usuario = caso.ejecutar(
        email=datos.email,
        password=datos.password,
        nombre=datos.nombre,
        apellidos=datos.apellidos,
        telefono=datos.telefono,
        direccion=datos.direccion,
        tipo=tipo,
        documento=datos.documento,
        especialidades_ids=datos.especialidades_ids,
    )
    token = servicios.tokens.emitir(usuario.id, {"email": usuario.email, "tipo": usuario.tipo.value})
    return SesionOut(
        access_token=token,
        expira_en_minutos=servicios.tokens.minutos_vigencia,
        usuario=_vista(repos, usuario.id),
    )


@router.get("/me", response_model=UsuarioOut, summary="Datos de la sesión activa")
def yo(usuario: UsuarioDep, repos: ReposDep) -> UsuarioOut:
    return _vista(repos, usuario.id)


@router.post("/password/cambiar", response_model=UsuarioOut, summary="Cambiar la contraseña")
def cambiar_password(
    datos: CambioPasswordIn, usuario: UsuarioDep, repos: ReposDep, servicios: ServiciosDep
) -> UsuarioOut:
    CambiarPassword(repos.usuarios, servicios.hasher).ejecutar(
        usuario.id, datos.password_actual, datos.password_nueva
    )
    return _vista(repos, usuario.id)


@router.post("/password/recuperar", summary="Solicitar un código de recuperación")
def recuperar(
    datos: RecuperacionIn, repos: ReposDep, servicios: ServiciosDep, configuracion: ConfigDep
) -> dict:
    caso = SolicitarCodigoRecuperacion(
        repos.usuarios, repos.codigos, servicios.generador, servicios.reloj
    )
    codigo = caso.ejecutar(datos.email)
    respuesta = {
        "detail": "Si el correo está registrado, recibirás un código de 6 dígitos",
    }
    # En desarrollo devolvemos el código: no hay servicio de email configurado.
    if codigo and not _es_produccion(configuracion):
        respuesta["codigo_debug"] = codigo.codigo
        respuesta["expira"] = codigo.fecha_expiracion.isoformat()
    return respuesta


@router.post("/password/restablecer", response_model=UsuarioOut, summary="Restablecer con código")
def restablecer(datos: RestablecerIn, repos: ReposDep, servicios: ServiciosDep) -> UsuarioOut:
    caso = RestablecerPassword(repos.usuarios, repos.codigos, servicios.hasher, servicios.reloj)
    usuario = caso.ejecutar(datos.email, datos.codigo, datos.password_nueva)
    return _vista(repos, usuario.id)


def _es_produccion(configuracion: Config) -> bool:
    return configuracion.es_produccion
