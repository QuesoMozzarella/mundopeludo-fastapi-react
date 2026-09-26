"""Casos de uso de especies y mascotas."""
from __future__ import annotations

from dataclasses import dataclass

from ...domain.errors import ConflictError, NotFoundError, ValidationError
from ...domain.model.mascota import Especie, Mascota
from ...domain.ports.repositories import (
    EspecieRepository,
    MascotaRepository,
    UsuarioRepository,
)
from ...domain.ports.services import Clock
from ...domain.value_objects import EstadoAdopcion
from ..cambios import SIN_CAMBIO, Cambio, nuevo, nuevo_o_vacio
from ..read_models import MascotaVista


class GestionarEspecies:
    def __init__(self, especies: EspecieRepository, mascotas: MascotaRepository):
        self.especies = especies
        self.mascotas = mascotas

    def listar(self) -> list[Especie]:
        return self.especies.listar()

    def obtener(self, especie_id: int) -> Especie:
        especie = self.especies.obtener(especie_id)
        if especie is None:
            raise NotFoundError("Especie", especie_id)
        return especie

    def crear(self, nombre: str) -> Especie:
        if self.especies.obtener_por_nombre(nombre):
            raise ConflictError(f"La especie '{nombre}' ya existe")
        return self.especies.crear(Especie(nombre=nombre))

    def actualizar(self, especie_id: int, nombre: str) -> Especie:
        especie = self.obtener(especie_id)
        duplicada = self.especies.obtener_por_nombre(nombre)
        if duplicada and duplicada.id != especie.id:
            raise ConflictError(f"La especie '{nombre}' ya existe")
        return self.especies.actualizar(Especie(id=especie.id, nombre=nombre))

    def eliminar(self, especie_id: int) -> None:
        self.obtener(especie_id)
        if self.mascotas.listar(especie_id=especie_id, activo=None):
            raise ConflictError("No se puede eliminar: hay mascotas registradas con esa especie")
        self.especies.eliminar(especie_id)


@dataclass(frozen=True, kw_only=True)
class RegistrarMascotaCmd:
    especie_id: int
    nombre: str
    sexo: str
    color: str
    cliente_id: int | None = None
    raza: str | None = None
    edad_anos: int = 1
    peso: float = 1.0
    esta_esterilizado: bool = False
    estado_adopcion: str = EstadoAdopcion.NORMAL.value


@dataclass(frozen=True, kw_only=True)
class ActualizarMascotaCmd:
    especie_id: Cambio[int | None] = SIN_CAMBIO
    nombre: Cambio[str | None] = SIN_CAMBIO
    sexo: Cambio[str | None] = SIN_CAMBIO
    color: Cambio[str | None] = SIN_CAMBIO
    cliente_id: Cambio[int | None] = SIN_CAMBIO
    raza: Cambio[str | None] = SIN_CAMBIO
    edad_anos: Cambio[int | None] = SIN_CAMBIO
    peso: Cambio[float | None] = SIN_CAMBIO
    esta_esterilizado: Cambio[bool | None] = SIN_CAMBIO
    estado_adopcion: Cambio[str | None] = SIN_CAMBIO
    activo: Cambio[bool | None] = SIN_CAMBIO


class ConsultarMascotas:
    def __init__(
        self,
        mascotas: MascotaRepository,
        especies: EspecieRepository,
        usuarios: UsuarioRepository,
    ):
        self.mascotas = mascotas
        self.especies = especies
        self.usuarios = usuarios

    def listar(
        self,
        cliente_id: int | None = None,
        especie_id: int | None = None,
        estado_adopcion: str | None = None,
        activo: bool | None = True,
        buscar: str | None = None,
    ) -> list[MascotaVista]:
        estado = (
            EstadoAdopcion.desde(estado_adopcion, campo="estado_adopcion")
            if estado_adopcion
            else None
        )
        encontradas = self.mascotas.listar(cliente_id, especie_id, estado, activo, buscar)
        return self._componer_muchas(encontradas)

    def obtener(self, mascota_id: int) -> MascotaVista:
        mascota = self.mascotas.obtener(mascota_id)
        if mascota is None:
            raise NotFoundError("Mascota", mascota_id)
        return self._componer_muchas([mascota])[0]

    def _componer_muchas(self, mascotas: list[Mascota]) -> list[MascotaVista]:
        if not mascotas:
            return []
        # Dos consultas de catálogo en vez de N+1 por mascota.
        especies = {e.id: e.nombre for e in self.especies.listar()}
        clientes_ids = {m.cliente_id for m in mascotas if m.cliente_id}
        clientes = {}
        for cliente_id in clientes_ids:
            usuario = self.usuarios.obtener(cliente_id)
            if usuario:
                clientes[cliente_id] = usuario
        vistas = []
        for mascota in mascotas:
            cliente = clientes.get(mascota.cliente_id)
            vistas.append(
                MascotaVista(
                    mascota=mascota,
                    especie_nombre=especies.get(mascota.especie_id, ""),
                    cliente_nombre=cliente.nombre_completo if cliente else None,
                    cliente_email=cliente.email if cliente else None,
                )
            )
        return vistas


