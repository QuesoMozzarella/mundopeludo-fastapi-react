"""Rutas de inventario: productos e imágenes."""
from __future__ import annotations

import base64
import binascii

from fastapi import APIRouter, Query, Response, status

from ....domain.errors import ValidationError
from ..casos import (
    ActualizarProductoDep,
    AjustarStockDep,
    ConsultarProductosDep,
    CrearProductoDep,
    DesactivarProductoDep,
    GestionarImagenesProductoDep,
)
from ..deps import SoloPersonal
from ..schemas.inventario import (
    AjusteStockIn,
    ImagenIn,
    ImagenOut,
    ProductoActualizarIn,
    ProductoIn,
    ProductoOut,
)

router = APIRouter(prefix="/api", tags=["inventario"])


@router.get("/productos", response_model=list[ProductoOut], summary="Listar productos")
def listar_productos(
    consulta: ConsultarProductosDep,
    categoria: str | None = None,
    buscar: str | None = Query(default=None, description="Nombre, marca, SKU o palabras clave"),
    solo_activos: bool = True,
    solo_online: bool | None = None,
    stock_bajo: bool = False,
    tipo_animal: str | None = None,
    search: str | None = Query(default=None, include_in_schema=False),
) -> list[ProductoOut]:
    vistas = consulta.listar(
        categoria, buscar or search, solo_activos, solo_online, stock_bajo, tipo_animal
    )
    return [ProductoOut.desde(v) for v in vistas]


@router.get("/productos/{producto_id}", response_model=ProductoOut, summary="Ver un producto")
def obtener_producto(producto_id: int, consulta: ConsultarProductosDep) -> ProductoOut:
    return ProductoOut.desde(consulta.obtener(producto_id))


@router.post(
    "/productos",
    response_model=ProductoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un producto (SKU automático)",
    dependencies=[SoloPersonal],
)
def crear_producto(
    datos: ProductoIn, caso: CrearProductoDep, consulta: ConsultarProductosDep
) -> ProductoOut:
    producto = caso.ejecutar(datos.model_dump())
    return ProductoOut.desde(consulta.obtener(producto.id))


@router.put(
    "/productos/{producto_id}",
    response_model=ProductoOut,
    summary="Actualizar un producto",
    dependencies=[SoloPersonal],
)
def actualizar_producto(
    producto_id: int,
    datos: ProductoActualizarIn,
    caso: ActualizarProductoDep,
    consulta: ConsultarProductosDep,
) -> ProductoOut:
    caso.ejecutar(producto_id, datos.model_dump(exclude_unset=True))
    return ProductoOut.desde(consulta.obtener(producto_id))


@router.post(
    "/productos/{producto_id}/stock",
    response_model=ProductoOut,
    summary="Ajustar el stock (+ repone, - descuenta)",
    dependencies=[SoloPersonal],
)
def ajustar_stock(
    producto_id: int, datos: AjusteStockIn, caso: AjustarStockDep, consulta: ConsultarProductosDep
) -> ProductoOut:
    caso.ejecutar(producto_id, datos.cantidad, datos.motivo)
    return ProductoOut.desde(consulta.obtener(producto_id))


@router.delete(
    "/productos/{producto_id}",
    response_model=ProductoOut,
    summary="Desactivar un producto (baja lógica)",
    dependencies=[SoloPersonal],
)
def desactivar_producto(
    producto_id: int, caso: DesactivarProductoDep, consulta: ConsultarProductosDep
) -> ProductoOut:
    caso.ejecutar(producto_id)
    return ProductoOut.desde(consulta.obtener(producto_id))


# ------------------------------ imágenes ------------------------------
@router.get(
    "/productos/{producto_id}/imagenes",
    response_model=list[ImagenOut],
    summary="Listar imágenes de un producto",
)
def listar_imagenes(producto_id: int, imagenes: GestionarImagenesProductoDep) -> list[ImagenOut]:
    return [ImagenOut.desde(i) for i in imagenes.listar(producto_id)]


@router.post(
    "/productos/{producto_id}/imagenes",
    response_model=ImagenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Subir una imagen en base64",
    dependencies=[SoloPersonal],
)
def subir_imagen(
    producto_id: int, datos: ImagenIn, imagenes: GestionarImagenesProductoDep
) -> ImagenOut:
    contenido = datos.imagen_base64.split(",", 1)[-1]  # admite data URIs
    try:
        binario = base64.b64decode(contenido, validate=True)
    except (binascii.Error, ValueError):
        raise ValidationError("El campo imagen_base64 no es base64 válido", "imagen_base64") from None
    imagen = imagenes.subir(producto_id, binario, datos.nombre_archivo, datos.tipo_contenido)
    return ImagenOut.desde(imagen)


@router.get(
    "/imagenes/{imagen_id}",
    summary="Descargar el binario de una imagen",
    response_class=Response,
    responses={200: {"content": {"image/*": {}}}},
)
def descargar_imagen(imagen_id: int, imagenes: GestionarImagenesProductoDep) -> Response:
    imagen = imagenes.obtener(imagen_id)
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
def eliminar_imagen(imagen_id: int, imagenes: GestionarImagenesProductoDep) -> None:
    imagenes.eliminar(imagen_id)
