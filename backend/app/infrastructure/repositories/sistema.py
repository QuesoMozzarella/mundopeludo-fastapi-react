"""Repositorios SQLite de los modelos transversales (`sananimal_clinic`)."""
from __future__ import annotations

import sqlite3
from datetime import datetime

from ...domain.model.sistema import ActividadSistema, CodigoRecuperacion
from ...domain.ports.repositories import (
    ActividadSistemaRepository,
    CodigoRecuperacionRepository,
)
from ._comun import RepositorioSQLite, a_bool, a_datetime


class SqliteActividadSistemaRepository(RepositorioSQLite, ActividadSistemaRepository):
    def registrar(self, actividad: ActividadSistema) -> ActividadSistema:
        actividad.id = self._insertar(
            "INSERT INTO actividades_sistema (usuario, tipo, descripcion, fecha) VALUES (?,?,?,?)",
            (actividad.usuario, actividad.tipo, actividad.descripcion, actividad.fecha),
        )
        return actividad

    def listar(self, limite: int = 50, tipo: str | None = None) -> list[ActividadSistema]:
        sql = "SELECT * FROM actividades_sistema"
        params: list = []
        if tipo:
            sql += " WHERE tipo=?"
            params.append(tipo)
        sql += " ORDER BY fecha DESC, id DESC LIMIT ?"
        params.append(max(1, min(int(limite), 500)))
        return [
            ActividadSistema(
                id=f["id"],
                usuario=f["usuario"],
                tipo=f["tipo"],
                descripcion=f["descripcion"],
                fecha=a_datetime(f["fecha"]) or datetime.now(),
            )
            for f in self._todos(sql, tuple(params))
        ]


class SqliteCodigoRecuperacionRepository(RepositorioSQLite, CodigoRecuperacionRepository):
    def _mapear(self, fila: sqlite3.Row) -> CodigoRecuperacion:
        return CodigoRecuperacion(
            id=fila["id"],
            usuario_id=fila["usuario_id"],
            codigo=fila["codigo"],
            fecha_creacion=a_datetime(fila["fecha_creacion"]) or datetime.now(),
            fecha_expiracion=a_datetime(fila["fecha_expiracion"]),
            intentos=fila["intentos"],
            activo=a_bool(fila["activo"]),
        )

    def crear(self, codigo: CodigoRecuperacion) -> CodigoRecuperacion:
        codigo.id = self._insertar(
            """INSERT INTO codigos_recuperacion
               (usuario_id, codigo, fecha_creacion, fecha_expiracion, intentos, activo)
               VALUES (?,?,?,?,?,?)""",
            (
                codigo.usuario_id, codigo.codigo, codigo.fecha_creacion,
                codigo.fecha_expiracion, codigo.intentos, int(codigo.activo),
            ),
        )
        return codigo

    def actualizar(self, codigo: CodigoRecuperacion) -> CodigoRecuperacion:
        self._ejecutar(
            "UPDATE codigos_recuperacion SET intentos=?, activo=? WHERE id=?",
            (codigo.intentos, int(codigo.activo), codigo.id),
        )
        return codigo

    def obtener_activo(self, usuario_id: int) -> CodigoRecuperacion | None:
        fila = self._uno(
            """SELECT * FROM codigos_recuperacion
               WHERE usuario_id=? AND activo=1
               ORDER BY fecha_creacion DESC, id DESC LIMIT 1""",
            (usuario_id,),
        )
        return self._mapear(fila) if fila else None

    def desactivar_todos(self, usuario_id: int) -> None:
        self._ejecutar("UPDATE codigos_recuperacion SET activo=0 WHERE usuario_id=?", (usuario_id,))
