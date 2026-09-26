"""Contexto `inventario` — adaptación de `legacy_django/inventario/models.py`.

Modelos Django originales: Producto, ImagenProducto, Carrito, CarritoItem.
Pedido/PedidoItem no existían en Django: se conservan porque el checkout de la
API actual los necesita (ver README, sección "Extensiones").
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from ..errors import BusinessRuleError, ValidationError
from ..value_objects import CategoriaProducto, TipoAnimal, UnidadMedida, dinero

PREFIJOS_SKU = {
    CategoriaProducto.MEDICAMENTO: "MED",
    CategoriaProducto.ALIMENTO: "ALI",
    CategoriaProducto.ACCESORIO: "ACC",
    CategoriaProducto.JUGUETE: "JUG",
    CategoriaProducto.HIGIENE: "HIG",
    CategoriaProducto.SUPLEMENTO: "SUP",
    CategoriaProducto.ANTIPULGAS: "ANT",
    CategoriaProducto.DESPARASITANTE: "DES",
}

DIAS_PARA_VENCER = 30


def slugify(texto: str) -> str:
    """Equivalente mínimo a `django.utils.text.slugify`."""
    normalizado = unicodedata.normalize("NFKD", texto or "")
    ascii_txt = normalizado.encode("ascii", "ignore").decode("ascii")
    ascii_txt = re.sub(r"[^\w\s-]", "", ascii_txt).strip().lower()
    return re.sub(r"[-\s]+", "-", ascii_txt)


def _entero(valor, campo: str, minimo: int = 0) -> int:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ValidationError(f"'{campo}' debe ser un número entero", campo) from None
    if numero < minimo:
        raise ValidationError(f"'{campo}' no puede ser menor que {minimo}", campo)
    return numero


@dataclass
class Producto:
    """Producto del inventario y de la tienda online."""

    nombre: str
    categoria: CategoriaProducto
    precio: Decimal
    descripcion: str | None = None
    marca: str | None = None
    descuento_porcentaje: Decimal = Decimal("0.00")
    stock: int = 0
    stock_minimo: int = 5
    total_vendidos: int = 0
    tipo_animal: TipoAnimal = TipoAnimal.TODOS
    unidad_medida: UnidadMedida = UnidadMedida.UNIDAD
    peso: Decimal | None = None
    lote: str | None = None
    fecha_vencimiento: date | None = None
    sku: str = ""
    disponible_online: bool = True
    palabras_clave: str | None = None
    activo: bool = True
    fecha_creacion: datetime = field(kw_only=True)
    fecha_actualizacion: datetime = field(kw_only=True)
    id: int | None = None

    def __post_init__(self) -> None:
        nombre = (self.nombre or "").strip()
        if len(nombre) < 2:
            raise ValidationError("El nombre del producto debe tener al menos 2 caracteres", "nombre")
        if len(nombre) > 200:
            raise ValidationError("El nombre del producto no puede superar 200 caracteres", "nombre")
        self.nombre = nombre
        self.categoria = CategoriaProducto.desde(self.categoria, campo="categoria")
        self.tipo_animal = TipoAnimal.desde(
            self.tipo_animal, campo="tipo_animal", por_defecto=TipoAnimal.TODOS
        )
        self.unidad_medida = UnidadMedida.desde(
            self.unidad_medida, campo="unidad_medida", por_defecto=UnidadMedida.UNIDAD
        )
        self.descripcion = (self.descripcion or "").strip()[:255] or None
        self.marca = (self.marca or "").strip()[:100] or None
        self.lote = (self.lote or "").strip()[:50] or None
        self.palabras_clave = (self.palabras_clave or "").strip()[:500] or None

        self.precio = dinero(self.precio, campo="precio")
        if self.precio < 0:
            raise ValidationError("El precio no puede ser negativo", "precio")
        self.descuento_porcentaje = dinero(
            self.descuento_porcentaje or 0, campo="descuento_porcentaje"
        )
        if not (Decimal("0") <= self.descuento_porcentaje <= Decimal("100")):
            raise ValidationError("El descuento debe estar entre 0 y 100", "descuento_porcentaje")

        self.stock = _entero(self.stock, "stock", minimo=0)
        self.stock_minimo = _entero(self.stock_minimo, "stock_minimo", minimo=0)
        self.total_vendidos = _entero(self.total_vendidos, "total_vendidos", minimo=0)

        if self.peso is not None and self.peso != "":
            self.peso = Decimal(str(self.peso)).quantize(Decimal("0.001"))
            if self.peso < 0:
                raise ValidationError("El peso no puede ser negativo", "peso")
        else:
            self.peso = None

        if isinstance(self.fecha_vencimiento, datetime):
            self.fecha_vencimiento = self.fecha_vencimiento.date()

    # --- propiedades calculadas del modelo Django ---
    @property
    def precio_final(self) -> Decimal:
        """Precio con el descuento aplicado (si corresponde)."""
        if self.descuento_porcentaje and self.descuento_porcentaje > 0:
            descuento = (self.precio * self.descuento_porcentaje) / Decimal("100")
            return dinero(self.precio - descuento)
        return self.precio

    @property
    def stock_disponible(self) -> bool:
        return self.stock > 0

    @property
    def stock_bajo(self) -> bool:
        return self.stock <= self.stock_minimo

    # `hoy` llega de fuera (el puerto Clock): el dominio no lee el reloj.
    def proximo_a_vencer(self, hoy: date) -> bool:
        if not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento <= hoy + timedelta(days=DIAS_PARA_VENCER)

    def vencido(self, hoy: date) -> bool:
        if not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento < hoy

    # --- comportamiento ---
    def sirve_para(self, animal: TipoAnimal) -> bool:
        """Un producto para `ambos` o `todos` también sirve para cada animal."""
        if animal is TipoAnimal.TODOS:
            return True
        return self.tipo_animal in (animal, TipoAnimal.AMBOS, TipoAnimal.TODOS)

    def sku_base(self) -> str:
        """Base del SKU (`PREFIJO-ABREV`), como el `_generate_sku()` original."""
        prefijo = PREFIJOS_SKU.get(self.categoria, "PRD")
        palabras = [p for p in slugify(self.nombre).upper().split("-") if p]
        codigo = "".join(p[:3] for p in palabras[:2]) or "GEN"
        return f"{prefijo}-{codigo}"

    def descontar_stock(self, cantidad: int, ahora: datetime) -> None:
        cantidad = _entero(cantidad, "cantidad", minimo=1)
        if cantidad > self.stock:
            raise BusinessRuleError(
                f"Stock insuficiente para {self.nombre}: quedan {self.stock} unidades"
            )
        self.stock -= cantidad
        self.total_vendidos += cantidad
        self.fecha_actualizacion = ahora

    def reponer_stock(self, cantidad: int, ahora: datetime) -> None:
        self.stock += _entero(cantidad, "cantidad", minimo=1)
        self.fecha_actualizacion = ahora

    def desactivar(self, ahora: datetime) -> None:
        self.activo = False
        self.disponible_online = False
        self.fecha_actualizacion = ahora


@dataclass
class ImagenProducto:
    """`ImagenProducto`: el binario vive en la base, igual que el `BinaryField`."""

    producto_id: int
    imagen_data: bytes | None = None
    nombre_archivo: str | None = None
    tipo_contenido: str = "image/jpeg"
    fecha_subida: datetime = field(kw_only=True)
    id: int | None = None

    def __post_init__(self) -> None:
        self.nombre_archivo = (self.nombre_archivo or "").strip()[:255] or None
        self.tipo_contenido = (self.tipo_contenido or "image/jpeg").strip()[:100]
        if self.imagen_data is not None:
            if not isinstance(self.imagen_data, (bytes, bytearray)):
                raise ValidationError("imagen_data debe ser binario", "imagen_data")
            self.imagen_data = bytes(self.imagen_data)

    @property
    def tamano_bytes(self) -> int:
        return len(self.imagen_data or b"")


@dataclass
class CarritoItem:
    """`CarritoItem`: línea del carrito con el precio congelado al agregarlo."""

    producto_id: int
    cantidad: int = 1
    precio_unitario: Decimal = Decimal("0.00")
    carrito_id: int | None = None
    fecha_agregado: datetime = field(kw_only=True)
    id: int | None = None

    def __post_init__(self) -> None:
        self.cantidad = _entero(self.cantidad, "cantidad", minimo=1)
        self.precio_unitario = dinero(self.precio_unitario, campo="precio_unitario")

    @property
    def subtotal(self) -> Decimal:
        return dinero(self.precio_unitario * self.cantidad)


@dataclass
class Carrito:
    """`Carrito`: uno por usuario, raíz del agregado de sus items."""

    usuario_id: int
    items: list[CarritoItem] = field(default_factory=list)
    fecha_creacion: datetime = field(kw_only=True)
    fecha_actualizacion: datetime = field(kw_only=True)
    id: int | None = None

    @property
    def total_items(self) -> int:
        return sum(item.cantidad for item in self.items)

    @property
    def subtotal(self) -> Decimal:
        return dinero(sum((item.subtotal for item in self.items), Decimal("0")))

    @property
    def total(self) -> Decimal:
        return self.subtotal

    def buscar_item(self, producto_id: int) -> CarritoItem | None:
        return next((i for i in self.items if i.producto_id == producto_id), None)

    def agregar_producto(self, producto: Producto, cantidad: int, ahora: datetime) -> CarritoItem:
        """Agrega o acumula, refrescando el precio como hacía Django."""
        cantidad = _entero(cantidad, "cantidad", minimo=1)
        item = self.buscar_item(producto.id)
        if item is None:
            item = CarritoItem(
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=producto.precio_final,
                carrito_id=self.id,
                fecha_agregado=ahora,
            )
            self.items.append(item)
        else:
            item.cantidad += cantidad
            item.precio_unitario = producto.precio_final
        self.fecha_actualizacion = ahora
        return item

    def actualizar_cantidad(self, producto_id: int, cantidad: int, ahora: datetime) -> bool:
        item = self.buscar_item(producto_id)
        if item is None:
            return False
        if cantidad <= 0:
            self.items.remove(item)
        else:
            item.cantidad = _entero(cantidad, "cantidad", minimo=1)
        self.fecha_actualizacion = ahora
        return True

    def eliminar_producto(self, producto_id: int, ahora: datetime) -> bool:
        item = self.buscar_item(producto_id)
        if item is None:
            return False
        self.items.remove(item)
        self.fecha_actualizacion = ahora
        return True

    def vaciar(self, ahora: datetime) -> None:
        self.items.clear()
        self.fecha_actualizacion = ahora


@dataclass
class PedidoItem:
    """Extensión (no existía en Django): línea histórica de un pedido."""

    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: Decimal
    pedido_id: int | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.cantidad = _entero(self.cantidad, "cantidad", minimo=1)
        self.precio_unitario = dinero(self.precio_unitario, campo="precio_unitario")

    @property
    def subtotal(self) -> Decimal:
        return dinero(self.precio_unitario * self.cantidad)


@dataclass
class Pedido:
    """Extensión (no existía en Django): resultado del checkout de la tienda."""

    usuario_id: int
    total: Decimal = Decimal("0.00")
    metodo_pago: str = "efectivo"
    direccion: str | None = None
    estado: str = "Completado"
    fecha: datetime = field(kw_only=True)
    items: list[PedidoItem] = field(default_factory=list)
    id: int | None = None

    def __post_init__(self) -> None:
        self.metodo_pago = (self.metodo_pago or "").strip() or "efectivo"
        self.direccion = (self.direccion or "").strip() or None
        self.estado = (self.estado or "Completado").strip()
        self.total = dinero(self.total, campo="total")

    def recalcular_total(self) -> Decimal:
        self.total = dinero(sum((i.subtotal for i in self.items), Decimal("0")))
        return self.total
