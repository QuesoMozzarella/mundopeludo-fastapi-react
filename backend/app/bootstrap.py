"""Arranque de la aplicación: monta el adaptador HTTP sobre el núcleo.

Es el único punto donde FastAPI, los casos de uso y los adaptadores se
encuentran; el dominio nunca importa nada de aquí.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Config, config as config_global
from .interfaces.http.deps import Contenedor, instalar_contenedor
from .interfaces.http.errors import registrar_manejadores
from .interfaces.http.routers import (
    adopciones,
    auth,
    carrito,
    citas,
    historiales,
    inventario,
    mascotas,
    sistema,
    usuarios,
)

log = logging.getLogger("mundopeludo")

DESCRIPCION = """
API de la Clínica Veterinaria **MundoPeludo**.

Migración del backend Django original a **FastAPI + sqlite3** siguiendo
**arquitectura hexagonal** (puertos y adaptadores):

* `domain/` — entidades, objetos de valor y puertos. Sin dependencias externas.
* `application/` — casos de uso que orquestan el dominio.
* `infrastructure/` — adaptadores de salida: SQLite, hash de contraseñas, JWT.
* `interfaces/http/` — adaptador de entrada: routers y esquemas de FastAPI.
"""


def create_app(configuracion: Config | None = None) -> FastAPI:
    configuracion = configuracion or config_global
    configuracion.validar()
    if not configuracion.exigir_auth:
        log.warning("MP_REQUIRE_AUTH=0: la API está ABIERTA, sin token ni permisos")
    if not configuracion.correo_configurado:
        log.warning("MP_EMAIL_HOST vacío: los códigos de recuperación no se envían por correo")
    contenedor = Contenedor(configuracion)
    contenedor.preparar()

    app = FastAPI(
        title="MundoPeludo API",
        description=DESCRIPCION,
        version=sistema.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    instalar_contenedor(app, contenedor)

    origenes = contenedor.config.origenes_cors or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origenes,
        # La sesión va en la cabecera Authorization, no en cookies. Con "*" y
        # credenciales, Starlette reflejaría cualquier origen como permitido.
        allow_credentials="*" not in origenes,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    registrar_manejadores(app)

    for router in (
        sistema.router,
        auth.router,
        usuarios.router,
        mascotas.router,
        adopciones.router,
        citas.router,
        historiales.router,
        inventario.router,
        carrito.router,
    ):
        app.include_router(router)

    return app
