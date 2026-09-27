/**
 * Datos públicos de la clínica: rellénalos aquí y aparecen en el inicio y en
 * el pie de página. Un campo vacío no se muestra (y si no hay ninguno de
 * contacto, la sección de contacto tampoco).
 */
export const CLINICA = {
  nombre: 'Mundo Peludo',
  lema: 'Clínica veterinaria',
  /** Una o dos frases para el pie de página. */
  presentacion: 'Consultas, vacunación, cirugía, adopciones y farmacia para tu mascota.',

  /** Ej.: "Calle 50 # 45-20, Bello, Antioquia". */
  direccion: '',
  /** Ej.: "+57 300 000 0000". Se enlaza a WhatsApp si `whatsapp` es true. */
  telefono: '',
  whatsapp: true,
  /** Correo de contacto para el público. */
  correo: '',
  /** Texto libre, ej.: "Lunes a sábado, 9:00 a 13:00 y 15:00 a 19:00". */
  horario: '',
  /** Ej.: "Urgencias 24 horas". Vacío si la clínica no las atiende. */
  urgencias: ''
};

export const hayContacto = Boolean(
  CLINICA.direccion || CLINICA.telefono || CLINICA.correo || CLINICA.horario || CLINICA.urgencias
);

/** Enlace de WhatsApp a partir del teléfono (sólo dígitos). */
export function enlaceTelefono(): string | null {
  if (!CLINICA.telefono) return null;
  const digitos = CLINICA.telefono.replace(/\D/g, '');
  return CLINICA.whatsapp ? `https://wa.me/${digitos}` : `tel:+${digitos}`;
}
