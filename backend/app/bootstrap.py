"""Arranque de la aplicación: monta el adaptador HTTP sobre el núcleo.

Es el único punto donde FastAPI, los casos de uso y los adaptadores se
encuentran; el dominio nunca importa nada de aquí.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
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
    # El último middleware registrado es el más externo: las cabeceras de
    # seguridad se añaden también a las redirecciones a https.
    if contenedor.config.es_produccion:
        _forzar_https(app, contenedor.config.host_canonico)
    _cabeceras_de_seguridad(app, hsts=contenedor.config.es_produccion)

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


def _forzar_https(app: FastAPI, host_canonico: str) -> None:
    """En producción todo va por https y, si se indica, a un único dominio.

    Heroku termina TLS en su router y avisa con X-Forwarded-Proto. Una petición
    por http, o por un dominio distinto del canónico (la raíz sin www o el de
    herokuapp.com), recibe una redirección a https://<canónico>/<misma ruta>.
    GET y HEAD con 301; el resto con 308 para no convertir un POST en GET.
    """

    @app.middleware("http")
    async def redirigir(request, call_next):
        protocolo = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = (request.headers.get("host") or "").split(":")[0].lower()
        destino = host_canonico or host
        if protocolo == "https" and host == destino:
            return await call_next(request)
        url = f"https://{destino}{request.url.path}"
        if request.url.query:
            url += f"?{request.url.query}"
        codigo = 301 if request.method in ("GET", "HEAD") else 308
        return RedirectResponse(url, status_code=codigo)


def _cabeceras_de_seguridad(app: FastAPI, hsts: bool) -> None:
    """Cabeceras básicas en todas las respuestas (web y API).

    * nosniff: el navegador no "adivina" tipos (una imagen subida no se ejecuta).
    * frame-ancestors / X-Frame-Options: nadie incrusta la app en un iframe
      para engañar clics.
    * Referrer-Policy: las URLs internas no se filtran a otros sitios.
    * HSTS sólo en producción: en local se usa http.
    """
    fijas = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": "frame-ancestors 'none'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
    if hsts:
        fijas["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    @app.middleware("http")
    async def seguridad(request, call_next):
        respuesta = await call_next(request)
        for nombre, valor in fijas.items():
            respuesta.headers.setdefault(nombre, valor)
        return respuesta


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
