"""Repositorios SQLite del contexto `citas` (+ historiales médicos)."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, time

from ...domain.model.cita import Cita, Disponibilidad, EstadoCita, Servicio
from ...domain.model.historial import HistorialMedico
from ...domain.ports.repositories import (
    CitaRepository,
    DisponibilidadRepository,
    EstadoCitaRepository,
    HistorialMedicoRepository,
    ServicioRepository,
)
from ...domain.value_objects import DiaSemana
from ._comun import RepositorioSQLite, a_bool, a_datetime, a_time


class SqliteEstadoCitaRepository(RepositorioSQLite, EstadoCitaRepository):
    def _mapear(self, fila: sqlite3.Row) -> EstadoCita:
        return EstadoCita(
            id=fila["id"],
            nombre=fila["nombre"],
            descripcion=fila["descripcion"],
            orden=fila["orden"],
        )

    def crear(self, estado: EstadoCita) -> EstadoCita:
        estado.id = self._insertar(
            "INSERT INTO estados_cita (nombre, descripcion, orden) VALUES (?,?,?)",
            (estado.nombre, estado.descripcion, estado.orden),
        )
        return estado

    def actualizar(self, estado: EstadoCita) -> EstadoCita:
        self._ejecutar(
            "UPDATE estados_cita SET nombre=?, descripcion=?, orden=? WHERE id=?",
            (estado.nombre, estado.descripcion, estado.orden, estado.id),
        )
        return estado

    def obtener(self, estado_id: int) -> EstadoCita | None:
        fila = self._uno("SELECT * FROM estados_cita WHERE id=?", (estado_id,))
        return self._mapear(fila) if fila else None

    def obtener_por_nombre(self, nombre: str) -> EstadoCita | None:
        fila = self._uno(
            "SELECT * FROM estados_cita WHERE lower(nombre)=?", ((nombre or "").strip().lower(),)
        )
        return self._mapear(fila) if fila else None

    def listar(self) -> list[EstadoCita]:
        return [self._mapear(f) for f in self._todos("SELECT * FROM estados_cita ORDER BY orden, nombre")]

    def eliminar(self, estado_id: int) -> None:
        self._ejecutar("DELETE FROM estados_cita WHERE id=?", (estado_id,))


class SqliteServicioRepository(RepositorioSQLite, ServicioRepository):
    def _mapear(self, fila: sqlite3.Row) -> Servicio:
        return Servicio(
            id=fila["id"],
            nombre=fila["nombre"],
            descripcion=fila["descripcion"],
            activo=a_bool(fila["activo"]),
            veterinarios_ids=[
                f["veterinario_id"]
                for f in self._todos(
                    "SELECT veterinario_id FROM servicio_veterinarios WHERE servicio_id=?",
                    (fila["id"],),
                )
            ],
            especialidades_ids=[
                f["especialidad_id"]
                for f in self._todos(
                    "SELECT especialidad_id FROM servicio_especialidades WHERE servicio_id=?",
                    (fila["id"],),
                )
            ],
        )

    def _guardar_m2m(self, servicio: Servicio) -> None:
        self._ejecutar("DELETE FROM servicio_veterinarios WHERE servicio_id=?", (servicio.id,))
        self._ejecutar("DELETE FROM servicio_especialidades WHERE servicio_id=?", (servicio.id,))
        for veterinario_id in servicio.veterinarios_ids:
            self._ejecutar(
                "INSERT OR IGNORE INTO servicio_veterinarios (servicio_id, veterinario_id) VALUES (?,?)",
                (servicio.id, veterinario_id),
            )
        for especialidad_id in servicio.especialidades_ids:
            self._ejecutar(
                "INSERT OR IGNORE INTO servicio_especialidades (servicio_id, especialidad_id) VALUES (?,?)",
                (servicio.id, especialidad_id),
            )

    def crear(self, servicio: Servicio) -> Servicio:
        servicio.id = self._insertar(
            "INSERT INTO servicios (nombre, descripcion, activo) VALUES (?,?,?)",
            (servicio.nombre, servicio.descripcion, int(servicio.activo)),
        )
        self._guardar_m2m(servicio)
        return servicio

    def actualizar(self, servicio: Servicio) -> Servicio:
        self._ejecutar(
            "UPDATE servicios SET nombre=?, descripcion=?, activo=? WHERE id=?",
            (servicio.nombre, servicio.descripcion, int(servicio.activo), servicio.id),
        )
        self._guardar_m2m(servicio)
        return servicio

    def obtener(self, servicio_id: int) -> Servicio | None:
        fila = self._uno("SELECT * FROM servicios WHERE id=?", (servicio_id,))
        return self._mapear(fila) if fila else None

    def listar(self, solo_activos: bool = False, veterinario_id: int | None = None) -> list[Servicio]:
        sql = "SELECT s.* FROM servicios s"
        params: list = []
        if veterinario_id is not None:
            sql += " JOIN servicio_veterinarios sv ON sv.servicio_id = s.id AND sv.veterinario_id = ?"
            params.append(veterinario_id)
        if solo_activos:
            sql += " WHERE s.activo=1"
        sql += " ORDER BY s.nombre"
        return [self._mapear(f) for f in self._todos(sql, tuple(params))]

    def eliminar(self, servicio_id: int) -> None:
        self._ejecutar("DELETE FROM servicios WHERE id=?", (servicio_id,))


class SqliteDisponibilidadRepository(RepositorioSQLite, DisponibilidadRepository):
    def _mapear(self, fila: sqlite3.Row) -> Disponibilidad:
        return Disponibilidad(
            id=fila["id"],
            veterinario_id=fila["veterinario_id"],
            dia_semana=DiaSemana(fila["dia_semana"]),
            hora_inicio=a_time(fila["hora_inicio"]) or time(0, 0),
            hora_fin=a_time(fila["hora_fin"]) or time(23, 59),
        )

    def crear(self, disponibilidad: Disponibilidad) -> Disponibilidad:
        disponibilidad.id = self._insertar(
            """INSERT INTO disponibilidades (veterinario_id, dia_semana, hora_inicio, hora_fin)
               VALUES (?,?,?,?)""",
            (
                disponibilidad.veterinario_id, disponibilidad.dia_semana.value,
                disponibilidad.hora_inicio, disponibilidad.hora_fin,
            ),
        )
        return disponibilidad

    def actualizar(self, disponibilidad: Disponibilidad) -> Disponibilidad:
        self._ejecutar(
            """UPDATE disponibilidades SET veterinario_id=?, dia_semana=?, hora_inicio=?, hora_fin=?
               WHERE id=?""",
            (
                disponibilidad.veterinario_id, disponibilidad.dia_semana.value,
                disponibilidad.hora_inicio, disponibilidad.hora_fin, disponibilidad.id,
            ),
        )
        return disponibilidad

    def obtener(self, disponibilidad_id: int) -> Disponibilidad | None:
        fila = self._uno("SELECT * FROM disponibilidades WHERE id=?", (disponibilidad_id,))
        return self._mapear(fila) if fila else None

    def listar(self, veterinario_id=None, dia_semana=None) -> list[Disponibilidad]:
        sql = "SELECT * FROM disponibilidades WHERE 1=1"
        params: list = []
        if veterinario_id is not None:
            sql += " AND veterinario_id=?"
            params.append(veterinario_id)
        if dia_semana is not None:
            sql += " AND dia_semana=?"
            params.append(int(dia_semana))
        sql += " ORDER BY veterinario_id, dia_semana, hora_inicio"
        return [self._mapear(f) for f in self._todos(sql, tuple(params))]

    def eliminar(self, disponibilidad_id: int) -> None:
        self._ejecutar("DELETE FROM disponibilidades WHERE id=?", (disponibilidad_id,))


def _a_cita(fila: sqlite3.Row) -> Cita:
    return Cita(
        id=fila["id"],
        mascota_id=fila["mascota_id"],
        veterinario_id=fila["veterinario_id"],
        estado_id=fila["estado_id"],
        servicio_id=fila["servicio_id"],
        fecha_hora=a_datetime(fila["fecha_hora"]),
        peso=fila["peso"],
        motivo=fila["motivo"],
        notas=fila["notas"],
    )


class SqliteCitaRepository(RepositorioSQLite, CitaRepository):
    def crear(self, cita: Cita) -> Cita:
        cita.id = self._insertar(
            """INSERT INTO citas
               (mascota_id, veterinario_id, estado_id, servicio_id, fecha_hora, peso, motivo, notas)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                cita.mascota_id, cita.veterinario_id, cita.estado_id, cita.servicio_id,
                cita.fecha_hora, cita.peso, cita.motivo, cita.notas,
            ),
        )
        return cita

    def actualizar(self, cita: Cita) -> Cita:
        self._ejecutar(
            """UPDATE citas SET mascota_id=?, veterinario_id=?, estado_id=?, servicio_id=?,
                   fecha_hora=?, peso=?, motivo=?, notas=? WHERE id=?""",
            (
                cita.mascota_id, cita.veterinario_id, cita.estado_id, cita.servicio_id,
                cita.fecha_hora, cita.peso, cita.motivo, cita.notas, cita.id,
            ),
        )
        return cita

    def obtener(self, cita_id: int) -> Cita | None:
        fila = self._uno("SELECT * FROM citas WHERE id=?", (cita_id,))
        return _a_cita(fila) if fila else None

    def listar(
        self,
        mascota_id=None,
        veterinario_id=None,
        cliente_id=None,
        estado_id=None,
        desde=None,
        hasta=None,
    ) -> list[Cita]:
        sql = "SELECT c.* FROM citas c"
        params: list = []
        if cliente_id is not None:
            sql += " JOIN mascotas m ON m.id = c.mascota_id AND m.cliente_id = ?"
            params.append(cliente_id)
        sql += " WHERE 1=1"
        if mascota_id is not None:
            sql += " AND c.mascota_id=?"
            params.append(mascota_id)
        if veterinario_id is not None:
            sql += " AND c.veterinario_id=?"
            params.append(veterinario_id)
        if estado_id is not None:
            sql += " AND c.estado_id=?"
            params.append(estado_id)
        if desde is not None:
            sql += " AND c.fecha_hora >= ?"
            params.append(desde)
        if hasta is not None:
            sql += " AND c.fecha_hora <= ?"
            params.append(hasta)
        sql += " ORDER BY c.fecha_hora DESC"
        return [_a_cita(f) for f in self._todos(sql, tuple(params))]

    def listar_por_veterinario_y_dia(self, veterinario_id: int, dia: date) -> list[Cita]:
        return [
            _a_cita(f)
            for f in self._todos(
                "SELECT * FROM citas WHERE veterinario_id=? AND date(fecha_hora)=? ORDER BY fecha_hora",
                (veterinario_id, dia.isoformat()),
            )
        ]

    def eliminar(self, cita_id: int) -> None:
        self._ejecutar("DELETE FROM citas WHERE id=?", (cita_id,))

    def contar(self, dia: date | None = None, estado_id: int | None = None) -> int:
        sql = "SELECT COUNT(*) FROM citas WHERE 1=1"
        params: list = []
        if dia is not None:
            sql += " AND date(fecha_hora)=?"
            params.append(dia.isoformat())
        if estado_id is not None:
            sql += " AND estado_id=?"
            params.append(estado_id)
        return int(self._escalar(sql, tuple(params)) or 0)


