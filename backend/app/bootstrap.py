"""Arranque de la aplicación: monta el adaptador HTTP sobre el núcleo.

Es el único punto donde FastAPI, los casos de uso y los adaptadores se
encuentran; el dominio nunca importa nada de aquí.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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

    frontend = Path(configuracion.dir_frontend)
    if (frontend / "index.html").is_file():
        _servir_frontend(app, frontend)

    return app


def _servir_frontend(app: FastAPI, carpeta: Path) -> None:
    """Sirve la SPA compilada (`npm run build`) desde el mismo proceso.

    En producción (Heroku) no hay servidor Node: FastAPI entrega la web y la
    API. Las rutas de la API van antes; cualquier otra ruta devuelve el
    archivo pedido si existe o `index.html` (la SPA decide qué mostrar).
    """
    carpeta = carpeta.resolve()
    indice = carpeta / "index.html"
    if (carpeta / "assets").is_dir():
        # Nombres con hash de Vite: se pueden cachear sin miedo.
        app.mount("/assets", StaticFiles(directory=carpeta / "assets"), name="assets")

    @app.get("/{ruta:path}", include_in_schema=False)
    def spa(ruta: str) -> FileResponse:
        if ruta == "api" or ruta.startswith("api/"):
            raise HTTPException(status_code=404, detail="Recurso no encontrado")
        archivo = (carpeta / ruta).resolve()
        if ruta and archivo.is_file() and carpeta in archivo.parents:
            return FileResponse(archivo)
        # index.html sin caché: tras un despliegue se carga la versión nueva.
        return FileResponse(indice, headers={"Cache-Control": "no-cache"})

    log.info("Sirviendo el frontend desde %s", carpeta)
