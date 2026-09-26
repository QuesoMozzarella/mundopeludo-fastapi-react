"""Adaptador de persistencia: conexión SQLite3 cruda (sin ORM).

Cada petición HTTP abre una conexión que actúa como *unit of work*: se hace
COMMIT si el handler termina bien y ROLLBACK si lanza.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Iterator

from ...domain.errors import ServicioNoDisponibleError
from .schema import DDL, SEMILLA_MINIMA, migrar

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
        # La conexión ":memory:" es única y compartida: sus transacciones no
        # pueden solaparse entre hilos.
        self._cerrojo_memoria = threading.RLock()

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
        # isolation_level=None: las transacciones las abre `unidad_de_trabajo`
        # con BEGIN explícito. El modo implícito de sqlite3 sólo abría la
        # transacción al primer INSERT/UPDATE, así que las lecturas previas
        # (p. ej. el stock) quedaban fuera y dos compras simultáneas podían
        # vender la misma última unidad.
        conn = sqlite3.connect(
            self.ruta, isolation_level=None, check_same_thread=False, timeout=10
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    @contextmanager
    def unidad_de_trabajo(self, escritura: bool = True) -> Iterator[sqlite3.Connection]:
        """Transacción explícita: commit al salir bien, rollback ante error.

        Con `escritura`, BEGIN IMMEDIATE toma el cerrojo de escritura desde la
        primera lectura: las peticiones que modifican datos se serializan y
        leer-calcular-escribir es atómico. Las de sólo lectura usan BEGIN
        normal y, gracias a WAL, no esperan a nadie.
        """
        memoria = self.ruta == ":memory:"
        if memoria:
            self._cerrojo_memoria.acquire()
        conn = self.conectar()
        try:
            try:
                conn.execute("BEGIN IMMEDIATE" if escritura else "BEGIN")
            except sqlite3.OperationalError as exc:
                # Otro escritor retuvo el cerrojo más que el `timeout`.
                raise ServicioNoDisponibleError(
                    "La base de datos está ocupada; intenta de nuevo en unos segundos"
                ) from exc
            yield conn
            conn.commit()
        except BaseException as exc:
            # BaseException y no Exception: una cancelación o un GeneratorExit
            # también deben deshacer la transacción. Con ":memory:" la conexión
            # no se cierra y el cambio a medias quedaría visible a la siguiente
            # petición.
            if getattr(exc, "conservar_cambios", False):
                conn.commit()
            else:
                conn.rollback()
            raise
        finally:
            if memoria:
                self._cerrojo_memoria.release()
            else:
                conn.close()

    def crear_esquema(self) -> None:
        conn = self.conectar()
        try:
            migrar(conn)
            conn.executescript(DDL)
            for sentencia, parametros in SEMILLA_MINIMA:
                conn.executemany(sentencia, parametros)
            conn.commit()
        finally:
            if self.ruta != ":memory:":
                conn.close()
