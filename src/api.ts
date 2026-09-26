import {
  User, Especie, Mascota, SolicitudAdopcion, Servicio,
  Cita, HistorialMedico, Producto, DashboardStats, Sesion
} from './types';

const API_BASE = '/api';
const CLAVE_SESION = 'mundopeludo_sesion';

// ---------------------------------------------------------------------------
// Sesión: el token JWT viaja en la cabecera Authorization de cada petición.
// ---------------------------------------------------------------------------
let sesionActual: Sesion | null = leerSesionGuardada();
let alExpirarSesion: (() => void) | null = null;

function leerSesionGuardada(): Sesion | null {
  try {
    const guardada = localStorage.getItem(CLAVE_SESION);
    return guardada ? JSON.parse(guardada) : null;
  } catch {
    return null;
  }
}

export function obtenerSesion(): Sesion | null {
  return sesionActual;
}

export function guardarSesion(sesion: Sesion | null) {
  sesionActual = sesion;
  try {
    if (sesion) localStorage.setItem(CLAVE_SESION, JSON.stringify(sesion));
    else localStorage.removeItem(CLAVE_SESION);
  } catch {
    // Sin almacenamiento (modo privado): la sesión dura lo que la pestaña.
  }
}

/** La app registra aquí qué hacer cuando el backend rechaza el token (401). */
export function alCaducarSesion(callback: (() => void) | null) {
  alExpirarSesion = callback;
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
  }
}

async function wait(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function request<T>(endpoint: string, options: RequestInit = {}, retries = 2): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {})
  };
  if (sesionActual) {
    headers['Authorization'] = `Bearer ${sesionActual.token}`;
  }

  const isGet = !options.method || options.method === 'GET';
  const maxIntentos = isGet ? retries : 0;

  for (let attempt = 0; ; attempt++) {
    let response: Response;
    try {
      response = await fetch(url, { ...options, headers });
    } catch (err) {
      // Error de red (backend arrancando): se reintenta sólo en lecturas.
      if (attempt < maxIntentos) {
        await wait(350 * (attempt + 1));
        continue;
      }
      throw new ApiError('No se pudo conectar con el servidor', 0);
    }

    if (response.ok) {
      return response.status === 204 ? (undefined as T) : await response.json();
    }

    // 5xx: el backend puede estar calentando; los 4xx nunca se reintentan.
    if (response.status >= 500 && attempt < maxIntentos) {
      await wait(350 * (attempt + 1));
      continue;
    }

    let mensaje = `Error HTTP ${response.status}`;
    try {
      const datos = await response.json();
      mensaje = datos.detail || datos.message || mensaje;
      if (Array.isArray(mensaje)) {
        // Errores de validación de FastAPI/Pydantic
        mensaje = mensaje.map((e: any) => e.msg).join('. ');
      }
    } catch {
      mensaje = response.statusText || mensaje;
    }

    if (response.status === 401 && sesionActual && !endpoint.startsWith('/auth/')) {
      guardarSesion(null);
      alExpirarSesion?.();
    }
    throw new ApiError(mensaje, response.status);
  }
}

// ---------------------------------------------------------------------------
// Adaptadores: la API usa sus propios nombres de campo; las vistas, los de
// `types.ts`. Traducir aquí evita tocar cada componente.
// ---------------------------------------------------------------------------
type Json = Record<string, any>;
const num = (v: unknown) => (v ? 1 : 0);

function aUsuario(u: Json): User {
  return {
    id: u.id,
    email: u.email,
    nombre: u.nombre,
    apellidos: u.apellidos,
    telefono: u.telefono ?? undefined,
    direccion: u.direccion ?? undefined,
    tipo: u.tipo,
    documento: u.documento ?? undefined,
    especialidad: (u.especialidades || []).join(', ') || undefined,
    activo: num(u.activo)
  };
}

function aMascota(m: Json): Mascota {
  return {
    ...m,
    especie_nombre: m.especie,
    tutor_nombre: m.cliente_nombre ?? undefined,
    tutor_apellidos: '',
    tutor_email: m.cliente_email ?? undefined,
    activo: num(m.activo)
  } as Mascota;
}

