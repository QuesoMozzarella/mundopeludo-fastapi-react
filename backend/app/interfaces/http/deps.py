"""Composition root del adaptador HTTP.

Aquí —y sólo aquí— se decide qué implementación concreta recibe cada puerto.
Cambiar SQLite por otra tecnología significa tocar este archivo y los
repositorios, nada más.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Annotated, Iterator

from fastapi import Depends, Header, Request

from ...application.use_cases.autenticacion import ObtenerUsuarioDesdeToken
from ...config import Config, config as config_global
from ...domain.errors import AuthenticationError, AuthorizationError
from ...domain.model.usuario import Usuario
from ...domain.ports.services import Clock, GeneradorCodigos, PasswordHasher, TokenService
from ...infrastructure.db.connection import Database
from ...infrastructure.repositories.citas import (
    SqliteCitaRepository,
    SqliteDisponibilidadRepository,
    SqliteEstadoCitaRepository,
    SqliteHistorialMedicoRepository,
    SqliteServicioRepository,
)
from ...infrastructure.repositories.inventario import (
    SqliteCarritoRepository,
    SqliteImagenProductoRepository,
    SqlitePedidoRepository,
    SqliteProductoRepository,
)
from ...infrastructure.repositories.mascotas import (
    SqliteEspecieRepository,
    SqliteMascotaRepository,
    SqliteSolicitudAdopcionRepository,
)
from ...infrastructure.repositories.sistema import (
    SqliteActividadSistemaRepository,
    SqliteCodigoRecuperacionRepository,
)
from ...infrastructure.repositories.usuarios import (
    SqliteEspecialidadRepository,
    SqlitePerfilClienteRepository,
    SqlitePerfilVeterinarioRepository,
    SqliteUsuarioRepository,
)
from ...infrastructure.security.adapters import (
    GeneradorCodigosSeguro,
    JwtTokenService,
    Pbkdf2PasswordHasher,
    RelojSistema,
)


@dataclass
class Servicios:
    """Adaptadores sin estado: se construyen una vez por proceso."""

    hasher: PasswordHasher
    tokens: TokenService
    reloj: Clock
    generador: GeneradorCodigos


@dataclass
class Repositorios:
    """Todos los repositorios de una petición, sobre la misma conexión."""

    usuarios: SqliteUsuarioRepository
    perfiles_cliente: SqlitePerfilClienteRepository
    perfiles_veterinario: SqlitePerfilVeterinarioRepository
    especialidades: SqliteEspecialidadRepository
    especies: SqliteEspecieRepository
    mascotas: SqliteMascotaRepository
    solicitudes: SqliteSolicitudAdopcionRepository
    estados_cita: SqliteEstadoCitaRepository
    servicios: SqliteServicioRepository
    disponibilidades: SqliteDisponibilidadRepository
    citas: SqliteCitaRepository
    historiales: SqliteHistorialMedicoRepository
    productos: SqliteProductoRepository
    imagenes: SqliteImagenProductoRepository
    carritos: SqliteCarritoRepository
    pedidos: SqlitePedidoRepository
    actividades: SqliteActividadSistemaRepository
    codigos: SqliteCodigoRecuperacionRepository


class Contenedor:
    """Guarda la base de datos y los servicios compartidos de la aplicación."""

    def __init__(self, configuracion: Config | None = None):
        self.config = configuracion or config_global
        self.db = Database(self.config.ruta_bd)
        self.servicios = Servicios(
            hasher=Pbkdf2PasswordHasher(),
            tokens=JwtTokenService(self.config.secreto_jwt, self.config.minutos_token),
            reloj=RelojSistema(),
            generador=GeneradorCodigosSeguro(),
        )

    def preparar(self) -> None:
        self.db.crear_esquema()

    def repositorios(self, conexion: sqlite3.Connection) -> Repositorios:
        return Repositorios(
            usuarios=SqliteUsuarioRepository(conexion),
            perfiles_cliente=SqlitePerfilClienteRepository(conexion),
            perfiles_veterinario=SqlitePerfilVeterinarioRepository(conexion),
            especialidades=SqliteEspecialidadRepository(conexion),
            especies=SqliteEspecieRepository(conexion),
            mascotas=SqliteMascotaRepository(conexion),
            solicitudes=SqliteSolicitudAdopcionRepository(conexion),
            estados_cita=SqliteEstadoCitaRepository(conexion),
            servicios=SqliteServicioRepository(conexion),
            disponibilidades=SqliteDisponibilidadRepository(conexion),
            citas=SqliteCitaRepository(conexion),
            historiales=SqliteHistorialMedicoRepository(conexion),
            productos=SqliteProductoRepository(conexion),
            imagenes=SqliteImagenProductoRepository(conexion),
            carritos=SqliteCarritoRepository(conexion),
            pedidos=SqlitePedidoRepository(conexion),
            actividades=SqliteActividadSistemaRepository(conexion),
            codigos=SqliteCodigoRecuperacionRepository(conexion),
        )


def instalar_contenedor(app, contenedor: Contenedor) -> None:
    """Guarda el contenedor en la app: cada instancia tiene el suyo."""
    app.state.contenedor = contenedor


def obtener_contenedor(request: Request) -> Contenedor:
    return request.app.state.contenedor


def obtener_config(request: Request) -> Config:
    return obtener_contenedor(request).config


def obtener_servicios(request: Request) -> Servicios:
    return obtener_contenedor(request).servicios


def obtener_repos(request: Request) -> Iterator[Repositorios]:
    """Una conexión por petición: commit al terminar bien, rollback si falla."""
    contenedor = obtener_contenedor(request)
    with contenedor.db.unidad_de_trabajo() as conexion:
        yield contenedor.repositorios(conexion)


ReposDep = Annotated[Repositorios, Depends(obtener_repos)]
ServiciosDep = Annotated[Servicios, Depends(obtener_servicios)]
ConfigDep = Annotated[Config, Depends(obtener_config)]


def usuario_opcional(
    repos: ReposDep,
    servicios: ServiciosDep,
    authorization: Annotated[str | None, Header()] = None,
) -> Usuario | None:
    """Resuelve el usuario del `Authorization: Bearer <token>`, si viene."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        return ObtenerUsuarioDesdeToken(repos.usuarios, servicios.tokens).ejecutar(token)
    except AuthenticationError:
        return None


UsuarioOpcionalDep = Annotated[Usuario | None, Depends(usuario_opcional)]


def usuario_actual(usuario: UsuarioOpcionalDep) -> Usuario:
    if usuario is None:
        raise AuthenticationError("Se requiere iniciar sesión")
    return usuario


UsuarioDep = Annotated[Usuario, Depends(usuario_actual)]


def exigir_roles(*roles: str):
    """Dependencia de autorización por rol.

    Si `MP_REQUIRE_AUTH=0` (valor por defecto en desarrollo) no bloquea: deja
    pasar la petición aunque no venga token, para no romper al cliente actual.
    """

    def verificar(usuario: UsuarioOpcionalDep, configuracion: ConfigDep) -> Usuario | None:
        if not configuracion.exigir_auth:
            return usuario
        if usuario is None:
            raise AuthenticationError("Se requiere iniciar sesión")
        if roles and usuario.tipo.value not in roles:
            raise AuthorizationError(
                "Tu rol no tiene permiso para esta operación (requiere: " + ", ".join(roles) + ")"
            )
        return usuario

    return verificar


SoloPersonal = Depends(exigir_roles("administrador", "veterinario"))
SoloAdmin = Depends(exigir_roles("administrador"))
Autenticado = Depends(exigir_roles())
