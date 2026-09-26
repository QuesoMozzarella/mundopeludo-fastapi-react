"""Esquemas Pydantic de inventario, carrito y pedidos."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from ....application.read_models import CarritoVista, ProductoVista
from ....domain.model.inventario import ImagenProducto, Pedido
from ....domain.value_objects import etiqueta


class ProductoIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=200)
    categoria: str
    precio: Decimal = Field(ge=0)
    descripcion: str | None = None
    marca: str | None = None
    descuento_porcentaje: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    stock: int = Field(default=0, ge=0)
    stock_minimo: int = Field(default=5, ge=0)
    tipo_animal: str = "todos"
    unidad_medida: str = "unidad"
    peso: Decimal | None = None
    lote: str | None = None
    fecha_vencimiento: date | None = None
    disponible_online: bool = True
    palabras_clave: str | None = None
    activo: bool = True


class ProductoActualizarIn(BaseModel):
    nombre: str | None = None
    categoria: str | None = None
    precio: Decimal | None = Field(default=None, ge=0)
    descripcion: str | None = None
    marca: str | None = None
    descuento_porcentaje: Decimal | None = Field(default=None, ge=0, le=100)
    stock: int | None = Field(default=None, ge=0)
    stock_minimo: int | None = Field(default=None, ge=0)
    tipo_animal: str | None = None
    unidad_medida: str | None = None
    peso: Decimal | None = None
    lote: str | None = None
    fecha_vencimiento: date | None = None
    disponible_online: bool | None = None
    palabras_clave: str | None = None
    activo: bool | None = None


class AjusteStockIn(BaseModel):
    cantidad: int = Field(description="Positivo repone, negativo descuenta")
    motivo: str = "ajuste"


class ProductoOut(BaseModel):
    """Las cifras monetarias salen como números JSON.

    El dominio trabaja con `Decimal` (exacto); la serialización a float ocurre
    sólo en el borde HTTP, porque los clientes JavaScript esperan números.
    """

    id: int
    nombre: str
    descripcion: str | None = None
    categoria: str
    categoria_nombre: str
    marca: str | None = None
    precio: float
    descuento_porcentaje: float
    precio_final: float
    stock: int
    stock_minimo: int
    stock_disponible: bool
    stock_bajo: bool
    total_vendidos: int
    tipo_animal: str
    tipo_animal_nombre: str
    unidad_medida: str
    unidad_medida_nombre: str
    peso: float | None = None
    lote: str | None = None
    fecha_vencimiento: date | None = None
    proximo_a_vencer: bool
    vencido: bool
    sku: str
    disponible_online: bool
    palabras_clave: str | None = None
    activo: bool
    imagenes_ids: list[int] = Field(default_factory=list)
    fecha_creacion: datetime

    @classmethod
    def desde(cls, vista: ProductoVista) -> "ProductoOut":
        p = vista.producto
        return cls(
            id=p.id,
            nombre=p.nombre,
            descripcion=p.descripcion,
            categoria=p.categoria.value,
            categoria_nombre=etiqueta(p.categoria),
            marca=p.marca,
            precio=p.precio,
            descuento_porcentaje=p.descuento_porcentaje,
            precio_final=p.precio_final,
            stock=p.stock,
            stock_minimo=p.stock_minimo,
            stock_disponible=p.stock_disponible,
            stock_bajo=p.stock_bajo,
            total_vendidos=p.total_vendidos,
            tipo_animal=p.tipo_animal.value,
            tipo_animal_nombre=etiqueta(p.tipo_animal),
            unidad_medida=p.unidad_medida.value,
            unidad_medida_nombre=etiqueta(p.unidad_medida),
            peso=p.peso,
            lote=p.lote,
            fecha_vencimiento=p.fecha_vencimiento,
            proximo_a_vencer=vista.proximo_a_vencer,
            vencido=vista.vencido,
            sku=p.sku,
            disponible_online=p.disponible_online,
            palabras_clave=p.palabras_clave,
            activo=p.activo,
            imagenes_ids=vista.imagenes_ids,
            fecha_creacion=p.fecha_creacion,
        )


class ImagenIn(BaseModel):
    """La imagen viaja en base64 dentro del JSON.

    Evita la dependencia `python-multipart` y encaja con el `BinaryField` del
    modelo Django, que también guardaba los bytes en la propia base de datos.
    """

    imagen_base64: str
    nombre_archivo: str | None = None
    tipo_contenido: str = "image/jpeg"


class ImagenOut(BaseModel):
    id: int
    producto_id: int
    nombre_archivo: str | None = None
    tipo_contenido: str
    tamano_bytes: int
    fecha_subida: datetime
    url: str

    @classmethod
    def desde(cls, imagen: ImagenProducto) -> "ImagenOut":
        return cls(
            id=imagen.id,
            producto_id=imagen.producto_id,
            nombre_archivo=imagen.nombre_archivo,
            tipo_contenido=imagen.tipo_contenido,
            tamano_bytes=imagen.tamano_bytes,
            fecha_subida=imagen.fecha_subida,
            url=f"/api/imagenes/{imagen.id}",
        )


class ItemCarritoIn(BaseModel):
    producto_id: int
    cantidad: int = Field(default=1, ge=1)


class CantidadIn(BaseModel):
    cantidad: int = Field(ge=0)


class ItemCarritoOut(BaseModel):
    producto_id: int
    nombre: str
    sku: str
    categoria: str
    cantidad: int
    precio_unitario: float
    subtotal: float
    stock_disponible: int


class CarritoOut(BaseModel):
    usuario_id: int
    items: list[ItemCarritoOut]
    total_items: int
    subtotal: float
    total: float

    @classmethod
    def desde(cls, vista: CarritoVista) -> "CarritoOut":
        return cls(
            usuario_id=vista.carrito.usuario_id,
            items=[
                ItemCarritoOut(
                    producto_id=d.item.producto_id,
                    nombre=d.nombre,
                    sku=d.sku,
                    categoria=d.categoria,
                    cantidad=d.item.cantidad,
                    precio_unitario=d.item.precio_unitario,
                    subtotal=d.item.subtotal,
                    stock_disponible=d.stock,
                )
                for d in vista.items
            ],
            total_items=vista.carrito.total_items,
            subtotal=vista.carrito.subtotal,
            total=vista.carrito.total,
        )


class CheckoutIn(BaseModel):
    usuario_id: int
    metodo_pago: str = "efectivo"
    direccion: str | None = None
    # Compra directa: si viene, se compran estos items y el carrito guardado
    # no se toca. El cliente SPA gestiona el carrito en el navegador.
    items: list[ItemCarritoIn] | None = None


class PedidoItemOut(BaseModel):
    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: float
    subtotal: float


class PedidoOut(BaseModel):
    id: int
    pedido_id: int  # alias de `id`: nombre que usaba la API anterior
    usuario_id: int
    total: float
    metodo_pago: str
    direccion: str | None = None
    estado: str
    fecha: datetime
    items: list[PedidoItemOut]

    @classmethod
    def desde(cls, pedido: Pedido) -> "PedidoOut":
        return cls(
            id=pedido.id,
            pedido_id=pedido.id,
            usuario_id=pedido.usuario_id,
            total=pedido.total,
            metodo_pago=pedido.metodo_pago,
            direccion=pedido.direccion,
            estado=pedido.estado,
            fecha=pedido.fecha,
            items=[
                PedidoItemOut(
                    producto_id=i.producto_id,
                    nombre_producto=i.nombre_producto,
                    cantidad=i.cantidad,
                    precio_unitario=i.precio_unitario,
                    subtotal=i.subtotal,
                )
                for i in pedido.items
            ],
        )
