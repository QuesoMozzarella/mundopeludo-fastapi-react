"""Configuración por variables de entorno (el equivalente a `settings.py`)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SECRETO_DESARROLLO = "mundopeludo-dev-secret-cambiar-en-produccion"


def _bool(nombre: str, por_defecto: bool) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


@dataclass
class Config:
    ruta_bd: str = field(default_factory=lambda: os.getenv("MP_DB_PATH", str(RAIZ / "data" / "mundopeludo.db")))
    secreto_jwt: str = field(default_factory=lambda: os.getenv("MP_SECRET_KEY", SECRETO_DESARROLLO))
    minutos_token: int = field(default_factory=lambda: int(os.getenv("MP_TOKEN_MINUTES", "720")))
    origenes_cors: list[str] = field(default_factory=lambda: [o for o in os.getenv("MP_CORS_ORIGINS", "*").split(",") if o])
    # La API está cerrada por defecto: token, rol y propiedad del recurso.
    # `MP_REQUIRE_AUTH=0` la abre por completo; sólo para desarrollo local.
    exigir_auth: bool = field(default_factory=lambda: _bool("MP_REQUIRE_AUTH", True))
    entorno: str = field(default_factory=lambda: os.getenv("MP_ENV", "desarrollo"))

    # Correo saliente (el EMAIL_* de settings.py). Sin host no se envía nada.
    correo_host: str = field(default_factory=lambda: os.getenv("MP_EMAIL_HOST", ""))
    correo_puerto: int = field(default_factory=lambda: int(os.getenv("MP_EMAIL_PORT", "587")))
    correo_tls: bool = field(default_factory=lambda: _bool("MP_EMAIL_USE_TLS", True))
    correo_usuario: str = field(default_factory=lambda: os.getenv("MP_EMAIL_USER", ""))
    correo_password: str = field(default_factory=lambda: os.getenv("MP_EMAIL_PASSWORD", ""))
    correo_remitente: str = field(default_factory=lambda: os.getenv("MP_EMAIL_FROM", ""))
    # Fuera de producción, todos los correos van a esta dirección en vez de al
    # destinatario real (los tutores de `seed.py` no existen).
    correo_redirigir_a: str = field(
        default_factory=lambda: os.getenv("MP_EMAIL_REDIRIGIR_A", "").strip()
    )

    @property
    def correo_configurado(self) -> bool:
        return bool(self.correo_host)

    @property
    def es_produccion(self) -> bool:
        return self.entorno.lower().startswith("prod")

    def validar(self) -> None:
        """Falla al arrancar antes que servir en producción con valores inseguros."""
        if self.es_produccion and self.secreto_jwt == SECRETO_DESARROLLO:
            # La clave de desarrollo está en el repositorio: con ella cualquiera
            # puede firmar un token de administrador.
            raise RuntimeError("MP_SECRET_KEY es obligatoria en producción")
        if self.es_produccion and self.correo_redirigir_a:
            # En producción los avisos tienen que llegar a cada tutor.
            raise RuntimeError("MP_EMAIL_REDIRIGIR_A sólo se admite fuera de producción")


config = Config()
