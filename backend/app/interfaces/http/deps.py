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
from ...domain.ports.repositories import (
    ActividadSistemaRepository,
    CarritoRepository,
    CitaRepository,
    CodigoRecuperacionRepository,
    DisponibilidadRepository,
    EspecialidadRepository,
    EspecieRepository,
    EstadoCitaRepository,
    HistorialMedicoRepository,
    ImagenProductoRepository,
    MascotaRepository,
    PedidoRepository,
    PerfilClienteRepository,
    PerfilVeterinarioRepository,
    ProductoRepository,
    ServicioRepository,
    SolicitudAdopcionRepository,
    UsuarioRepository,
)
from ...domain.ports.services import (
    Clock,
    GeneradorCodigos,
    Notificaciones,
    PasswordHasher,
    TokenService,
)
from ...domain.value_objects import TipoUsuario
from ...infrastructure.db.connection import Database
from ...infrastructure.notificaciones.adaptadores import (
    CorreoSmtp,
    NotificacionesEnRegistro,
)
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
    notificaciones: Notificaciones


@dataclass
class Repositorios:
    """Todos los repositorios de una petición, sobre la misma conexión.

    Los campos se declaran con los puertos del dominio, no con las clases
    SQLite: quien consume `Repositorios` sólo conoce los contratos.
    """

    usuarios: UsuarioRepository
    perfiles_cliente: PerfilClienteRepository
    perfiles_veterinario: PerfilVeterinarioRepository
    especialidades: EspecialidadRepository
    especies: EspecieRepository
    mascotas: MascotaRepository
    solicitudes: SolicitudAdopcionRepository
    estados_cita: EstadoCitaRepository
    servicios: ServicioRepository
    disponibilidades: DisponibilidadRepository
    citas: CitaRepository
    historiales: HistorialMedicoRepository
    productos: ProductoRepository
    imagenes: ImagenProductoRepository
    carritos: CarritoRepository
    pedidos: PedidoRepository
    actividades: ActividadSistemaRepository
    codigos: CodigoRecuperacionRepository


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
            notificaciones=self._notificaciones(),
        )

    def _notificaciones(self) -> Notificaciones:
        c = self.config
        if not c.correo_configurado:
            return NotificacionesEnRegistro()
        return CorreoSmtp(
            c.correo_host,
            c.correo_puerto,
            c.correo_usuario,
            c.correo_password,
            c.correo_remitente,
            usar_tls=c.correo_tls,
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


METODOS_DE_LECTURA = {"GET", "HEAD", "OPTIONS"}


def obtener_repos(request: Request) -> Iterator[Repositorios]:
    """Una conexión por petición: commit al terminar bien, rollback si falla."""
    contenedor = obtener_contenedor(request)
    escritura = request.method not in METODOS_DE_LECTURA
    with contenedor.db.unidad_de_trabajo(escritura) as conexion:
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


def exigir_roles(*roles: TipoUsuario):
    """Dependencia de autorización por rol.

    Si `MP_REQUIRE_AUTH=0` (valor por defecto en desarrollo) no bloquea: deja
    pasar la petición aunque no venga token, para no romper al cliente actual.
    """

    def verificar(usuario: UsuarioOpcionalDep, configuracion: ConfigDep) -> Usuario | None:
        if not configuracion.exigir_auth:
            return usuario
        if usuario is None:
            raise AuthenticationError("Se requiere iniciar sesión")
        if roles and usuario.tipo not in roles:
            requeridos = ", ".join(rol.value for rol in roles)
            raise AuthorizationError(
                f"Tu rol no tiene permiso para esta operación (requiere: {requeridos})"
            )
        return usuario

    return verificar


PERSONAL = (TipoUsuario.ADMINISTRADOR, TipoUsuario.VETERINARIO)

SoloPersonal = Depends(exigir_roles(*PERSONAL))
SoloAdmin = Depends(exigir_roles(TipoUsuario.ADMINISTRADOR))
Autenticado = Depends(exigir_roles())


@dataclass
class Acceso:
    """Autorización a nivel de recurso: quién pide y de quién es lo que pide.

    `exigir_roles` sólo mira el rol; esto además comprueba la propiedad
    (el carrito, las citas o las mascotas de *otro* cliente). Igual que
    `exigir_roles`, no restringe nada cuando `MP_REQUIRE_AUTH=0`.
    """

    usuario: Usuario | None
    exigir: bool

    @property
    def es_personal(self) -> bool:
        return self.usuario is not None and self.usuario.tipo in PERSONAL

    def propietario(self, dueno_id: int | None, *, personal: bool = True) -> None:
        """Deja pasar al dueño del recurso, al administrador y, si `personal`, al veterinario."""
        if not self.exigir:
            return
        usuario = self._sesion()
        if usuario.es_administrador or (personal and self.es_personal):
            return
        if dueno_id is None or usuario.id != dueno_id:
            raise AuthorizationError("No tienes permiso sobre datos de otro usuario")

    def solo_personal(self) -> None:
        if self.exigir:
            self._sesion()
            if not self.es_personal:
                raise AuthorizationError("Operación reservada al personal de la clínica")

    def solo_administrador(self) -> None:
        if self.exigir and not self._sesion().es_administrador:
            raise AuthorizationError("Operación reservada a administradores")

    def filtro_propio(self, dueno_id: int | None) -> int | None:
        """Para listados: el personal consulta lo que pida; un cliente, sólo lo suyo."""
        if not self.exigir or self.es_personal:
            return dueno_id
        usuario = self._sesion()
        if dueno_id is not None and dueno_id != usuario.id:
            raise AuthorizationError("No tienes permiso sobre datos de otro usuario")
        return usuario.id

    def _sesion(self) -> Usuario:
        if self.usuario is None:
            raise AuthenticationError("Se requiere iniciar sesión")
        return self.usuario


def obtener_acceso(usuario: UsuarioOpcionalDep, configuracion: ConfigDep) -> Acceso:
    return Acceso(usuario=usuario, exigir=configuracion.exigir_auth)


AccesoDep = Annotated[Acceso, Depends(obtener_acceso)]