class RegistrarMascota:
    def __init__(
        self,
        mascotas: MascotaRepository,
        especies: EspecieRepository,
        usuarios: UsuarioRepository,
        reloj: Clock,
    ):
        self.mascotas = mascotas
        self.especies = especies
        self.usuarios = usuarios
        self.reloj = reloj

    def ejecutar(self, cmd: RegistrarMascotaCmd) -> Mascota:
        especie_id = cmd.especie_id
        if self.especies.obtener(especie_id) is None:
            raise NotFoundError("Especie", especie_id)

        cliente_id = cmd.cliente_id
        if cliente_id is not None:
            cliente = self.usuarios.obtener(cliente_id)
            if cliente is None:
                raise NotFoundError("Usuario", cliente_id)
            if not cliente.es_cliente:
                raise ValidationError("La mascota sólo puede asignarse a un cliente", "cliente_id")

        mascota = Mascota(
            cliente_id=cliente_id,
            especie_id=especie_id,
            nombre=cmd.nombre,
            raza=cmd.raza,
            edad_anos=cmd.edad_anos,
            sexo=cmd.sexo,
            color=cmd.color,
            peso=cmd.peso,
            esta_esterilizado=cmd.esta_esterilizado,
            estado_adopcion=cmd.estado_adopcion,
            fecha_registro=self.reloj.hoy(),
        )
        return self.mascotas.crear(mascota)


class ActualizarMascota:
    def __init__(
        self,
        mascotas: MascotaRepository,
        especies: EspecieRepository,
        usuarios: UsuarioRepository,
    ):
        self.mascotas = mascotas
        self.especies = especies
        self.usuarios = usuarios

    def ejecutar(self, mascota_id: int, cmd: ActualizarMascotaCmd) -> Mascota:
        actual = self.mascotas.obtener(mascota_id)
        if actual is None:
            raise NotFoundError("Mascota", mascota_id)

        especie_id = nuevo(cmd.especie_id, actual.especie_id)
        if especie_id != actual.especie_id and self.especies.obtener(especie_id) is None:
            raise NotFoundError("Especie", especie_id)

        # `null` en cliente_id deja la mascota sin tutor (p. ej. para adopción).
        cliente_id = nuevo_o_vacio(cmd.cliente_id, actual.cliente_id)
        if cliente_id is not None and cliente_id != actual.cliente_id:
            cliente = self.usuarios.obtener(cliente_id)
            if cliente is None:
                raise NotFoundError("Usuario", cliente_id)
            if not cliente.es_cliente:
                raise ValidationError("La mascota sólo puede asignarse a un cliente", "cliente_id")

        # Reconstruir la entidad revalida todas las invariantes del dominio.
        actualizada = Mascota(
            id=actual.id,
            cliente_id=cliente_id,
            especie_id=especie_id,
            nombre=nuevo(cmd.nombre, actual.nombre),
            raza=nuevo_o_vacio(cmd.raza, actual.raza),
            edad_anos=nuevo(cmd.edad_anos, actual.edad_anos),
            sexo=nuevo(cmd.sexo, actual.sexo),
            color=nuevo(cmd.color, actual.color),
            peso=nuevo(cmd.peso, actual.peso),
            esta_esterilizado=nuevo(cmd.esta_esterilizado, actual.esta_esterilizado),
            activo=nuevo(cmd.activo, actual.activo),
            fecha_registro=actual.fecha_registro,
            estado_adopcion=nuevo(cmd.estado_adopcion, actual.estado_adopcion),
        )
        return self.mascotas.actualizar(actualizada)


class DarDeBajaMascota:
    """Baja lógica (`activo = False`), como el campo homónimo en Django."""

    def __init__(self, mascotas: MascotaRepository):
        self.mascotas = mascotas

    def ejecutar(self, mascota_id: int) -> Mascota:
        mascota = self.mascotas.obtener(mascota_id)
        if mascota is None:
            raise NotFoundError("Mascota", mascota_id)
        mascota.desactivar()
        return self.mascotas.actualizar(mascota)
