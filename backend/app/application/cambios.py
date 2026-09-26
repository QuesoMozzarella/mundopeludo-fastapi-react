"""Ayudas para las actualizaciones parciales (PUT con sólo algunos campos).

Un comando de actualización distingue tres casos por campo:

* no enviado            -> ``SIN_CAMBIO`` (se conserva el valor actual);
* enviado como ``null`` -> ``None``;
* enviado con valor     -> el valor.

Cómo se trata ``None`` depende del campo: en los obligatorios (precio, stock,
activo...) significa "sin cambio" (`nuevo`); en los opcionales (descripción,
notas, teléfono...) significa "vaciarlo" (`nuevo_o_vacio`).
"""
from __future__ import annotations

from typing import Final, TypeVar, Union


class _SinCambio:
    """Marca de "campo no enviado". Hay una única instancia: ``SIN_CAMBIO``."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "SIN_CAMBIO"


SIN_CAMBIO: Final = _SinCambio()

T = TypeVar("T")
# `Cambio[int | None]`: el tipo de un campo en un comando de actualización.
Cambio = Union[T, _SinCambio]


def enviado(valor: object) -> bool:
    """El campo llegó con un valor (ni ausente ni `null`)."""
    return valor is not SIN_CAMBIO and valor is not None


def nuevo(valor: Cambio[T | None], actual: T) -> T:
    """Campo obligatorio: si no llega o llega `null`, se conserva el actual."""
    return valor if enviado(valor) else actual


def nuevo_o_vacio(valor: Cambio[T | None], actual: T | None) -> T | None:
    """Campo opcional: si no llega se conserva; `null` lo vacía."""
    return actual if valor is SIN_CAMBIO else valor
