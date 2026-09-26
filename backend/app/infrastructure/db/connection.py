"""Adaptador de persistencia: conexión SQLite3 cruda (sin ORM).

Cada petición HTTP abre una conexión que actúa como *unit of work*: se hace
COMMIT si el handler termina bien y ROLLBACK si lanza.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Iterator

from .schema import DDL, SEMILLA_MINIMA

# SQLite no sabe guardar estos tipos: se serializan en texto ISO / decimal.
sqlite3.register_adapter(datetime, lambda v: v.replace(microsecond=0).isoformat(sep=" "))
sqlite3.register_adapter(date, lambda v: v.isoformat())
sqlite3.register_adapter(time, lambda v: v.strftime("%H:%M:%S"))
sqlite3.register_adapter(Decimal, lambda v: float(v))


class Database:
    """Fábrica de conexiones y responsable de crear el esquema."""

    def __init__(self, ruta: str | Path):
        self.ruta = str(ruta)
        if self.ruta != ":memory:":
            Path(self.ruta).parent.mkdir(parents=True, exist_ok=True)
        self._memoria: sqlite3.Connection | None = None

    def conectar(self) -> sqlite3.Connection:
        if self.ruta == ":memory:":
            # Una sola conexión compartida: de otro modo cada una vería su propia BD.
            if self._memoria is None:
                self._memoria = self._nueva_conexion()
            return self._memoria
        return self._nueva_conexion()

    def _nueva_conexion(self) -> sqlite3.Connection:
        # check_same_thread=False: FastAPI ejecuta las dependencias con `yield`
        # en su threadpool, y el __enter__, el handler y el __exit__ pueden caer
        # en hilos distintos. La conexión sigue perteneciendo a una sola
        # petición, así que no hay uso concurrente real.
        conn = sqlite3.connect(
            self.ruta, isolation_level="DEFERRED", check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    @contextmanager
    def unidad_de_trabajo(self) -> Iterator[sqlite3.Connection]:
        """Transacción explícita: commit al salir bien, rollback ante error."""
        conn = self.conectar()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if self.ruta != ":memory:":
                conn.close()

    def crear_esquema(self) -> None:
        conn = self.conectar()
        try:
            conn.executescript(DDL)
            for sentencia, parametros in SEMILLA_MINIMA:
                conn.executemany(sentencia, parametros)
            conn.commit()
        finally:
            if self.ruta != ":memory:":
                conn.close()
