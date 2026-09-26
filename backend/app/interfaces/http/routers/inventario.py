"""Rutas de inventario: productos e imágenes."""
from __future__ import annotations

import base64
import binascii

from fastapi import APIRouter, Query, Response, status

from ....application.use_cases.inventario import (
    ActualizarProducto,
    AjustarStock,
    ConsultarProductos,
    CrearProducto,
    DesactivarProducto,
    GeneradorSku,
    GestionarImagenesProducto,
)
from ....domain.errors import ValidationError
from ..deps import ReposDep, ServiciosDep, SoloPersonal
from ..schemas.inventario import (
    AjusteStockIn,
    ImagenIn,
    ImagenOut,
    ProductoActualizarIn,
    ProductoIn,
    ProductoOut,
)

router = APIRouter(prefix="/api", tags=["inventario"])


def _consulta(repos: ReposDep) -> ConsultarProductos:
    return ConsultarProductos(repos.productos, repos.imagenes)


def _imagenes(repos: ReposDep, servicios: ServiciosDep) -> GestionarImagenesProducto:
    return GestionarImagenesProducto(repos.imagenes, repos.productos, servicios.reloj)


@router.get("/productos", response_model=list[ProductoOut], summary="Listar productos")
def listar_productos(
    repos: ReposDep,
    categoria: str | None = None,
    buscar: str | None = Query(default=None, description="Nombre, marca, SKU o palabras clave"),
    solo_activos: bool = True,
    solo_online: bool | None = None,
    stock_bajo: bool = False,
) -> list[ProductoOut]:
    vistas = _consulta(repos).listar(categoria, buscar, solo_activos, solo_online, stock_bajo)
    return [ProductoOut.desde(v) for v in vistas]


@router.get("/productos/{producto_id}", response_model=ProductoOut, summary="Ver un producto")
def obtener_producto(producto_id: int, repos: ReposDep) -> ProductoOut:
    return ProductoOut.desde(_consulta(repos).obtener(producto_id))


@router.post(
    "/productos",
    response_model=ProductoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un producto (SKU automático)",
    dependencies=[SoloPersonal],
)
def crear_producto(datos: ProductoIn, repos: ReposDep, servicios: ServiciosDep) -> ProductoOut:
    caso = CrearProducto(repos.productos, GeneradorSku(repos.productos), servicios.reloj)
    producto = caso.ejecutar(datos.model_dump())
    return ProductoOut.desde(_consulta(repos).obtener(producto.id))


@router.put(
    "/productos/{producto_id}",
    response_model=ProductoOut,
    summary="Actualizar un producto",
    dependencies=[SoloPersonal],
)
def actualizar_producto(
    producto_id: int, datos: ProductoActualizarIn, repos: ReposDep
) -> ProductoOut:
    caso = ActualizarProducto(repos.productos, GeneradorSku(repos.productos))
    caso.ejecutar(producto_id, datos.model_dump(exclude_unset=True))
    return ProductoOut.desde(_consulta(repos).obtener(producto_id))


@router.post(
    "/productos/{producto_id}/stock",
    response_model=ProductoOut,
    summary="Ajustar el stock (+ repone, - descuenta)",
    dependencies=[SoloPersonal],
)
def ajustar_stock(producto_id: int, datos: AjusteStockIn, repos: ReposDep) -> ProductoOut:
    AjustarStock(repos.productos).ejecutar(producto_id, datos.cantidad, datos.motivo)
    return ProductoOut.desde(_consulta(repos).obtener(producto_id))


@router.delete(
    "/productos/{producto_id}",
    response_model=ProductoOut,
    summary="Desactivar un producto (baja lógica)",
    dependencies=[SoloPersonal],
)
def desactivar_producto(producto_id: int, repos: ReposDep) -> ProductoOut:
    DesactivarProducto(repos.productos).ejecutar(producto_id)
    return ProductoOut.desde(_consulta(repos).obtener(producto_id))


# ------------------------------ imágenes ------------------------------
@router.get(
    "/productos/{producto_id}/imagenes",
    response_model=list[ImagenOut],
    summary="Listar imágenes de un producto",
)
def listar_imagenes(producto_id: int, repos: ReposDep, servicios: ServiciosDep) -> list[ImagenOut]:
    return [ImagenOut.desde(i) for i in _imagenes(repos, servicios).listar(producto_id)]


@router.post(
    "/productos/{producto_id}/imagenes",
    response_model=ImagenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Subir una imagen en base64",
    dependencies=[SoloPersonal],
)
def subir_imagen(
    producto_id: int, datos: ImagenIn, repos: ReposDep, servicios: ServiciosDep
) -> ImagenOut:
    contenido = datos.imagen_base64.split(",", 1)[-1]  # admite data URIs
    try:
        binario = base64.b64decode(contenido, validate=True)
    except (binascii.Error, ValueError):
        raise ValidationError("El campo imagen_base64 no es base64 válido", "imagen_base64") from None
    imagen = _imagenes(repos, servicios).subir(
        producto_id, binario, datos.nombre_archivo, datos.tipo_contenido
    )
    return ImagenOut.desde(imagen)


@router.get(
    "/imagenes/{imagen_id}",
    summary="Descargar el binario de una imagen",
    response_class=Response,
    responses={200: {"content": {"image/*": {}}}},
)
def descargar_imagen(imagen_id: int, repos: ReposDep, servicios: ServiciosDep) -> Response:
    imagen = _imagenes(repos, servicios).obtener(imagen_id)
    return Response(
        content=imagen.imagen_data or b"",
        media_type=imagen.tipo_contenido,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.delete(
    "/imagenes/{imagen_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una imagen",
    dependencies=[SoloPersonal],
)
def eliminar_imagen(imagen_id: int, repos: ReposDep, servicios: ServiciosDep) -> None:
    _imagenes(repos, servicios).eliminar(imagen_id)