function aServicio(s: Json): Servicio {
  return { ...s, activo: num(s.activo) } as Servicio;
}

function aCita(c: Json): Cita {
  return {
    ...c,
    notas: c.notas ?? undefined,
    tutor_nombre: c.cliente_nombre ?? '',
    tutor_apellidos: '',
    vet_nombre: c.veterinario_nombre,
    vet_apellidos: '',
    servicio_precio: 0
  } as Cita;
}

function aHistorial(h: Json): HistorialMedico {
  return {
    ...h,
    observaciones: h.observaciones ?? undefined,
    vet_nombre: h.veterinario_nombre,
    vet_apellidos: '',
    cita_fecha: h.fecha_cita ?? undefined
  } as HistorialMedico;
}

function aSolicitud(s: Json): SolicitudAdopcion {
  return {
    ...s,
    cliente_apellidos: '',
    revisado_por: s.revisado_por_id ?? undefined,
    revisor_nombre: s.revisor_nombre ?? undefined
  } as SolicitudAdopcion;
}

function aProducto(p: Json): Producto {
  return {
    ...p,
    peso: p.peso ?? 0,
    disponible_online: num(p.disponible_online),
    activo: num(p.activo)
  } as Producto;
}

function aEstadisticas(s: Json): DashboardStats {
  return {
    total_mascotas: s.total_mascotas,
    total_citas: s.citas_totales,
    citas_hoy: s.citas_hoy,
    mascotas_adopcion: s.mascotas_en_adopcion,
    solicitudes_pendientes: s.solicitudes_pendientes,
    total_productos: s.total_productos,
    stock_bajo: s.productos_stock_bajo,
    ingresos_totales: s.ingresos_totales
  };
}

function aSesion(r: Json): Sesion {
  return { token: r.access_token, usuario: aUsuario(r.usuario) };
}

const lista = <T>(mapa: (x: Json) => T) => (datos: Json[]) => datos.map(mapa);

// ---------------------------------------------------------------------------
// Salud
// ---------------------------------------------------------------------------
export async function fetchHealth(): Promise<{ status: string; version?: string }> {
  try {
    return await request('/health', {}, 2);
  } catch {
    return { status: 'offline' };
  }
}

// ---------------------------------------------------------------------------
// Autenticación
// ---------------------------------------------------------------------------
export async function loginUser(email: string, password: string): Promise<Sesion> {
  const r = await request<Json>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
  return aSesion(r);
}

export async function registerUser(data: {
  email: string;
  password: string;
  nombre: string;
  apellidos: string;
  telefono?: string;
  direccion?: string;
}): Promise<Sesion> {
  // El registro público sólo crea clientes: no se envía `tipo`.
  const r = await request<Json>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data)
  });
  return aSesion(r);
}

export async function fetchMe(): Promise<User> {
  return aUsuario(await request<Json>('/auth/me'));
}

export async function solicitarCodigoRecuperacion(email: string): Promise<{ detail: string; codigo_debug?: string }> {
  return request('/auth/password/recuperar', {
    method: 'POST',
    body: JSON.stringify({ email })
  });
}

export async function restablecerPassword(email: string, codigo: string, passwordNueva: string): Promise<void> {
  await request('/auth/password/restablecer', {
    method: 'POST',
    body: JSON.stringify({ email, codigo, password_nueva: passwordNueva })
  });
}

// ---------------------------------------------------------------------------
// Usuarios
// ---------------------------------------------------------------------------
export async function fetchUsers(tipo?: string): Promise<User[]> {
  const q = tipo ? `?tipo=${tipo}` : '';
  return request<Json[]>(`/users${q}`).then(lista(aUsuario));
}

export async function fetchVeterinarios(): Promise<User[]> {
  return request<Json[]>('/veterinarios').then(lista(aUsuario));
}

// Especies & Servicios
export async function fetchEspecies(): Promise<Especie[]> {
  return request('/especies');
}

export async function fetchServicios(): Promise<Servicio[]> {
  return request<Json[]>('/servicios').then(lista(aServicio));
}

