// Formato de fechas para mostrar. La API envía fechas ISO en hora local de la
// clínica sin zona ("2026-09-28T10:30:00"); `new Date` las interpreta como
// hora local, que es lo que se quiere mostrar.
const LOCALE = 'es-CO';

const fechaHora = new Intl.DateTimeFormat(LOCALE, {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
  hour12: true
});

const soloFecha = new Intl.DateTimeFormat(LOCALE, {
  day: 'numeric',
  month: 'short',
  year: 'numeric'
});

function aFecha(valor: string | null | undefined): Date | null {
  if (!valor) return null;
  const fecha = new Date(valor);
  return Number.isNaN(fecha.getTime()) ? null : fecha;
}

/** "lun, 28 sept 2026, 10:30 a. m." — para citas y fichas clínicas. */
export function formatearFechaHora(valor: string | null | undefined): string {
  const fecha = aFecha(valor);
  return fecha ? fechaHora.format(fecha) : valor || '—';
}

/** "28 de sept de 2026" — cuando la hora no aporta. */
export function formatearFecha(valor: string | null | undefined): string {
  const fecha = aFecha(valor);
  return fecha ? soloFecha.format(fecha) : valor || '—';
}

/** "$25.000" — pesos sin decimales, con el separador de miles de la tienda. */
export function formatearPrecio(valor: number | null | undefined): string {
  return `$${Math.round(valor ?? 0).toLocaleString('es-CL')}`;
}
