"""Casos de uso del carrito de compras y del checkout."""
from __future__ import annotations

from ...domain.errors import BusinessRuleError, NotFoundError, ValidationError
from ...domain.model.inventario import Carrito, Pedido, PedidoItem
from ...domain.model.sistema import ActividadSistema
from ...domain.ports.repositories import (
    ActividadSistemaRepository,
    CarritoRepository,
    PedidoRepository,
    ProductoRepository,
    UsuarioRepository,
)
from ...domain.ports.services import Clock
from ..read_models import CarritoVista, ItemCarritoVista


class GestionarCarrito:
    def __init__(
        self,
        carritos: CarritoRepository,
        productos: ProductoRepository,
        usuarios: UsuarioRepository,
        reloj: Clock,
    ):
        self.carritos = carritos
        self.productos = productos
        self.usuarios = usuarios
        self.reloj = reloj

    def ver(self, usuario_id: int) -> CarritoVista:
        return self._componer(self._carrito(usuario_id))

    def agregar(self, usuario_id: int, producto_id: int, cantidad: int = 1) -> CarritoVista:
        carrito = self._carrito(usuario_id)
        producto = self.productos.obtener(producto_id)
        if producto is None:
            raise NotFoundError("Producto", producto_id)
        if not producto.activo or not producto.disponible_online:
            raise BusinessRuleError(f"'{producto.nombre}' no está disponible en la tienda")

        item_previo = carrito.buscar_item(producto_id)
        cantidad_total = cantidad + (item_previo.cantidad if item_previo else 0)
        if cantidad_total > producto.stock:
            raise BusinessRuleError(
                f"Stock insuficiente para {producto.nombre}: quedan {producto.stock} unidades"
            )

        carrito.agregar_producto(producto, cantidad, self.reloj.ahora())
        return self._componer(self.carritos.guardar(carrito))

    def actualizar_cantidad(self, usuario_id: int, producto_id: int, cantidad: int) -> CarritoVista:
        carrito = self._carrito(usuario_id)
        producto = self.productos.obtener(producto_id)
        if producto is None:
            raise NotFoundError("Producto", producto_id)
        if cantidad > producto.stock:
            raise BusinessRuleError(
                f"Stock insuficiente para {producto.nombre}: quedan {producto.stock} unidades"
            )
        if not carrito.actualizar_cantidad(producto_id, cantidad, self.reloj.ahora()):
            raise NotFoundError("Item del carrito", producto_id)
        return self._componer(self.carritos.guardar(carrito))

    def quitar(self, usuario_id: int, producto_id: int) -> CarritoVista:
        carrito = self._carrito(usuario_id)
        if not carrito.eliminar_producto(producto_id, self.reloj.ahora()):
            raise NotFoundError("Item del carrito", producto_id)
        return self._componer(self.carritos.guardar(carrito))

    def vaciar(self, usuario_id: int) -> CarritoVista:
        carrito = self._carrito(usuario_id)
        carrito.vaciar(self.reloj.ahora())
        return self._componer(self.carritos.guardar(carrito))

    def _carrito(self, usuario_id: int) -> Carrito:
        if self.usuarios.obtener(usuario_id) is None:
            raise NotFoundError("Usuario", usuario_id)
        carrito = self.carritos.obtener_por_usuario(usuario_id)
        if carrito is None:
            ahora = self.reloj.ahora()
            carrito = Carrito(
                usuario_id=usuario_id, fecha_creacion=ahora, fecha_actualizacion=ahora
            )
        return carrito

    def _componer(self, carrito: Carrito) -> CarritoVista:
        detalles = []
        for item in carrito.items:
            producto = self.productos.obtener(item.producto_id)
            detalles.append(
                ItemCarritoVista(
                    item=item,
                    nombre=producto.nombre if producto else "",
                    sku=producto.sku if producto else "",
                    stock=producto.stock if producto else 0,
                    categoria=producto.categoria.value if producto else "",
                )
            )
        return CarritoVista(carrito=carrito, items=detalles)


