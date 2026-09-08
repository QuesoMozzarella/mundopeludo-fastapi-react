import {
  User, Especie, Mascota, SolicitudAdopcion, Servicio,
  Cita, HistorialMedico, Producto, CarritoItem, DashboardStats
} from './types';

const API_BASE = '/api';

async function wait(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function request<T>(endpoint: string, options: RequestInit = {}, retries = 2): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  const isGet = !options.method || options.method === 'GET';
  let lastError: any = null;

  for (let attempt = 0; attempt <= (isGet ? retries : 0); attempt++) {
    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let errorMsg = `Error HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          errorMsg = errorData.detail || errorData.message || errorMsg;
        } catch {
          errorMsg = response.statusText || errorMsg;
        }

        // If backend is warming up (500, 502, 503, 504), retry with backoff for GET
        if (isGet && attempt < retries && [500, 502, 503, 504].includes(response.status)) {
          await wait(350 * (attempt + 1));
          continue;
        }
        throw new Error(errorMsg);
      }
      return await response.json();
    } catch (err: any) {
      lastError = err;
      if (isGet && attempt < retries) {
        await wait(350 * (attempt + 1));
        continue;
      }
      throw err;
    }
  }
  throw lastError || new Error('Error en la petición');
}

// Health check
export async function fetchHealth(): Promise<{ status: string; service: string; timestamp: string; database?: string }> {
  try {
    return await request('/health', {}, 2);
  } catch {
    return {
      status: 'offline',
      service: 'MundoPeludo FastAPI Backend',
      timestamp: new Date().toISOString(),
      database: 'Conectando...'
    };
  }
}

// Auth & Users
export async function loginUser(email: string, password: string): Promise<{ user: User; token: string }> {
  return request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
}

export async function registerUser(data: {
  email: string;
  password: string;
  nombre: string;
  apellidos: string;
  telefono?: string;
  direccion?: string;
  tipo?: string;
}): Promise<{ user: User; token: string }> {
  return request('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function fetchUsers(tipo?: string): Promise<User[]> {
  const q = tipo ? `?tipo=${tipo}` : '';
  return request(`/users${q}`);
}

export async function fetchVeterinarios(): Promise<User[]> {
  return request('/veterinarios');
}

// Especies & Servicios
export async function fetchEspecies(): Promise<Especie[]> {
  return request('/especies');
}

export async function fetchServicios(): Promise<Servicio[]> {
  return request('/servicios');
}

// Mascotas
export async function fetchMascotas(clienteId?: number, estadoAdopcion?: string, search?: string): Promise<Mascota[]> {
  const params = new URLSearchParams();
  if (clienteId) params.append('cliente_id', String(clienteId));
  if (estadoAdopcion) params.append('estado_adopcion', estadoAdopcion);
  if (search) params.append('search', search);
  const q = params.toString() ? `?${params.toString()}` : '';
  return request(`/mascotas${q}`);
}

export async function fetchMascotaDetail(id: number): Promise<Mascota> {
  return request(`/mascotas/${id}`);
}

export async function createMascota(data: Partial<Mascota>): Promise<Mascota> {
  return request('/mascotas', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function updateMascota(id: number, data: Partial<Mascota>): Promise<Mascota> {
  return request(`/mascotas/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function deleteMascota(id: number): Promise<{ success: boolean; message: string }> {
  return request(`/mascotas/${id}`, {
    method: 'DELETE'
  });
}

// Adopciones
export async function fetchAdopciones(): Promise<Mascota[]> {
  return request('/adopciones');
}

export async function fetchSolicitudesAdopcion(clienteId?: number): Promise<SolicitudAdopcion[]> {
  const q = clienteId ? `?cliente_id=${clienteId}` : '';
  return request(`/adopciones/solicitudes${q}`);
}

export async function createSolicitudAdopcion(mascotaId: number, clienteId: number, notasCliente: string): Promise<{ id: number; message: string }> {
  return request('/adopciones/solicitudes', {
    method: 'POST',
    body: JSON.stringify({ mascota_id: mascotaId, cliente_id: clienteId, notas_cliente: notasCliente })
  });
}

export async function aprobarSolicitudAdopcion(id: number, revisorId: number, notasRevisor?: string): Promise<{ success: boolean; message: string }> {
  return request(`/adopciones/solicitudes/${id}/aprobar`, {
    method: 'PUT',
    body: JSON.stringify({ revisor_id: revisorId, notas_revisor: notasRevisor || '' })
  });
}

export async function rechazarSolicitudAdopcion(id: number, revisorId: number, notasRevisor?: string): Promise<{ success: boolean; message: string }> {
  return request(`/adopciones/solicitudes/${id}/rechazar`, {
    method: 'PUT',
    body: JSON.stringify({ revisor_id: revisorId, notas_revisor: notasRevisor || '' })
  });
}

// Citas
export async function fetchCitas(clienteId?: number, veterinarioId?: number, estado?: string): Promise<Cita[]> {
  const params = new URLSearchParams();
  if (clienteId) params.append('cliente_id', String(clienteId));
  if (veterinarioId) params.append('veterinario_id', String(veterinarioId));
  if (estado) params.append('estado', estado);
  const q = params.toString() ? `?${params.toString()}` : '';
  return request(`/citas${q}`);
}

export async function createCita(data: {
  mascota_id: number;
  veterinario_id: number;
  servicio_id: number;
  fecha_hora: string;
  peso?: number;
  motivo: string;
  notas?: string;
}): Promise<{ id: number; message: string; estado: string }> {
  return request('/citas', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function updateCitaEstado(id: number, estado: string): Promise<{ success: boolean; estado: string }> {
  return request(`/citas/${id}/estado`, {
    method: 'PUT',
    body: JSON.stringify({ estado })
  });
}

// Historiales Médicos
export async function fetchHistoriales(mascotaId?: number): Promise<HistorialMedico[]> {
  const q = mascotaId ? `?mascota_id=${mascotaId}` : '';
  return request(`/historiales-medicos${q}`);
}

export async function createHistorial(data: {
  cita_id?: number | null;
  mascota_id: number;
  veterinario_id: number;
  diagnostico: string;
  tratamiento: string;
  observaciones?: string;
}): Promise<{ id: number; message: string }> {
  return request('/historiales-medicos', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

// Productos & Tienda
export async function fetchProductos(categoria?: string, tipoAnimal?: string, search?: string): Promise<Producto[]> {
  const params = new URLSearchParams();
  if (categoria) params.append('categoria', categoria);
  if (tipoAnimal) params.append('tipo_animal', tipoAnimal);
  if (search) params.append('search', search);
  const q = params.toString() ? `?${params.toString()}` : '';
  return request(`/productos${q}`);
}

export async function createProducto(data: Partial<Producto>): Promise<{ id: number; sku: string; message: string }> {
  return request('/productos', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

export async function updateProducto(id: number, data: Partial<Producto>): Promise<{ success: boolean; message: string }> {
  return request(`/productos/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

export async function deleteProducto(id: number): Promise<{ success: boolean; message: string }> {
  return request(`/productos/${id}`, {
    method: 'DELETE'
  });
}

// Carrito
export async function fetchCarrito(userId: number): Promise<{ items: CarritoItem[]; total: number; total_items: number }> {
  return request(`/carrito/${userId}`);
}

export async function addToCarrito(userId: number, productoId: number, cantidad: number = 1): Promise<{ success: boolean }> {
  return request(`/carrito/${userId}`, {
    method: 'POST',
    body: JSON.stringify({ producto_id: productoId, cantidad })
  });
}

export async function removeFromCarrito(userId: number, productoId: number): Promise<{ success: boolean }> {
  return request(`/carrito/${userId}/${productoId}`, {
    method: 'DELETE'
  });
}

export async function clearCarrito(userId: number): Promise<{ success: boolean }> {
  return request(`/carrito/${userId}`, {
    method: 'DELETE'
  });
}

export async function checkout(userId: number, metodoPago: string, direccion: string): Promise<{
  success: boolean;
  pedido_id: number;
  total: number;
  metodo_pago: string;
  message: string;
}> {
  return request('/checkout', {
    method: 'POST',
    body: JSON.stringify({
      usuario_id: userId,
      metodo_pago: metodoPago,
      direccion: direccion
    })
  });
}

// Dashboard
export async function fetchDashboardStats(): Promise<DashboardStats> {
  return request('/dashboard/stats');
}

export const apiService = {
  getHealth: fetchHealth,
  getUsuarios: fetchUsers,
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
    } else {
      return rechazarSolicitudAdopcion(id, data.revisor_id, data.notas_revisor);
    }
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
    // Check if user has items in cart or direct checkout
    return request('/checkout', {
      method: 'POST',
      body: JSON.stringify({
        usuario_id: data.cliente_id,
        metodo_pago: data.metodo_pago,
        direccion: data.direccion_envio,
        items: data.items
      })
    });
  }
};

