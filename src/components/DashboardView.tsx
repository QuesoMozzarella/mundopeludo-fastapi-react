import React from 'react';
import { DashboardStats, User, Cita, Mascota } from '../types';
import { formatearFechaHora } from '../formato';
import { 
  Users, 
  Calendar, 
  Dog, 
  Heart, 
  DollarSign, 
  Package, 
  Activity, 
  Clock, 
  CheckCircle2, 
  Stethoscope, 
  ShieldCheck 
} from 'lucide-react';

interface DashboardViewProps {
  stats: DashboardStats | null;
  currentUser: User;
  citas: Cita[];
  mascotas: Mascota[];
  onNavigate: (tab: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  stats,
  currentUser,
  citas,
  mascotas,
  onNavigate,
}) => {
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-600 bg-amber-50 px-2.5 py-0.5 rounded-full">
              Panel de Control
            </span>
            <span className="text-xs text-slate-400 capitalize">
              Rol: <strong>{currentUser.tipo}</strong>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Bienvenido/a, {currentUser.nombre} {currentUser.apellidos}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Monitoreo en tiempo real de la clínica veterinaria MundoPeludo.
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-400 mb-3">
              <span className="text-xs font-bold uppercase tracking-wider">Pacientes</span>
              <Dog className="w-5 h-5 text-amber-500" />
            </div>
            <div className="text-3xl font-extrabold text-slate-900">{stats.total_mascotas}</div>
            <div className="text-xs text-slate-500 mt-1">Mascotas activas en clínica</div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-400 mb-3">
              <span className="text-xs font-bold uppercase tracking-wider">Citas Médicas</span>
              <Calendar className="w-5 h-5 text-blue-500" />
            </div>
            <div className="text-3xl font-extrabold text-slate-900">{stats.total_citas}</div>
            <div className="text-xs text-slate-500 mt-1">
              <span className="text-emerald-600 font-semibold">{stats.citas_activas ?? 2} activas</span> • {stats.solicitudes_pendientes ?? 0} pendientes
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-400 mb-3">
              <span className="text-xs font-bold uppercase tracking-wider">En Adopción</span>
              <Heart className="w-5 h-5 text-rose-500" />
            </div>
            <div className="text-3xl font-extrabold text-rose-600">{stats.mascotas_adopcion}</div>
            <div className="text-xs text-slate-500 mt-1">Rescatados buscando familia</div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-400 mb-3">
              <span className="text-xs font-bold uppercase tracking-wider">Ventas Tienda</span>
              <DollarSign className="w-5 h-5 text-emerald-500" />
            </div>
            <div className="text-2xl sm:text-3xl font-extrabold text-slate-900">
              ${(stats.ingresos_totales ?? stats.total_ventas ?? 0).toLocaleString('es-CL')}
            </div>
            <div className="text-xs text-slate-500 mt-1">Facturación acumulada</div>
          </div>
        </div>
      )}

      {/* Two Column Layout: Next appointments and Quick actions */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Next Appointments */}
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200 p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-lg text-slate-900">Próximas Citas Veterinarias</h3>
              <p className="text-xs text-slate-500">Agenda médica reciente</p>
            </div>
            <button
              onClick={() => onNavigate('citas')}
              className="text-xs font-bold text-amber-600 hover:text-amber-700"
            >
              Ver agenda completa
            </button>
          </div>

          <div className="space-y-3">
            {citas.slice(0, 4).map((c) => (
              <div 
                key={c.id} 
                className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-xs"
              >
                <div className="flex items-center gap-3">
                  <img 
                    src={c.mascota_imagen || "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=100&auto=format&fit=crop&q=80"} 
                    alt={c.mascota_nombre} 
                    className="w-10 h-10 rounded-lg object-cover"
                  />
                  <div>
                    <h4 className="font-bold text-slate-900">{c.mascota_nombre}</h4>
                    <p className="text-slate-500 text-[11px]">{c.servicio_nombre} con {c.vet_nombre}</p>
                  </div>
                </div>

                <div className="text-right">
                  <div className="font-bold text-slate-800">{formatearFechaHora(c.fecha_hora)}</div>
                  <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold mt-0.5 ${
                    c.estado === 'Confirmada' ? 'bg-emerald-100 text-emerald-800' :
                    c.estado === 'Pendiente' ? 'bg-amber-100 text-amber-800' :
                    c.estado === 'Completada' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-700'
                  }`}>
                    {c.estado}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Operations / Stack architecture */}
        <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-6">
          <div>
            <h3 className="font-bold text-lg text-slate-900 mb-1">Acciones Rápidas</h3>
            <p className="text-xs text-slate-500 mb-4">Accesos directos más utilizados</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                onClick={() => onNavigate('citas')}
                className="p-3 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-800 font-bold text-left transition-colors flex flex-col gap-1"
              >
                <Calendar className="w-4 h-4 text-amber-600" />
                <span>Agendar Cita</span>
              </button>

              <button
                onClick={() => onNavigate('mascotas')}
                className="p-3 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 font-bold text-left transition-colors flex flex-col gap-1"
              >
                <Dog className="w-4 h-4 text-slate-600" />
                <span>Nueva Mascota</span>
              </button>

              <button
                onClick={() => onNavigate('historial')}
                className="p-3 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-800 font-bold text-left transition-colors flex flex-col gap-1"
              >
                <Stethoscope className="w-4 h-4 text-blue-600" />
                <span>Historial Médico</span>
              </button>

              <button
                onClick={() => onNavigate('tienda')}
                className="p-3 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 font-bold text-left transition-colors flex flex-col gap-1"
              >
                <Package className="w-4 h-4 text-emerald-600" />
                <span>Tienda & Stock</span>
              </button>
            </div>
          </div>

          {/* Architecture info */}
          <div className="pt-4 border-t border-slate-100">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Arquitectura de la App</h4>
            <div className="space-y-2 text-xs text-slate-600">
              <div className="flex items-center justify-between bg-slate-50 p-2 rounded-lg">
                <span className="font-semibold text-slate-700">API Backend:</span>
                <span className="font-mono text-emerald-600 font-bold">FastAPI 0.115 + Python</span>
              </div>
              <div className="flex items-center justify-between bg-slate-50 p-2 rounded-lg">
                <span className="font-semibold text-slate-700">Servidor Web / Proxy:</span>
                <span className="font-mono text-slate-800 font-bold">Node.js Express</span>
              </div>
              <div className="flex items-center justify-between bg-slate-50 p-2 rounded-lg">
                <span className="font-semibold text-slate-700">Frontend UI:</span>
                <span className="font-mono text-blue-600 font-bold">React 18 + Tailwind</span>
              </div>
              <div className="flex items-center justify-between bg-slate-50 p-2 rounded-lg">
                <span className="font-semibold text-slate-700">Base de Datos:</span>
                <span className="font-mono text-purple-600 font-bold">SQLite Persistente</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
