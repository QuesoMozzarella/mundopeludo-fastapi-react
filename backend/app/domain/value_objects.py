"""Objetos de valor y enumeraciones del dominio.

Reemplazan los `*_CHOICES` de los modelos Django originales.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum

from .errors import ValidationError

CENTAVOS = Decimal("0.01")


class _TextEnum(str, Enum):
    """Enum de texto con parseo tolerante y etiqueta legible."""

    @classmethod
    def desde(cls, valor: "str | _TextEnum | None", *, campo: str, por_defecto=None):
        if valor is None or valor == "":
            if por_defecto is not None:
                return por_defecto
            raise ValidationError(f"El campo '{campo}' es obligatorio", campo)
        if isinstance(valor, cls):
            return valor
        texto = str(valor).strip()
        for miembro in cls:
            if miembro.value.lower() == texto.lower():
                return miembro
        validos = ", ".join(m.value for m in cls)
        raise ValidationError(
            f"Valor inválido para '{campo}': {valor!r}. Válidos: {validos}", campo
        )

    def __str__(self) -> str:  # pragma: no cover - conveniencia
        return self.value


class TipoUsuario(_TextEnum):
    CLIENTE = "cliente"
    VETERINARIO = "veterinario"
    ADMINISTRADOR = "administrador"


class Sexo(_TextEnum):
    MACHO = "Macho"
    HEMBRA = "Hembra"


class EstadoAdopcion(_TextEnum):
    """`Mascota.ESTADO_ADOPCION_CHOICES` del modelo Django."""

    NORMAL = "normal"
    EN_ADOPCION = "en_adopcion"
    ADOPTADA = "adoptada"
    PENDIENTE = "pendiente"


class EstadoSolicitud(_TextEnum):
    """`AdopcionSolicitud.ESTADO_CHOICES`."""

    PENDIENTE = "pendiente"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
    CANCELADA = "cancelada"


class DiaSemana(int, Enum):
    LUNES = 0
    MARTES = 1
    MIERCOLES = 2
    JUEVES = 3
    VIERNES = 4
    SABADO = 5
    DOMINGO = 6

    @property
    def etiqueta(self) -> str:
        return _DIAS[self.value]

    @classmethod
    def desde(cls, valor: "int | DiaSemana") -> "DiaSemana":
        if isinstance(valor, cls):
            return valor
        try:
            return cls(int(valor))
        except (TypeError, ValueError):
            raise ValidationError(
                "dia_semana debe ser un entero entre 0 (Lunes) y 6 (Domingo)",
                "dia_semana",
            ) from None


_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


class CategoriaProducto(_TextEnum):
    MEDICAMENTO = "medicamento"
    ALIMENTO = "alimento"
    ACCESORIO = "accesorio"
    JUGUETE = "juguete"
    HIGIENE = "higiene"
    SUPLEMENTO = "suplemento"
    ANTIPULGAS = "antipulgas"
    DESPARASITANTE = "desparasitante"


class UnidadMedida(_TextEnum):
    UNIDAD = "unidad"
    KG = "kg"
    GR = "gr"
    ML = "ml"
    LT = "lt"
    SOBRE = "sobre"
    CAJA = "caja"


class TipoAnimal(_TextEnum):
    PERRO = "perro"
    GATO = "gato"
    AMBOS = "ambos"
    AVE = "ave"
    REPTIL = "reptil"
    ROEDOR = "roedor"
    TODOS = "todos"


ETIQUETAS = {
    CategoriaProducto.MEDICAMENTO: "Medicamento",
    CategoriaProducto.ALIMENTO: "Alimento",
    CategoriaProducto.ACCESORIO: "Accesorio",
    CategoriaProducto.JUGUETE: "Juguete",
    CategoriaProducto.HIGIENE: "Higiene",
    CategoriaProducto.SUPLEMENTO: "Suplemento",
    CategoriaProducto.ANTIPULGAS: "Antipulgas",
    CategoriaProducto.DESPARASITANTE: "Desparasitante",
    UnidadMedida.UNIDAD: "Unidad",
    UnidadMedida.KG: "Kilogramo",
    UnidadMedida.GR: "Gramo",
    UnidadMedida.ML: "Mililitro",
    UnidadMedida.LT: "Litro",
    UnidadMedida.SOBRE: "Sobre",
    UnidadMedida.CAJA: "Caja",
    TipoAnimal.PERRO: "Perro",
    TipoAnimal.GATO: "Gato",
    TipoAnimal.AMBOS: "Perro y Gato",
    TipoAnimal.AVE: "Ave",
    TipoAnimal.REPTIL: "Reptil",
    TipoAnimal.ROEDOR: "Roedor",
    TipoAnimal.TODOS: "Todos los animales",
}


def etiqueta(valor) -> str:
    """Equivalente a `get_FOO_display()` de Django."""
    return ETIQUETAS.get(valor, getattr(valor, "value", str(valor)))


def hora_local(momento: datetime) -> datetime:
    """Pasa una fecha con zona horaria a la hora local del servidor, sin zona.

    La agenda y el reloj (`RelojSistema`) trabajan con hora local ingenua; si
    entra un "...Z" o un "-05:00" sin convertir, compararlo con `ahora()`
    lanza `TypeError`.
    """
    if momento.tzinfo is not None:
        return momento.astimezone().replace(tzinfo=None)
    return momento


def dinero(valor, *, campo: str = "precio") -> Decimal:
    """Normaliza cualquier entrada numérica a un Decimal de 2 decimales."""
    invalido = ValidationError(f"'{campo}' no es un valor monetario válido", campo)
    if valor is None:
        return Decimal("0").quantize(CENTAVOS)
    try:
        base = valor if isinstance(valor, Decimal) else Decimal(str(valor))
        if base.is_nan() or base.is_infinite():
            raise invalido
        # `quantize` también falla con exponentes fuera de rango (p. ej. 1e999999999).
        return base.quantize(CENTAVOS, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise invalido from None
