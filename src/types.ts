export type UserTipo = 'cliente' | 'veterinario' | 'administrador';

export interface User {
  id: number;
  email: string;
  nombre: string;
  apellidos: string;
  telefono?: string;
  direccion?: string;
  tipo: UserTipo;
  documento?: string;
  especialidad?: string;
  activo: number;
}

export interface Sesion {
  token: string;
  usuario: User;
}

export interface Especie {
  id: number;
  nombre: string;
}

export interface Servicio {
  id: number;
  nombre: string;
  descripcion: string;
  // Minutos de agenda que ocupa cada cita del servicio.
  duracion_min: number;
  // Sin precio publicado, no llega.
  precio?: number;
  // Vacío: lo puede prestar cualquier veterinario.
  veterinarios_ids: number[];
  activo: number;
}

/** Franja semanal de atención de un veterinario (0 = lunes … 6 = domingo). */
export interface Disponibilidad {
  id: number;
  veterinario_id: number;
  veterinario_nombre: string;
  dia_semana: number;
  dia: string;
  hora_inicio: string; // "HH:MM:SS"
  hora_fin: string;
}

export interface Mascota {
  id: number;
  cliente_id?: number | null;
  especie_id: number;
  especie_nombre?: string;
  nombre: string;
  raza?: string;
  edad_anos: number;
  sexo: 'Macho' | 'Hembra';
  color: string;
  peso: number;
  esta_esterilizado: number | boolean;
  activo: number;
  fecha_registro: string;
  estado_adopcion: 'normal' | 'en_adopcion' | 'adoptada' | 'pendiente';
  imagen_url?: string;
  descripcion?: string;
  tutor_nombre?: string;
  tutor_apellidos?: string;
  tutor_telefono?: string;
  tutor_email?: string;
  historial?: HistorialMedico[];
}

export interface SolicitudAdopcion {
  id: number;
  mascota_id: number;
  cliente_id: number;
  fecha_solicitud: string;
  fecha_actualizacion: string;
  estado: 'pendiente' | 'aprobada' | 'rechazada' | 'cancelada';
  notas_cliente: string;
  notas_revisor?: string;
  revisado_por?: number;
  fecha_revision?: string;
  mascota_nombre: string;
  mascota_raza?: string;
  mascota_imagen?: string;
  mascota_estado?: string;
  cliente_nombre: string;
  cliente_apellidos: string;
  cliente_email: string;
  cliente_telefono?: string;
  revisor_nombre?: string;
  revisor_apellidos?: string;
}

export interface Cita {
  id: number;
  mascota_id: number;
  veterinario_id: number;
  servicio_id: number;
  fecha_hora: string;
  peso: number;
  motivo: string;
  notas?: string;
  estado: 'Confirmada' | 'Pendiente' | 'Completada' | 'Cancelada';
  created_at?: string;
  mascota_nombre: string;
  mascota_raza?: string;
  mascota_imagen?: string;
  tutor_nombre: string;
  tutor_apellidos: string;
  tutor_telefono?: string;
  tutor_email?: string;
  vet_nombre: string;
  vet_apellidos: string;
  vet_especialidad?: string;
  servicio_nombre: string;
  tiene_historial?: boolean;
  servicio_precio?: number;
  servicio_duracion_min: number;
}

export interface HistorialMedico {
  id: number;
  cita_id?: number | null;
  mascota_id: number;
  veterinario_id: number;
  diagnostico: string;
  tratamiento: string;
  observaciones?: string;
  fecha_creacion: string;
  mascota_nombre?: string;
  mascota_raza?: string;
  vet_nombre?: string;
  vet_apellidos?: string;
  cita_motivo?: string;
  cita_fecha?: string;
}

export interface Producto {
  id: number;
  nombre: string;
  descripcion?: string;
  categoria: string;
  marca?: string;
  precio: number;
  descuento_porcentaje: number;
  precio_final: number;
  stock: number;
  stock_minimo: number;
  total_vendidos: number;
  tipo_animal: string;
  unidad_medida: string;
  peso: number;
  sku: string;
  // La más reciente de las imágenes subidas (`imagenes_ids`), si hay alguna.
  imagen_url?: string;
  imagenes_ids: number[];
  disponible_online: number;
  activo: number;
  stock_bajo?: boolean;
}

export interface CarritoItem {
  id: number;
  producto_id: number;
  cantidad: number;
  nombre: string;
  precio: number;
  descuento_porcentaje: number;
  precio_final: number;
  subtotal: number;
  imagen_url?: string;
  stock: number;
  sku: string;
}

export interface CartItem {
  producto: Producto;
  cantidad: number;
}

export interface DashboardStats {
  total_mascotas: number;
  total_citas: number;
  citas_activas?: number;
  citas_hoy?: number;
  citas_pendientes?: number;
  mascotas_adopcion: number;
  solicitudes_pendientes?: number;
  total_productos?: number;
  stock_bajo?: number;
  ingresos_totales?: number;
  total_ventas?: number;
}

