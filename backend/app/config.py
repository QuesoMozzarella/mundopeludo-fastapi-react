"""Configuración por variables de entorno (el equivalente a `settings.py`)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _bool(nombre: str, por_defecto: bool) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


@dataclass
class Config:
    ruta_bd: str = field(default_factory=lambda: os.getenv("MP_DB_PATH", str(RAIZ / "data" / "mundopeludo.db")))
    secreto_jwt: str = field(default_factory=lambda: os.getenv("MP_SECRET_KEY", "mundopeludo-dev-secret-cambiar-en-produccion"))
    minutos_token: int = field(default_factory=lambda: int(os.getenv("MP_TOKEN_MINUTES", "720")))
    origenes_cors: list[str] = field(default_factory=lambda: [o for o in os.getenv("MP_CORS_ORIGINS", "*").split(",") if o])
    # Con `MP_REQUIRE_AUTH=1` los endpoints de escritura exigen token y rol.
    # Por defecto queda en 0 para no romper al cliente SPA existente, que aún
    # no envía cabecera Authorization.
    exigir_auth: bool = field(default_factory=lambda: _bool("MP_REQUIRE_AUTH", False))
    entorno: str = field(default_factory=lambda: os.getenv("MP_ENV", "desarrollo"))

    @property
    def es_produccion(self) -> bool:
        return self.entorno.lower().startswith("prod")


config = Config()