// ---------------------------------------------------------------------------
// Mascotas
// ---------------------------------------------------------------------------
export async function fetchMascotas(clienteId?: number, estadoAdopcion?: string, buscar?: string): Promise<Mascota[]> {
  const params = new URLSearchParams();
  if (clienteId) params.append('cliente_id', String(clienteId));
  if (estadoAdopcion) params.append('estado_adopcion', estadoAdopcion);
  if (buscar) params.append('buscar', buscar);
  const q = params.toString() ? `?${params.toString()}` : '';
  return request<Json[]>(`/mascotas${q}`).then(lista(aMascota));
}

export async function fetchMascotaDetail(id: number): Promise<Mascota> {
  return aMascota(await request<Json>(`/mascotas/${id}`));
}

export async function createMascota(data: Partial<Mascota>): Promise<Mascota> {
  return aMascota(await request<Json>('/mascotas', {
    method: 'POST',
    body: JSON.stringify(data)
  }));
}

export async function updateMascota(id: number, data: Partial<Mascota>): Promise<Mascota> {
  return aMascota(await request<Json>(`/mascotas/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }));
}

export async function deleteMascota(id: number): Promise<Mascota> {
  return aMascota(await request<Json>(`/mascotas/${id}`, { method: 'DELETE' }));
}

// ---------------------------------------------------------------------------
// Adopciones
// ---------------------------------------------------------------------------
export async function fetchAdopciones(): Promise<Mascota[]> {
  return request<Json[]>('/adopciones').then(lista(aMascota));
}

export async function fetchSolicitudesAdopcion(clienteId?: number): Promise<SolicitudAdopcion[]> {
  const q = clienteId ? `?cliente_id=${clienteId}` : '';
  return request<Json[]>(`/adopciones/solicitudes${q}`).then(lista(aSolicitud));
}

export async function createSolicitudAdopcion(mascotaId: number, clienteId: number, notasCliente: string): Promise<SolicitudAdopcion> {
  return aSolicitud(await request<Json>('/adopciones/solicitudes', {
    method: 'POST',
    body: JSON.stringify({ mascota_id: mascotaId, cliente_id: clienteId, notas_cliente: notasCliente })
  }));
}

export async function aprobarSolicitudAdopcion(id: number, revisorId: number, notasRevisor?: string): Promise<SolicitudAdopcion> {
  return aSolicitud(await request<Json>(`/adopciones/solicitudes/${id}/aprobar`, {
    method: 'PUT',
    body: JSON.stringify({ revisor_id: revisorId, notas_revisor: notasRevisor || '' })
  }));
}

export async function rechazarSolicitudAdopcion(id: number, revisorId: number, notasRevisor?: string): Promise<SolicitudAdopcion> {
  return aSolicitud(await request<Json>(`/adopciones/solicitudes/${id}/rechazar`, {
    method: 'PUT',
    body: JSON.stringify({ revisor_id: revisorId, notas_revisor: notasRevisor || '' })
  }));
}

// ---------------------------------------------------------------------------
// Citas
// ---------------------------------------------------------------------------
export async function fetchCitas(clienteId?: number, veterinarioId?: number, estado?: string): Promise<Cita[]> {
  const params = new URLSearchParams();
  if (clienteId) params.append('cliente_id', String(clienteId));
  if (veterinarioId) params.append('veterinario_id', String(veterinarioId));
  if (estado) params.append('estado', estado);
  const q = params.toString() ? `?${params.toString()}` : '';
  return request<Json[]>(`/citas${q}`).then(lista(aCita));
}

export async function createCita(data: {
  mascota_id: number;
  veterinario_id: number;
  servicio_id: number;
  fecha_hora: string;
  peso?: number;
  motivo: string;
  notas?: string;
}): Promise<Cita> {
  return aCita(await request<Json>('/citas', {
    method: 'POST',
    body: JSON.stringify(data)
  }));
}

export async function updateCitaEstado(id: number, estado: string): Promise<Cita> {
  return aCita(await request<Json>(`/citas/${id}/estado`, {
    method: 'PUT',
    body: JSON.stringify({ estado })
  }));
}

// ---------------------------------------------------------------------------
// Historiales médicos
// ---------------------------------------------------------------------------
export async function fetchHistoriales(mascotaId?: number): Promise<HistorialMedico[]> {
  const q = mascotaId ? `?mascota_id=${mascotaId}` : '';
  return request<Json[]>(`/historiales-medicos${q}`).then(lista(aHistorial));
}

export async function createHistorial(data: {
  cita_id?: number | null;
  mascota_id: number;
  veterinario_id?: number;
  diagnostico: string;
  tratamiento: string;
  observaciones?: string;
}): Promise<HistorialMedico> {
  return aHistorial(await request<Json>('/historiales-medicos', {
    method: 'POST',
    body: JSON.stringify(data)
  }));
}

// ---------------------------------------------------------------------------
// Productos & Tienda
// ---------------------------------------------------------------------------
export async function fetchProductos(categoria?: string, tipoAnimal?: string, buscar?: string): Promise<Producto[]> {
  const params = new URLSearchParams();
  if (categoria) params.append('categoria', categoria);
  if (tipoAnimal) params.append('tipo_animal', tipoAnimal);
  if (buscar) params.append('buscar', buscar);
  const q = params.toString() ? `?${params.toString()}` : '';
  return request<Json[]>(`/productos${q}`).then(lista(aProducto));
}

export async function createProducto(data: Partial<Producto>): Promise<Producto> {
  return aProducto(await request<Json>('/productos', {
    method: 'POST',
    body: JSON.stringify(data)
  }));
}

export async function updateProducto(id: number, data: Partial<Producto>): Promise<Producto> {
  return aProducto(await request<Json>(`/productos/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  }));
}

