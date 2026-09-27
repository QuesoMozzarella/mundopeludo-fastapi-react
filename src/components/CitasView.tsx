import React, { useEffect, useState } from 'react';
import { Cita, Mascota, Servicio, User } from '../types';
import { formatearFechaHora, formatearPrecio } from '../formato';
import { fetchHorasLibres } from '../api';
import { Encabezado, ErrorFormulario, EstadoCita, FotoMascota, Modal, PieModal, Vacio, useInterfaz } from './ui';
import { CalendarSearch, Check, ClipboardPlus, Plus, Stethoscope, X } from 'lucide-react';

/** Fecha local "AAAA-MM-DD" dentro de `dias` días (toISOString daría la de UTC). */
function fechaLocal(dias: number, desde = new Date()): string {
  const d = new Date(desde);
  d.setDate(d.getDate() + dias);
  const dos = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${dos(d.getMonth() + 1)}-${dos(d.getDate())}`;
}

const DIAS_A_BUSCAR = 30;

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

const FILTROS = [
  { id: 'todos', nombre: 'Todas' },
  { id: 'Pendiente', nombre: 'Pendientes' },
  { id: 'Confirmada', nombre: 'Confirmadas' },
  { id: 'Completada', nombre: 'Completadas' },
  { id: 'Cancelada', nombre: 'Canceladas' }
];

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
  const { avisar, confirmar } = useInterfaz();
  const esPersonal = currentUser.tipo !== 'cliente';
  const [modalOpen, setModalOpen] = useState(false);
  const [estadoFilter, setEstadoFilter] = useState<string>('todos');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Formulario
  const [mascotaId, setMascotaId] = useState<number>(mascotas[0]?.id || 0);
  const [servicioId, setServicioId] = useState<number>(preselectedServicioId || servicios[0]?.id || 0);
  const [veterinarioId, setVeterinarioId] = useState<number>(veterinarios[0]?.id || 0);
  const [fecha, setFecha] = useState<string>(() => fechaLocal(1));
  const [hora, setHora] = useState<string>('');
  const [motivo, setMotivo] = useState<string>('');
  const [peso, setPeso] = useState<number>(mascotas[0]?.peso || 1);
  const [notas, setNotas] = useState<string>('');
  // null mientras se consultan; [] si ese día no hay huecos.
  const [horasLibres, setHorasLibres] = useState<string[] | null>(null);
  const [errorHoras, setErrorHoras] = useState<string | null>(null);
  const [consultaHoras, setConsultaHoras] = useState(0);
  const [buscandoDia, setBuscandoDia] = useState(false);

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

  // El peso de partida es el último registrado de la mascota.
  useEffect(() => {
    const mascota = mascotas.find((m) => m.id === mascotaId);
    if (mascota?.peso) setPeso(mascota.peso);
  }, [mascotaId]);

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

  /** Recorre los próximos días hasta encontrar uno con horas libres. */
  const buscarProximoDia = async () => {
    setBuscandoDia(true);
    try {
      const desde = new Date(`${fecha}T12:00:00`);
      for (let i = 1; i <= DIAS_A_BUSCAR; i++) {
        const dia = fechaLocal(i, desde);
        const horas = await fetchHorasLibres(veterinarioId, dia, servicioId);
        if (horas.length) {
          setFecha(dia);
          return;
        }
      }
      setErrorHoras(`No hay horas libres en los próximos ${DIAS_A_BUSCAR} días con este veterinario. Prueba con otro.`);
    } catch (err: any) {
      setErrorHoras(err.message || 'No se pudieron consultar las horas libres.');
    } finally {
      setBuscandoDia(false);
    }
  };

  const citasFiltradas = citas
    .filter((c) => estadoFilter === 'todos' || c.estado === estadoFilter)
    .sort((a, b) => b.fecha_hora.localeCompare(a.fecha_hora));

  const cuenta = (estado: string) =>
    estado === 'todos' ? citas.length : citas.filter((c) => c.estado === estado).length;

  const abrirFormulario = () => {
    setErrorMsg(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    if (!motivo.trim()) {
      setErrorMsg('Escribe el motivo de la cita.');
      return;
    }
    if (!hora) {
      setErrorMsg('Elige una hora libre.');
      return;
    }
    try {
      setIsSubmitting(true);
      await onBookCita({
        mascota_id: Number(mascotaId),
        veterinario_id: Number(veterinarioId),
        servicio_id: Number(servicioId),
        fecha_hora: `${fecha} ${hora}:00`,
        peso: Number(peso),
        motivo: motivo.trim(),
        notas: notas.trim()
      });
      setModalOpen(false);
      setMotivo('');
      setNotas('');
      avisar('Cita agendada. Queda pendiente de confirmación.');
    } catch (err: any) {
      setErrorMsg(err.message || 'No se pudo agendar la cita.');
      // Quizá alguien ocupó la hora mientras tanto: se vuelven a pedir.
      setConsultaHoras((n) => n + 1);
    } finally {
      setIsSubmitting(false);
    }
  };

  const cambiarEstado = async (cita: Cita, estado: string) => {
    if (estado === 'Cancelada') {
      const ok = await confirmar({
        titulo: 'Cancelar la cita',
        mensaje: `La cita de ${cita.mascota_nombre} del ${formatearFechaHora(cita.fecha_hora)} se cancelará y su hora quedará libre.`,
        confirmar: 'Cancelar la cita',
        peligro: true
      });
      if (!ok) return;
    }
    try {
      await onUpdateEstado(cita.id, estado);
      avisar(estado === 'Cancelada' ? 'Cita cancelada.' : `Cita ${estado.toLowerCase()}.`);
    } catch (err: any) {
      avisar(err.message || 'No se pudo cambiar el estado de la cita.', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <Encabezado
        titulo={esPersonal ? 'Agenda de citas' : 'Mis citas'}
        descripcion={
          esPersonal
            ? 'Confirma, atiende o cancela las citas de la clínica.'
            : 'Pide una cita y sigue su estado: pendiente, confirmada o completada.'
        }
      >
        <button id="btn-nueva-cita" onClick={abrirFormulario} className="mp-btn mp-btn--primario">
          <Plus className="w-4 h-4" />
          Nueva cita
        </button>
      </Encabezado>

      <div role="group" aria-label="Filtrar por estado" className="flex flex-wrap gap-2">
        {FILTROS.map((f) => (
          <button
            key={f.id}
            id={`filter-citas-${f.id}`}
            onClick={() => setEstadoFilter(f.id)}
            aria-pressed={estadoFilter === f.id}
            className="mp-filtro"
          >
            {f.nombre} <span className="opacity-70">{cuenta(f.id)}</span>
          </button>
        ))}
      </div>

      {citasFiltradas.length === 0 ? (
        <Vacio
          icono={Stethoscope}
          titulo={estadoFilter === 'todos' ? 'Todavía no hay citas' : 'No hay citas con este estado'}
          texto="Elige mascota, servicio y veterinario, y te mostramos las horas libres."
        >
          <button onClick={abrirFormulario} className="mp-btn mp-btn--claro">
            <Plus className="w-4 h-4" />
            Pedir una cita
          </button>
        </Vacio>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {citasFiltradas.map((cita) => {
            const especie = mascotas.find((m) => m.id === cita.mascota_id)?.especie_nombre;
            return (
              <article key={cita.id} className="mp-papel-blanco p-5 flex flex-col gap-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <FotoMascota
                      nombre={cita.mascota_nombre}
                      imagen={cita.mascota_imagen}
                      especie={especie}
                      className="w-12 h-12 rounded-full shrink-0"
                      tamanoIcono="w-6 h-6"
                    />
                    <div className="min-w-0">
                      <h2 className="font-titulo text-lg font-semibold text-[#1d4f60] leading-tight">
                        {cita.mascota_nombre}
                        {cita.mascota_raza && <span className="ml-1.5 text-sm font-normal text-slate-500">{cita.mascota_raza}</span>}
                      </h2>
                      {esPersonal && cita.tutor_nombre && (
                        <p className="text-sm text-slate-500 truncate">Tutor: {cita.tutor_nombre}</p>
                      )}
                    </div>
                  </div>
                  <EstadoCita estado={cita.estado} />
                </div>

                <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm bg-[#f3f7fa] rounded-lg p-3">
                  <dt className="text-slate-500">Servicio</dt>
                  <dd className="font-semibold text-right">
                    {cita.servicio_nombre}{' '}
                    <span className="font-normal text-slate-500">
                      ({cita.servicio_duracion_min} min{cita.servicio_precio != null && ` · ${formatearPrecio(cita.servicio_precio)}`})
                    </span>
                  </dd>
                  <dt className="text-slate-500">Veterinario</dt>
                  <dd className="text-right">{cita.vet_nombre}</dd>
                  <dt className="text-slate-500">Fecha</dt>
                  <dd className="font-semibold text-right">{formatearFechaHora(cita.fecha_hora)}</dd>
                  <dt className="text-slate-500">Motivo</dt>
                  <dd className="text-right">{cita.motivo}</dd>
                  {cita.notas && (
                    <>
                      <dt className="text-slate-500">Notas</dt>
                      <dd className="text-right text-slate-600">{cita.notas}</dd>
                    </>
                  )}
                </dl>

                {(cita.estado === 'Pendiente' || cita.estado === 'Confirmada') && (
                  <div className="flex flex-wrap items-center justify-end gap-2">
                    {cita.estado === 'Pendiente' && esPersonal && (
                      <button id={`btn-confirmar-cita-${cita.id}`} onClick={() => cambiarEstado(cita, 'Confirmada')} className="mp-btn mp-btn--exito mp-btn--sm">
                        <Check className="w-4 h-4" />
                        Confirmar
                      </button>
                    )}
                    {cita.estado === 'Confirmada' && esPersonal && (
                      <button id={`btn-atender-cita-${cita.id}`} onClick={() => onOpenHistorialModal(cita)} className="mp-btn mp-btn--azul mp-btn--sm">
                        <ClipboardPlus className="w-4 h-4" />
                        Atender y registrar historia
                      </button>
                    )}
                    <button id={`btn-cancelar-cita-${cita.id}`} onClick={() => cambiarEstado(cita, 'Cancelada')} className="mp-btn mp-btn--borde mp-btn--sm">
                      <X className="w-4 h-4" />
                      Cancelar
                    </button>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}

      {modalOpen && (
        <Modal
          titulo="Nueva cita"
          icono={<Stethoscope className="w-5 h-5 text-[#ff9f43]" />}
          onCerrar={() => setModalOpen(false)}
          idCerrar="btn-cerrar-modal-cita"
        >
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <ErrorFormulario texto={errorMsg} />

            <div>
              <label htmlFor="select-cita-mascota" className="mp-etiqueta">Mascota</label>
              <select id="select-cita-mascota" value={mascotaId} onChange={(e) => setMascotaId(Number(e.target.value))} className="mp-campo">
                {mascotas.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.nombre} · {m.especie_nombre}{m.raza ? `, ${m.raza}` : ''}{esPersonal && m.tutor_nombre ? ` (tutor: ${m.tutor_nombre})` : ''}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="select-cita-servicio" className="mp-etiqueta">Servicio</label>
              <select id="select-cita-servicio" value={servicioId} onChange={(e) => setServicioId(Number(e.target.value))} className="mp-campo">
                {servicios.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nombre}
                    {s.precio != null && ` - ${formatearPrecio(s.precio)}`}
                    {` (${s.duracion_min} min)`}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="select-cita-veterinario" className="mp-etiqueta">Veterinario</label>
              <select id="select-cita-veterinario" value={veterinarioId} onChange={(e) => setVeterinarioId(Number(e.target.value))} className="mp-campo">
                {veterinariosDelServicio.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.nombre} {v.apellidos}{v.especialidad ? ` (${v.especialidad})` : ''}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="input-cita-fecha" className="mp-etiqueta">Fecha</label>
                <input
                  type="date"
                  id="input-cita-fecha"
                  value={fecha}
                  onChange={(e) => setFecha(e.target.value)}
                  min={fechaLocal(0)}
                  className="mp-campo"
                  required
                />
              </div>
              <div>
                <label htmlFor="select-cita-hora" className="mp-etiqueta">Hora</label>
                <select
                  id="select-cita-hora"
                  value={hora}
                  onChange={(e) => setHora(e.target.value)}
                  disabled={!horasLibres?.length}
                  aria-describedby={horasLibres?.length === 0 ? 'aviso-sin-horas' : undefined}
                  className="mp-campo"
                >
                  {horasLibres === null ? (
                    <option value="">Consultando…</option>
                  ) : horasLibres.length === 0 ? (
                    <option value="">Sin horas libres</option>
                  ) : (
                    horasLibres.map((h) => <option key={h} value={h}>{h} hrs</option>)
                  )}
                </select>
              </div>
            </div>

            {horasLibres?.length === 0 && (
              <div id="aviso-sin-horas" className="mp-aviso mp-aviso--info flex-col sm:flex-row sm:items-center">
                <span className="flex-1">
                  {errorHoras || 'Ese día no hay horas libres con este veterinario para este servicio.'}
                </span>
                <button
                  type="button"
                  id="btn-buscar-proximo-dia"
                  onClick={buscarProximoDia}
                  disabled={buscandoDia}
                  className="mp-btn mp-btn--azul mp-btn--sm"
                >
                  <CalendarSearch className="w-4 h-4" />
                  {buscandoDia ? 'Buscando…' : 'Buscar el próximo día con horas'}
                </button>
              </div>
            )}

            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2">
                <label htmlFor="input-cita-motivo" className="mp-etiqueta">Motivo</label>
                <input
                  type="text"
                  id="input-cita-motivo"
                  placeholder="Vacuna anual, decaimiento, tos…"
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                  className="mp-campo"
                  required
                  minLength={3}
                />
              </div>
              <div>
                <label htmlFor="input-cita-peso" className="mp-etiqueta">Peso (kg)</label>
                <input
                  type="number"
                  id="input-cita-peso"
                  step="0.1"
                  min="0.1"
                  value={peso}
                  onChange={(e) => setPeso(parseFloat(e.target.value))}
                  className="mp-campo"
                />
              </div>
            </div>

            <div>
              <label htmlFor="textarea-cita-notas" className="mp-etiqueta">Notas (opcional)</label>
              <textarea
                id="textarea-cita-notas"
                rows={2}
                placeholder="Síntomas, medicamentos que toma…"
                value={notas}
                onChange={(e) => setNotas(e.target.value)}
                className="mp-campo resize-none"
              />
            </div>

            <PieModal>
              <button type="button" onClick={() => setModalOpen(false)} className="mp-btn mp-btn--borde">
                Cancelar
              </button>
              <button type="submit" id="btn-submit-cita" disabled={isSubmitting || !hora} className="mp-btn mp-btn--primario">
                {isSubmitting ? 'Agendando…' : 'Agendar cita'}
              </button>
            </PieModal>
          </form>
        </Modal>
      )}
    </div>
  );
};
