"""Repositorios SQLite del contexto `mascotas`."""
from __future__ import annotations

import sqlite3

from ...domain.model.mascota import Especie, Mascota, SolicitudAdopcion
from ...domain.ports.repositories import (
    EspecieRepository,
    MascotaRepository,
    SolicitudAdopcionRepository,
)
from ...domain.value_objects import EstadoAdopcion, EstadoSolicitud, Sexo
from ._comun import RepositorioSQLite, a_bool, a_date, a_datetime, filtro_like


class SqliteEspecieRepository(RepositorioSQLite, EspecieRepository):
    def crear(self, especie: Especie) -> Especie:
        especie.id = self._insertar("INSERT INTO especies (nombre) VALUES (?)", (especie.nombre,))
        return especie

    def actualizar(self, especie: Especie) -> Especie:
        self._ejecutar("UPDATE especies SET nombre=? WHERE id=?", (especie.nombre, especie.id))
        return especie

    def obtener(self, especie_id: int) -> Especie | None:
        fila = self._uno("SELECT * FROM especies WHERE id=?", (especie_id,))
        return Especie(id=fila["id"], nombre=fila["nombre"]) if fila else None

    def obtener_por_nombre(self, nombre: str) -> Especie | None:
        fila = self._uno("SELECT * FROM especies WHERE lower(nombre)=?", ((nombre or "").strip().lower(),))
        return Especie(id=fila["id"], nombre=fila["nombre"]) if fila else None

    def listar(self) -> list[Especie]:
        return [
            Especie(id=f["id"], nombre=f["nombre"])
            for f in self._todos("SELECT * FROM especies ORDER BY nombre")
        ]

    def eliminar(self, especie_id: int) -> None:
        self._ejecutar("DELETE FROM especies WHERE id=?", (especie_id,))


def _a_mascota(fila: sqlite3.Row) -> Mascota:
    return Mascota(
        id=fila["id"],
        cliente_id=fila["cliente_id"],
        especie_id=fila["especie_id"],
        nombre=fila["nombre"],
        raza=fila["raza"],
        edad_anos=fila["edad_anos"],
        sexo=Sexo(fila["sexo"]),
        color=fila["color"],
        peso=fila["peso"],
        esta_esterilizado=a_bool(fila["esta_esterilizado"]),
        activo=a_bool(fila["activo"]),
        fecha_registro=a_date(fila["fecha_registro"]),
        estado_adopcion=EstadoAdopcion(fila["estado_adopcion"]),
    )


