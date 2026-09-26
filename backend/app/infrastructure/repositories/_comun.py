"""Utilidades compartidas por los repositorios SQLite."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, time
from decimal import Decimal

from ...domain.errors import ConflictError


class RepositorioSQLite:
    """Base con la conexión de la petición y el manejo de errores de integridad."""

    def __init__(self, conexion: sqlite3.Connection):
        self.conexion = conexion

    def _ejecutar(self, sql: str, parametros: tuple = ()) -> sqlite3.Cursor:
        try:
            return self.conexion.execute(sql, parametros)
        except sqlite3.IntegrityError as exc:
            raise ConflictError(_traducir_integridad(exc)) from exc

    def _uno(self, sql: str, parametros: tuple = ()) -> sqlite3.Row | None:
        return self._ejecutar(sql, parametros).fetchone()

    def _todos(self, sql: str, parametros: tuple = ()) -> list[sqlite3.Row]:
        return self._ejecutar(sql, parametros).fetchall()

    def _insertar(self, sql: str, parametros: tuple) -> int:
        return self._ejecutar(sql, parametros).lastrowid

    def _escalar(self, sql: str, parametros: tuple = ()) -> object:
        fila = self._uno(sql, parametros)
        return fila[0] if fila else None


def _traducir_integridad(exc: sqlite3.IntegrityError) -> str:
    mensaje = str(exc)
    if "UNIQUE constraint failed" in mensaje:
        campo = mensaje.split(":")[-1].strip()
        return f"Ya existe un registro con ese valor ({campo})"
    if "FOREIGN KEY constraint failed" in mensaje:
        return "La referencia indicada no existe (clave foránea inválida)"
    if "CHECK constraint failed" in mensaje:
        return f"Valor fuera de los permitidos ({mensaje.split(':')[-1].strip()})"
    if "NOT NULL constraint failed" in mensaje:
        return f"Falta un campo obligatorio ({mensaje.split(':')[-1].strip()})"
    return mensaje


# --- conversiones desde el texto plano de SQLite ---
def a_bool(valor) -> bool:
    return bool(valor)


def a_datetime(valor) -> datetime | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, datetime):
        return valor
    texto = str(valor).strip().replace("T", " ")
    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    return None


def a_date(valor) -> date | None:
    momento = a_datetime(valor)
    return momento.date() if momento else None


def a_time(valor) -> time | None:
    if valor in (None, ""):
        return None
    if isinstance(valor, time):
        return valor
    texto = str(valor).strip()
    for formato in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(texto, formato).time()
        except ValueError:
            continue
    return None


def a_decimal(valor) -> Decimal:
    return Decimal(str(valor if valor is not None else 0))


def filtro_like(texto: str) -> str:
    return f"%{texto.strip().lower()}%"
