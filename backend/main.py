"""Punto de entrada ASGI: `uvicorn backend.main:app`.

Sólo construye la aplicación; toda la lógica vive en `backend/app/`.
Se mantiene esta ruta para no tocar `server.ts` ni `vite.config.ts`.
"""
from __future__ import annotations

import os
import sys

# Permite importar el paquete `app` tanto con `backend.main:app` como
# ejecutando este archivo directamente.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.bootstrap import create_app  # noqa: E402

app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
