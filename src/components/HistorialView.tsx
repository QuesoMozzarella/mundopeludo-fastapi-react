import React, { useState } from 'react';
import { HistorialMedico, Mascota, User, Cita } from '../types';
import { 
  ClipboardList, 
  Plus, 
  Calendar, 
  User as UserIcon, 
  Stethoscope, 
  Pill, 
  FileText, 
  CheckCircle2, 
  X, 
  Search 
} from 'lucide-react';

interface HistorialViewProps {
  historiales: HistorialMedico[];
  mascotas: Mascota[];
  citas: Cita[];
  currentUser: User;
  onCreateHistorial: (data: {
    cita_id?: number | null;
    mascota_id: number;
    veterinario_id: number;
    diagnostico: string;
    tratamiento: string;
    observaciones?: string;
  }) => Promise<void>;
  initialSelectedPet?: Mascota | null;
}

export const HistorialView: React.FC<HistorialViewProps> = ({
  historiales,
  mascotas,
  citas,
  currentUser,
  onCreateHistorial,
  initialSelectedPet
}) => {
  const [selectedPetFilter, setSelectedPetFilter] = useState<string>(initialSelectedPet ? String(initialSelectedPet.id) : 'todos');
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form State
  const [mascotaId, setMascotaId] = useState<number>(initialSelectedPet?.id || mascotas[0]?.id || 1);
  const [citaId, setCitaId] = useState<number | null>(null);
  const [diagnostico, setDiagnostico] = useState('');
  const [tratamiento, setTratamiento] = useState('');
  const [observaciones, setObservaciones] = useState('');

  const filteredHistoriales = historiales.filter((h) => {
    if (selectedPetFilter !== 'todos' && String(h.mascota_id) !== selectedPetFilter) {
      return false;
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        (h.mascota_nombre && h.mascota_nombre.toLowerCase().includes(q)) ||
        h.diagnostico.toLowerCase().includes(q) ||
        h.tratamiento.toLowerCase().includes(q) ||
        (h.vet_nombre && h.vet_nombre.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!diagnostico.trim() || !tratamiento.trim()) {
      alert('Por favor ingresa tanto el diagnóstico como el tratamiento.');
      return;
    }

    try {
      setIsSubmitting(true);
      await onCreateHistorial({
        mascota_id: Number(mascotaId),
        cita_id: citaId ? Number(citaId) : null,
        veterinario_id: currentUser.tipo === 'veterinario' ? currentUser.id : 2,
        diagnostico: diagnostico.trim(),
        tratamiento: tratamiento.trim(),
        observaciones: observaciones.trim()
      });

      setModalOpen(false);
      setDiagnostico('');
      setTratamiento('');
      setObservaciones('');
    } catch (err: any) {
      alert(err.message || 'Error al guardar el historial médico.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Historiales Clínicos Digitales
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Registro de evoluciones médicas, prescripciones farmacológicas y exámenes de laboratorio.
          </p>
        </div>

        {(currentUser.tipo === 'veterinario' || currentUser.tipo === 'administrador') && (
          <button
            id="btn-nuevo-historial"
            onClick={() => setModalOpen(true)}
            className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm shadow-sm flex items-center justify-center gap-2 transition-colors self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Nueva Entrada Médica</span>
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            id="input-search-historiales"
            placeholder="Buscar por diagnóstico o medicamento..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          />
        </div>

        <div className="w-full sm:w-64">
          <select
            id="select-filter-mascota-historial"
            value={selectedPetFilter}
            onChange={(e) => setSelectedPetFilter(e.target.value)}
            className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option value="todos">Todos los pacientes</option>
            {mascotas.map((m) => (
              <option key={m.id} value={m.id}>
                {m.nombre} ({m.especie_nombre})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Historial Cards List */}
      {filteredHistoriales.length === 0 ? (
        <div className="bg-white rounded-3xl border border-dashed border-slate-300 p-16 text-center">
          <ClipboardList className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No hay registros clínicos disponibles</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            Los historiales médicos se generan cuando un médico veterinario atiende una cita o ingresa una consulta.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredHistoriales.map((h) => (
            <div 
              key={h.id}
              className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs hover:shadow-md transition-shadow"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                    🐾
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                      {h.mascota_nombre || 'Paciente'}
                      <span className="text-xs font-normal text-slate-500">({h.mascota_raza || 'Mascota'})</span>
                    </h3>
                    <p className="text-xs text-slate-500 flex items-center gap-1">
                      <Stethoscope className="w-3.5 h-3.5 text-blue-500" />
                      Médico: {h.vet_nombre} {h.vet_apellidos}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500 bg-slate-50 px-3 py-1.5 rounded-lg self-start sm:self-auto">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>{h.fecha_creacion}</span>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4 text-xs">
                {/* Diagnóstico */}
                <div className="bg-slate-50 p-4 rounded-xl space-y-1.5">
                  <div className="font-bold text-slate-900 flex items-center gap-1.5 text-xs uppercase tracking-wider">
                    <FileText className="w-3.5 h-3.5 text-blue-600" />
                    <span>Diagnóstico Clínico</span>
                  </div>
                  <p className="text-slate-700 leading-relaxed font-medium">
                    {h.diagnostico}
                  </p>
                </div>

                {/* Tratamiento */}
                <div className="bg-emerald-50/50 border border-emerald-100/80 p-4 rounded-xl space-y-1.5">
                  <div className="font-bold text-emerald-900 flex items-center gap-1.5 text-xs uppercase tracking-wider">
                    <Pill className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Tratamiento & Prescripción</span>
                  </div>
                  <p className="text-emerald-950 leading-relaxed font-medium">
                    {h.tratamiento}
                  </p>
                </div>
              </div>

              {h.observaciones && (
                <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-600">
                  <span className="font-bold text-slate-800">Observaciones y Cuidados en Casa:</span>{' '}
                  {h.observaciones}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Modal Registrar Nuevo Historial */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden my-8">
            <div className="bg-blue-600 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-white" />
                <h3 className="font-bold text-lg">Registrar Consulta Médica</h3>
              </div>
              <button 
                onClick={() => setModalOpen(false)}
                className="text-blue-200 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Paciente (Mascota) *
                </label>
                <select
                  id="select-historial-mascota"
                  value={mascotaId}
                  onChange={(e) => setMascotaId(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                >
                  {mascotas.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.nombre} - {m.especie_nombre} ({m.raza || 'Mestizo'})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Diagnóstico Clínico *
                </label>
                <textarea
                  id="textarea-historial-diagnostico"
                  rows={3}
                  placeholder="Descripción de los hallazgos físicos, temperatura, constantes vitales y diagnóstico definitivo o presuntivo..."
                  value={diagnostico}
                  onChange={(e) => setDiagnostico(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Tratamiento y Medicación Prescrita *
                </label>
                <textarea
                  id="textarea-historial-tratamiento"
                  rows={3}
                  placeholder="Medicamentos, dosis (mg/kg), vía de administración y duración del tratamiento..."
                  value={tratamiento}
                  onChange={(e) => setTratamiento(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Recomendaciones para el Tutor (Opcional)
                </label>
                <textarea
                  id="textarea-historial-observaciones"
                  rows={2}
                  placeholder="Control en X días, dieta blanda, reposo absoluto, signos de alarma..."
                  value={observaciones}
                  onChange={(e) => setObservaciones(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-sm font-semibold hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  id="btn-submit-historial"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold shadow-md transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? 'Guardando...' : 'Guardar en Ficha Clínica'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
