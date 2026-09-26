"""Casos de uso de autenticación.

Sustituyen a `usuarios/api_auth.py`, `backends.py` y al flujo de
`CodigoRecuperacion` del Django original.
"""
from __future__ import annotations

from dataclasses import dataclass

from ...domain.errors import (
    AuthenticationError,
    ConflictError,
    IntentoFallidoError,
    NotFoundError,
    ValidationError,
)
from ...domain.model.sistema import ActividadSistema, CodigoRecuperacion
from ...domain.model.usuario import PerfilCliente, PerfilVeterinario, Usuario
from ...domain.ports.repositories import (
    ActividadSistemaRepository,
    CodigoRecuperacionRepository,
    PerfilClienteRepository,
    PerfilVeterinarioRepository,
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

LONGITUD_MINIMA_PASSWORD = 8


@dataclass
class SesionIniciada:
    usuario: Usuario
    token: str
    expira_en_minutos: int


class RegistrarUsuario:
    """Alta de un usuario + su perfil según el tipo (cliente o veterinario)."""

    def __init__(
        self,
        usuarios: UsuarioRepository,
        perfiles_cliente: PerfilClienteRepository,
        perfiles_veterinario: PerfilVeterinarioRepository,
        hasher: PasswordHasher,
        reloj: Clock,
        actividades: ActividadSistemaRepository | None = None,
    ):
        self.usuarios = usuarios
        self.perfiles_cliente = perfiles_cliente
        self.perfiles_veterinario = perfiles_veterinario
        self.hasher = hasher
        self.reloj = reloj
        self.actividades = actividades

    def ejecutar(
        self,
        email: str,
        password: str,
        nombre: str,
        apellidos: str,
        telefono: str | None = None,
        direccion: str | None = None,
        tipo: TipoUsuario | str = TipoUsuario.CLIENTE,
        documento: str | None = None,
        especialidades_ids: list[int] | None = None,
    ) -> Usuario:
        validar_password(password)
        if self.usuarios.obtener_por_email(email):
            raise ConflictError("Ya existe una cuenta registrada con ese correo")

        usuario = Usuario(
            email=email,
            nombre=nombre,
            apellidos=apellidos,
            telefono=telefono,
            direccion=direccion,
            tipo=tipo,
            password_hash=self.hasher.hash(password),
            date_joined=self.reloj.ahora(),
        )
        usuario = self.usuarios.crear(usuario)

        if usuario.es_cliente:
            self.perfiles_cliente.guardar(
                PerfilCliente(
                    usuario_id=usuario.id,
                    documento=documento,
                    fecha_actualizacion=self.reloj.ahora(),
                )
            )
        elif usuario.es_veterinario:
            self.perfiles_veterinario.guardar(
                PerfilVeterinario(
                    usuario_id=usuario.id,
                    documento=documento,
                    fecha_contratacion=self.reloj.hoy(),
                    especialidades_ids=especialidades_ids or [],
                )
            )

        if self.actividades:
            self.actividades.registrar(
                ActividadSistema(
                    usuario=usuario.email,
                    tipo="registro",
                    descripcion=f"Nuevo usuario {usuario.tipo.value} registrado",
                    fecha=self.reloj.ahora(),
                )
            )
        return usuario


class AutenticarUsuario:
    """Login por email + contraseña; emite el JWT de sesión."""

    def __init__(
        self,
        usuarios: UsuarioRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        reloj: Clock,
        actividades: ActividadSistemaRepository | None = None,
    ):
        self.usuarios = usuarios
        self.hasher = hasher
        self.tokens = tokens
        self.reloj = reloj
        self.actividades = actividades

    def ejecutar(self, email: str, password: str) -> SesionIniciada:
        usuario = self.usuarios.obtener_por_email(email)
        if usuario is None:
            # Mismo mensaje y mismo coste que una contraseña errónea: ni el
            # texto ni el tiempo de respuesta revelan si el correo existe.
            self.hasher.verificar(password, self._hash_senuelo())
            raise AuthenticationError("Correo o contraseña incorrectos")
        if not self.hasher.verificar(password, usuario.password_hash):
            raise AuthenticationError("Correo o contraseña incorrectos")
        if not usuario.is_active:
            raise AuthenticationError("La cuenta está desactivada")

        usuario.registrar_acceso(self.reloj.ahora())
        self.usuarios.actualizar(usuario)

        token = self.tokens.emitir(
            usuario.id, {"email": usuario.email, "tipo": usuario.tipo.value}
        )
        if self.actividades:
            self.actividades.registrar(
                ActividadSistema(
                    usuario=usuario.email,
                    tipo="login",
                    descripcion="Inicio de sesión correcto",
                    fecha=self.reloj.ahora(),
                )
            )
        return SesionIniciada(
            usuario=usuario, token=token, expira_en_minutos=self.tokens.minutos_vigencia
        )


    _senuelo: str | None = None

    def _hash_senuelo(self) -> str:
        if AutenticarUsuario._senuelo is None:
            AutenticarUsuario._senuelo = self.hasher.hash("senuelo-sin-cuenta")
        return AutenticarUsuario._senuelo


class ObtenerUsuarioDesdeToken:
    def __init__(self, usuarios: UsuarioRepository, tokens: TokenService):
        self.usuarios = usuarios
        self.tokens = tokens

    def ejecutar(self, token: str) -> Usuario:
        payload = self.tokens.decodificar(token)
        try:
            usuario_id = int(payload.get("sub"))
        except (TypeError, ValueError):
            raise AuthenticationError("Token sin sujeto válido") from None
        usuario = self.usuarios.obtener(usuario_id)
        if usuario is None or not usuario.is_active:
            raise AuthenticationError("La sesión ya no es válida")
        return usuario


class SolicitarCodigoRecuperacion:
    """Genera el código de 6 dígitos del modelo `CodigoRecuperacion` y lo envía.

    Si el aviso falla, la excepción deshace la transacción: no queda un código
    activo que el usuario nunca recibió.
    """

    def __init__(
        self,
        usuarios: UsuarioRepository,
        codigos: CodigoRecuperacionRepository,
        generador: GeneradorCodigos,
        reloj: Clock,
        notificaciones: Notificaciones,
    ):
        self.usuarios = usuarios
        self.codigos = codigos
        self.generador = generador
        self.reloj = reloj
        self.notificaciones = notificaciones

    def ejecutar(self, email: str) -> CodigoRecuperacion | None:
        usuario = self.usuarios.obtener_por_email(email)
        if usuario is None:
            # Silencio deliberado: no confirmamos qué correos existen.
            return None
        self.codigos.desactivar_todos(usuario.id)
        codigo = CodigoRecuperacion(
            usuario_id=usuario.id,
            codigo=self.generador.numerico(6),
            fecha_creacion=self.reloj.ahora(),
        )
        codigo = self.codigos.crear(codigo)
        self.notificaciones.codigo_recuperacion(usuario, codigo)
        return codigo


class RestablecerPassword:
    def __init__(
        self,
        usuarios: UsuarioRepository,
        codigos: CodigoRecuperacionRepository,
        hasher: PasswordHasher,
        reloj: Clock,
    ):
        self.usuarios = usuarios
        self.codigos = codigos
        self.hasher = hasher
        self.reloj = reloj

    def ejecutar(self, email: str, codigo: str, password_nueva: str) -> Usuario:
        validar_password(password_nueva)
        usuario = self.usuarios.obtener_por_email(email)
        if usuario is None:
            raise AuthenticationError("Código de recuperación inválido")

        # Se busca el código activo del usuario y se compara aquí: si se
        # buscara por el valor exacto, un código erróneo nunca sumaría un
        # intento y el límite de MAX_INTENTOS_CODIGO no frenaría la fuerza bruta.
        registro = self.codigos.obtener_activo(usuario.id)
        if registro is None:
            raise AuthenticationError("Código de recuperación inválido")
        if not registro.es_utilizable(self.reloj.ahora()):
            raise AuthenticationError("El código expiró o se agotaron los intentos")
        if not registro.coincide(codigo):
            registro.incrementar_intento()
            self.codigos.actualizar(registro)
            raise IntentoFallidoError("Código de recuperación inválido")

        registro.consumir()
        self.codigos.actualizar(registro)

        usuario.password_hash = self.hasher.hash(password_nueva)
        return self.usuarios.actualizar(usuario)


class CambiarPassword:
    def __init__(self, usuarios: UsuarioRepository, hasher: PasswordHasher):
        self.usuarios = usuarios
        self.hasher = hasher

    def ejecutar(self, usuario_id: int, password_actual: str, password_nueva: str) -> Usuario:
        usuario = self.usuarios.obtener(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario", usuario_id)
        if not self.hasher.verificar(password_actual, usuario.password_hash):
            raise AuthenticationError("La contraseña actual no es correcta")
        validar_password(password_nueva)
        usuario.password_hash = self.hasher.hash(password_nueva)
        return self.usuarios.actualizar(usuario)


def validar_password(password: str) -> None:
    """Política mínima, equivalente a los validadores de `settings.py`."""
    if not password or len(password) < LONGITUD_MINIMA_PASSWORD:
        raise ValidationError(
            f"La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres", "password"
        )
    if password.isdigit():
        raise ValidationError("La contraseña no puede ser sólo numérica", "password")
