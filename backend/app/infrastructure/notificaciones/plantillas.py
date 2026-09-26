"""Textos de los correos. Replican el formato de `legacy_django/sananimal_clinic/views.py`.

Cada función devuelve (asunto, texto plano, html): el texto plano es la
alternativa para clientes de correo que no muestran HTML.
"""
from __future__ import annotations

from datetime import datetime
from html import escape

from ...domain.model.sistema import HORAS_VIGENCIA_CODIGO, MAX_INTENTOS_CODIGO
from ...domain.ports.services import AvisoCita, AvisoHistorial

LEMA = "Con MundoPeludo, la salud de las mascotas está en buenas manos"

_ESTILOS = """
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .header { background: #1d95c8; color: white; padding: 20px; text-align: center;
              border-radius: 8px 8px 0 0; }
    .header.cancelada { background: #c0392b; }
    .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }
    .code { font-size: 36px; font-weight: bold; color: #1d95c8; text-align: center;
            background: white; padding: 20px; border-radius: 8px; margin: 20px 0;
            letter-spacing: 5px; border: 2px solid #1d95c8; }
    .ficha { background: white; border-radius: 8px; padding: 16px 20px; margin: 20px 0;
             border: 1px solid #d6e9f3; }
    .ficha td { padding: 6px 0; vertical-align: top; }
    .ficha td.etiqueta { color: #666; width: 130px; font-weight: bold; }
    .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
"""

_DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
_MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_legible(momento: datetime) -> str:
    """"lunes 28 de septiembre de 2026, 10:30 a. m." (sin depender del locale del SO)."""
    hora = momento.hour % 12 or 12
    sufijo = "a. m." if momento.hour < 12 else "p. m."
    return (
        f"{_DIAS[momento.weekday()]} {momento.day} de {_MESES[momento.month - 1]} "
        f"de {momento.year}, {hora}:{momento.minute:02d} {sufijo}"
    )


def _documento(titulo: str, subtitulo: str, contenido: str, cabecera: str = "") -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{escape(titulo)}</title>
  <style>{_ESTILOS}</style>
</head>
<body>
  <div class="container">
    <div class="header {cabecera}">
      <h1>🐾 MundoPeludo</h1>
      <h2>{escape(subtitulo)}</h2>
    </div>
    <div class="content">
{contenido}
    </div>
    <div class="footer">
      <p>Este es un mensaje automático, por favor no responder.</p>
      <p>🐾 <em>{LEMA}</em> 🐾</p>
    </div>
  </div>
