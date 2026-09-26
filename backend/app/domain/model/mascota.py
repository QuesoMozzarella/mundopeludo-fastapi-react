"""Contexto `mascotas` — adaptación de `legacy_django/mascotas/models.py`.

Modelos Django originales: Especie, Mascota, AdopcionSolicitud.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from ..errors import BusinessRuleError, ValidationError
from ..value_objects import EstadoAdopcion, EstadoSolicitud, Sexo


MAX_DESCRIPCION = 1000
MAX_URL_IMAGEN = 500


@dataclass
class Especie:
    """`Especie`: nombre único."""

    nombre: str
    id: int | None = None

    def __post_init__(self) -> None:
        limpio = (self.nombre or "").strip()
        if len(limpio) < 2:
            raise ValidationError("El nombre de la especie debe tener al menos 2 caracteres", "nombre")
        if len(limpio) > 100:
            raise ValidationError("El nombre de la especie no puede superar 100 caracteres", "nombre")
        self.nombre = limpio


@dataclass
class Mascota:
    """`Mascota` con las validaciones de `clean()` y la normalización de `save()`."""

    especie_id: int
    nombre: str
    sexo: Sexo
    color: str
    cliente_id: int | None = None
    raza: str | None = None
    edad_anos: int = 1
    peso: float = 0.0
    esta_esterilizado: bool = False
    activo: bool = True
    fecha_registro: date = field(kw_only=True)
    estado_adopcion: EstadoAdopcion = EstadoAdopcion.NORMAL
    descripcion: str | None = None
    imagen_url: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.sexo = Sexo.desde(self.sexo, campo="sexo")
        self.estado_adopcion = EstadoAdopcion.desde(
            self.estado_adopcion, campo="estado_adopcion", por_defecto=EstadoAdopcion.NORMAL
        )
        if isinstance(self.fecha_registro, datetime):
            self.fecha_registro = self.fecha_registro.date()

        # --- normalización equivalente a Mascota.save() ---
        nombre = (self.nombre or "").strip().title()
        if len(nombre) < 2:
            raise ValidationError("El nombre debe tener al menos 2 caracteres", "nombre")
        if len(nombre) > 100:
            raise ValidationError("El nombre no puede superar 100 caracteres", "nombre")
        if any(c.isdigit() for c in nombre):
            raise ValidationError("El nombre no puede contener números", "nombre")
        self.nombre = nombre

        if self.raza is not None:
            raza = self.raza.strip().title()
            if raza and len(raza) < 2:
                raise ValidationError("La raza debe tener al menos 2 caracteres", "raza")
            self.raza = raza or None

        color = (self.color or "").strip().lower()
        if len(color) < 2:
            raise ValidationError("El color debe tener al menos 2 caracteres", "color")
        if any(c.isdigit() for c in color):
            raise ValidationError("El color no puede contener números", "color")
        self.color = color

        # --- validadores de campo ---
        try:
            self.edad_anos = int(self.edad_anos)
        except (TypeError, ValueError):
            raise ValidationError("La edad debe ser un número entero", "edad_anos") from None
        if self.edad_anos < 0:
            raise ValidationError("La edad no puede ser negativa", "edad_anos")
        if self.edad_anos > 30:
            raise ValidationError("La edad máxima es 30 años", "edad_anos")

        try:
            self.peso = float(self.peso)
        except (TypeError, ValueError):
            raise ValidationError("El peso debe ser un número", "peso") from None
        if self.peso <= 0:
            raise ValidationError("El peso debe ser mayor a 0", "peso")
        if self.peso > 100:
            raise ValidationError("El peso máximo es 100 kg", "peso")

        if self.especie_id is None:
            raise ValidationError("La mascota debe pertenecer a una especie", "especie_id")

        self.descripcion = (self.descripcion or "").strip() or None
        if self.descripcion and len(self.descripcion) > MAX_DESCRIPCION:
            raise ValidationError(
                f"La descripción no puede superar {MAX_DESCRIPCION} caracteres", "descripcion"
            )
        self.imagen_url = (self.imagen_url or "").strip() or None
        if self.imagen_url:
            # Sólo http(s): se pinta en un <img>, y un "javascript:" no debe llegar ahí.
            if not self.imagen_url.lower().startswith(("http://", "https://")):
                raise ValidationError("La imagen debe ser una URL http(s)", "imagen_url")
            if len(self.imagen_url) > MAX_URL_IMAGEN:
                raise ValidationError(
                    f"La URL de la imagen no puede superar {MAX_URL_IMAGEN} caracteres",
                    "imagen_url",
                )

    @property
    def disponible_para_adopcion(self) -> bool:
        return self.activo and self.estado_adopcion is EstadoAdopcion.EN_ADOPCION

    def publicar_en_adopcion(self) -> None:
        if self.estado_adopcion is EstadoAdopcion.ADOPTADA:
            raise BusinessRuleError("Una mascota ya adoptada no puede volver a publicarse")
        self.estado_adopcion = EstadoAdopcion.EN_ADOPCION

    def retirar_de_adopcion(self) -> None:
        self.estado_adopcion = EstadoAdopcion.NORMAL

    def transferir_a(self, cliente_id: int) -> None:
        """Cambio de tutor tras aprobar una adopción."""
        self.cliente_id = cliente_id
        self.estado_adopcion = EstadoAdopcion.NORMAL

    def desactivar(self) -> None:
        self.activo = False


@dataclass
class SolicitudAdopcion:
    """`AdopcionSolicitud` con sus transiciones `aprobar`/`rechazar`/`cancelar`."""

    mascota_id: int
    cliente_id: int
    estado: EstadoSolicitud = EstadoSolicitud.PENDIENTE
    fecha_solicitud: datetime = field(kw_only=True)
    fecha_actualizacion: datetime = field(kw_only=True)
    revisado_por_id: int | None = None
    fecha_revision: datetime | None = None
    notas_revisor: str = ""
    notas_cliente: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        self.estado = EstadoSolicitud.desde(
            self.estado, campo="estado", por_defecto=EstadoSolicitud.PENDIENTE
        )
        self.notas_revisor = (self.notas_revisor or "").strip()
        self.notas_cliente = (self.notas_cliente or "").strip()

    @property
    def esta_pendiente(self) -> bool:
        return self.estado is EstadoSolicitud.PENDIENTE

    def _exigir_pendiente(self, accion: str) -> None:
        if not self.esta_pendiente:
            raise BusinessRuleError(
                f"No se puede {accion} una solicitud en estado '{self.estado.value}'"
            )

    def aprobar(self, revisor_id: int, momento: datetime, notas: str = "") -> None:
        """Aprueba y deja la mascota lista para transferirse al cliente.

        Igual que en Django, la aprobación transfiere de inmediato (sin fase
        'pendiente'); la transferencia la aplica el caso de uso sobre la mascota.
        """
        self._exigir_pendiente("aprobar")
        self.estado = EstadoSolicitud.APROBADA
        self.revisado_por_id = revisor_id
        self.fecha_revision = momento
        self.fecha_actualizacion = momento
        self.notas_revisor = (notas or "").strip()

    def rechazar(self, revisor_id: int, momento: datetime, notas: str = "") -> None:
        self._exigir_pendiente("rechazar")
        self.estado = EstadoSolicitud.RECHAZADA
        self.revisado_por_id = revisor_id
        self.fecha_revision = momento
        self.fecha_actualizacion = momento
        self.notas_revisor = (notas or "").strip()

    def cancelar(self, momento: datetime) -> None:
        """Cancelación por parte del cliente, con nota automática."""
        self._exigir_pendiente("cancelar")
        self.estado = EstadoSolicitud.CANCELADA
        self.fecha_actualizacion = momento
        nota = f"[Cancelada por el cliente el {momento.strftime('%d/%m/%Y %H:%M')}]"
        self.notas_cliente = f"{self.notas_cliente}\n\n{nota}".strip() if self.notas_cliente else nota
