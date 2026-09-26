"""Traducción de errores de dominio a respuestas HTTP.

Es la única parte del sistema que conoce a la vez el dominio y los códigos de
estado; así los casos de uso nunca importan FastAPI.
"""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from ...domain.errors import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    DemasiadosIntentosError,
    DomainError,
    NotFoundError,
    ServicioNoDisponibleError,
    ValidationError,
)

# Starlette renombró la constante del 422 entre versiones; usamos el número.
HTTP_422 = 422

CODIGOS = {
    ValidationError: HTTP_422,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    BusinessRuleError: status.HTTP_409_CONFLICT,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    DemasiadosIntentosError: status.HTTP_429_TOO_MANY_REQUESTS,
    ServicioNoDisponibleError: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def _respuesta(exc: DomainError, codigo: int) -> JSONResponse:
    cuerpo = {"detail": exc.mensaje, "error": type(exc).__name__}
    campo = getattr(exc, "campo", None)
    if campo:
        cuerpo["campo"] = campo
    cabeceras = {"WWW-Authenticate": "Bearer"} if codigo == status.HTTP_401_UNAUTHORIZED else None
    if isinstance(exc, DemasiadosIntentosError):
        cabeceras = {"Retry-After": str(exc.reintentar_en_segundos)}
    return JSONResponse(status_code=codigo, content=cuerpo, headers=cabeceras)


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error(request: Request, exc: DomainError):  # noqa: ARG001
        for tipo, codigo in CODIGOS.items():
            if isinstance(exc, tipo):
                return _respuesta(exc, codigo)
        return _respuesta(exc, status.HTTP_400_BAD_REQUEST)