class ProcesarCheckout:
    """Convierte el carrito en pedido, descuenta stock y vacía el carrito.

    Todo ocurre dentro de la transacción de la petición: si algo falla a mitad
    (por ejemplo, el stock del tercer producto), no se persiste nada.
    """

    def __init__(
        self,
        carritos: CarritoRepository,
        productos: ProductoRepository,
        pedidos: PedidoRepository,
        usuarios: UsuarioRepository,
        reloj: Clock,
        actividades: ActividadSistemaRepository | None = None,
    ):
        self.carritos = carritos
        self.productos = productos
        self.pedidos = pedidos
        self.usuarios = usuarios
        self.reloj = reloj
        self.actividades = actividades

    def ejecutar(
        self,
        usuario_id: int,
        metodo_pago: str = "efectivo",
        direccion: str | None = None,
        items: list[tuple[int, int]] | None = None,
    ) -> Pedido:
        """Con `items` (producto_id, cantidad) compra esos productos sin tocar
        el carrito guardado; sin ellos, compra el carrito del usuario."""
        usuario = self.usuarios.obtener(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario", usuario_id)

        compra_directa = items is not None
        if compra_directa:
            carrito = self._carrito_temporal(usuario_id, items)
        else:
            carrito = self.carritos.obtener_por_usuario(usuario_id)
        if carrito is None or not carrito.items:
            raise ValidationError("El carrito está vacío", "carrito")

        pedido = Pedido(
            usuario_id=usuario_id,
            metodo_pago=metodo_pago,
            direccion=direccion or usuario.direccion,
            fecha=self.reloj.ahora(),
        )
        for item in carrito.items:
            producto = self.productos.obtener(item.producto_id)
            if producto is None:
                raise NotFoundError("Producto", item.producto_id)
            # Puede haberse retirado de la tienda después de meterlo al carrito.
            if not producto.activo or not producto.disponible_online:
                raise BusinessRuleError(f"'{producto.nombre}' no está disponible en la tienda")
            producto.descontar_stock(item.cantidad, pedido.fecha)
            self.productos.actualizar(producto)
            pedido.items.append(
                PedidoItem(
                    producto_id=producto.id,
                    nombre_producto=producto.nombre,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                )
            )

        pedido.recalcular_total()
        pedido = self.pedidos.crear(pedido)

        if not compra_directa:
            carrito.vaciar(pedido.fecha)
            self.carritos.guardar(carrito)

        if self.actividades:
            self.actividades.registrar(
                ActividadSistema(
                    usuario=usuario.email,
                    tipo="compra",
                    descripcion=f"Pedido #{pedido.id} por {pedido.total}",
                    fecha=self.reloj.ahora(),
                )
            )
        return pedido

    def _carrito_temporal(self, usuario_id: int, items: list[tuple[int, int]]) -> Carrito:
        """Carrito en memoria (no se persiste) con el precio vigente de cada producto."""
        ahora = self.reloj.ahora()
        carrito = Carrito(usuario_id=usuario_id, fecha_creacion=ahora, fecha_actualizacion=ahora)
        for producto_id, cantidad in items:
            producto = self.productos.obtener(producto_id)
            if producto is None:
                raise NotFoundError("Producto", producto_id)
            carrito.agregar_producto(producto, cantidad, ahora)
        return carrito


class ConsultarPedidos:
    def __init__(self, pedidos: PedidoRepository):
        self.pedidos = pedidos

    def listar(self, usuario_id: int | None = None) -> list[Pedido]:
        return self.pedidos.listar(usuario_id)

    def obtener(self, pedido_id: int) -> Pedido:
        pedido = self.pedidos.obtener(pedido_id)
        if pedido is None:
            raise NotFoundError("Pedido", pedido_id)
        return pedido
