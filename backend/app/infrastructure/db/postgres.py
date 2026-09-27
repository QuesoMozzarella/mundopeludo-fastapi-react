"""Adaptador de persistencia para PostgreSQL (Heroku Postgres).

Los repositorios hablan el SQL de SQLite a través de una conexión con la
interfaz de `sqlite3` (`execute`, `fetchone`, filas por nombre). Esta clase
la ofrece sobre psycopg y traduce lo poco que difiere entre ambos motores:

* `?`                         -> `%s`
* `INSERT OR IGNORE ...`      -> `INSERT ... ON CONFLICT DO NOTHING`
* `date(columna)`             -> `CAST(columna AS date)`
* `lastrowid`                 -> `... RETURNING id` (en `RepositorioSQLite._insertar`)
* `BEGIN IMMEDIATE`           -> `pg_advisory_xact_lock`: las transacciones de
  escritura se serializan igual que en SQLite, así que leer-calcular-escribir
  (el stock de una compra) sigue siendo atómico.

Las fechas se guardan como texto ISO, igual que en SQLite: los mismos
repositorios leen los mismos valores con cualquiera de los dos motores.
"""
from __future__ import annotations

import re
from contextlib import contextmanager
from datetime import date, datetime, time
from decimal import Decimal
from typing import Iterator

import psycopg
from psycopg import errors as pg
from psycopg.types.numeric import NumericLoader
from psycopg_pool import ConnectionPool, PoolTimeout

from ...domain.errors import ConflictError, ServicioNoDisponibleError, ValidationError
from .schema import DDL, SEMILLA_MINIMA, migrar

# Número arbitrario y fijo para el cerrojo consultivo de escritura.
CERROJO_ESCRITURA = 7274_2026
MAX_BIGINT = 2**63 - 1


# ------------------------------ traducción ------------------------------
_TRADUCIDAS: dict[str, str] = {}


def traducir(sql: str) -> str:
    """SQL de SQLite -> SQL de PostgreSQL (con caché: las sentencias se repiten)."""
    traducida = _TRADUCIDAS.get(sql)
    if traducida is None:
        t = sql.replace("%", "%%").replace("?", "%s")
        t = re.sub(r"\bdate\(([\w.]+)\)", r"CAST(\1 AS date)", t)
        if re.match(r"\s*INSERT\s+OR\s+IGNORE\b", t, re.I):
            t = re.sub(r"INSERT\s+OR\s+IGNORE", "INSERT", t, count=1, flags=re.I)
            partes = re.split(r"(?i)\bRETURNING\b", t, maxsplit=1)
            t = partes[0].rstrip() + " ON CONFLICT DO NOTHING"
            if len(partes) == 2:
                t += " RETURNING" + partes[1]
        _TRADUCIDAS[sql] = traducida = t
    return traducida


def ddl_postgres(ddl: str) -> list[str]:
    """El DDL de SQLite convertido a sentencias de PostgreSQL.

    INTEGER pasa a BIGINT (SQLite guarda enteros de 64 bits), REAL a DOUBLE
    PRECISION (precios sin redondeos de float4) y BLOB a BYTEA.
    """
    t = ddl.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
    t = re.sub(r"\bINTEGER\b", "BIGINT", t)
    t = re.sub(r"\bREAL\b", "DOUBLE PRECISION", t)
    t = re.sub(r"\bBLOB\b", "BYTEA", t)
    sentencias = []
    for trozo in t.split(";"):
        codigo = "\n".join(l for l in trozo.splitlines() if not l.strip().startswith("--")).strip()
        if codigo:
            sentencias.append(codigo)
    return sentencias


def _valor(v):
    """Los mismos tipos que guardan los adaptadores de sqlite3 (connection.py)."""
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, int) and abs(v) > MAX_BIGINT:
        # Como en SQLite: el repositorio lo convierte en un 422.
        raise OverflowError("entero fuera de 64 bits")
    if isinstance(v, datetime):
        return v.replace(microsecond=0).isoformat(sep=" ")
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, time):
        return v.strftime("%H:%M:%S")
    if isinstance(v, Decimal):
        return float(v)
    return v


