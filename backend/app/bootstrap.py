"""Arranque de la aplicación: monta el adaptador HTTP sobre el núcleo.

Es el único punto donde FastAPI, los casos de uso y los adaptadores se
encuentran; el dominio nunca importa nada de aquí.
"""
from __future__ import annotations

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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=contenedor.config.origenes_cors or ["*"],
        allow_credentials=True,
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
