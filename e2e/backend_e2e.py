"""Backend aislado para las pruebas e2e de Playwright.

Cada ejecución parte de una base SQLite nueva con los datos de `seed.py`, en un
puerto propio: nunca toca la base de desarrollo ni un backend ya levantado.
El correo queda desactivado para no enviar avisos a las cuentas de ejemplo.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TMP = Path(__file__).resolve().parent / ".tmp"
BD = TMP / "e2e.db"
PUERTO = os.environ.get("E2E_PUERTO_API", "8011")

entorno = {
    **os.environ,
    "MP_DB_PATH": str(BD),
    "MP_EMAIL_HOST": "",  # vacío (no ausente): así el .env no lo rellena
    "MP_REQUIRE_AUTH": "1",
    "MP_ENV": "desarrollo",
    "MP_SECRET_KEY": "clave-solo-para-pruebas-e2e",
    "PYTHONIOENCODING": "utf-8",
}

TMP.mkdir(exist_ok=True)
for sufijo in ("", "-wal", "-shm"):
    Path(f"{BD}{sufijo}").unlink(missing_ok=True)

subprocess.run([sys.executable, str(RAIZ / "backend" / "seed.py")], env=entorno, check=True)
# Proceso hijo (no os.exec*): en Windows exec lanza otro proceso y Playwright
# perdería el rastro de uvicorn al terminar.
sys.exit(
    subprocess.call(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "127.0.0.1", "--port", PUERTO],
        env=entorno,
        cwd=RAIZ,
    )
)