def _a_historial(fila: sqlite3.Row) -> HistorialMedico:
    return HistorialMedico(
        id=fila["id"],
        mascota_id=fila["mascota_id"],
        cita_id=fila["cita_id"],
        veterinario_id=fila["veterinario_id"],
        diagnostico=fila["diagnostico"],
        tratamiento=fila["tratamiento"],
        observaciones=fila["observaciones"],
        fecha_creacion=a_datetime(fila["fecha_creacion"]) or datetime.now(),
    )


class SqliteHistorialMedicoRepository(RepositorioSQLite, HistorialMedicoRepository):
    def crear(self, historial: HistorialMedico) -> HistorialMedico:
        historial.id = self._insertar(
            """INSERT INTO historiales_medicos
               (mascota_id, cita_id, veterinario_id, diagnostico, tratamiento,
                observaciones, fecha_creacion)
               VALUES (?,?,?,?,?,?,?)""",
            (
                historial.mascota_id, historial.cita_id, historial.veterinario_id,
                historial.diagnostico,
                historial.tratamiento, historial.observaciones, historial.fecha_creacion,
            ),
        )
        return historial

    def actualizar(self, historial: HistorialMedico) -> HistorialMedico:
        self._ejecutar(
            """UPDATE historiales_medicos SET veterinario_id=?, diagnostico=?, tratamiento=?,
                   observaciones=? WHERE id=?""",
            (
                historial.veterinario_id, historial.diagnostico, historial.tratamiento,
                historial.observaciones, historial.id,
            ),
        )
        return historial

    def obtener(self, historial_id: int) -> HistorialMedico | None:
        fila = self._uno("SELECT * FROM historiales_medicos WHERE id=?", (historial_id,))
        return _a_historial(fila) if fila else None

    def obtener_por_cita(self, cita_id: int) -> HistorialMedico | None:
        fila = self._uno("SELECT * FROM historiales_medicos WHERE cita_id=?", (cita_id,))
        return _a_historial(fila) if fila else None

    def listar(self, mascota_id=None, veterinario_id=None, cliente_id=None) -> list[HistorialMedico]:
        sql = "SELECT h.* FROM historiales_medicos h"
        params: list = []
        if cliente_id is not None:
            sql += " JOIN mascotas m ON m.id = h.mascota_id AND m.cliente_id = ?"
            params.append(cliente_id)
        sql += " WHERE 1=1"
        if mascota_id is not None:
            sql += " AND h.mascota_id=?"
            params.append(mascota_id)
        if veterinario_id is not None:
            sql += " AND h.veterinario_id=?"
            params.append(veterinario_id)
        sql += " ORDER BY h.fecha_creacion DESC"
        return [_a_historial(f) for f in self._todos(sql, tuple(params))]

    def eliminar(self, historial_id: int) -> None:
        self._ejecutar("DELETE FROM historiales_medicos WHERE id=?", (historial_id,))
