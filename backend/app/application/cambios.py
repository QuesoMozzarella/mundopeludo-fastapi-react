"""Ayudas para las actualizaciones parciales (PUT con sólo algunos campos)."""
from __future__ import annotations


def valor(cambios: dict, campo: str, actual):
    """Nuevo valor de un campo obligatorio; `null` explícito significa "sin cambio".

    Con `cambios.get(campo, actual)` un `{"precio": null}` llegaba a la entidad
    y el precio quedaba en 0 (o fallaba al guardar un booleano). Los campos que
    sí se pueden vaciar (descripción, notas, teléfono...) siguen usando
    `cambios.get(campo, actual)`.
    """
    nuevo = cambios.get(campo)
    return actual if nuevo is None else nuevo