# ------------------------------ filas ------------------------------
class Fila(dict):
    """Fila accesible por nombre y por posición, como `sqlite3.Row`."""

    def __getitem__(self, clave):
        if isinstance(clave, int):
            return list(self.values())[clave]
        return super().__getitem__(clave)


def _fabrica_filas(cursor):
    nombres = [c.name for c in cursor.description] if cursor.description else []
    return lambda valores: Fila(zip(nombres, valores))


class _Numero(NumericLoader):
    """NUMERIC (p. ej. un SUM de enteros) llega como int o float, no Decimal."""

    def load(self, data):
        valor = super().load(data)
        return int(valor) if valor == valor.to_integral_value() else float(valor)


def _configurar(conn: psycopg.Connection) -> None:
    conn.adapters.register_loader("numeric", _Numero)


# ------------------------------ conexión ------------------------------
class ConexionPostgres:
    """La cara de `sqlite3.Connection` que usan los repositorios."""

    dialecto = "postgres"

    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    def execute(self, sql: str, parametros=()) -> psycopg.Cursor:
        cursor = self._conn.cursor(row_factory=_fabrica_filas)
        try:
            cursor.execute(traducir(sql), tuple(_valor(v) for v in parametros))
        except pg.UniqueViolation as exc:
            raise ConflictError(f"Ya existe un registro con ese valor ({_detalle(exc)})") from exc
        except pg.ForeignKeyViolation as exc:
            raise ConflictError("La referencia indicada no existe (clave foránea inválida)") from exc
        except pg.CheckViolation as exc:
            raise ConflictError(f"Valor fuera de los permitidos ({_detalle(exc)})") from exc
        except pg.NotNullViolation as exc:
            raise ConflictError(f"Falta un campo obligatorio ({_detalle(exc)})") from exc
        except (pg.NumericValueOutOfRange, pg.InvalidDatetimeFormat, pg.DatetimeFieldOverflow) as exc:
            raise ValidationError("Valor fuera del rango admitido") from exc
        return cursor

    def executemany(self, sql: str, filas) -> None:
        with self._conn.cursor() as cursor:
            cursor.executemany(traducir(sql), [tuple(_valor(v) for v in f) for f in filas])

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()


def _detalle(exc: psycopg.Error) -> str:
    diag = exc.diag
    return diag.column_name or diag.constraint_name or diag.message_primary or str(exc)


class DatabasePostgres:
    """Fábrica de unidades de trabajo sobre un pool de conexiones."""

    def __init__(self, url: str, max_conexiones: int = 5):
        self.url = url
        self._pool = ConnectionPool(
            url,
            min_size=1,
            max_size=max_conexiones,
            configure=_configurar,
            open=True,
            name="mundopeludo",
        )

    @contextmanager
    def unidad_de_trabajo(self, escritura: bool = True) -> Iterator[ConexionPostgres]:
        """Transacción: commit al salir bien, rollback ante error.

        Con `escritura` toma un cerrojo consultivo de transacción: las
        peticiones que modifican datos se serializan, como con BEGIN IMMEDIATE
        en SQLite. Las lecturas no esperan a nadie.
        """
        try:
            conn = self._pool.getconn(timeout=10)
        except PoolTimeout as exc:
            raise ServicioNoDisponibleError(
                "La base de datos está ocupada; intenta de nuevo en unos segundos"
            ) from exc
        try:
            if escritura:
                conn.execute("SELECT pg_advisory_xact_lock(%s)", (CERROJO_ESCRITURA,))
            yield ConexionPostgres(conn)
            conn.commit()
        except BaseException as exc:
            if getattr(exc, "conservar_cambios", False):
                conn.commit()
            else:
                conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def crear_esquema(self) -> None:
        with self.unidad_de_trabajo(escritura=True) as conexion:
            # Con el cerrojo: dos dynos que arrancan a la vez no chocan.
            migrar(conexion)
            for sentencia in ddl_postgres(DDL):
                conexion._conn.execute(sentencia)
            for sentencia, parametros in SEMILLA_MINIMA:
                conexion.executemany(sentencia, parametros)

    def cerrar(self) -> None:
        self._pool.close()
