"""Repositorios SQLite del contexto `usuarios`."""
from __future__ import annotations

import sqlite3

from ...domain.model.usuario import Especialidad, PerfilCliente, PerfilVeterinario, Usuario
from ...domain.ports.repositories import (
    EspecialidadRepository,
    PerfilClienteRepository,
    PerfilVeterinarioRepository,
    UsuarioRepository,
)
from ...domain.value_objects import TipoUsuario
from ._comun import RepositorioSQLite, a_bool, a_date, a_datetime, filtro_like

CAMPOS_USUARIO = (
    "id, email, password_hash, nombre, apellidos, telefono, direccion, tipo, "
    "is_active, is_staff, is_superuser, date_joined, last_login, "
    "intentos_fallidos, bloqueado_hasta"
)


def _a_usuario(fila: sqlite3.Row) -> Usuario:
    return Usuario(
        id=fila["id"],
        email=fila["email"],
        password_hash=fila["password_hash"],
        nombre=fila["nombre"],
        apellidos=fila["apellidos"],
        telefono=fila["telefono"],
        direccion=fila["direccion"],
        tipo=TipoUsuario(fila["tipo"]),
        is_active=a_bool(fila["is_active"]),
        is_staff=a_bool(fila["is_staff"]),
        is_superuser=a_bool(fila["is_superuser"]),
        date_joined=a_datetime(fila["date_joined"]),
        last_login=a_datetime(fila["last_login"]),
        intentos_fallidos=fila["intentos_fallidos"],
        bloqueado_hasta=a_datetime(fila["bloqueado_hasta"]),
    )


