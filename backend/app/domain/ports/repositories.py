"""Puertos de salida: contratos de persistencia.

El dominio y la capa de aplicación dependen sólo de estas interfaces; quién las
implementa (SQLite, Postgres, memoria) es irrelevante para ellos.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime

from ..model.cita import Cita, Disponibilidad, EstadoCita, Servicio
from ..model.historial import HistorialMedico
from ..model.inventario import Carrito, ImagenProducto, Pedido, Producto
from ..model.mascota import Especie, Mascota, SolicitudAdopcion
from ..model.sistema import ActividadSistema, CodigoRecuperacion
from ..model.usuario import Especialidad, PerfilCliente, PerfilVeterinario, Usuario
from ..value_objects import (
    CategoriaProducto,
    EstadoAdopcion,
    EstadoSolicitud,
    TipoUsuario,
)


# --------------------------------------------------------------------------
# usuarios
# --------------------------------------------------------------------------
class UsuarioRepository(ABC):
    @abstractmethod
    def crear(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def obtener(self, usuario_id: int) -> Usuario | None: ...

    @abstractmethod
    def obtener_por_email(self, email: str) -> Usuario | None: ...

    @abstractmethod
    def listar(
        self, tipo: TipoUsuario | None = None, activos: bool | None = None, buscar: str | None = None
    ) -> list[Usuario]: ...

    @abstractmethod
    def eliminar(self, usuario_id: int) -> None: ...

    @abstractmethod
    def contar(self, tipo: TipoUsuario | None = None) -> int: ...


class PerfilClienteRepository(ABC):
    @abstractmethod
    def guardar(self, perfil: PerfilCliente) -> PerfilCliente: ...

    @abstractmethod
    def obtener_por_usuario(self, usuario_id: int) -> PerfilCliente | None: ...

    @abstractmethod
    def eliminar_por_usuario(self, usuario_id: int) -> None: ...


class EspecialidadRepository(ABC):
    @abstractmethod
    def crear(self, especialidad: Especialidad) -> Especialidad: ...

    @abstractmethod
    def actualizar(self, especialidad: Especialidad) -> Especialidad: ...

    @abstractmethod
    def obtener(self, especialidad_id: int) -> Especialidad | None: ...

    @abstractmethod
    def obtener_por_codigo(self, codigo: str) -> Especialidad | None: ...

    @abstractmethod
    def listar(self, solo_activas: bool = False) -> list[Especialidad]: ...

    @abstractmethod
    def eliminar(self, especialidad_id: int) -> None: ...


class PerfilVeterinarioRepository(ABC):
    @abstractmethod
    def guardar(self, perfil: PerfilVeterinario) -> PerfilVeterinario: ...

    @abstractmethod
    def obtener_por_usuario(self, usuario_id: int) -> PerfilVeterinario | None: ...

    @abstractmethod
    def listar(self, solo_activos: bool = False) -> list[PerfilVeterinario]: ...

    @abstractmethod
    def eliminar_por_usuario(self, usuario_id: int) -> None: ...


# --------------------------------------------------------------------------
# mascotas
# --------------------------------------------------------------------------
class EspecieRepository(ABC):
    @abstractmethod
    def crear(self, especie: Especie) -> Especie: ...

    @abstractmethod
    def actualizar(self, especie: Especie) -> Especie: ...

    @abstractmethod
    def obtener(self, especie_id: int) -> Especie | None: ...

    @abstractmethod
    def obtener_por_nombre(self, nombre: str) -> Especie | None: ...

    @abstractmethod
    def listar(self) -> list[Especie]: ...

    @abstractmethod
    def eliminar(self, especie_id: int) -> None: ...


class MascotaRepository(ABC):
    @abstractmethod
    def crear(self, mascota: Mascota) -> Mascota: ...

    @abstractmethod
    def actualizar(self, mascota: Mascota) -> Mascota: ...

    @abstractmethod
    def obtener(self, mascota_id: int) -> Mascota | None: ...

    @abstractmethod
    def listar(
        self,
        cliente_id: int | None = None,
        especie_id: int | None = None,
        estado_adopcion: EstadoAdopcion | None = None,
        activo: bool | None = True,
        buscar: str | None = None,
    ) -> list[Mascota]: ...

    @abstractmethod
    def eliminar(self, mascota_id: int) -> None: ...

    @abstractmethod
    def contar(self, activo: bool | None = True) -> int: ...


class SolicitudAdopcionRepository(ABC):
    @abstractmethod
    def crear(self, solicitud: SolicitudAdopcion) -> SolicitudAdopcion: ...

    @abstractmethod
    def actualizar(self, solicitud: SolicitudAdopcion) -> SolicitudAdopcion: ...

    @abstractmethod
    def obtener(self, solicitud_id: int) -> SolicitudAdopcion | None: ...

    @abstractmethod
    def listar(
        self,
        cliente_id: int | None = None,
        mascota_id: int | None = None,
        estado: EstadoSolicitud | None = None,
    ) -> list[SolicitudAdopcion]: ...

    @abstractmethod
    def existe_pendiente(self, mascota_id: int, cliente_id: int) -> bool: ...

    @abstractmethod
    def eliminar(self, solicitud_id: int) -> None: ...


# --------------------------------------------------------------------------
# citas
# --------------------------------------------------------------------------
class EstadoCitaRepository(ABC):
    @abstractmethod
    def crear(self, estado: EstadoCita) -> EstadoCita: ...

    @abstractmethod
    def actualizar(self, estado: EstadoCita) -> EstadoCita: ...

    @abstractmethod
    def obtener(self, estado_id: int) -> EstadoCita | None: ...

    @abstractmethod
    def obtener_por_nombre(self, nombre: str) -> EstadoCita | None: ...

    @abstractmethod
    def listar(self) -> list[EstadoCita]: ...

    @abstractmethod
    def eliminar(self, estado_id: int) -> None: ...


class ServicioRepository(ABC):
    @abstractmethod
    def crear(self, servicio: Servicio) -> Servicio: ...

    @abstractmethod
    def actualizar(self, servicio: Servicio) -> Servicio: ...

    @abstractmethod
    def obtener(self, servicio_id: int) -> Servicio | None: ...

    @abstractmethod
    def listar(self, solo_activos: bool = False, veterinario_id: int | None = None) -> list[Servicio]: ...

    @abstractmethod
    def eliminar(self, servicio_id: int) -> None: ...


class DisponibilidadRepository(ABC):
    @abstractmethod
    def crear(self, disponibilidad: Disponibilidad) -> Disponibilidad: ...

    @abstractmethod
    def actualizar(self, disponibilidad: Disponibilidad) -> Disponibilidad: ...

    @abstractmethod
    def obtener(self, disponibilidad_id: int) -> Disponibilidad | None: ...

    @abstractmethod
    def listar(self, veterinario_id: int | None = None, dia_semana: int | None = None) -> list[Disponibilidad]: ...

    @abstractmethod
    def eliminar(self, disponibilidad_id: int) -> None: ...


class CitaRepository(ABC):
    @abstractmethod
    def crear(self, cita: Cita) -> Cita: ...

    @abstractmethod
    def actualizar(self, cita: Cita) -> Cita: ...

    @abstractmethod
    def obtener(self, cita_id: int) -> Cita | None: ...

    @abstractmethod
    def listar(
        self,
        mascota_id: int | None = None,
        veterinario_id: int | None = None,
        cliente_id: int | None = None,
        estado_id: int | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> list[Cita]: ...

    @abstractmethod
    def listar_por_veterinario_y_dia(self, veterinario_id: int, dia: date) -> list[Cita]: ...

    @abstractmethod
    def eliminar(self, cita_id: int) -> None: ...

    @abstractmethod
    def contar(self, dia: date | None = None, estado_id: int | None = None) -> int: ...


# --------------------------------------------------------------------------
# historiales médicos
# --------------------------------------------------------------------------
class HistorialMedicoRepository(ABC):
    @abstractmethod
    def crear(self, historial: HistorialMedico) -> HistorialMedico: ...

    @abstractmethod
    def actualizar(self, historial: HistorialMedico) -> HistorialMedico: ...

    @abstractmethod
    def obtener(self, historial_id: int) -> HistorialMedico | None: ...

    @abstractmethod
    def obtener_por_cita(self, cita_id: int) -> HistorialMedico | None: ...

    @abstractmethod
    def listar(
        self,
        mascota_id: int | None = None,
        veterinario_id: int | None = None,
        cliente_id: int | None = None,
    ) -> list[HistorialMedico]: ...

    @abstractmethod
    def eliminar(self, historial_id: int) -> None: ...


# --------------------------------------------------------------------------
# inventario / tienda
# --------------------------------------------------------------------------
class ProductoRepository(ABC):
    @abstractmethod
    def crear(self, producto: Producto) -> Producto: ...

    @abstractmethod
    def actualizar(self, producto: Producto) -> Producto: ...

    @abstractmethod
    def obtener(self, producto_id: int) -> Producto | None: ...

    @abstractmethod
    def obtener_por_sku(self, sku: str) -> Producto | None: ...

    @abstractmethod
    def existe_sku(self, sku: str, excluir_id: int | None = None) -> bool: ...

    @abstractmethod
    def listar(
        self,
        categoria: CategoriaProducto | None = None,
        buscar: str | None = None,
        solo_activos: bool = True,
        solo_online: bool | None = None,
        stock_bajo: bool = False,
    ) -> list[Producto]: ...

    @abstractmethod
    def eliminar(self, producto_id: int) -> None: ...

    @abstractmethod
    def contar(self, solo_activos: bool = True) -> int: ...


class ImagenProductoRepository(ABC):
    @abstractmethod
    def crear(self, imagen: ImagenProducto) -> ImagenProducto: ...

    @abstractmethod
    def obtener(self, imagen_id: int, incluir_binario: bool = True) -> ImagenProducto | None: ...

    @abstractmethod
    def listar_por_producto(self, producto_id: int) -> list[ImagenProducto]: ...

    @abstractmethod
    def eliminar(self, imagen_id: int) -> None: ...


class CarritoRepository(ABC):
    @abstractmethod
    def obtener_por_usuario(self, usuario_id: int) -> Carrito | None: ...

    @abstractmethod
    def guardar(self, carrito: Carrito) -> Carrito:
        """Persiste el agregado completo (carrito + items)."""

    @abstractmethod
    def eliminar_por_usuario(self, usuario_id: int) -> None: ...


class PedidoRepository(ABC):
    @abstractmethod
    def crear(self, pedido: Pedido) -> Pedido: ...

    @abstractmethod
    def obtener(self, pedido_id: int) -> Pedido | None: ...

    @abstractmethod
    def listar(self, usuario_id: int | None = None) -> list[Pedido]: ...

    @abstractmethod
    def total_ingresos(self, desde: datetime | None = None) -> float: ...


# --------------------------------------------------------------------------
# sistema
# --------------------------------------------------------------------------
class ActividadSistemaRepository(ABC):
    @abstractmethod
    def registrar(self, actividad: ActividadSistema) -> ActividadSistema: ...

    @abstractmethod
    def listar(self, limite: int = 50, tipo: str | None = None) -> list[ActividadSistema]: ...


class CodigoRecuperacionRepository(ABC):
    @abstractmethod
    def crear(self, codigo: CodigoRecuperacion) -> CodigoRecuperacion: ...

    @abstractmethod
    def actualizar(self, codigo: CodigoRecuperacion) -> CodigoRecuperacion: ...

    @abstractmethod
    def obtener_activo(self, usuario_id: int) -> CodigoRecuperacion | None:
        """Último código activo del usuario, sea cual sea su valor."""

    @abstractmethod
    def desactivar_todos(self, usuario_id: int) -> None: ...
