import React, { useEffect, useState } from 'react';
import { Cita, Mascota, Servicio, User } from '../types';
import { formatearFechaHora } from '../formato';
import { fetchHorasLibres } from '../api';

/** Fecha local "AAAA-MM-DD" dentro de `dias` días (toISOString daría la de UTC). */
function fechaLocal(dias: number): string {
  const d = new Date();
  d.setDate(d.getDate() + dias);
  const dos = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${dos(d.getMonth() + 1)}-${dos(d.getDate())}`;
}
import { 
  Calendar, 
  Clock, 
  Plus, 
  CheckCircle, 
  XCircle, 
  FileText, 
  User as UserIcon, 
  Filter, 
  AlertCircle,
  Stethoscope,
  X
} from 'lucide-react';

interface CitasViewProps {
  citas: Cita[];
  mascotas: Mascota[];
  servicios: Servicio[];
  veterinarios: User[];
  currentUser: User;
  onBookCita: (data: {
    mascota_id: number;
    veterinario_id: number;
    servicio_id: number;
    fecha_hora: string;
    peso?: number;
    motivo: string;
    notas?: string;
  }) => Promise<void>;
  onUpdateEstado: (id: number, estado: string) => Promise<void>;
  onOpenHistorialModal: (cita: Cita) => void;
  preselectedServicioId?: number | null;
}

export const CitasView: React.FC<CitasViewProps> = ({
  citas,
  mascotas,
  servicios,
  veterinarios,
  currentUser,
  onBookCita,
  onUpdateEstado,
  onOpenHistorialModal,
  preselectedServicioId
}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [estadoFilter, setEstadoFilter] = useState<string>('todos');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form State
  const [mascotaId, setMascotaId] = useState<number>(mascotas[0]?.id || 1);
  const [servicioId, setServicioId] = useState<number>(preselectedServicioId || servicios[0]?.id || 1);
  const [veterinarioId, setVeterinarioId] = useState<number>(veterinarios[0]?.id || 2);
  const [fecha, setFecha] = useState<string>(() => fechaLocal(1));
  const [hora, setHora] = useState<string>('');
  const [motivo, setMotivo] = useState<string>('');
  const [peso, setPeso] = useState<number>(10);
  const [notas, setNotas] = useState<string>('');
  // null mientras se consultan; [] si ese día no hay huecos.
  const [horasLibres, setHorasLibres] = useState<string[] | null>(null);
  const [errorHoras, setErrorHoras] = useState<string | null>(null);
  const [consultaHoras, setConsultaHoras] = useState(0);

  // Sólo los veterinarios que prestan el servicio (sin asignados, todos).
  const servicioElegido = servicios.find((s) => s.id === servicioId);
  const veterinariosDelServicio = veterinarios.filter(
    (v) => !servicioElegido?.veterinarios_ids?.length || servicioElegido.veterinarios_ids.includes(v.id)
  );

  useEffect(() => {
    if (veterinariosDelServicio.length && !veterinariosDelServicio.some((v) => v.id === veterinarioId)) {
      setVeterinarioId(veterinariosDelServicio[0].id);
    }
  }, [servicioId, veterinarios]);

  // Las horas salen de la agenda del veterinario: sus franjas, sin las citas
  // que ya ocupan el día y sólo donde cabe la duración del servicio.
  useEffect(() => {
    if (!modalOpen || !fecha || !veterinarioId) return;
    let vigente = true;
    setHorasLibres(null);
    setErrorHoras(null);
    fetchHorasLibres(veterinarioId, fecha, servicioId)
      .then((horas) => {
        if (!vigente) return;
        setHorasLibres(horas);
        setHora((actual) => (horas.includes(actual) ? actual : horas[0] ?? ''));
      })
      .catch((err) => {
        if (!vigente) return;
        setHorasLibres([]);
        setHora('');
        setErrorHoras(err.message || 'No se pudieron consultar las horas libres.');
      });
    return () => {
      vigente = false;
    };
  }, [modalOpen, veterinarioId, fecha, servicioId, consultaHoras]);

  // Filter citas based on role and tab
  const filteredCitas = citas.filter((c) => {
    // Si es cliente, solo ve sus citas o todas si es admin/vet
    if (currentUser.tipo === 'cliente' && c.tutor_email !== currentUser.email && c.tutor_nombre !== currentUser.nombre) {
      // Si el cliente no coincide, verificar por ID de mascota
      const userPets = mascotas.filter(m => m.cliente_id === currentUser.id).map(m => m.id);
      if (!userPets.includes(c.mascota_id)) return false;
    }

    if (estadoFilter !== 'todos' && c.estado !== estadoFilter) {
      return false;
    }
    return true;
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!motivo.trim()) {
      setErrorMsg('Por favor describe el motivo de la cita médica.');
      return;
    }
    if (!hora) {
      setErrorMsg('Elige una hora libre.');
      return;
    }

    try {
      setIsSubmitting(true);
      const fechaHora = `${fecha} ${hora}:00`;
      await onBookCita({
        mascota_id: Number(mascotaId),
        veterinario_id: Number(veterinarioId),
        servicio_id: Number(servicioId),
        fecha_hora: fechaHora,
        peso: Number(peso),
        motivo,
        notas
      });

      setModalOpen(false);
      setMotivo('');
      setNotas('');
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al agendar la cita.');
      // Quizá alguien ocupó la hora mientras tanto: se vuelven a pedir.
      setConsultaHoras((n) => n + 1);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (estado: string) => {
    switch (estado) {
      case 'Confirmada':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#5dca88] text-white">Confirmada</span>;
      case 'Pendiente':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#ff9f43] text-white">Pendiente</span>;
      case 'Completada':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#1d95c8] text-white">Completada</span>;
      case 'Cancelada':
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500 text-white">Cancelada</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-200 text-slate-800">{estado}</span>;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header and Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#156a8e] tracking-tight">
            Gestión de Citas Médicas
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Agenda consultas, cirugías, vacunación y mantén seguimiento de la agenda veterinaria.
          </p>
        </div>

        <button
          id="btn-nueva-cita"
          onClick={() => setModalOpen(true)}
          className="px-5 py-2.5 rounded-xl bg-[#ff9f43] hover:bg-[#f08e30] text-white font-bold text-sm shadow-sm flex items-center justify-center gap-2 transition-all self-start sm:self-auto active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>Nueva Cita</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-1.5 text-xs font-bold text-[#156a8e] uppercase tracking-wider mr-2">
          <Filter className="w-3.5 h-3.5" />
          <span>Filtrar:</span>
        </div>
        {[
          { id: 'todos', label: 'Todas las citas' },
          { id: 'Confirmada', label: 'Confirmadas' },
          { id: 'Pendiente', label: 'Pendientes' },
          { id: 'Completada', label: 'Completadas' },
          { id: 'Cancelada', label: 'Canceladas' }
        ].map((tab) => (
          <button
            key={tab.id}
            id={`filter-citas-${tab.id}`}
            onClick={() => setEstadoFilter(tab.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${estadoFilter === tab.id ? 'bg-[#1d95c8] text-white shadow-xs' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Citas List */}
      {filteredCitas.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center">
          <Calendar className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-700">No hay citas en esta categoría</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
            Puedes agendar una nueva cita médica seleccionando fecha, paciente y especialista.
          </p>
          <button
            onClick={() => setModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-[#ff9f43] text-white text-xs font-bold shadow-xs hover:bg-[#f08e30]"
          >
            Agendar Cita Ahora
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {filteredCitas.map((cita) => (
            <div 
              key={cita.id}
              className="card-mundo p-5 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-3">
                    <img 
                      src={cita.mascota_imagen || "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=200&auto=format&fit=crop&q=80"} 
                      alt={cita.mascota_nombre}
                      className="w-12 h-12 rounded-xl object-cover border border-slate-100 shadow-2xs"
                    />
                    <div>
                      <h4 className="text-base font-bold text-slate-900 flex items-center gap-2">
                        {cita.mascota_nombre}
                        <span className="text-xs font-normal text-slate-500">({cita.mascota_raza || 'Mascota'})</span>
                      </h4>
                      <p className="text-xs text-slate-500 flex items-center gap-1">
                        <UserIcon className="w-3 h-3" /> Tutor: {cita.tutor_nombre} {cita.tutor_apellidos}
                      </p>
                    </div>
                  </div>
                  {getStatusBadge(cita.estado)}
                </div>

                <div className="bg-slate-50 rounded-xl p-3 space-y-1.5 text-xs text-slate-700 mb-4">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-500">Servicio:</span>
                    <span className="font-bold text-slate-900">
                      {cita.servicio_nombre}
                      <span className="font-normal text-slate-500">
                        {' '}({cita.servicio_duracion_min} min
                        {cita.servicio_precio != null && ` · $${cita.servicio_precio.toLocaleString('es-CL')}`})
                      </span>
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-500">Especialista:</span>
                    <span className="font-medium text-amber-700">{cita.vet_nombre} {cita.vet_apellidos}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-500">Fecha y Hora:</span>
                    <span className="font-bold text-slate-900 flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-400" />
                      {formatearFechaHora(cita.fecha_hora)}
                    </span>
                  </div>
                  <div className="flex items-start justify-between pt-1 border-t border-slate-200">
                    <span className="font-semibold text-slate-500">Motivo:</span>
                    <span className="text-slate-800 max-w-[65%] text-right font-medium">{cita.motivo}</span>
                  </div>
                  {cita.notas && (
                    <div className="text-[11px] text-slate-500 italic pt-1">
                      "{cita.notas}"
                    </div>
                  )}
                </div>
              </div>

              {/* Status Actions */}
              <div className="flex flex-wrap items-center justify-end gap-2 pt-2 border-t border-slate-100">
                {cita.estado === 'Pendiente' && (
                  <button
                    id={`btn-confirmar-cita-${cita.id}`}
                    onClick={() => onUpdateEstado(cita.id, 'Confirmada')}
                    className="px-3 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-semibold flex items-center gap-1 transition-colors"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Confirmar</span>
                  </button>
                )}

                {cita.estado === 'Confirmada' && (currentUser.tipo === 'veterinario' || currentUser.tipo === 'administrador') && (
                  <button
                    id={`btn-atender-cita-${cita.id}`}
                    onClick={() => onOpenHistorialModal(cita)}
                    className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold flex items-center gap-1 shadow-xs transition-colors"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Atender e Historial</span>
                  </button>
                )}

                {cita.estado !== 'Cancelada' && cita.estado !== 'Completada' && (
                  <button
                    id={`btn-cancelar-cita-${cita.id}`}
                    onClick={() => onUpdateEstado(cita.id, 'Cancelada')}
                    className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-red-50 text-slate-600 hover:text-red-600 text-xs font-semibold flex items-center gap-1 transition-colors"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Cancelar</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Agendar Nueva Cita */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden my-8">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Stethoscope className="w-5 h-5 text-amber-400" />
                <h3 className="font-bold text-lg">Agendar Cita Médica</h3>
              </div>
              <button 
                id="btn-cerrar-modal-cita"
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {errorMsg && (
                <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Mascota selector */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Paciente (Mascota)
                </label>
                <select
                  id="select-cita-mascota"
                  value={mascotaId}
                  onChange={(e) => setMascotaId(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
                >
                  {mascotas.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.nombre} - {m.especie_nombre} ({m.raza || 'Mestizo'}) [Tutor: {m.tutor_nombre || 'Clínica'}]
                    </option>
                  ))}
                </select>
              </div>

              {/* Servicio selector */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Servicio Veterinario
                </label>
                <select
                  id="select-cita-servicio"
                  value={servicioId}
                  onChange={(e) => setServicioId(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
                >
                  {servicios.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.nombre}
                      {s.precio != null && ` - $${s.precio.toLocaleString('es-CL')}`}
                      {` (${s.duracion_min} min)`}
                    </option>
                  ))}
                </select>
              </div>

              {/* Veterinario selector */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Médico Especialista
                </label>
                <select
                  id="select-cita-veterinario"
                  value={veterinarioId}
                  onChange={(e) => setVeterinarioId(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
                >
                  {veterinariosDelServicio.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.nombre} {v.apellidos} ({v.especialidad || 'Veterinario General'})
                    </option>
                  ))}
                </select>
              </div>

              {/* Fecha y Horario */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Fecha
                  </label>
                  <input 
                    type="date"
                    id="input-cita-fecha"
                    value={fecha}
                    onChange={(e) => setFecha(e.target.value)}
                    min={fechaLocal(0)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Hora
                  </label>
                  <select
                    id="select-cita-hora"
                    value={hora}
                    onChange={(e) => setHora(e.target.value)}
                    disabled={!horasLibres?.length}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white disabled:bg-slate-50 disabled:text-slate-400"
                  >
                    {horasLibres === null ? (
                      <option value="">Consultando…</option>
                    ) : horasLibres.length === 0 ? (
                      <option value="">Sin horas libres</option>
                    ) : (
                      horasLibres.map((h) => (
                        <option key={h} value={h}>{h} hrs</option>
                      ))
                    )}
                  </select>
                  {horasLibres?.length === 0 && (
                    <p id="aviso-sin-horas" className="text-[11px] text-slate-500 mt-1">
                      {errorHoras || 'Este veterinario no tiene huecos para este servicio ese día. Prueba otra fecha u otro especialista.'}
                    </p>
                  )}
                </div>
              </div>

              {/* Motivo y Peso */}
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Motivo de la Cita
                  </label>
                  <input
                    type="text"
                    id="input-cita-motivo"
                    placeholder="Ej: Control de vacunas, decaimiento, tos..."
                    value={motivo}
                    onChange={(e) => setMotivo(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Peso (kg)
                  </label>
                  <input
                    type="number"
                    id="input-cita-peso"
                    step="0.1"
                    min="0.1"
                    value={peso}
                    onChange={(e) => setPeso(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>
              </div>

              {/* Notas adicionales */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Notas u Observaciones (Opcional)
                </label>
                <textarea
                  id="textarea-cita-notas"
                  rows={2}
                  placeholder="Síntomas observados, medicamentos actuales, etc."
                  value={notas}
                  onChange={(e) => setNotas(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 resize-none"
                />
              </div>

              {/* Actions */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-sm font-semibold hover:bg-slate-50 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  id="btn-submit-cita"
                  disabled={isSubmitting || !hora}
                  className="px-5 py-2 rounded-xl bg-[#ff9f43] hover:bg-[#f08e30] text-white text-sm font-bold shadow-sm transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? 'Guardando...' : 'Confirmar Cita'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
