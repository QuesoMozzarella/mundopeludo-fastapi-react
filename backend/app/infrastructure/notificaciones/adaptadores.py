"""Adaptadores del puerto `Notificaciones`, sólo con la librería estándar."""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from ...domain.errors import ServicioNoDisponibleError
from ...domain.model.sistema import CodigoRecuperacion
from ...domain.model.usuario import Usuario
from ...domain.ports.services import Notificaciones
from . import plantillas

log = logging.getLogger("mundopeludo.notificaciones")

PUERTO_SSL = 465


class CorreoSmtp(Notificaciones):
    """Envía los avisos por SMTP (el `EmailBackend` de Django).

    Con el puerto 465 abre la conexión cifrada desde el inicio; con cualquier
    otro (587 en Gmail) usa STARTTLS si `usar_tls` está activo.
    """

    def __init__(
        self,
        host: str,
        puerto: int,
        usuario: str,
        password: str,
        remitente: str,
        usar_tls: bool = True,
        timeout: float = 15,
    ):
        self.host = host
        self.puerto = puerto
        self.usuario = usuario
        self.password = password
        self.remitente = remitente or usuario
        self.usar_tls = usar_tls
        self.timeout = timeout

    def codigo_recuperacion(self, usuario: Usuario, codigo: CodigoRecuperacion) -> None:
        asunto, texto, html = plantillas.codigo_recuperacion(
            usuario.nombre_completo or usuario.email, codigo.codigo
        )
        self._enviar(usuario.email, asunto, texto, html)

    def _enviar(self, destinatario: str, asunto: str, texto: str, html: str) -> None:
        mensaje = EmailMessage()
        mensaje["Subject"] = asunto
        mensaje["From"] = self.remitente
        mensaje["To"] = destinatario
        mensaje.set_content(texto)
        mensaje.add_alternative(html, subtype="html")

        contexto = ssl.create_default_context()
        try:
            if self.puerto == PUERTO_SSL:
                conexion = smtplib.SMTP_SSL(
                    self.host, self.puerto, timeout=self.timeout, context=contexto
                )
            else:
                conexion = smtplib.SMTP(self.host, self.puerto, timeout=self.timeout)
            with conexion:
                if self.usar_tls and self.puerto != PUERTO_SSL:
                    conexion.starttls(context=contexto)
                if self.usuario:
                    conexion.login(self.usuario, self.password)
                conexion.send_message(mensaje)
        except (smtplib.SMTPException, OSError) as exc:
            log.error("No se pudo enviar '%s' a %s: %s", asunto, destinatario, exc)
            raise ServicioNoDisponibleError(
                "No se pudo enviar el correo. Intenta de nuevo en unos minutos."
            ) from exc
        log.info("Correo '%s' enviado a %s", asunto, destinatario)


class NotificacionesEnRegistro(Notificaciones):
    """Sin SMTP configurado: deja constancia en el log y no envía nada.

    En desarrollo el código de recuperación viaja en `codigo_debug`.
    """

    def codigo_recuperacion(self, usuario: Usuario, codigo: CodigoRecuperacion) -> None:
        log.warning(
            "Correo no configurado (MP_EMAIL_HOST): no se envió el código de recuperación a %s",
            usuario.email,
        )
