"""Rutas del carrito de compras, checkout y pedidos."""
from __future__ import annotations

from fastapi import APIRouter, status

from ..casos import ConsultarPedidosDep, GestionarCarritoDep, ProcesarCheckoutDep
from ..deps import AccesoDep
from ..schemas.inventario import (
    CantidadIn,
    CarritoOut,
    CheckoutIn,
    ItemCarritoIn,
    PedidoOut,
)

router = APIRouter(prefix="/api", tags=["tienda"])


@router.get("/carrito/{usuario_id}", response_model=CarritoOut, summary="Ver el carrito")
def ver_carrito(usuario_id: int, carrito: GestionarCarritoDep, acceso: AccesoDep) -> CarritoOut:
    acceso.propietario(usuario_id)
    return CarritoOut.desde(carrito.ver(usuario_id))


@router.post("/carrito/{usuario_id}", response_model=CarritoOut, summary="Agregar un producto")
def agregar(
    usuario_id: int, datos: ItemCarritoIn, carrito: GestionarCarritoDep, acceso: AccesoDep
) -> CarritoOut:
    acceso.propietario(usuario_id)
    return CarritoOut.desde(carrito.agregar(usuario_id, datos.producto_id, datos.cantidad))


@router.put(
    "/carrito/{usuario_id}/{producto_id}",
    response_model=CarritoOut,
    summary="Fijar la cantidad de un producto",
)
def actualizar_cantidad(
    usuario_id: int,
    producto_id: int,
    datos: CantidadIn,
    carrito: GestionarCarritoDep,
    acceso: AccesoDep,
) -> CarritoOut:
    acceso.propietario(usuario_id)
    vista = carrito.actualizar_cantidad(usuario_id, producto_id, datos.cantidad)
    return CarritoOut.desde(vista)


@router.delete(
    "/carrito/{usuario_id}/{producto_id}",
    response_model=CarritoOut,
    summary="Quitar un producto del carrito",
)
def quitar(
    usuario_id: int, producto_id: int, carrito: GestionarCarritoDep, acceso: AccesoDep
) -> CarritoOut:
    acceso.propietario(usuario_id)
    return CarritoOut.desde(carrito.quitar(usuario_id, producto_id))


@router.delete("/carrito/{usuario_id}", response_model=CarritoOut, summary="Vaciar el carrito")
def vaciar(usuario_id: int, carrito: GestionarCarritoDep, acceso: AccesoDep) -> CarritoOut:
    acceso.propietario(usuario_id)
    return CarritoOut.desde(carrito.vaciar(usuario_id))


@router.post(
    "/checkout",
    response_model=PedidoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Confirmar la compra del carrito",
)
def checkout(datos: CheckoutIn, caso: ProcesarCheckoutDep, acceso: AccesoDep) -> PedidoOut:
    acceso.propietario(datos.usuario_id)
    items = None
    if datos.items is not None:
        items = [(item.producto_id, item.cantidad) for item in datos.items]
    pedido = caso.ejecutar(datos.usuario_id, datos.metodo_pago, datos.direccion, items)
    return PedidoOut.desde(pedido)


@router.get("/pedidos", response_model=list[PedidoOut], summary="Listar pedidos")
def listar_pedidos(
    consulta: ConsultarPedidosDep, acceso: AccesoDep, usuario_id: int | None = None
) -> list[PedidoOut]:
    usuario_id = acceso.filtro_propio(usuario_id)
    return [PedidoOut.desde(p) for p in consulta.listar(usuario_id)]


@router.get("/pedidos/{pedido_id}", response_model=PedidoOut, summary="Ver un pedido")
def obtener_pedido(pedido_id: int, consulta: ConsultarPedidosDep, acceso: AccesoDep) -> PedidoOut:
    pedido = consulta.obtener(pedido_id)
    acceso.propietario(pedido.usuario_id)
    return PedidoOut.desde(pedido)
