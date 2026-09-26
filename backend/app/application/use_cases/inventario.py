"""Casos de uso de inventario: productos e imágenes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ...domain.errors import NotFoundError, ValidationError
from ...domain.model.inventario import ImagenProducto, Producto
from ...domain.ports.repositories import ImagenProductoRepository, ProductoRepository
from ...domain.ports.services import Clock
from ...domain.value_objects import TipoAnimal
from ..cambios import SIN_CAMBIO, Cambio, nuevo, nuevo_o_vacio
from ..read_models import ProductoVista

MAX_BYTES_IMAGEN = 5 * 1024 * 1024
TIPOS_IMAGEN = {"image/jpeg", "image/png", "image/webp", "image/gif"}


class GeneradorSku:
    """Servicio de aplicación: replica `Producto._generate_sku()` de Django.

    La entidad calcula la base del SKU; la unicidad necesita ir a la base, así
    que el bucle de desambiguación vive aquí y no en el dominio.
    """

    def __init__(self, productos: ProductoRepository):
        self.productos = productos

    def para(self, producto: Producto) -> str:
        base = producto.sku_base()
        candidato = base
        contador = 1
        while self.productos.existe_sku(candidato, excluir_id=producto.id):
            candidato = f"{base}-{contador:03d}"
            contador += 1
        return candidato


class ConsultarProductos:
    def __init__(
        self, productos: ProductoRepository, imagenes: ImagenProductoRepository, reloj: Clock
    ):
        self.productos = productos
        self.imagenes = imagenes
        self.reloj = reloj

    def listar(
        self,
        categoria: str | None = None,
        buscar: str | None = None,
        solo_activos: bool = True,
        solo_online: bool | None = None,
        stock_bajo: bool = False,
        tipo_animal: str | None = None,
    ) -> list[ProductoVista]:
        encontrados = self.productos.listar(categoria, buscar, solo_activos, solo_online, stock_bajo)
        if tipo_animal:
            animal = TipoAnimal.desde(tipo_animal, campo="tipo_animal")
            encontrados = [p for p in encontrados if p.sirve_para(animal)]
        return [self._componer(p) for p in encontrados]

    def obtener(self, producto_id: int) -> ProductoVista:
        producto = self.productos.obtener(producto_id)
        if producto is None:
            raise NotFoundError("Producto", producto_id)
        return self._componer(producto)

    def _componer(self, producto: Producto) -> ProductoVista:
        hoy = self.reloj.hoy()
        return ProductoVista(
            producto=producto,
            imagenes_ids=[i.id for i in self.imagenes.listar_por_producto(producto.id)],
            proximo_a_vencer=producto.proximo_a_vencer(hoy),
            vencido=producto.vencido(hoy),
        )


@dataclass(frozen=True, kw_only=True)
class CrearProductoCmd:
    nombre: str
    categoria: str
    precio: Decimal
    descripcion: str | None = None
    marca: str | None = None
    descuento_porcentaje: Decimal = Decimal("0")
    stock: int = 0
    stock_minimo: int = 5
    tipo_animal: str = "todos"
    unidad_medida: str = "unidad"
    peso: Decimal | None = None
    lote: str | None = None
    fecha_vencimiento: date | None = None
    disponible_online: bool = True
    palabras_clave: str | None = None
    activo: bool = True


@dataclass(frozen=True, kw_only=True)
class ActualizarProductoCmd:
    nombre: Cambio[str | None] = SIN_CAMBIO
    categoria: Cambio[str | None] = SIN_CAMBIO
    precio: Cambio[Decimal | None] = SIN_CAMBIO
    descripcion: Cambio[str | None] = SIN_CAMBIO
    marca: Cambio[str | None] = SIN_CAMBIO
    descuento_porcentaje: Cambio[Decimal | None] = SIN_CAMBIO
    stock: Cambio[int | None] = SIN_CAMBIO
    stock_minimo: Cambio[int | None] = SIN_CAMBIO
    tipo_animal: Cambio[str | None] = SIN_CAMBIO
    unidad_medida: Cambio[str | None] = SIN_CAMBIO
    peso: Cambio[Decimal | None] = SIN_CAMBIO
    lote: Cambio[str | None] = SIN_CAMBIO
    fecha_vencimiento: Cambio[date | None] = SIN_CAMBIO
    disponible_online: Cambio[bool | None] = SIN_CAMBIO
    palabras_clave: Cambio[str | None] = SIN_CAMBIO
    activo: Cambio[bool | None] = SIN_CAMBIO


class CrearProducto:
    def __init__(self, productos: ProductoRepository, sku: GeneradorSku, reloj: Clock):
        self.productos = productos
        self.sku = sku
        self.reloj = reloj

    def ejecutar(self, cmd: CrearProductoCmd) -> Producto:
        ahora = self.reloj.ahora()
        producto = Producto(
            nombre=cmd.nombre,
            descripcion=cmd.descripcion,
            categoria=cmd.categoria,
            marca=cmd.marca,
            precio=cmd.precio,
            descuento_porcentaje=cmd.descuento_porcentaje,
            stock=cmd.stock,
            stock_minimo=cmd.stock_minimo,
            tipo_animal=cmd.tipo_animal,
            unidad_medida=cmd.unidad_medida,
            peso=cmd.peso,
            lote=cmd.lote,
            fecha_vencimiento=cmd.fecha_vencimiento,
            disponible_online=cmd.disponible_online,
            palabras_clave=cmd.palabras_clave,
            activo=cmd.activo,
            fecha_creacion=ahora,
            fecha_actualizacion=ahora,
        )
        producto.sku = self.sku.para(producto)
        return self.productos.crear(producto)


class ActualizarProducto:
    def __init__(self, productos: ProductoRepository, sku: GeneradorSku, reloj: Clock):
        self.productos = productos
        self.sku = sku
        self.reloj = reloj

    def ejecutar(self, producto_id: int, cmd: ActualizarProductoCmd) -> Producto:
        actual = self.productos.obtener(producto_id)
        if actual is None:
            raise NotFoundError("Producto", producto_id)

        actualizado = Producto(
            id=actual.id,
            nombre=nuevo(cmd.nombre, actual.nombre),
            descripcion=nuevo_o_vacio(cmd.descripcion, actual.descripcion),
            categoria=nuevo(cmd.categoria, actual.categoria),
            marca=nuevo_o_vacio(cmd.marca, actual.marca),
            precio=nuevo(cmd.precio, actual.precio),
            descuento_porcentaje=nuevo(cmd.descuento_porcentaje, actual.descuento_porcentaje),
            stock=nuevo(cmd.stock, actual.stock),
            stock_minimo=nuevo(cmd.stock_minimo, actual.stock_minimo),
            total_vendidos=actual.total_vendidos,
            tipo_animal=nuevo(cmd.tipo_animal, actual.tipo_animal),
            unidad_medida=nuevo(cmd.unidad_medida, actual.unidad_medida),
            peso=nuevo_o_vacio(cmd.peso, actual.peso),
            lote=nuevo_o_vacio(cmd.lote, actual.lote),
            fecha_vencimiento=nuevo_o_vacio(cmd.fecha_vencimiento, actual.fecha_vencimiento),
            sku=actual.sku,
            disponible_online=nuevo(cmd.disponible_online, actual.disponible_online),
            palabras_clave=nuevo_o_vacio(cmd.palabras_clave, actual.palabras_clave),
            activo=nuevo(cmd.activo, actual.activo),
            fecha_creacion=actual.fecha_creacion,
            fecha_actualizacion=self.reloj.ahora(),
        )
        # El SKU deriva de nombre + categoría: sólo se recalcula si cambian.
        if actualizado.nombre != actual.nombre or actualizado.categoria is not actual.categoria:
            actualizado.sku = self.sku.para(actualizado)
        return self.productos.actualizar(actualizado)


class AjustarStock:
    def __init__(self, productos: ProductoRepository, reloj: Clock):
        self.productos = productos
        self.reloj = reloj

    def ejecutar(self, producto_id: int, cantidad: int, motivo: str = "ajuste") -> Producto:
        producto = self.productos.obtener(producto_id)
        if producto is None:
            raise NotFoundError("Producto", producto_id)
        if cantidad == 0:
            raise ValidationError("La cantidad del ajuste no puede ser cero", "cantidad")
        if cantidad > 0:
            producto.reponer_stock(cantidad, self.reloj.ahora())
        else:
            producto.descontar_stock(abs(cantidad), self.reloj.ahora())
        return self.productos.actualizar(producto)


class DesactivarProducto:
    def __init__(self, productos: ProductoRepository, reloj: Clock):
        self.productos = productos
        self.reloj = reloj

    def ejecutar(self, producto_id: int) -> Producto:
        producto = self.productos.obtener(producto_id)
        if producto is None:
            raise NotFoundError("Producto", producto_id)
        producto.desactivar(self.reloj.ahora())
        return self.productos.actualizar(producto)


class ConsultarImagenesProducto:
    """`ImagenProducto`: binarios guardados en la propia base, como en Django."""

    def __init__(self, imagenes: ImagenProductoRepository, productos: ProductoRepository):
        self.imagenes = imagenes
        self.productos = productos

    def listar(self, producto_id: int) -> list[ImagenProducto]:
        _producto_o_error(self.productos, producto_id)
        return self.imagenes.listar_por_producto(producto_id)

    def obtener(self, imagen_id: int) -> ImagenProducto:
        return _imagen_o_error(self.imagenes, imagen_id)


class SubirImagenProducto:
    def __init__(
        self,
        imagenes: ImagenProductoRepository,
        productos: ProductoRepository,
        reloj: Clock,
    ):
        self.imagenes = imagenes
        self.productos = productos
        self.reloj = reloj

    def ejecutar(
        self,
        producto_id: int,
        contenido: bytes,
        nombre_archivo: str | None = None,
        tipo_contenido: str = "image/jpeg",
    ) -> ImagenProducto:
        _producto_o_error(self.productos, producto_id)
        if not contenido:
            raise ValidationError("La imagen está vacía", "imagen_base64")
        if len(contenido) > MAX_BYTES_IMAGEN:
            raise ValidationError("La imagen supera el máximo de 5 MB", "imagen_base64")
        if tipo_contenido not in TIPOS_IMAGEN:
            raise ValidationError(
                f"Tipo de imagen no admitido: {tipo_contenido}", "tipo_contenido"
            )
        return self.imagenes.crear(
            ImagenProducto(
                producto_id=producto_id,
                imagen_data=contenido,
                nombre_archivo=nombre_archivo,
                tipo_contenido=tipo_contenido,
                fecha_subida=self.reloj.ahora(),
            )
        )


class EliminarImagenProducto:
    def __init__(self, imagenes: ImagenProductoRepository):
        self.imagenes = imagenes

    def ejecutar(self, imagen_id: int) -> None:
        _imagen_o_error(self.imagenes, imagen_id)
        self.imagenes.eliminar(imagen_id)


def _producto_o_error(productos: ProductoRepository, producto_id: int) -> Producto:
    producto = productos.obtener(producto_id)
    if producto is None:
        raise NotFoundError("Producto", producto_id)
    return producto


def _imagen_o_error(imagenes: ImagenProductoRepository, imagen_id: int) -> ImagenProducto:
    imagen = imagenes.obtener(imagen_id)
    if imagen is None:
        raise NotFoundError("Imagen de producto", imagen_id)
    return imagen
