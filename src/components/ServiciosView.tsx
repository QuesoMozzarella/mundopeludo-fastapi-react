import React, { useEffect, useState } from 'react';
import { Disponibilidad, Servicio, User } from '../types';
import {
  ServicioDatos,
  createDisponibilidad,
  createServicio,
  deleteDisponibilidad,
  deleteServicio,
  fetchDisponibilidades,
  updateServicio
} from '../api';
import {
  AlertCircle,
  CalendarClock,
  Clock,
  Edit3,
  Plus,
  Power,
  Stethoscope,
  Trash2,
  X
} from 'lucide-react';

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

interface ServiciosViewProps {
  servicios: Servicio[];
  veterinarios: User[];
  currentUser: User;
  /** Vuelve a pedir los servicios a la API tras un cambio. */
  onRecargarServicios: () => Promise<void>;
}

const FORMULARIO_VACIO: ServicioDatos = {
  nombre: '',
  descripcion: '',
  precio: null,
  duracion_min: 30,
  activo: true,
  veterinarios_ids: []
};

const estiloCampo =
  'w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white';
const estiloEtiqueta = 'block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5';

/** "09:00:00" -> "09:00" */
const hhmm = (hora: string) => hora.slice(0, 5);

function Aviso({ texto, onCerrar }: { texto: string; onCerrar?: () => void }) {
  return (
    <div role="alert" className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2">
      <AlertCircle className="w-4 h-4 shrink-0 mt-px" />
      <span className="flex-1">{texto}</span>
      {onCerrar && (
        <button type="button" onClick={onCerrar} className="text-red-400 hover:text-red-700">
          <X className="w-3.5 h-3.5" />
        </button>
      )}
    </div>
  );
}