class SqliteUsuarioRepository(RepositorioSQLite, UsuarioRepository):
    def crear(self, usuario: Usuario) -> Usuario:
        usuario.id = self._insertar(
            """INSERT INTO usuarios
               (email, password_hash, nombre, apellidos, telefono, direccion, tipo,
                is_active, is_staff, is_superuser, date_joined, last_login,
                intentos_fallidos, bloqueado_hasta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                usuario.email, usuario.password_hash, usuario.nombre, usuario.apellidos,
                usuario.telefono, usuario.direccion, usuario.tipo.value,
                int(usuario.is_active), int(usuario.is_staff), int(usuario.is_superuser),
                usuario.date_joined, usuario.last_login,
                usuario.intentos_fallidos, usuario.bloqueado_hasta,
            ),
        )
        return usuario

    def actualizar(self, usuario: Usuario) -> Usuario:
        self._ejecutar(
            """UPDATE usuarios SET email=?, password_hash=?, nombre=?, apellidos=?,
                   telefono=?, direccion=?, tipo=?, is_active=?, is_staff=?,
                   is_superuser=?, last_login=?, intentos_fallidos=?, bloqueado_hasta=?
               WHERE id=?""",
            (
                usuario.email, usuario.password_hash, usuario.nombre, usuario.apellidos,
                usuario.telefono, usuario.direccion, usuario.tipo.value,
                int(usuario.is_active), int(usuario.is_staff), int(usuario.is_superuser),
                usuario.last_login, usuario.intentos_fallidos, usuario.bloqueado_hasta,
                usuario.id,
            ),
        )
        return usuario

    def obtener(self, usuario_id: int) -> Usuario | None:
        fila = self._uno(f"SELECT {CAMPOS_USUARIO} FROM usuarios WHERE id=?", (usuario_id,))
        return _a_usuario(fila) if fila else None

    def obtener_por_email(self, email: str) -> Usuario | None:
        fila = self._uno(
            f"SELECT {CAMPOS_USUARIO} FROM usuarios WHERE lower(email)=?",
            ((email or "").strip().lower(),),
        )
        return _a_usuario(fila) if fila else None

    def listar(self, tipo=None, activos=None, buscar=None) -> list[Usuario]:
        sql = f"SELECT {CAMPOS_USUARIO} FROM usuarios WHERE 1=1"
        params: list = []
        if tipo is not None:
            sql += " AND tipo=?"
            params.append(TipoUsuario.desde(tipo, campo="tipo").value)
        if activos is not None:
            sql += " AND is_active=?"
            params.append(int(activos))
        if buscar:
            sql += " AND (lower(nombre) LIKE ? OR lower(apellidos) LIKE ? OR lower(email) LIKE ?)"
            params += [filtro_like(buscar)] * 3
        sql += " ORDER BY nombre, apellidos"
        return [_a_usuario(f) for f in self._todos(sql, tuple(params))]

    def eliminar(self, usuario_id: int) -> None:
        self._ejecutar("DELETE FROM usuarios WHERE id=?", (usuario_id,))

    def contar(self, tipo=None) -> int:
        if tipo is None:
            return int(self._escalar("SELECT COUNT(*) FROM usuarios WHERE is_active=1") or 0)
        return int(
            self._escalar(
                "SELECT COUNT(*) FROM usuarios WHERE is_active=1 AND tipo=?",
                (TipoUsuario.desde(tipo, campo="tipo").value,),
            )
            or 0
        )


class SqlitePerfilClienteRepository(RepositorioSQLite, PerfilClienteRepository):
    def guardar(self, perfil: PerfilCliente) -> PerfilCliente:
        existente = self.obtener_por_usuario(perfil.usuario_id)
        if existente is None:
            perfil.id = self._insertar(
                "INSERT INTO perfiles_cliente (usuario_id, documento, fecha_actualizacion) VALUES (?,?,?)",
                (perfil.usuario_id, perfil.documento, perfil.fecha_actualizacion),
            )
        else:
            perfil.id = existente.id
            self._ejecutar(
                "UPDATE perfiles_cliente SET documento=?, fecha_actualizacion=? WHERE id=?",
                (perfil.documento, perfil.fecha_actualizacion, perfil.id),
            )
        return perfil

    def obtener_por_usuario(self, usuario_id: int) -> PerfilCliente | None:
        fila = self._uno("SELECT * FROM perfiles_cliente WHERE usuario_id=?", (usuario_id,))
        if not fila:
            return None
        return PerfilCliente(
            id=fila["id"],
            usuario_id=fila["usuario_id"],
            documento=fila["documento"],
            fecha_actualizacion=a_datetime(fila["fecha_actualizacion"]),
        )

    def eliminar_por_usuario(self, usuario_id: int) -> None:
        self._ejecutar("DELETE FROM perfiles_cliente WHERE usuario_id=?", (usuario_id,))


class SqliteEspecialidadRepository(RepositorioSQLite, EspecialidadRepository):
    def _mapear(self, fila: sqlite3.Row) -> Especialidad:
        return Especialidad(
            id=fila["id"],
            codigo=fila["codigo"],
            nombre=fila["nombre"],
            descripcion=fila["descripcion"],
            activa=a_bool(fila["activa"]),
        )

    def crear(self, especialidad: Especialidad) -> Especialidad:
        especialidad.id = self._insertar(
            "INSERT INTO especialidades (codigo, nombre, descripcion, activa) VALUES (?,?,?,?)",
            (especialidad.codigo, especialidad.nombre, especialidad.descripcion, int(especialidad.activa)),
        )
        return especialidad

    def actualizar(self, especialidad: Especialidad) -> Especialidad:
        self._ejecutar(
            "UPDATE especialidades SET codigo=?, nombre=?, descripcion=?, activa=? WHERE id=?",
            (
                especialidad.codigo, especialidad.nombre, especialidad.descripcion,
                int(especialidad.activa), especialidad.id,
            ),
        )
        return especialidad

    def obtener(self, especialidad_id: int) -> Especialidad | None:
        fila = self._uno("SELECT * FROM especialidades WHERE id=?", (especialidad_id,))
        return self._mapear(fila) if fila else None

    def obtener_por_codigo(self, codigo: str) -> Especialidad | None:
        fila = self._uno("SELECT * FROM especialidades WHERE codigo=?", ((codigo or "").strip().lower(),))
        return self._mapear(fila) if fila else None

    def listar(self, solo_activas: bool = False) -> list[Especialidad]:
        sql = "SELECT * FROM especialidades"
        if solo_activas:
            sql += " WHERE activa=1"
        sql += " ORDER BY nombre"
        return [self._mapear(f) for f in self._todos(sql)]

    def eliminar(self, especialidad_id: int) -> None:
        self._ejecutar("DELETE FROM especialidades WHERE id=?", (especialidad_id,))


class SqlitePerfilVeterinarioRepository(RepositorioSQLite, PerfilVeterinarioRepository):
    def _mapear(self, fila: sqlite3.Row) -> PerfilVeterinario:
        return PerfilVeterinario(
            id=fila["id"],
            usuario_id=fila["usuario_id"],
            fecha_contratacion=a_date(fila["fecha_contratacion"]),
            documento=fila["documento"],
            activo=a_bool(fila["activo"]),
            especialidades_ids=self._especialidades(fila["id"]),
        )

    def _especialidades(self, perfil_id: int) -> list[int]:
        filas = self._todos(
            "SELECT especialidad_id FROM veterinario_especialidades WHERE perfil_veterinario_id=?",
            (perfil_id,),
        )
        return [f["especialidad_id"] for f in filas]

    def guardar(self, perfil: PerfilVeterinario) -> PerfilVeterinario:
        existente = self.obtener_por_usuario(perfil.usuario_id)
        if existente is None:
            perfil.id = self._insertar(
                """INSERT INTO perfiles_veterinario
                   (usuario_id, fecha_contratacion, documento, activo) VALUES (?,?,?,?)""",
                (perfil.usuario_id, perfil.fecha_contratacion, perfil.documento, int(perfil.activo)),
            )
        else:
            perfil.id = existente.id
            self._ejecutar(
                """UPDATE perfiles_veterinario
                   SET fecha_contratacion=?, documento=?, activo=? WHERE id=?""",
                (perfil.fecha_contratacion, perfil.documento, int(perfil.activo), perfil.id),
            )
        self._ejecutar(
            "DELETE FROM veterinario_especialidades WHERE perfil_veterinario_id=?", (perfil.id,)
        )
        for especialidad_id in perfil.especialidades_ids:
            self._ejecutar(
                """INSERT OR IGNORE INTO veterinario_especialidades
                   (perfil_veterinario_id, especialidad_id) VALUES (?,?)""",
                (perfil.id, especialidad_id),
            )
        return perfil

    def obtener_por_usuario(self, usuario_id: int) -> PerfilVeterinario | None:
        fila = self._uno("SELECT * FROM perfiles_veterinario WHERE usuario_id=?", (usuario_id,))
        return self._mapear(fila) if fila else None

    def listar(self, solo_activos: bool = False) -> list[PerfilVeterinario]:
        sql = "SELECT * FROM perfiles_veterinario"
        if solo_activos:
            sql += " WHERE activo=1"
        return [self._mapear(f) for f in self._todos(sql)]

    def eliminar_por_usuario(self, usuario_id: int) -> None:
        self._ejecutar("DELETE FROM perfiles_veterinario WHERE usuario_id=?", (usuario_id,))
