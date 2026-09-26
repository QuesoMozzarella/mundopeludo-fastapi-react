"""Repositorios SQLite del contexto `inventario` (productos, carrito, pedidos)."""
from __future__ import annotations

import sqlite3
from datetime import datetime

from ...domain.model.inventario import (
    Carrito,
    CarritoItem,
    ImagenProducto,
    Pedido,
    PedidoItem,
    Producto,
)
from ...domain.ports.repositories import (
    CarritoRepository,
    ImagenProductoRepository,
    PedidoRepository,
    ProductoRepository,
)
from ...domain.value_objects import CategoriaProducto, TipoAnimal, UnidadMedida
from ._comun import RepositorioSQLite, a_bool, a_date, a_datetime, a_decimal, filtro_like


def _a_producto(fila: sqlite3.Row) -> Producto:
    return Producto(
        id=fila["id"],
        nombre=fila["nombre"],
        descripcion=fila["descripcion"],
        categoria=CategoriaProducto(fila["categoria"]),
        marca=fila["marca"],
        precio=a_decimal(fila["precio"]),
        descuento_porcentaje=a_decimal(fila["descuento_porcentaje"]),
        stock=fila["stock"],
        stock_minimo=fila["stock_minimo"],
        total_vendidos=fila["total_vendidos"],
        tipo_animal=TipoAnimal(fila["tipo_animal"]),
        unidad_medida=UnidadMedida(fila["unidad_medida"]),
        peso=a_decimal(fila["peso"]) if fila["peso"] is not None else None,
        lote=fila["lote"],
        fecha_vencimiento=a_date(fila["fecha_vencimiento"]),
        sku=fila["sku"],
        disponible_online=a_bool(fila["disponible_online"]),
        palabras_clave=fila["palabras_clave"],
        activo=a_bool(fila["activo"]),
        fecha_creacion=a_datetime(fila["fecha_creacion"]) or datetime.now(),
        fecha_actualizacion=a_datetime(fila["fecha_actualizacion"]) or datetime.now(),
    )


