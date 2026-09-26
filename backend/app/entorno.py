"""Carga del archivo `.env` de la raíz del repositorio.

Va aparte de `config.py` a propósito: hay que llamarla *antes* de importar la
configuración, que lee las variables al importarse. Las pruebas no la usan, así
que nunca heredan las credenciales reales de correo.
"""
from __future__ import annotations

import os
from pathlib import Path

ENV_REPO = Path(__file__).resolve().parent.parent.parent / ".env"


def cargar_env(ruta: Path = ENV_REPO) -> None:
    """Lee `CLAVE=valor` sin pisar variables que ya existan en el entorno."""
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
            valor = valor[1:-1]
        os.environ.setdefault(clave.strip(), valor)
