"""Casos de uso de usuarios, perfiles y especialidades."""
from __future__ import annotations

from ...domain.errors import ConflictError, NotFoundError, ValidationError
from ...domain.model.usuario import Especialidad, PerfilCliente, PerfilVeterinario, Usuario
from ...domain.ports.repositories import (
    EspecialidadRepository,
    PerfilClienteRepository,
    PerfilVeterinarioRepository,
    UsuarioRepository,
)
from ...domain.ports.services import Clock
from ...domain.value_objects import TipoUsuario
from ..read_models import UsuarioVista


class ConsultarUsuarios:
    def __init__(
        self,
        usuarios: UsuarioRepository,
        perfiles_cliente: PerfilClienteRepository,
        perfiles_veterinario: PerfilVeterinarioRepository,
        especialidades: EspecialidadRepository,
    ):
        self.usuarios = usuarios
        self.perfiles_cliente = perfiles_cliente
        self.perfiles_veterinario = perfiles_veterinario
        self.especialidades = especialidades

    def listar(
        self, tipo: str | None = None, activos: bool | None = None, buscar: str | None = None
    ) -> list[UsuarioVista]:
        tipo_enum = TipoUsuario.desde(tipo, campo="tipo") if tipo else None
        return [self._componer(u) for u in self.usuarios.listar(tipo_enum, activos, buscar)]

    def obtener(self, usuario_id: int) -> UsuarioVista:
        usuario = self.usuarios.obtener(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario", usuario_id)
        return self._componer(usuario)

    def _componer(self, usuario: Usuario) -> UsuarioVista:
        vista = UsuarioVista(usuario=usuario)
        if usuario.es_cliente:
            vista.perfil_cliente = self.perfiles_cliente.obtener_por_usuario(usuario.id)
        elif usuario.es_veterinario:
            perfil = self.perfiles_veterinario.obtener_por_usuario(usuario.id)
            vista.perfil_veterinario = perfil
            if perfil and perfil.especialidades_ids:
                catalogo = {e.id: e.nombre for e in self.especialidades.listar()}
                vista.especialidades = [
                    catalogo[i] for i in perfil.especialidades_ids if i in catalogo
                ]
        return vista


class ActualizarUsuario:
    def __init__(
        self,
        usuarios: UsuarioRepository,
        perfiles_cliente: PerfilClienteRepository,
        perfiles_veterinario: PerfilVeterinarioRepository,
        reloj: Clock,
    ):
        self.usuarios = usuarios
        self.perfiles_cliente = perfiles_cliente
        self.perfiles_veterinario = perfiles_veterinario
        self.reloj = reloj

    def ejecutar(self, usuario_id: int, cambios: dict) -> Usuario:
        usuario = self.usuarios.obtener(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario", usuario_id)

        if "email" in cambios and cambios["email"]:
            nuevo = str(cambios["email"]).strip().lower()
            existente = self.usuarios.obtener_por_email(nuevo)
            if existente and existente.id != usuario.id:
                raise ConflictError("Ese correo ya está en uso por otra cuenta")

        actualizado = Usuario(
            id=usuario.id,
            email=cambios.get("email") or usuario.email,
            nombre=cambios.get("nombre") or usuario.nombre,
            apellidos=cambios.get("apellidos") or usuario.apellidos,
            telefono=cambios.get("telefono", usuario.telefono),
            direccion=cambios.get("direccion", usuario.direccion),
            tipo=cambios.get("tipo") or usuario.tipo,
            password_hash=usuario.password_hash,
            is_active=cambios.get("is_active", usuario.is_active),
            is_staff=usuario.is_staff,
            is_superuser=usuario.is_superuser,
            date_joined=usuario.date_joined,
            last_login=usuario.last_login,
        )
        self.usuarios.actualizar(actualizado)

        documento = cambios.get("documento")
        if documento is not None:
            if actualizado.es_cliente:
                perfil = self.perfiles_cliente.obtener_por_usuario(usuario.id) or PerfilCliente(
                    usuario_id=usuario.id
                )
                perfil.documento = documento
                perfil.fecha_actualizacion = self.reloj.ahora()
                self.perfiles_cliente.guardar(perfil)
            elif actualizado.es_veterinario:
                perfil = self.perfiles_veterinario.obtener_por_usuario(usuario.id) or PerfilVeterinario(
                    usuario_id=usuario.id, fecha_contratacion=self.reloj.hoy()
                )
                perfil.documento = documento
                self.perfiles_veterinario.guardar(perfil)
        return actualizado


class DesactivarUsuario:
    """Baja lógica; coherente con cómo Django trataba a los usuarios."""

    def __init__(self, usuarios: UsuarioRepository):
        self.usuarios = usuarios

    def ejecutar(self, usuario_id: int) -> Usuario:
        usuario = self.usuarios.obtener(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario", usuario_id)
        usuario.desactivar()
        return self.usuarios.actualizar(usuario)


class GestionarPerfilVeterinario:
    def __init__(
        self,
        usuarios: UsuarioRepository,
        perfiles: PerfilVeterinarioRepository,
        especialidades: EspecialidadRepository,
        reloj: Clock,
    ):
        self.usuarios = usuarios
        self.perfiles = perfiles
        self.especialidades = especialidades
        self.reloj = reloj

    def guardar(
        self,
        usuario_id: int,
        documento: str | None = None,
        activo: bool | None = None,
        especialidades_ids: list[int] | None = None,
        fecha_contratacion=None,
    ) -> PerfilVeterinario:
        usuario = self.usuarios.obtener(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario", usuario_id)
        if not usuario.es_veterinario:
            raise ValidationError("El usuario no es de tipo veterinario", "usuario_id")

        perfil = self.perfiles.obtener_por_usuario(usuario_id) or PerfilVeterinario(
            usuario_id=usuario_id, fecha_contratacion=self.reloj.hoy()
        )
        if documento is not None:
            perfil.documento = documento
        if activo is not None:
            perfil.activo = bool(activo)
        if fecha_contratacion is not None:
            perfil.fecha_contratacion = fecha_contratacion
        if especialidades_ids is not None:
            conocidas = {e.id for e in self.especialidades.listar()}
            desconocidas = [i for i in especialidades_ids if i not in conocidas]
            if desconocidas:
                raise NotFoundError("Especialidad", desconocidas[0])
            perfil.asignar_especialidades(especialidades_ids)
        return self.perfiles.guardar(perfil)


class GestionarPerfilCliente:
    def __init__(
        self, usuarios: UsuarioRepository, perfiles: PerfilClienteRepository, reloj: Clock
    ):
        self.usuarios = usuarios
        self.perfiles = perfiles
        self.reloj = reloj

    def guardar(self, usuario_id: int, documento: str | None = None) -> PerfilCliente:
        usuario = self.usuarios.obtener(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario", usuario_id)
        perfil = self.perfiles.obtener_por_usuario(usuario_id) or PerfilCliente(usuario_id=usuario_id)
        perfil.documento = documento
        perfil.fecha_actualizacion = self.reloj.ahora()
        return self.perfiles.guardar(perfil)


class GestionarEspecialidades:
    def __init__(self, especialidades: EspecialidadRepository):
        self.especialidades = especialidades

    def listar(self, solo_activas: bool = False) -> list[Especialidad]:
        return self.especialidades.listar(solo_activas)

    def obtener(self, especialidad_id: int) -> Especialidad:
        especialidad = self.especialidades.obtener(especialidad_id)
        if especialidad is None:
            raise NotFoundError("Especialidad", especialidad_id)
        return especialidad

    def crear(
        self, codigo: str, nombre: str, descripcion: str | None = None, activa: bool = True
    ) -> Especialidad:
        if self.especialidades.obtener_por_codigo(codigo):
            raise ConflictError(f"Ya existe una especialidad con el código '{codigo}'")
        return self.especialidades.crear(
            Especialidad(codigo=codigo, nombre=nombre, descripcion=descripcion, activa=activa)
        )

    def actualizar(self, especialidad_id: int, cambios: dict) -> Especialidad:
        actual = self.obtener(especialidad_id)
        nueva = Especialidad(
            id=actual.id,
            codigo=cambios.get("codigo") or actual.codigo,
            nombre=cambios.get("nombre") or actual.nombre,
            descripcion=cambios.get("descripcion", actual.descripcion),
            activa=cambios.get("activa", actual.activa),
        )
        duplicada = self.especialidades.obtener_por_codigo(nueva.codigo)
        if duplicada and duplicada.id != actual.id:
            raise ConflictError(f"Ya existe una especialidad con el código '{nueva.codigo}'")
        return self.especialidades.actualizar(nueva)

    def eliminar(self, especialidad_id: int) -> None:
        self.obtener(especialidad_id)
        self.especialidades.eliminar(especialidad_id)
