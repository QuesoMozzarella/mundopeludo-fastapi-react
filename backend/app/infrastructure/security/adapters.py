"""Adaptadores de los puertos técnicos, sólo con la librería estándar.

No se añaden dependencias externas: el hash es compatible con el formato
`pbkdf2_sha256$...` de Django, y el JWT HS256 se firma con `hmac`.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from ...domain.errors import AuthenticationError
from ...domain.ports.services import Clock, GeneradorCodigos, PasswordHasher, TokenService

ALGORITMO = "pbkdf2_sha256"
ITERACIONES = 320_000


class Pbkdf2PasswordHasher(PasswordHasher):
    """Hash `pbkdf2_sha256$iteraciones$salt$hash`, idéntico al de Django.

    Gracias a ese formato, los hashes exportados desde la base de Django
    siguen validando aquí sin necesidad de que el usuario cambie su clave.
    """

    def __init__(self, iteraciones: int = ITERACIONES):
        self.iteraciones = iteraciones

    def hash(self, password_plano: str) -> str:
        if not password_plano:
            raise AuthenticationError("La contraseña no puede estar vacía")
        salt = secrets.token_hex(8)
        return self._codificar(password_plano, salt, self.iteraciones)

    def verificar(self, password_plano: str, hash_guardado: str) -> bool:
        if not password_plano or not hash_guardado:
            return False
        partes = hash_guardado.split("$")
        if len(partes) != 4 or partes[0] != ALGORITMO:
            return False
        _, iteraciones, salt, _ = partes
        try:
            candidato = self._codificar(password_plano, salt, int(iteraciones))
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(candidato, hash_guardado)

    def _codificar(self, password: str, salt: str, iteraciones: int) -> str:
        derivado = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iteraciones)
        return f"{ALGORITMO}${iteraciones}${salt}${base64.b64encode(derivado).decode('ascii')}"


def _b64url(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode("ascii")


def _de_b64url(texto: str) -> bytes:
    relleno = "=" * (-len(texto) % 4)
    return base64.urlsafe_b64decode(texto + relleno)


class JwtTokenService(TokenService):
    """JWT HS256 mínimo (header.payload.firma) implementado con `hmac`."""

    def __init__(self, secreto: str, minutos_vigencia: int = 60 * 12):
        self.secreto = secreto.encode("utf-8")
        self._minutos_vigencia = minutos_vigencia

    @property
    def minutos_vigencia(self) -> int:
        return self._minutos_vigencia

    def emitir(self, sujeto: int, datos: dict | None = None) -> str:
        ahora = datetime.now(timezone.utc)
        payload = {
            "sub": str(sujeto),
            "iat": int(ahora.timestamp()),
            "exp": int((ahora + timedelta(minutes=self.minutos_vigencia)).timestamp()),
            **(datos or {}),
        }
        cabecera = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
        cuerpo = _b64url(json.dumps(payload, separators=(",", ":")).encode())
        firma = self._firmar(f"{cabecera}.{cuerpo}")
        return f"{cabecera}.{cuerpo}.{firma}"

    def decodificar(self, token: str) -> dict:
        try:
            cabecera, cuerpo, firma = token.split(".")
        except ValueError:
            raise AuthenticationError("Token malformado") from None
        if not hmac.compare_digest(firma, self._firmar(f"{cabecera}.{cuerpo}")):
            raise AuthenticationError("Firma de token inválida")
        try:
            payload = json.loads(_de_b64url(cuerpo))
        except (ValueError, json.JSONDecodeError):
            raise AuthenticationError("Token malformado") from None
        if payload.get("exp", 0) < int(datetime.now(timezone.utc).timestamp()):
            raise AuthenticationError("El token ha expirado")
        return payload

    def _firmar(self, mensaje: str) -> str:
        return _b64url(hmac.new(self.secreto, mensaje.encode("ascii"), hashlib.sha256).digest())


class RelojSistema(Clock):
    def ahora(self) -> datetime:
        return datetime.now().replace(microsecond=0)


class GeneradorCodigosSeguro(GeneradorCodigos):
    def numerico(self, longitud: int = 6) -> str:
        return "".join(secrets.choice("0123456789") for _ in range(longitud))
