"""Rutas de autenticación y recuperación de contraseña."""
from __future__ import annotations

from fastapi import APIRouter, status

from ....application.use_cases.autenticacion import SesionIniciada
from ....domain.value_objects import TipoUsuario
from ..casos import (
    AutenticarUsuarioDep,
    CambiarPasswordDep,
    ConsultarUsuariosDep,
    RegistrarUsuarioDep,
    RestablecerPasswordDep,
    SolicitarCodigoRecuperacionDep,
)
from ..deps import AccesoDep, ConfigDep, UsuarioDep
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


def _sesion_out(sesion: SesionIniciada, usuarios: ConsultarUsuariosDep) -> SesionOut:
    return SesionOut(
        access_token=sesion.token,
        expira_en_minutos=sesion.expira_en_minutos,
        usuario=UsuarioOut.desde(usuarios.obtener(sesion.usuario.id)),
    )


@router.post("/login", response_model=SesionOut, summary="Iniciar sesión")
def login(
    datos: LoginIn, caso: AutenticarUsuarioDep, usuarios: ConsultarUsuariosDep
) -> SesionOut:
    return _sesion_out(caso.ejecutar(datos.email, datos.password), usuarios)


@router.post(
    "/register",
    response_model=SesionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una cuenta nueva",
)
def registrar(
    datos: RegistroIn,
    caso: RegistrarUsuarioDep,
    autenticacion: AutenticarUsuarioDep,
    usuarios: ConsultarUsuariosDep,
    acceso: AccesoDep,
) -> SesionOut:
    # El registro público sólo da de alta clientes; las cuentas de personal
    # (veterinario, administrador) las crea un administrador.
    tipo = TipoUsuario.desde(datos.tipo, campo="tipo", por_defecto=TipoUsuario.CLIENTE)
    if tipo is not TipoUsuario.CLIENTE:
        acceso.solo_administrador()
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
    return _sesion_out(autenticacion.sesion_para(usuario), usuarios)


@router.get("/me", response_model=UsuarioOut, summary="Datos de la sesión activa")
def yo(usuario: UsuarioDep, usuarios: ConsultarUsuariosDep) -> UsuarioOut:
    return UsuarioOut.desde(usuarios.obtener(usuario.id))


@router.post("/password/cambiar", response_model=UsuarioOut, summary="Cambiar la contraseña")
def cambiar_password(
    datos: CambioPasswordIn,
    usuario: UsuarioDep,
    caso: CambiarPasswordDep,
    usuarios: ConsultarUsuariosDep,
) -> UsuarioOut:
    caso.ejecutar(usuario.id, datos.password_actual, datos.password_nueva)
    return UsuarioOut.desde(usuarios.obtener(usuario.id))


@router.post("/password/recuperar", summary="Solicitar un código de recuperación")
def recuperar(
    datos: RecuperacionIn, caso: SolicitarCodigoRecuperacionDep, configuracion: ConfigDep
) -> dict:
    codigo = caso.ejecutar(datos.email)
    respuesta = {
        "detail": "Si el correo está registrado, recibirás un código de 6 dígitos",
    }
    # Sólo sin correo configurado y fuera de producción se devuelve el código:
    # con él en la respuesta, cualquiera podría restablecer cualquier cuenta.
    if codigo and not configuracion.correo_configurado and not configuracion.es_produccion:
        respuesta["codigo_debug"] = codigo.codigo
        respuesta["expira"] = codigo.fecha_expiracion.isoformat()
    return respuesta


@router.post("/password/restablecer", response_model=UsuarioOut, summary="Restablecer con código")
def restablecer(
    datos: RestablecerIn, caso: RestablecerPasswordDep, usuarios: ConsultarUsuariosDep
) -> UsuarioOut:
    usuario = caso.ejecutar(datos.email, datos.codigo, datos.password_nueva)
    return UsuarioOut.desde(usuarios.obtener(usuario.id))
