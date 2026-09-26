"""Textos de los correos. Replican el formato de `legacy_django/sananimal_clinic/views.py`."""
from __future__ import annotations

from html import escape

from ...domain.model.sistema import HORAS_VIGENCIA_CODIGO, MAX_INTENTOS_CODIGO

LEMA = "Con MundoPeludo, la salud de las mascotas está en buenas manos"

_ESTILOS = """
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: #1d95c8; color: white; padding: 20px; text-align: center;
              border-radius: 8px 8px 0 0; }
    .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }
    .code { font-size: 36px; font-weight: bold; color: #1d95c8; text-align: center;
            background: white; padding: 20px; border-radius: 8px; margin: 20px 0;
            letter-spacing: 5px; border: 2px solid #1d95c8; }
    .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
"""


def codigo_recuperacion(nombre: str, codigo: str) -> tuple[str, str, str]:
    """Devuelve (asunto, texto plano, html)."""
    asunto = "Código de Recuperación - MundoPeludo"
    horas = "1 hora" if HORAS_VIGENCIA_CODIGO == 1 else f"{HORAS_VIGENCIA_CODIGO} horas"

    texto = f"""Hola {nombre},

Tu código de recuperación es: {codigo}

Este código expira en {horas} y tienes {MAX_INTENTOS_CODIGO} intentos para usarlo.

Si no solicitaste este código, ignora este mensaje.

Saludos,
El equipo de MundoPeludo
🐾 {LEMA} 🐾
"""

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{asunto}</title>
  <style>{_ESTILOS}</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🐾 MundoPeludo</h1>
      <h2>Código de Recuperación</h2>
    </div>
    <div class="content">
      <p>Hola <strong>{escape(nombre)}</strong>,</p>
      <p>Has solicitado recuperar tu contraseña. Usa el siguiente código:</p>
      <div class="code">{codigo}</div>
      <p><strong>Información importante:</strong></p>
      <ul>
        <li>Este código expira en <strong>{horas}</strong></li>
        <li>Tienes <strong>{MAX_INTENTOS_CODIGO} intentos</strong> para ingresarlo correctamente</li>
        <li>Si no solicitaste este código, ignora este mensaje</li>
      </ul>
      <p>Si no puedes copiar el código, ingrésalo manualmente: <strong>{codigo}</strong></p>
    </div>
    <div class="footer">
      <p>Este es un mensaje automático, por favor no responder.</p>
      <p>🐾 <em>{LEMA}</em> 🐾</p>
    </div>
  </div>
</body>
</html>
"""
    return asunto, texto, html