class SqliteMascotaRepository(RepositorioSQLite, MascotaRepository):
    def crear(self, mascota: Mascota) -> Mascota:
        mascota.id = self._insertar(
            """INSERT INTO mascotas
               (cliente_id, especie_id, nombre, raza, edad_anos, sexo, color, peso,
                esta_esterilizado, activo, fecha_registro, estado_adopcion)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                mascota.cliente_id, mascota.especie_id, mascota.nombre, mascota.raza,
                mascota.edad_anos, mascota.sexo.value, mascota.color, mascota.peso,
                int(mascota.esta_esterilizado), int(mascota.activo),
                mascota.fecha_registro, mascota.estado_adopcion.value,
            ),
        )
        return mascota

    def actualizar(self, mascota: Mascota) -> Mascota:
        self._ejecutar(
            """UPDATE mascotas SET cliente_id=?, especie_id=?, nombre=?, raza=?, edad_anos=?,
                   sexo=?, color=?, peso=?, esta_esterilizado=?, activo=?, estado_adopcion=?
               WHERE id=?""",
            (
                mascota.cliente_id, mascota.especie_id, mascota.nombre, mascota.raza,
                mascota.edad_anos, mascota.sexo.value, mascota.color, mascota.peso,
                int(mascota.esta_esterilizado), int(mascota.activo),
                mascota.estado_adopcion.value, mascota.id,
            ),
        )
        return mascota

    def obtener(self, mascota_id: int) -> Mascota | None:
        fila = self._uno("SELECT * FROM mascotas WHERE id=?", (mascota_id,))
        return _a_mascota(fila) if fila else None

    def listar(
        self,
        cliente_id=None,
        especie_id=None,
        estado_adopcion=None,
        activo=True,
        buscar=None,
    ) -> list[Mascota]:
        sql = "SELECT * FROM mascotas WHERE 1=1"
        params: list = []
        if cliente_id is not None:
            sql += " AND cliente_id=?"
            params.append(cliente_id)
        if especie_id is not None:
            sql += " AND especie_id=?"
            params.append(especie_id)
        if estado_adopcion is not None:
            sql += " AND estado_adopcion=?"
            params.append(EstadoAdopcion.desde(estado_adopcion, campo="estado_adopcion").value)
        if activo is not None:
            sql += " AND activo=?"
            params.append(int(activo))
        if buscar:
            sql += " AND (lower(nombre) LIKE ? OR lower(raza) LIKE ?)"
            params += [filtro_like(buscar)] * 2
        sql += " ORDER BY nombre"
        return [_a_mascota(f) for f in self._todos(sql, tuple(params))]

    def eliminar(self, mascota_id: int) -> None:
        self._ejecutar("DELETE FROM mascotas WHERE id=?", (mascota_id,))

    def contar(self, activo=True) -> int:
        if activo is None:
            return int(self._escalar("SELECT COUNT(*) FROM mascotas") or 0)
        return int(self._escalar("SELECT COUNT(*) FROM mascotas WHERE activo=?", (int(activo),)) or 0)


def _a_solicitud(fila: sqlite3.Row) -> SolicitudAdopcion:
    return SolicitudAdopcion(
        id=fila["id"],
        mascota_id=fila["mascota_id"],
        cliente_id=fila["cliente_id"],
        estado=EstadoSolicitud(fila["estado"]),
        fecha_solicitud=a_datetime(fila["fecha_solicitud"]),
        fecha_actualizacion=a_datetime(fila["fecha_actualizacion"]),
        revisado_por_id=fila["revisado_por_id"],
        fecha_revision=a_datetime(fila["fecha_revision"]),
        notas_revisor=fila["notas_revisor"] or "",
        notas_cliente=fila["notas_cliente"] or "",
    )


class SqliteSolicitudAdopcionRepository(RepositorioSQLite, SolicitudAdopcionRepository):
    def crear(self, solicitud: SolicitudAdopcion) -> SolicitudAdopcion:
        solicitud.id = self._insertar(
            """INSERT INTO solicitudes_adopcion
               (mascota_id, cliente_id, fecha_solicitud, fecha_actualizacion, estado,
                revisado_por_id, fecha_revision, notas_revisor, notas_cliente)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                solicitud.mascota_id, solicitud.cliente_id, solicitud.fecha_solicitud,
                solicitud.fecha_actualizacion, solicitud.estado.value, solicitud.revisado_por_id,
                solicitud.fecha_revision, solicitud.notas_revisor, solicitud.notas_cliente,
            ),
        )
        return solicitud

    def actualizar(self, solicitud: SolicitudAdopcion) -> SolicitudAdopcion:
        self._ejecutar(
            """UPDATE solicitudes_adopcion SET estado=?, fecha_actualizacion=?, revisado_por_id=?,
                   fecha_revision=?, notas_revisor=?, notas_cliente=?
               WHERE id=?""",
            (
                solicitud.estado.value, solicitud.fecha_actualizacion, solicitud.revisado_por_id,
                solicitud.fecha_revision, solicitud.notas_revisor, solicitud.notas_cliente,
                solicitud.id,
            ),
        )
        return solicitud

    def obtener(self, solicitud_id: int) -> SolicitudAdopcion | None:
        fila = self._uno("SELECT * FROM solicitudes_adopcion WHERE id=?", (solicitud_id,))
        return _a_solicitud(fila) if fila else None

    def listar(self, cliente_id=None, mascota_id=None, estado=None) -> list[SolicitudAdopcion]:
        sql = "SELECT * FROM solicitudes_adopcion WHERE 1=1"
        params: list = []
        if cliente_id is not None:
            sql += " AND cliente_id=?"
            params.append(cliente_id)
        if mascota_id is not None:
            sql += " AND mascota_id=?"
            params.append(mascota_id)
        if estado is not None:
            sql += " AND estado=?"
            params.append(EstadoSolicitud.desde(estado, campo="estado").value)
        sql += " ORDER BY fecha_solicitud DESC"
        return [_a_solicitud(f) for f in self._todos(sql, tuple(params))]

    def existe_pendiente(self, mascota_id: int, cliente_id: int) -> bool:
        total = self._escalar(
            """SELECT COUNT(*) FROM solicitudes_adopcion
               WHERE mascota_id=? AND cliente_id=? AND estado='pendiente'""",
            (mascota_id, cliente_id),
        )
        return bool(total)

    def eliminar(self, solicitud_id: int) -> None:
        self._ejecutar("DELETE FROM solicitudes_adopcion WHERE id=?", (solicitud_id,))
