"""Casos de uso de inventario: productos e imágenes."""
from __future__ import annotations

from ...domain.errors import NotFoundError, ValidationError
from ...domain.model.inventario import ImagenProducto, Producto
from ...domain.ports.repositories import ImagenProductoRepository, ProductoRepository
from ...domain.ports.services import Clock
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
    def __init__(self, productos: ProductoRepository, imagenes: ImagenProductoRepository):
        self.productos = productos
        self.imagenes = imagenes

    def listar(
        self,
        categoria: str | None = None,
        buscar: str | None = None,
        solo_activos: bool = True,
        solo_online: bool | None = None,
        stock_bajo: bool = False,
    ) -> list[ProductoVista]:
        encontrados = self.productos.listar(categoria, buscar, solo_activos, solo_online, stock_bajo)
        return [self._componer(p) for p in encontrados]

    def obtener(self, producto_id: int) -> ProductoVista:
        producto = self.productos.obtener(producto_id)
        if producto is None:
            raise NotFoundError("Producto", producto_id)
        return self._componer(producto)

    def _componer(self, producto: Producto) -> ProductoVista:
        return ProductoVista(
            producto=producto,
            imagenes_ids=[i.id for i in self.imagenes.listar_por_producto(producto.id)],
        )


class CrearProducto:
    def __init__(self, productos: ProductoRepository, sku: GeneradorSku, reloj: Clock):
        self.productos = productos
        self.sku = sku
        self.reloj = reloj

    def ejecutar(self, datos: dict) -> Producto:
        ahora = self.reloj.ahora()
        producto = Producto(
            nombre=datos.get("nombre"),
            descripcion=datos.get("descripcion"),
            categoria=datos.get("categoria"),
            marca=datos.get("marca"),
            precio=datos.get("precio"),
            descuento_porcentaje=datos.get("descuento_porcentaje") or 0,
            stock=datos.get("stock", 0),
            stock_minimo=datos.get("stock_minimo", 5),
            tipo_animal=datos.get("tipo_animal") or "todos",
            unidad_medida=datos.get("unidad_medida") or "unidad",
            peso=datos.get("peso"),
            lote=datos.get("lote"),
            fecha_vencimiento=datos.get("fecha_vencimiento"),
            disponible_online=datos.get("disponible_online", True),
            palabras_clave=datos.get("palabras_clave"),
            activo=datos.get("activo", True),
            fecha_creacion=ahora,
            fecha_actualizacion=ahora,
        )
        producto.sku = self.sku.para(producto)
        return self.productos.crear(producto)


class ActualizarProducto:
    def __init__(self, productos: ProductoRepository, sku: GeneradorSku):
        self.productos = productos
        self.sku = sku

    def ejecutar(self, producto_id: int, cambios: dict) -> Producto:
        actual = self.productos.obtener(producto_id)
        if actual is None:
            raise NotFoundError("Producto", producto_id)

        actualizado = Producto(
            id=actual.id,
            nombre=cambios.get("nombre") or actual.nombre,
            descripcion=cambios.get("descripcion", actual.descripcion),
            categoria=cambios.get("categoria") or actual.categoria,
            marca=cambios.get("marca", actual.marca),
            precio=cambios.get("precio", actual.precio),
            descuento_porcentaje=cambios.get("descuento_porcentaje", actual.descuento_porcentaje),
            stock=cambios.get("stock", actual.stock),
            stock_minimo=cambios.get("stock_minimo", actual.stock_minimo),
            total_vendidos=actual.total_vendidos,
            tipo_animal=cambios.get("tipo_animal") or actual.tipo_animal,
            unidad_medida=cambios.get("unidad_medida") or actual.unidad_medida,
            peso=cambios.get("peso", actual.peso),
            lote=cambios.get("lote", actual.lote),
            fecha_vencimiento=cambios.get("fecha_vencimiento", actual.fecha_vencimiento),
            sku=actual.sku,
            disponible_online=cambios.get("disponible_online", actual.disponible_online),
            palabras_clave=cambios.get("palabras_clave", actual.palabras_clave),
            activo=cambios.get("activo", actual.activo),
            fecha_creacion=actual.fecha_creacion,
        )
        # El SKU deriva de nombre + categoría: sólo se recalcula si cambian.
        if actualizado.nombre != actual.nombre or actualizado.categoria is not actual.categoria:
            actualizado.sku = self.sku.para(actualizado)
        return self.productos.actualizar(actualizado)


class AjustarStock:
    def __init__(self, productos: ProductoRepository):
        self.productos = productos

    def ejecutar(self, producto_id: int, cantidad: int, motivo: str = "ajuste") -> Producto:
        producto = self.productos.obtener(producto_id)
        if producto is None:
            raise NotFoundError("Producto", producto_id)
        if cantidad == 0:
            raise ValidationError("La cantidad del ajuste no puede ser cero", "cantidad")
        if cantidad > 0:
            producto.reponer_stock(cantidad)
        else:
            producto.descontar_stock(abs(cantidad))
        return self.productos.actualizar(producto)


class DesactivarProducto:
    def __init__(self, productos: ProductoRepository):
        self.productos = productos

    def ejecutar(self, producto_id: int) -> Producto:
        producto = self.productos.obtener(producto_id)
        if producto is None:
            raise NotFoundError("Producto", producto_id)
        producto.desactivar()
        return self.productos.actualizar(producto)


class GestionarImagenesProducto:
    """`ImagenProducto`: binarios guardados en la propia base, como en Django."""

    def __init__(
        self,
        imagenes: ImagenProductoRepository,
        productos: ProductoRepository,
        reloj: Clock,
    ):
        self.imagenes = imagenes
        self.productos = productos
        self.reloj = reloj

    def listar(self, producto_id: int) -> list[ImagenProducto]:
        self._producto(producto_id)
        return self.imagenes.listar_por_producto(producto_id)

    def obtener(self, imagen_id: int) -> ImagenProducto:
        imagen = self.imagenes.obtener(imagen_id)
        if imagen is None:
            raise NotFoundError("Imagen de producto", imagen_id)
        return imagen

    def subir(
        self,
        producto_id: int,
        contenido: bytes,
        nombre_archivo: str | None = None,
        tipo_contenido: str = "image/jpeg",
    ) -> ImagenProducto:
        self._producto(producto_id)
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

    def eliminar(self, imagen_id: int) -> None:
        self.obtener(imagen_id)
        self.imagenes.eliminar(imagen_id)

    def _producto(self, producto_id: int) -> Producto:
        producto = self.productos.obtener(producto_id)
        if producto is None:
            raise NotFoundError("Producto", producto_id)
        return producto