export async function deleteProducto(id: number): Promise<Producto> {
  return aProducto(await request<Json>(`/productos/${id}`, { method: 'DELETE' }));
}

// Compra directa: el carrito vive en el navegador y viaja entero en `items`.
export async function checkout(data: {
  usuario_id: number;
  items: { producto_id: number; cantidad: number }[];
  direccion: string;
  metodo_pago: string;
}): Promise<{ pedido_id: number; total: number; metodo_pago: string }> {
  return request('/checkout', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

// Dashboard (sólo personal)
export async function fetchDashboardStats(): Promise<DashboardStats> {
  return aEstadisticas(await request<Json>('/dashboard/stats'));
}

export const apiService = {
  getHealth: fetchHealth,
  getVeterinarios: fetchVeterinarios,
  getEspecies: fetchEspecies,
  getServicios: fetchServicios,
  getMascotas: fetchMascotas,
  getCitas: fetchCitas,
  getAdopciones: fetchAdopciones,
  getSolicitudesAdopcion: fetchSolicitudesAdopcion,
  getProductos: fetchProductos,
  getHistoriales: fetchHistoriales,
  getStats: fetchDashboardStats,
  createCita,
  updateCitaEstado,
  createMascota,
  solicitarAdopcion: async (data: { mascota_id: number; cliente_id: number; notas_cliente: string }) => {
    return createSolicitudAdopcion(data.mascota_id, data.cliente_id, data.notas_cliente);
  },
  revisarSolicitudAdopcion: async (id: number, data: { estado: string; revisor_id: number; notas_revisor?: string }) => {
    if (data.estado === 'aprobada') {
      return aprobarSolicitudAdopcion(id, data.revisor_id, data.notas_revisor);
    }
    return rechazarSolicitudAdopcion(id, data.revisor_id, data.notas_revisor);
  },
  createHistorial,
  createProducto,
  updateProducto,
  deleteProducto,
  createPedido: async (data: {
    cliente_id: number;
    items: { producto_id: number; cantidad: number }[];
    direccion_envio: string;
    metodo_pago: string;
  }) => {
    return checkout({
      usuario_id: data.cliente_id,
      items: data.items,
      direccion: data.direccion_envio,
      metodo_pago: data.metodo_pago
    });
  }
};