class SqliteProductoRepository(RepositorioSQLite, ProductoRepository):
    def crear(self, producto: Producto) -> Producto:
        producto.id = self._insertar(
            """INSERT INTO productos
               (nombre, descripcion, categoria, marca, precio, descuento_porcentaje, stock,
                stock_minimo, total_vendidos, tipo_animal, unidad_medida, peso, lote,
                fecha_vencimiento, sku, disponible_online, palabras_clave, activo,
                fecha_creacion, fecha_actualizacion)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                producto.nombre, producto.descripcion, producto.categoria.value, producto.marca,
                producto.precio, producto.descuento_porcentaje, producto.stock,
                producto.stock_minimo, producto.total_vendidos, producto.tipo_animal.value,
                producto.unidad_medida.value, producto.peso, producto.lote,
                producto.fecha_vencimiento, producto.sku, int(producto.disponible_online),
                producto.palabras_clave, int(producto.activo),
                producto.fecha_creacion, producto.fecha_actualizacion,
            ),
        )
        return producto

    def actualizar(self, producto: Producto) -> Producto:
        self._ejecutar(
            """UPDATE productos SET nombre=?, descripcion=?, categoria=?, marca=?, precio=?,
                   descuento_porcentaje=?, stock=?, stock_minimo=?, total_vendidos=?,
                   tipo_animal=?, unidad_medida=?, peso=?, lote=?, fecha_vencimiento=?, sku=?,
                   disponible_online=?, palabras_clave=?, activo=?, fecha_actualizacion=?
               WHERE id=?""",
            (
                producto.nombre, producto.descripcion, producto.categoria.value, producto.marca,
                producto.precio, producto.descuento_porcentaje, producto.stock,
                producto.stock_minimo, producto.total_vendidos, producto.tipo_animal.value,
                producto.unidad_medida.value, producto.peso, producto.lote,
                producto.fecha_vencimiento, producto.sku, int(producto.disponible_online),
                producto.palabras_clave, int(producto.activo), datetime.now(), producto.id,
            ),
        )
        return producto

    def obtener(self, producto_id: int) -> Producto | None:
        fila = self._uno("SELECT * FROM productos WHERE id=?", (producto_id,))
        return _a_producto(fila) if fila else None

    def obtener_por_sku(self, sku: str) -> Producto | None:
        fila = self._uno("SELECT * FROM productos WHERE sku=?", (sku,))
        return _a_producto(fila) if fila else None

    def existe_sku(self, sku: str, excluir_id: int | None = None) -> bool:
        if excluir_id is None:
            total = self._escalar("SELECT COUNT(*) FROM productos WHERE sku=?", (sku,))
        else:
            total = self._escalar(
                "SELECT COUNT(*) FROM productos WHERE sku=? AND id<>?", (sku, excluir_id)
            )
        return bool(total)

    def listar(
        self,
        categoria=None,
        buscar=None,
        solo_activos=True,
        solo_online=None,
        stock_bajo=False,
    ) -> list[Producto]:
        sql = "SELECT * FROM productos WHERE 1=1"
        params: list = []
        if solo_activos:
            sql += " AND activo=1"
        if solo_online is not None:
            sql += " AND disponible_online=?"
            params.append(int(solo_online))
        if categoria is not None:
            sql += " AND categoria=?"
            params.append(CategoriaProducto.desde(categoria, campo="categoria").value)
        if buscar:
            sql += (
                " AND (lower(nombre) LIKE ? OR lower(descripcion) LIKE ?"
                " OR lower(marca) LIKE ? OR lower(palabras_clave) LIKE ? OR lower(sku) LIKE ?)"
            )
            params += [filtro_like(buscar)] * 5
        if stock_bajo:
            sql += " AND stock <= stock_minimo"
        sql += " ORDER BY nombre"
        return [_a_producto(f) for f in self._todos(sql, tuple(params))]

    def eliminar(self, producto_id: int) -> None:
        self._ejecutar("DELETE FROM productos WHERE id=?", (producto_id,))

    def contar(self, solo_activos: bool = True) -> int:
        sql = "SELECT COUNT(*) FROM productos"
        if solo_activos:
            sql += " WHERE activo=1"
        return int(self._escalar(sql) or 0)


class SqliteImagenProductoRepository(RepositorioSQLite, ImagenProductoRepository):
    def _mapear(self, fila: sqlite3.Row, incluir_binario: bool = True) -> ImagenProducto:
        return ImagenProducto(
            id=fila["id"],
            producto_id=fila["producto_id"],
            imagen_data=bytes(fila["imagen_data"]) if incluir_binario and fila["imagen_data"] else None,
            nombre_archivo=fila["nombre_archivo"],
            tipo_contenido=fila["tipo_contenido"],
            fecha_subida=a_datetime(fila["fecha_subida"]) or datetime.now(),
        )

    def crear(self, imagen: ImagenProducto) -> ImagenProducto:
        imagen.id = self._insertar(
            """INSERT INTO imagenes_producto
               (producto_id, imagen_data, nombre_archivo, tipo_contenido, fecha_subida)
               VALUES (?,?,?,?,?)""",
            (
                imagen.producto_id, imagen.imagen_data, imagen.nombre_archivo,
                imagen.tipo_contenido, imagen.fecha_subida,
            ),
        )
        return imagen

    def obtener(self, imagen_id: int, incluir_binario: bool = True) -> ImagenProducto | None:
        fila = self._uno("SELECT * FROM imagenes_producto WHERE id=?", (imagen_id,))
        return self._mapear(fila, incluir_binario) if fila else None

    def listar_por_producto(self, producto_id: int) -> list[ImagenProducto]:
        filas = self._todos(
            """SELECT id, producto_id, NULL AS imagen_data, nombre_archivo, tipo_contenido,
                      fecha_subida
               FROM imagenes_producto WHERE producto_id=? ORDER BY id""",
            (producto_id,),
        )
        return [self._mapear(f, incluir_binario=False) for f in filas]

    def eliminar(self, imagen_id: int) -> None:
        self._ejecutar("DELETE FROM imagenes_producto WHERE id=?", (imagen_id,))


class SqliteCarritoRepository(RepositorioSQLite, CarritoRepository):
    def obtener_por_usuario(self, usuario_id: int) -> Carrito | None:
        fila = self._uno("SELECT * FROM carritos WHERE usuario_id=?", (usuario_id,))
        if not fila:
            return None
        items = [
            CarritoItem(
                id=f["id"],
                carrito_id=f["carrito_id"],
                producto_id=f["producto_id"],
                cantidad=f["cantidad"],
                precio_unitario=a_decimal(f["precio_unitario"]),
                fecha_agregado=a_datetime(f["fecha_agregado"]) or datetime.now(),
            )
            for f in self._todos(
                "SELECT * FROM carrito_items WHERE carrito_id=? ORDER BY id", (fila["id"],)
            )
        ]
        return Carrito(
            id=fila["id"],
            usuario_id=fila["usuario_id"],
            items=items,
            fecha_creacion=a_datetime(fila["fecha_creacion"]) or datetime.now(),
            fecha_actualizacion=a_datetime(fila["fecha_actualizacion"]) or datetime.now(),
        )

    def guardar(self, carrito: Carrito) -> Carrito:
        """Reescribe el agregado completo: es pequeño y evita estados a medias."""
        if carrito.id is None:
            fila = self._uno("SELECT id FROM carritos WHERE usuario_id=?", (carrito.usuario_id,))
            carrito.id = fila["id"] if fila else None
        if carrito.id is None:
            carrito.id = self._insertar(
                "INSERT INTO carritos (usuario_id, fecha_creacion, fecha_actualizacion) VALUES (?,?,?)",
                (carrito.usuario_id, carrito.fecha_creacion, carrito.fecha_actualizacion),
            )
        else:
            self._ejecutar(
                "UPDATE carritos SET fecha_actualizacion=? WHERE id=?",
                (carrito.fecha_actualizacion, carrito.id),
            )
        self._ejecutar("DELETE FROM carrito_items WHERE carrito_id=?", (carrito.id,))
        for item in carrito.items:
            item.carrito_id = carrito.id
            item.id = self._insertar(
                """INSERT INTO carrito_items
                   (carrito_id, producto_id, cantidad, precio_unitario, fecha_agregado)
                   VALUES (?,?,?,?,?)""",
                (carrito.id, item.producto_id, item.cantidad, item.precio_unitario, item.fecha_agregado),
            )
        return carrito

    def eliminar_por_usuario(self, usuario_id: int) -> None:
        self._ejecutar("DELETE FROM carritos WHERE usuario_id=?", (usuario_id,))


class SqlitePedidoRepository(RepositorioSQLite, PedidoRepository):
    def crear(self, pedido: Pedido) -> Pedido:
        pedido.id = self._insertar(
            """INSERT INTO pedidos (usuario_id, total, metodo_pago, direccion, estado, fecha)
               VALUES (?,?,?,?,?,?)""",
            (
                pedido.usuario_id, pedido.total, pedido.metodo_pago, pedido.direccion,
                pedido.estado, pedido.fecha,
            ),
        )
        for item in pedido.items:
            item.pedido_id = pedido.id
            item.id = self._insertar(
                """INSERT INTO pedido_items
                   (pedido_id, producto_id, nombre_producto, cantidad, precio_unitario)
                   VALUES (?,?,?,?,?)""",
                (pedido.id, item.producto_id, item.nombre_producto, item.cantidad, item.precio_unitario),
            )
        return pedido

    def _items(self, pedido_id: int) -> list[PedidoItem]:
        return [
            PedidoItem(
                id=f["id"],
                pedido_id=f["pedido_id"],
                producto_id=f["producto_id"],
                nombre_producto=f["nombre_producto"],
                cantidad=f["cantidad"],
                precio_unitario=a_decimal(f["precio_unitario"]),
            )
            for f in self._todos("SELECT * FROM pedido_items WHERE pedido_id=? ORDER BY id", (pedido_id,))
        ]

    def _mapear(self, fila: sqlite3.Row) -> Pedido:
        return Pedido(
            id=fila["id"],
            usuario_id=fila["usuario_id"],
            total=a_decimal(fila["total"]),
            metodo_pago=fila["metodo_pago"],
            direccion=fila["direccion"],
            estado=fila["estado"],
            fecha=a_datetime(fila["fecha"]) or datetime.now(),
            items=self._items(fila["id"]),
        )

    def obtener(self, pedido_id: int) -> Pedido | None:
        fila = self._uno("SELECT * FROM pedidos WHERE id=?", (pedido_id,))
        return self._mapear(fila) if fila else None

    def listar(self, usuario_id: int | None = None) -> list[Pedido]:
        if usuario_id is None:
            filas = self._todos("SELECT * FROM pedidos ORDER BY fecha DESC")
        else:
            filas = self._todos(
                "SELECT * FROM pedidos WHERE usuario_id=? ORDER BY fecha DESC", (usuario_id,)
            )
        return [self._mapear(f) for f in filas]

    def total_ingresos(self, desde: datetime | None = None) -> float:
        if desde is None:
            total = self._escalar("SELECT COALESCE(SUM(total), 0) FROM pedidos")
        else:
            total = self._escalar("SELECT COALESCE(SUM(total), 0) FROM pedidos WHERE fecha >= ?", (desde,))
        return float(total or 0)
