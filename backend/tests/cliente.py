"""Cliente ASGI mínimo para probar la API sin dependencias externas.

`fastapi.testclient` necesita `httpx`, que no forma parte de los requisitos de
ejecución; este cliente habla directamente el protocolo ASGI.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode


@dataclass
class Respuesta:
    status: int
    cuerpo: bytes
    headers: dict[str, str]

    def json(self) -> Any:
        return json.loads(self.cuerpo or b"null")

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def __repr__(self) -> str:  # pragma: no cover - sólo para depurar
        return f"<Respuesta {self.status} {self.cuerpo[:200]!r}>"


class ClienteASGI:
    def __init__(self, app):
        self.app = app

    def solicitar(
        self,
        metodo: str,
        ruta: str,
        json_body: Any = None,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Respuesta:
        return asyncio.run(self._enviar(metodo, ruta, json_body, params, headers))

    def get(self, ruta, **kw) -> Respuesta:
        return self.solicitar("GET", ruta, **kw)

    def post(self, ruta, json_body=None, **kw) -> Respuesta:
        return self.solicitar("POST", ruta, json_body, **kw)

    def put(self, ruta, json_body=None, **kw) -> Respuesta:
        return self.solicitar("PUT", ruta, json_body, **kw)

    def delete(self, ruta, **kw) -> Respuesta:
        return self.solicitar("DELETE", ruta, **kw)

    async def _enviar(self, metodo, ruta, json_body, params, headers) -> Respuesta:
        cuerpo = b"" if json_body is None else json.dumps(json_body).encode()
        extra = {clave.lower(): str(valor) for clave, valor in (headers or {}).items()}
        # El host de la prueba, si lo indica, sustituye al de por defecto.
        cabeceras = [(b"host", extra.pop("host", "testserver").encode())]
        if json_body is not None:
            cabeceras.append((b"content-type", b"application/json"))
        for clave, valor in extra.items():
            cabeceras.append((clave.encode(), valor.encode()))

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": metodo.upper(),
            "scheme": "http",
            "path": ruta,
            "raw_path": ruta.encode(),
            "query_string": urlencode(params or {}, doseq=True).encode(),
            "root_path": "",
            "headers": cabeceras,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }

        recibido = {"enviado": False}

        async def receive():
            if recibido["enviado"]:
                return {"type": "http.disconnect"}
            recibido["enviado"] = True
            return {"type": "http.request", "body": cuerpo, "more_body": False}

        respuesta = {"status": 500, "cuerpo": b"", "headers": {}}

        async def send(mensaje):
            if mensaje["type"] == "http.response.start":
                respuesta["status"] = mensaje["status"]
                respuesta["headers"] = {
                    k.decode(): v.decode() for k, v in mensaje.get("headers", [])
                }
            elif mensaje["type"] == "http.response.body":
                respuesta["cuerpo"] += mensaje.get("body", b"")

        await self.app(scope, receive, send)
        return Respuesta(respuesta["status"], respuesta["cuerpo"], respuesta["headers"])


def crear_cliente(app) -> ClienteASGI:
    """Devuelve un cliente listo para usar.

    No hace falta arrancar ningún ciclo de vida: `create_app()` ya deja el
    contenedor de dependencias instalado en `app.state`.
    """
    return ClienteASGI(app)
