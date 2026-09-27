import React, { useEffect, useState } from 'react';
import { HistorialMedico, Mascota, User, Cita } from '../types';
import { formatearFechaHora } from '../formato';
import { Encabezado, ErrorFormulario, Modal, PieModal, Vacio, useInterfaz } from './ui';
import { ClipboardList, ClipboardPlus, Search, Stethoscope } from 'lucide-react';

/** Lo que llega al pulsar "Historia" en una mascota o "Atender" en una cita. */
export interface NuevaHistoria {
  mascota: Mascota | null;
  citaId?: number;
}

interface HistorialViewProps {
  historiales: HistorialMedico[];
  mascotas: Mascota[];
  citas: Cita[];
  currentUser: User;
  onCreateHistorial: (data: {
    cita_id?: number | null;
    mascota_id: number;
    veterinario_id?: number;
    diagnostico: string;
    tratamiento: string;
    observaciones?: string;
  }) => Promise<void>;
  /** Abre el formulario ya con la mascota (y la cita) elegidas. */
  nuevaHistoria?: NuevaHistoria | null;
}

export const HistorialView: React.FC<HistorialViewProps> = ({
  historiales,
  mascotas,
  citas,
  currentUser,
  onCreateHistorial,
  nuevaHistoria
}) => {
  const { avisar } = useInterfaz();
  const esPersonal = currentUser.tipo !== 'cliente';
  const [filtroMascota, setFiltroMascota] = useState<string>(nuevaHistoria?.mascota ? String(nuevaHistoria.mascota.id) : 'todos');
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Formulario
  const [mascotaId, setMascotaId] = useState<number>(nuevaHistoria?.mascota?.id || mascotas[0]?.id || 0);
  const [citaId, setCitaId] = useState<number | null>(nuevaHistoria?.citaId ?? null);
  const [diagnostico, setDiagnostico] = useState('');
  const [tratamiento, setTratamiento] = useState('');
  const [observaciones, setObservaciones] = useState('');

  useEffect(() => {
    if (nuevaHistoria?.mascota && esPersonal) setModalOpen(true);
  }, [nuevaHistoria]);

  // Citas de la mascota que todavía se pueden cerrar con esta historia.
  const citasAtendibles = citas.filter(
    (c) => c.mascota_id === mascotaId && (c.estado === 'Confirmada' || c.estado === 'Pendiente') && !c.tiene_historial
  );
  useEffect(() => {
    if (citaId && !citasAtendibles.some((c) => c.id === citaId)) setCitaId(null);
  }, [mascotaId]);

  const filtrados = historiales.filter((h) => {
    if (filtroMascota !== 'todos' && String(h.mascota_id) !== filtroMascota) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return [h.mascota_nombre, h.diagnostico, h.tratamiento, h.vet_nombre].some((t) => (t || '').toLowerCase().includes(q));
  });

  const abrirFormulario = () => {
    setErrorMsg(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    if (!diagnostico.trim() || !tratamiento.trim()) {
      setErrorMsg('Escribe el diagnóstico y el tratamiento.');
      return;
    }
    try {
      setIsSubmitting(true);
      await onCreateHistorial({
        mascota_id: Number(mascotaId),
        cita_id: citaId,
        // Firma el veterinario de la sesión; si es un administrador, el backend toma el de la cita.
        veterinario_id: currentUser.tipo === 'veterinario' ? currentUser.id : undefined,
        diagnostico: diagnostico.trim(),
        tratamiento: tratamiento.trim(),
        observaciones: observaciones.trim()
      });
      avisar(citaId ? 'Historia registrada y cita completada.' : 'Historia registrada.');
      setModalOpen(false);
      setCitaId(null);
      setDiagnostico('');
      setTratamiento('');
      setObservaciones('');
    } catch (err: any) {
      setErrorMsg(err.message || 'No se pudo guardar la historia.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Encabezado
        titulo={esPersonal ? 'Historias clínicas' : 'Historial de mis mascotas'}
        descripcion={esPersonal ? 'Diagnósticos, tratamientos y recomendaciones de cada consulta.' : 'Lo que el veterinario registró en cada consulta.'}
      >
        {esPersonal && (
          <button id="btn-nuevo-historial" onClick={abrirFormulario} className="mp-btn mp-btn--primario">
            <ClipboardPlus className="w-4 h-4" />
            Nueva historia
          </button>
        )}
      </Encabezado>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="mp-buscador w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" aria-hidden />
          <label htmlFor="input-search-historiales" className="sr-only">Buscar en el historial</label>
          <input
            type="search"
            id="input-search-historiales"
            placeholder="Diagnóstico, tratamiento o veterinario"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="mp-campo"
          />
        </div>
        <div className="w-full sm:w-64">
          <label htmlFor="select-filter-mascota-historial" className="sr-only">Mascota</label>
          <select id="select-filter-mascota-historial" value={filtroMascota} onChange={(e) => setFiltroMascota(e.target.value)} className="mp-campo">
            <option value="todos">Todas las mascotas</option>
            {mascotas.map((m) => (
              <option key={m.id} value={m.id}>{m.nombre} ({m.especie_nombre})</option>
            ))}
          </select>
        </div>
      </div>

      {filtrados.length === 0 ? (
        <Vacio
          icono={ClipboardList}
          titulo={historiales.length === 0 ? 'Todavía no hay historias clínicas' : 'Ninguna historia coincide'}
          texto={historiales.length === 0 ? 'Se registran al atender una cita o desde aquí mismo.' : 'Prueba con otra búsqueda o con todas las mascotas.'}
        />
      ) : (
        <ol className="space-y-4">
          {filtrados.map((h) => (
            <li key={h.id} className="mp-papel-blanco overflow-hidden">
              <div className="bg-[#1d4f60] text-white px-5 py-3 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-titulo text-lg font-semibold">
                  {h.mascota_nombre}
                  {h.mascota_raza && <span className="ml-2 text-sm font-normal text-white/70">{h.mascota_raza}</span>}
                </h2>
                <p className="text-sm text-white/80 flex items-center gap-2">
                  <Stethoscope className="w-4 h-4 text-[#9dddf5]" />
                  {h.vet_nombre} · {formatearFechaHora(h.fecha_creacion)}
                </p>
              </div>
              <div className="p-5 grid md:grid-cols-2 gap-4 text-sm">
                <div>
                  <h3 className="font-semibold text-[#156a8e] mb-1">Diagnóstico</h3>
                  <p className="text-slate-700 leading-relaxed">{h.diagnostico}</p>
                </div>
                <div>
                  <h3 className="font-semibold text-[#156a8e] mb-1">Tratamiento</h3>
                  <p className="text-slate-700 leading-relaxed">{h.tratamiento}</p>
                </div>
                {h.observaciones && (
                  <div className="md:col-span-2 bg-[#fff5e6] border-l-4 border-[#ff9f43] rounded-r-lg p-3">
                    <h3 className="font-semibold mb-0.5">Recomendaciones</h3>
                    <p className="text-slate-700">{h.observaciones}</p>
                  </div>
                )}
                {h.cita_fecha && (
                  <p className="md:col-span-2 text-xs text-slate-500">Cita del {formatearFechaHora(h.cita_fecha)}</p>
                )}
              </div>
            </li>
          ))}
        </ol>
      )}

      {modalOpen && (
        <Modal titulo="Nueva historia clínica" icono={<ClipboardPlus className="w-5 h-5 text-[#ff9f43]" />} onCerrar={() => setModalOpen(false)}>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <ErrorFormulario texto={errorMsg} />
            <div>
              <label htmlFor="select-historial-mascota" className="mp-etiqueta">Mascota</label>
              <select id="select-historial-mascota" value={mascotaId} onChange={(e) => setMascotaId(Number(e.target.value))} className="mp-campo">
                {mascotas.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.nombre} - {m.especie_nombre} ({m.raza || 'Mestizo'})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="select-historial-cita" className="mp-etiqueta">Cita que se atiende</label>
              <select
                id="select-historial-cita"
                value={citaId ?? ''}
                onChange={(e) => setCitaId(e.target.value ? Number(e.target.value) : null)}
                className="mp-campo"
              >
                <option value="">Sin cita (consulta fuera de agenda)</option>
                {citasAtendibles.map((c) => (
                  <option key={c.id} value={c.id}>
                    {formatearFechaHora(c.fecha_hora)} · {c.servicio_nombre}
                  </option>
                ))}
              </select>
              <p className="mp-ayuda">Con una cita elegida, la cita queda completada al guardar.</p>
            </div>

            <div>
              <label htmlFor="textarea-historial-diagnostico" className="mp-etiqueta">Diagnóstico</label>
              <textarea
                id="textarea-historial-diagnostico"
                rows={3}
                placeholder="Hallazgos, constantes y diagnóstico"
                value={diagnostico}
                onChange={(e) => setDiagnostico(e.target.value)}
                className="mp-campo resize-none"
                required
              />
            </div>
            <div>
              <label htmlFor="textarea-historial-tratamiento" className="mp-etiqueta">Tratamiento</label>
              <textarea
                id="textarea-historial-tratamiento"
                rows={3}
                placeholder="Medicamento, dosis, vía y duración"
                value={tratamiento}
                onChange={(e) => setTratamiento(e.target.value)}
                className="mp-campo resize-none"
                required
              />
            </div>
            <div>
              <label htmlFor="textarea-historial-observaciones" className="mp-etiqueta">Recomendaciones para el tutor (opcional)</label>
              <textarea
                id="textarea-historial-observaciones"
                rows={2}
                placeholder="Control en 10 días, dieta blanda…"
                value={observaciones}
                onChange={(e) => setObservaciones(e.target.value)}
                className="mp-campo resize-none"
              />
            </div>

            <PieModal>
              <button type="button" onClick={() => setModalOpen(false)} className="mp-btn mp-btn--borde">Cancelar</button>
              <button type="submit" id="btn-submit-historial" disabled={isSubmitting} className="mp-btn mp-btn--primario">
                {isSubmitting ? 'Guardando…' : 'Guardar historia'}
              </button>
            </PieModal>
          </form>
        </Modal>
      )}
    </div>
  );
};
