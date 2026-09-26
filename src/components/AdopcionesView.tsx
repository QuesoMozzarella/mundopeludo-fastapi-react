import React, { useState } from 'react';
import { Mascota, SolicitudAdopcion, User } from '../types';
import { formatearFecha } from '../formato';
import { 
  Heart, 
  CheckCircle, 
  XCircle, 
  Clock, 
  FileText, 
  Home, 
  User as UserIcon, 
  Sparkles, 
  X, 
  AlertCircle 
} from 'lucide-react';

interface AdopcionesViewProps {
  adopciones: Mascota[];
  solicitudes: SolicitudAdopcion[];
  /** null = visitante: ve el catálogo, pero postular pide iniciar sesión. */
  currentUser: User | null;
  onRequiereLogin: () => void;
  onApplyAdopcion: (mascotaId: number, clienteId: number, notas: string) => Promise<void>;
  onAprobarSolicitud: (solicitudId: number, revisorId: number, notas?: string) => Promise<void>;
  onRechazarSolicitud: (solicitudId: number, revisorId: number, notas?: string) => Promise<void>;
}

export const AdopcionesView: React.FC<AdopcionesViewProps> = ({
  adopciones,
  solicitudes,
  currentUser,
  onRequiereLogin,
  onApplyAdopcion,
  onAprobarSolicitud,
  onRechazarSolicitud
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'catalogo' | 'solicitudes'>('catalogo');
  const [selectedPetForAdoption, setSelectedPetForAdoption] = useState<Mascota | null>(null);
  const [notasCliente, setNotasCliente] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reviewNotes, setReviewNotes] = useState<{ [id: number]: string }>({});

  const handleApplySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPetForAdoption || !currentUser) return;

    if (!notasCliente.trim()) {
      alert('Por favor cuéntanos por qué deseas adoptar y las condiciones del hogar.');
      return;
    }

    try {
      setIsSubmitting(true);
      await onApplyAdopcion(selectedPetForAdoption.id, currentUser.id, notasCliente);
      setSelectedPetForAdoption(null);
      setNotasCliente('');
      setActiveSubTab('solicitudes');
    } catch (err: any) {
      alert(err.message || 'Error al enviar solicitud de adopción.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (estado: string) => {
    switch (estado) {
      case 'aprobada':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">Aprobada</span>;
      case 'pendiente':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">En Revisión</span>;
      case 'rechazada':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200">Rechazada</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800">{estado}</span>;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <span>Programa de Adopciones</span>
            <span className="text-rose-500">❤️</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Dales una segunda oportunidad. Todas nuestras mascotas están esterilizadas, vacunadas y desparasitadas.
          </p>
        </div>

        {/* Subtab selector */}
        <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200 self-start sm:self-auto">
          <button
            id="subtab-catalogo-adopciones"
            onClick={() => setActiveSubTab('catalogo')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${activeSubTab === 'catalogo' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'}`}
          >
            Mascotas Disponibles ({adopciones.length})
          </button>
          {currentUser && (
            <button
              id="subtab-solicitudes-adopciones"
              onClick={() => setActiveSubTab('solicitudes')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${activeSubTab === 'solicitudes' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'}`}
            >
              Gestión de Solicitudes ({solicitudes.length})
            </button>
          )}
        </div>
      </div>

      {activeSubTab === 'catalogo' ? (
        <div>
          {adopciones.length === 0 ? (
            <div className="bg-white rounded-3xl border border-dashed border-slate-300 p-16 text-center">
              <Heart className="w-12 h-12 text-rose-300 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800">No hay mascotas en adopción en este momento</h3>
              <p className="text-xs text-slate-500 mt-1">
                ¡Todas nuestras mascotas rescatadas han encontrado un hogar responsable!
              </p>
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {adopciones.map((pet) => (
                <div 
                  key={pet.id}
                  className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-xs hover:shadow-lg transition-all flex flex-col justify-between group"
                >
                  <div>
                    <div className="relative h-60 overflow-hidden bg-slate-100">
                      <img 
                        src={pet.imagen_url || "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=600&auto=format&fit=crop&q=80"} 
                        alt={pet.nombre}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                      <div className="absolute top-3 left-3 bg-rose-600 text-white text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full shadow-md flex items-center gap-1">
                        <Sparkles className="w-3 h-3" />
                        <span>En Adopción</span>
                      </div>
                      <div className="absolute bottom-3 right-3 bg-white/95 backdrop-blur-xs text-slate-900 text-xs font-bold px-2.5 py-1 rounded-full shadow-2xs">
                        {pet.especie_nombre}
                      </div>
                    </div>

                    <div className="p-6">
                      <div className="flex items-baseline justify-between mb-2">
                        <h3 className="text-xl font-bold text-slate-900">{pet.nombre}</h3>
                        <span className="text-xs font-semibold text-slate-500">{pet.raza || 'Mestizo'}</span>
                      </div>

                      <p className="text-sm text-slate-600 leading-relaxed mb-4">
                        {pet.descripcion || 'Una mascota dulce y cariñosa lista para llenar tu hogar de felicidad.'}
                      </p>

                      <div className="grid grid-cols-2 gap-2 text-xs bg-rose-50/50 p-3 rounded-2xl border border-rose-100/60 mb-2">
                        <div>
                          <span className="text-slate-400 font-medium">Edad:</span>{' '}
                          <span className="font-bold text-slate-800">{pet.edad_anos} {pet.edad_anos === 1 ? 'año' : 'años'}</span>
                        </div>
                        <div>
                          <span className="text-slate-400 font-medium">Sexo:</span>{' '}
                          <span className="font-bold text-slate-800">{pet.sexo}</span>
                        </div>
                        <div>
                          <span className="text-slate-400 font-medium">Peso:</span>{' '}
                          <span className="font-bold text-slate-800">{pet.peso} kg</span>
                        </div>
                        <div>
                          <span className="text-slate-400 font-medium">Esterilizado:</span>{' '}
                          <span className="font-bold text-emerald-600">✓ Sí</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-6 pt-0">
                    <button
                      id={`btn-solicitar-adopcion-${pet.id}`}
                      onClick={() => (currentUser ? setSelectedPetForAdoption(pet) : onRequiereLogin())}
                      className="w-full py-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-md shadow-rose-600/20 transition-all flex items-center justify-center gap-2"
                    >
                      <Heart className="w-4 h-4" />
                      <span>Postular a Adoptar a {pet.nombre}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Solicitudes de Adopción */
        <div className="space-y-4">
          {solicitudes.length === 0 ? (
            <div className="bg-white rounded-3xl border border-dashed border-slate-300 p-12 text-center">
              <FileText className="w-10 h-10 text-slate-400 mx-auto mb-2" />
              <h4 className="text-sm font-bold text-slate-700">No hay solicitudes registradas</h4>
              <p className="text-xs text-slate-500 mt-1">
                Cuando un cliente postule para adoptar una mascota, aparecerá aquí para revisión.
              </p>
            </div>
          ) : (
            solicitudes.map((sol) => (
              <div 
                key={sol.id}
                className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6"
              >
                <div className="flex items-start gap-4">
                  <img 
                    src={sol.mascota_imagen || "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=200&auto=format&fit=crop&q=80"} 
                    alt={sol.mascota_nombre} 
                    className="w-16 h-16 rounded-2xl object-cover shrink-0 border border-slate-100 shadow-2xs"
                  />
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <h4 className="text-base font-bold text-slate-900">
                        Postulación por {sol.mascota_nombre}
                      </h4>
                      {getStatusBadge(sol.estado)}
                    </div>

                    <div className="text-xs text-slate-500 flex flex-wrap items-center gap-x-4 gap-y-1 mb-2">
                      <span className="flex items-center gap-1 font-semibold text-slate-700">
                        <UserIcon className="w-3.5 h-3.5 text-amber-500" />
                        {sol.cliente_nombre} {sol.cliente_apellidos}
                      </span>
                      <span>Email: {sol.cliente_email}</span>
                      <span>Tel: {sol.cliente_telefono || 'No indicado'}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        {formatearFecha(sol.fecha_solicitud)}
                      </span>
                    </div>

                    <div className="bg-slate-50 rounded-xl p-3 text-xs text-slate-700 max-w-2xl">
                      <span className="font-bold text-slate-900 block mb-1">Motivación del adoptante:</span>
                      "{sol.notas_cliente}"
                    </div>

                    {sol.notas_revisor && (
                      <div className="mt-2 text-xs text-slate-600 bg-amber-50 p-2 rounded-lg">
                        <strong>Nota del revisor:</strong> {sol.notas_revisor}
                      </div>
                    )}
                  </div>
                </div>

                {/* Approver actions for Vet / Admin */}
                {currentUser && (currentUser.tipo === 'veterinario' || currentUser.tipo === 'administrador') && sol.estado === 'pendiente' && (
                  <div className="flex flex-col sm:flex-row items-end gap-2 shrink-0">
                    <input
                      type="text"
                      placeholder="Notas de revisión (opcional)..."
                      value={reviewNotes[sol.id] || ''}
                      onChange={(e) => setReviewNotes({ ...reviewNotes, [sol.id]: e.target.value })}
                      className="px-3 py-1.5 rounded-lg border border-slate-300 text-xs w-full sm:w-48"
                    />
                    <div className="flex gap-2">
                      <button
                        id={`btn-aprobar-solicitud-${sol.id}`}
                        onClick={() => onAprobarSolicitud(sol.id, currentUser.id, reviewNotes[sol.id])}
                        className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center gap-1 transition-colors shadow-2xs"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span>Aprobar</span>
                      </button>

                      <button
                        id={`btn-rechazar-solicitud-${sol.id}`}
                        onClick={() => onRechazarSolicitud(sol.id, currentUser.id, reviewNotes[sol.id])}
                        className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-rose-50 text-slate-600 hover:text-rose-600 text-xs font-semibold flex items-center gap-1 transition-colors"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Rechazar</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Modal Formulario de Adopción */}
      {selectedPetForAdoption && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden my-8">
            <div className="bg-rose-600 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Heart className="w-5 h-5 text-white" />
                <h3 className="font-bold text-lg">Solicitud de Adopción Responsable</h3>
              </div>
              <button 
                onClick={() => setSelectedPetForAdoption(null)}
                className="text-rose-200 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleApplySubmit} className="p-6 space-y-4">
              <div className="flex items-center gap-4 p-3 bg-rose-50 rounded-2xl border border-rose-100">
                <img 
                  src={selectedPetForAdoption.imagen_url || '/img/default-pet.jpg'} 
                  alt={selectedPetForAdoption.nombre} 
                  className="w-14 h-14 rounded-xl object-cover"
                />
                <div>
                  <h4 className="font-bold text-slate-900">{selectedPetForAdoption.nombre}</h4>
                  <p className="text-xs text-slate-500">{selectedPetForAdoption.especie_nombre} • {selectedPetForAdoption.edad_anos} años</p>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Tus Datos de Contacto
                </label>
                <div className="bg-slate-50 p-3 rounded-xl text-xs text-slate-700">
                  <p><strong>Postulante:</strong> {currentUser?.nombre} {currentUser?.apellidos}</p>
                  <p><strong>Email:</strong> {currentUser?.email}</p>
                  <p><strong>Teléfono:</strong> {currentUser?.telefono || 'Sin registrar'}</p>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  ¿Por qué deseas adoptar y cómo es tu hogar? *
                </label>
                <textarea
                  id="textarea-motivo-adopcion"
                  rows={4}
                  placeholder="Cuéntanos si vives en casa o departamento, si tienes patio cerrado, otras mascotas, horario disponible para paseos y compromiso veterinario..."
                  value={notasCliente}
                  onChange={(e) => setNotasCliente(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500 resize-none"
                  required
                />
              </div>

              <div className="flex items-start gap-2 text-[11px] text-slate-500">
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span>
                  Al enviar esta solicitud, me comprometo a brindar alimentación de calidad, controles veterinarios periódicos y un entorno lleno de amor y seguridad.
                </span>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setSelectedPetForAdoption(null)}
                  className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-sm font-semibold hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  id="btn-enviar-solicitud-adopcion"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-sm font-bold shadow-md transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? 'Enviando...' : 'Enviar Postulación'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