</body>
</html>
"""


def _ficha_html(filas: list[tuple[str, str]]) -> str:
    celdas = "".join(
        f'<tr><td class="etiqueta">{escape(e)}</td><td>{escape(v)}</td></tr>' for e, v in filas
    )
    return f'<table class="ficha" width="100%">{celdas}</table>'


def _ficha_texto(filas: list[tuple[str, str]]) -> str:
    return "\n".join(f"  {e}: {v}" for e, v in filas)


def _texto(nombre: str, cuerpo: str) -> str:
    return f"Hola {nombre},\n\n{cuerpo}\n\nSaludos,\nEl equipo de MundoPeludo\n🐾 {LEMA} 🐾\n"


def codigo_recuperacion(nombre: str, codigo: str) -> tuple[str, str, str]:
    asunto = "Código de Recuperación - MundoPeludo"
    horas = "1 hora" if HORAS_VIGENCIA_CODIGO == 1 else f"{HORAS_VIGENCIA_CODIGO} horas"
    texto = _texto(
        nombre,
        f"Tu código de recuperación es: {codigo}\n\n"
        f"Este código expira en {horas} y tienes {MAX_INTENTOS_CODIGO} intentos para usarlo.\n\n"
        "Si no solicitaste este código, ignora este mensaje.",
    )
    html = _documento(asunto, "Código de Recuperación", f"""
      <p>Hola <strong>{escape(nombre)}</strong>,</p>
      <p>Has solicitado recuperar tu contraseña. Usa el siguiente código:</p>
      <div class="code">{codigo}</div>
      <p><strong>Información importante:</strong></p>
      <ul>
        <li>Este código expira en <strong>{horas}</strong></li>
        <li>Tienes <strong>{MAX_INTENTOS_CODIGO} intentos</strong> para ingresarlo correctamente</li>
        <li>Si no solicitaste este código, ignora este mensaje</li>
      </ul>
      <p>Si no puedes copiar el código, ingrésalo manualmente: <strong>{codigo}</strong></p>""")
    return asunto, texto, html


def _filas_cita(aviso: AvisoCita) -> list[tuple[str, str]]:
    return [
        ("Mascota", aviso.mascota),
        ("Fecha y hora", fecha_legible(aviso.fecha_hora)),
        ("Servicio", aviso.servicio),
        ("Veterinario", aviso.veterinario),
        ("Motivo", aviso.motivo),
    ]


def cita_confirmada(aviso: AvisoCita) -> tuple[str, str, str]:
    asunto = f"Cita confirmada para {aviso.mascota} - MundoPeludo"
    filas = _filas_cita(aviso)
    texto = _texto(
        aviso.nombre,
        f"Tu cita para {aviso.mascota} está confirmada:\n\n{_ficha_texto(filas)}\n\n"
        "Te recomendamos llegar 10 minutos antes. Si no puedes asistir, cancélala "
        "desde la app para liberar el horario.",
    )
    html = _documento(asunto, "Cita confirmada", f"""
      <p>Hola <strong>{escape(aviso.nombre)}</strong>,</p>
      <p>Tu cita para <strong>{escape(aviso.mascota)}</strong> está confirmada:</p>
      {_ficha_html(filas)}
      <p>Te recomendamos llegar <strong>10 minutos antes</strong>. Si no puedes asistir,
      cancélala desde la app para liberar el horario.</p>""")
    return asunto, texto, html


def cita_cancelada(aviso: AvisoCita) -> tuple[str, str, str]:
    asunto = f"Cita cancelada para {aviso.mascota} - MundoPeludo"
    filas = _filas_cita(aviso)
    texto = _texto(
        aviso.nombre,
        f"La siguiente cita de {aviso.mascota} ha sido cancelada:\n\n{_ficha_texto(filas)}\n\n"
        "Si quieres reprogramarla, agenda una nueva cita desde la app.",
    )
    html = _documento(asunto, "Cita cancelada", f"""
      <p>Hola <strong>{escape(aviso.nombre)}</strong>,</p>
      <p>La siguiente cita de <strong>{escape(aviso.mascota)}</strong> ha sido cancelada:</p>
      {_ficha_html(filas)}
      <p>Si quieres reprogramarla, agenda una nueva cita desde la app.</p>""",
        cabecera="cancelada")
    return asunto, texto, html


def historial_registrado(aviso: AvisoHistorial) -> tuple[str, str, str]:
    asunto = f"Historia clínica de {aviso.mascota} - MundoPeludo"
    filas = [
        ("Mascota", aviso.mascota),
        ("Fecha", fecha_legible(aviso.fecha)),
        ("Veterinario", aviso.veterinario),
        ("Diagnóstico", aviso.diagnostico),
        ("Tratamiento", aviso.tratamiento),
    ]
    if aviso.observaciones:
        filas.append(("Observaciones", aviso.observaciones))
    texto = _texto(
        aviso.nombre,
        f"Registramos una nueva entrada en la historia clínica de {aviso.mascota}:\n\n"
        f"{_ficha_texto(filas)}\n\n"
        "Sigue las indicaciones del tratamiento y consúltanos ante cualquier duda.",
    )
    html = _documento(asunto, "Historia clínica", f"""
      <p>Hola <strong>{escape(aviso.nombre)}</strong>,</p>
      <p>Registramos una nueva entrada en la historia clínica de
      <strong>{escape(aviso.mascota)}</strong>:</p>
      {_ficha_html(filas)}
      <p>Sigue las indicaciones del tratamiento y consúltanos ante cualquier duda.</p>""")
    return asunto, texto, html
