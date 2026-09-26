"""Errores de dominio.

El núcleo no conoce HTTP: lanza estas excepciones y el adaptador primario
(FastAPI) las traduce a códigos de estado en `interfaces/http/errors.py`.
"""


class DomainError(Exception):
    """Raíz de todos los errores del dominio.

    `conservar_cambios=True` indica a la unidad de trabajo que confirme lo
    escrito antes del error en lugar de deshacerlo. Sirve para registrar un
    intento fallido (p. ej. un código de recuperación erróneo) aunque la
    operación termine rechazada.
    """

    conservar_cambios: bool = False

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class ValidationError(DomainError):
    """Una invariante de una entidad no se cumple."""

    def __init__(self, mensaje: str, campo: str | None = None):
        super().__init__(mensaje)
        self.campo = campo


class NotFoundError(DomainError):
    """No existe la entidad solicitada."""

    def __init__(self, entidad: str, identificador: object = None):
        detalle = f"{entidad} no encontrado"
        if identificador is not None:
            detalle = f"{entidad} con id {identificador!r} no encontrado"
        super().__init__(detalle)
        self.entidad = entidad
        self.identificador = identificador


class ConflictError(DomainError):
    """Violación de unicidad o estado incompatible con la operación."""


class BusinessRuleError(DomainError):
    """Regla de negocio incumplida (stock insuficiente, horario ocupado, ...)."""


class AuthenticationError(DomainError):
    """Credenciales inválidas o token expirado."""


class IntentoFallidoError(AuthenticationError):
    """Credencial incorrecta cuyo intento debe quedar registrado."""

    conservar_cambios = True


class AuthorizationError(DomainError):
    """El actor no tiene permisos para la operación."""