export const ServiciosView: React.FC<ServiciosViewProps> = ({
  servicios,
  veterinarios,
  currentUser,
  onRecargarServicios
}) => {
  const esAdmin = currentUser.tipo === 'administrador';

  // ------------------------------ servicios ------------------------------
  const [editando, setEditando] = useState<Servicio | 'nuevo' | null>(null);
  const [formulario, setFormulario] = useState<ServicioDatos>(FORMULARIO_VACIO);
  const [precioTexto, setPrecioTexto] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [errorModal, setErrorModal] = useState<string | null>(null);
  const [errorServicios, setErrorServicios] = useState<string | null>(null);

  const nombreVet = (id: number) => {
    const v = veterinarios.find((x) => x.id === id);
    return v ? `${v.nombre} ${v.apellidos}` : `#${id}`;
  };

  const abrirNuevo = () => {
    setFormulario(FORMULARIO_VACIO);
    setPrecioTexto('');
    setErrorModal(null);
    setEditando('nuevo');
  };

  const abrirEdicion = (s: Servicio) => {
    setFormulario({
      nombre: s.nombre,
      descripcion: s.descripcion || '',
      precio: s.precio ?? null,
      duracion_min: s.duracion_min,
      activo: Boolean(s.activo),
      veterinarios_ids: s.veterinarios_ids || []
    });
    setPrecioTexto(s.precio != null ? String(s.precio) : '');
    setErrorModal(null);
    setEditando(s);
  };

  const alternarVet = (id: number) => {
    setFormulario((f) => ({
      ...f,
      veterinarios_ids: f.veterinarios_ids.includes(id)
        ? f.veterinarios_ids.filter((x) => x !== id)
        : [...f.veterinarios_ids, id]
    }));
  };

  const guardarServicio = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorModal(null);
    // Precio vacío = sin precio publicado.
    const datos: ServicioDatos = {
      ...formulario,
      nombre: formulario.nombre.trim(),
      descripcion: formulario.descripcion?.trim() || null,
      precio: precioTexto.trim() === '' ? null : Number(precioTexto),
      duracion_min: Number(formulario.duracion_min)
    };
    try {
      setGuardando(true);
      if (editando === 'nuevo') await createServicio(datos);
      else if (editando) await updateServicio(editando.id, datos);
      await onRecargarServicios();
      setEditando(null);
    } catch (err: any) {
      setErrorModal(err.message || 'No se pudo guardar el servicio.');
    } finally {
      setGuardando(false);
    }
  };

  const cambiarActivo = async (s: Servicio) => {
    setErrorServicios(null);
    try {
      await updateServicio(s.id, { activo: !s.activo });
      await onRecargarServicios();
    } catch (err: any) {
      setErrorServicios(err.message || 'No se pudo cambiar el estado del servicio.');
    }
  };

  const eliminarServicio = async (s: Servicio) => {
    if (!confirm(`¿Eliminar el servicio "${s.nombre}"?`)) return;
    setErrorServicios(null);
    try {
      await deleteServicio(s.id);
      await onRecargarServicios();
    } catch (err: any) {
      // Con citas asociadas la API lo impide: se sugiere desactivarlo.
      setErrorServicios(
        err.status === 409 ? `${err.message}. Puedes desactivarlo para que no se agende más.` : err.message
      );
    }
  };

  // ------------------------------ horarios ------------------------------
  const [vetHorario, setVetHorario] = useState<number>(
    esAdmin ? veterinarios[0]?.id ?? 0 : currentUser.id
  );
  const [franjas, setFranjas] = useState<Disponibilidad[] | null>(null);
  const [errorHorario, setErrorHorario] = useState<string | null>(null);
  const [dia, setDia] = useState(0);
  const [inicio, setInicio] = useState('09:00');
  const [fin, setFin] = useState('13:00');
  const [agregando, setAgregando] = useState(false);

  useEffect(() => {
    if (esAdmin && !vetHorario && veterinarios.length) setVetHorario(veterinarios[0].id);
  }, [veterinarios]);

  const cargarFranjas = async () => {
    if (!vetHorario) return;
    try {
      setFranjas(await fetchDisponibilidades(vetHorario));
    } catch (err: any) {
      setFranjas([]);
      setErrorHorario(err.message || 'No se pudo cargar el horario.');
    }
  };

  useEffect(() => {
    setFranjas(null);
    setErrorHorario(null);
    cargarFranjas();
  }, [vetHorario]);

  const agregarFranja = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorHorario(null);
    try {
      setAgregando(true);
      await createDisponibilidad({
        veterinario_id: vetHorario,
        dia_semana: dia,
        hora_inicio: `${inicio}:00`,
        hora_fin: `${fin}:00`
      });
      await cargarFranjas();
    } catch (err: any) {
      setErrorHorario(err.message || 'No se pudo añadir la franja.');
    } finally {
      setAgregando(false);
    }
  };

  const quitarFranja = async (f: Disponibilidad) => {
    setErrorHorario(null);
    try {
      await deleteDisponibilidad(f.id);
      await cargarFranjas();
    } catch (err: any) {
      setErrorHorario(err.message || 'No se pudo quitar la franja.');
    }
  };

  const franjasDelDia = (d: number) =>
    (franjas || [])
      .filter((f) => f.dia_semana === d)
      .sort((a, b) => a.hora_inicio.localeCompare(b.hora_inicio));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Servicios y Horarios
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Precio y duración de cada servicio, quién lo presta y en qué horario atiende cada veterinario.
          La duración y el horario deciden qué horas se ofrecen al agendar.
        </p>
      </div>

      {/* ------------------------------ Servicios ------------------------------ */}
      <section className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-amber-600" />
            Servicios
          </h2>
          {esAdmin && (
            <button
              id="btn-nuevo-servicio"
              onClick={abrirNuevo}
              className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-sm shadow-sm flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              <span>Nuevo Servicio</span>
            </button>
          )}
        </div>

        {errorServicios && <Aviso texto={errorServicios} onCerrar={() => setErrorServicios(null)} />}

        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">Servicio</th>
                  <th className="px-4 py-3">Precio</th>
                  <th className="px-4 py-3">Duración</th>
                  <th className="px-4 py-3">Lo prestan</th>
                  <th className="px-4 py-3">Estado</th>
                  {esAdmin && <th className="px-4 py-3 text-right">Acciones</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {servicios.map((s) => (
                  <tr key={s.id} id={`fila-servicio-${s.id}`} className="hover:bg-slate-50/70">
                    <td className="px-4 py-3.5">
                      <div className="font-bold text-slate-900">{s.nombre}</div>
                      {s.descripcion && <div className="text-[11px] text-slate-400">{s.descripcion}</div>}
                    </td>
                    <td className="px-4 py-3.5 font-bold text-slate-900">
                      {s.precio != null ? `$${s.precio.toLocaleString('es-CL')}` : <span className="font-normal text-slate-400">Sin precio</span>}
                    </td>
                    <td className="px-4 py-3.5">{s.duracion_min} min</td>
                    <td className="px-4 py-3.5">
                      {s.veterinarios_ids?.length
                        ? s.veterinarios_ids.map(nombreVet).join(', ')
                        : <span className="text-slate-400">Cualquier veterinario</span>}
                    </td>
                    <td className="px-4 py-3.5">
                      {s.activo ? (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">Activo</span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-600">Inactivo</span>
                      )}
                    </td>
                    {esAdmin && (
                      <td className="px-4 py-3.5 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            id={`btn-editar-servicio-${s.id}`}
                            onClick={() => abrirEdicion(s)}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100"
                            title="Editar servicio"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button
                            id={`btn-estado-servicio-${s.id}`}
                            onClick={() => cambiarActivo(s)}
                            className="p-1.5 rounded-lg text-slate-500 hover:text-amber-700 hover:bg-amber-50"
                            title={s.activo ? 'Desactivar (no se podrá agendar)' : 'Activar'}
                          >
                            <Power className="w-4 h-4" />
                          </button>
                          <button
                            id={`btn-eliminar-servicio-${s.id}`}
                            onClick={() => eliminarServicio(s)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50"
                            title="Eliminar"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        {!esAdmin && (
          <p className="text-[11px] text-slate-400">Sólo un administrador puede modificar los servicios.</p>
        )}
      </section>

      {/* ------------------------------ Horarios ------------------------------ */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <CalendarClock className="w-5 h-5 text-sky-600" />
            Horario de atención
          </h2>
          <select
            id="select-horario-veterinario"
            value={vetHorario}
            onChange={(e) => setVetHorario(Number(e.target.value))}
            disabled={!esAdmin}
            className={`${estiloCampo} sm:w-72 disabled:bg-slate-50`}
          >
            {(esAdmin ? veterinarios : veterinarios.filter((v) => v.id === currentUser.id)).map((v) => (
              <option key={v.id} value={v.id}>{v.nombre} {v.apellidos}</option>
            ))}
            {!esAdmin && !veterinarios.some((v) => v.id === currentUser.id) && (
              <option value={currentUser.id}>{currentUser.nombre} {currentUser.apellidos}</option>
            )}
          </select>
        </div>

        {errorHorario && <Aviso texto={errorHorario} onCerrar={() => setErrorHorario(null)} />}

        {franjas !== null && franjas.length === 0 && (
          <p id="aviso-sin-horario" className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-xl p-3">
            Sin franjas declaradas: no se le pueden agendar citas hasta que tenga horario.
          </p>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          {DIAS.map((nombre, d) => (
            <div key={d} id={`dia-horario-${d}`} className="bg-white rounded-2xl border border-slate-200 p-3 space-y-2">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">{nombre}</div>
              {franjas === null ? (
                <div className="text-[11px] text-slate-300">…</div>
              ) : franjasDelDia(d).length === 0 ? (
                <div className="text-[11px] text-slate-400">No atiende</div>
              ) : (
                franjasDelDia(d).map((f) => (
                  <div key={f.id} className="flex items-center justify-between gap-1 text-xs font-semibold text-slate-800 bg-sky-50 rounded-lg px-2 py-1">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-sky-500" />
                      {hhmm(f.hora_inicio)}–{hhmm(f.hora_fin)}
                    </span>
                    <button
                      id={`btn-quitar-franja-${f.id}`}
                      onClick={() => quitarFranja(f)}
                      className="text-slate-400 hover:text-red-600"
                      title="Quitar franja"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          ))}
        </div>

        <form onSubmit={agregarFranja} className="bg-white rounded-2xl border border-slate-200 p-4 flex flex-col sm:flex-row sm:items-end gap-3">
          <div className="flex-1">
            <label className={estiloEtiqueta} htmlFor="select-franja-dia">Día</label>
            <select id="select-franja-dia" value={dia} onChange={(e) => setDia(Number(e.target.value))} className={estiloCampo}>
              {DIAS.map((nombre, d) => <option key={d} value={d}>{nombre}</option>)}
            </select>
          </div>
          <div>
            <label className={estiloEtiqueta} htmlFor="input-franja-inicio">Desde</label>
            <input id="input-franja-inicio" type="time" required value={inicio} onChange={(e) => setInicio(e.target.value)} className={estiloCampo} />
          </div>
          <div>
            <label className={estiloEtiqueta} htmlFor="input-franja-fin">Hasta</label>
            <input id="input-franja-fin" type="time" required value={fin} onChange={(e) => setFin(e.target.value)} className={estiloCampo} />
          </div>
          <button
            id="btn-agregar-franja"
            type="submit"
            disabled={agregando || !vetHorario}
            className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-sm font-bold shadow-sm flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            {agregando ? 'Añadiendo…' : 'Añadir franja'}
          </button>
        </form>
      </section>

      {/* ------------------------------ Modal servicio ------------------------------ */}
      {editando && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden my-8">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <h3 className="font-bold text-lg">{editando === 'nuevo' ? 'Nuevo Servicio' : 'Editar Servicio'}</h3>
              <button onClick={() => setEditando(null)} className="text-slate-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={guardarServicio} className="p-6 space-y-4">
              {errorModal && <Aviso texto={errorModal} />}

              <div>
                <label className={estiloEtiqueta} htmlFor="input-servicio-nombre">Nombre *</label>
                <input
                  id="input-servicio-nombre"
                  type="text"
                  required
                  minLength={3}
                  maxLength={100}
                  value={formulario.nombre}
                  onChange={(e) => setFormulario({ ...formulario, nombre: e.target.value })}
                  className={estiloCampo}
                />
              </div>

              <div>
                <label className={estiloEtiqueta} htmlFor="textarea-servicio-descripcion">Descripción</label>
                <textarea
                  id="textarea-servicio-descripcion"
                  rows={2}
                  value={formulario.descripcion || ''}
                  onChange={(e) => setFormulario({ ...formulario, descripcion: e.target.value })}
                  className={`${estiloCampo} resize-none`}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={estiloEtiqueta} htmlFor="input-servicio-precio">Precio ($ CLP)</label>
                  <input
                    id="input-servicio-precio"
                    type="number"
                    min="0"
                    placeholder="Sin precio"
                    value={precioTexto}
                    onChange={(e) => setPrecioTexto(e.target.value)}
                    className={estiloCampo}
                  />
                </div>
                <div>
                  <label className={estiloEtiqueta} htmlFor="input-servicio-duracion">Duración (min) *</label>
                  <input
                    id="input-servicio-duracion"
                    type="number"
                    required
                    min="5"
                    max="480"
                    step="5"
                    value={formulario.duracion_min}
                    onChange={(e) => setFormulario({ ...formulario, duracion_min: Number(e.target.value) })}
                    className={estiloCampo}
                  />
                </div>
              </div>

              <fieldset>
                <legend className={estiloEtiqueta}>Lo prestan</legend>
                <p className="text-[11px] text-slate-400 mb-2">Si no marcas ninguno, lo puede prestar cualquier veterinario.</p>
                <div className="grid grid-cols-2 gap-2">
                  {veterinarios.map((v) => (
                    <label key={v.id} className="flex items-center gap-2 text-xs text-slate-700">
                      <input
                        id={`check-servicio-vet-${v.id}`}
                        type="checkbox"
                        checked={formulario.veterinarios_ids.includes(v.id)}
                        onChange={() => alternarVet(v.id)}
                        className="rounded border-slate-300 text-amber-600 focus:ring-amber-500"
                      />
                      {v.nombre} {v.apellidos}
                    </label>
                  ))}
                </div>
              </fieldset>

              <label className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                <input
                  id="check-servicio-activo"
                  type="checkbox"
                  checked={formulario.activo}
                  onChange={(e) => setFormulario({ ...formulario, activo: e.target.checked })}
                  className="rounded border-slate-300 text-amber-600 focus:ring-amber-500"
                />
                Activo (se puede agendar)
              </label>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditando(null)}
                  className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-sm font-semibold hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  id="btn-guardar-servicio"
                  type="submit"
                  disabled={guardando}
                  className="px-5 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-sm font-bold shadow-md disabled:opacity-50"
                >
                  {guardando ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
