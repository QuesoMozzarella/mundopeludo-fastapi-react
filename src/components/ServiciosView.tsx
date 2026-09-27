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
import { Encabezado, ErrorFormulario, Modal, PieModal, useInterfaz } from './ui';
import { formatearPrecio } from '../formato';
import { CalendarClock, Clock, Pencil, Plus, Power, Stethoscope, Trash2, X } from 'lucide-react';

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

/** "09:00:00" -> "09:00" */
const hhmm = (hora: string) => hora.slice(0, 5);

export const ServiciosView: React.FC<ServiciosViewProps> = ({
  servicios,
  veterinarios,
  currentUser,
  onRecargarServicios
}) => {
  const esAdmin = currentUser.tipo === 'administrador';
  const { avisar, confirmar } = useInterfaz();

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
      avisar(editando === 'nuevo' ? `Servicio «${datos.nombre}» creado.` : 'Cambios guardados.');
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
      avisar(s.activo ? `«${s.nombre}» desactivado: ya no se puede agendar.` : `«${s.nombre}» activado.`);
    } catch (err: any) {
      setErrorServicios(err.message || 'No se pudo cambiar el estado del servicio.');
    }
  };

  const eliminarServicio = async (s: Servicio) => {
    const ok = await confirmar({
      titulo: 'Eliminar el servicio',
      mensaje: `«${s.nombre}» se eliminará. Si ya tiene citas no se podrá: en ese caso, desactívalo.`,
      confirmar: 'Eliminar servicio',
      peligro: true
    });
    if (!ok) return;
    setErrorServicios(null);
    try {
      await deleteServicio(s.id);
      await onRecargarServicios();
      avisar(`Servicio «${s.nombre}» eliminado.`);
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
      <Encabezado
        titulo="Servicios y horarios"
        descripcion="Precio y duración de cada servicio, quién lo presta y el horario de cada veterinario. La duración y el horario deciden qué horas se ofrecen al pedir una cita."
      />

      {/* ------------------------------ Servicios ------------------------------ */}
      <section className="space-y-4">
        <div className="flex items-center justify-between gap-4">
          <h2 className="font-titulo text-xl font-semibold flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-[#9dddf5]" />
            Servicios
          </h2>
          {esAdmin && (
            <button
              id="btn-nuevo-servicio"
              onClick={abrirNuevo}
              className="mp-btn mp-btn--primario"
            >
              <Plus className="w-4 h-4" />
              Nuevo servicio
            </button>
          )}
        </div>

        <ErrorFormulario texto={errorServicios} />

        <div className="mp-papel overflow-hidden">
          <div className="mp-desplazable">
            <table className="mp-tabla">
              <thead>
                <tr>
                  <th>Servicio</th>
                  <th>Precio</th>
                  <th>Duración</th>
                  <th>Lo prestan</th>
                  <th>Estado</th>
                  {esAdmin && <th className="text-right"><span className="sr-only">Acciones</span></th>}
                </tr>
              </thead>
              <tbody>
                {servicios.map((s) => (
                  <tr key={s.id} id={`fila-servicio-${s.id}`}>
                    <td>
                      <div className="font-semibold">{s.nombre}</div>
                      {s.descripcion && <div className="text-xs text-slate-500">{s.descripcion}</div>}
                    </td>
                    <td className="font-semibold whitespace-nowrap">
                      {s.precio != null ? formatearPrecio(s.precio) : <span className="font-normal text-slate-500">Sin precio</span>}
                    </td>
                    <td>{s.duracion_min} min</td>
                    <td>
                      {s.veterinarios_ids?.length
                        ? s.veterinarios_ids.map(nombreVet).join(', ')
                        : <span className="text-slate-500">Cualquier veterinario</span>}
                    </td>
                    <td>
                      {s.activo ? (
                        <span className="mp-pill mp-pill--exito">Activo</span>
                      ) : (
                        <span className="mp-pill mp-pill--neutro">Inactivo</span>
                      )}
                    </td>
                    {esAdmin && (
                      <td className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            id={`btn-editar-servicio-${s.id}`}
                            onClick={() => abrirEdicion(s)}
                            className="mp-accion"
                            title="Editar servicio"
                            aria-label={`Editar ${s.nombre}`}
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            id={`btn-estado-servicio-${s.id}`}
                            onClick={() => cambiarActivo(s)}
                            className="mp-accion mp-accion--neutro"
                            title={s.activo ? 'Desactivar (no se podrá agendar)' : 'Activar'}
                            aria-label={s.activo ? `Desactivar ${s.nombre}` : `Activar ${s.nombre}`}
                          >
                            <Power className="w-4 h-4" />
                          </button>
                          <button
                            id={`btn-eliminar-servicio-${s.id}`}
                            onClick={() => eliminarServicio(s)}
                            className="mp-accion mp-accion--peligro"
                            title="Eliminar"
                            aria-label={`Eliminar ${s.nombre}`}
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
          <p className="text-sm text-white/75">Sólo un administrador puede modificar los servicios.</p>
        )}
      </section>

      {/* ------------------------------ Horarios ------------------------------ */}
      <section className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="font-titulo text-xl font-semibold flex items-center gap-2">
            <CalendarClock className="w-5 h-5 text-[#9dddf5]" />
            Horario de atención
          </h2>
          <select
            id="select-horario-veterinario"
            value={vetHorario}
            onChange={(e) => setVetHorario(Number(e.target.value))}
            disabled={!esAdmin}
            className={`mp-campo sm:w-72 disabled:bg-slate-50`}
          >
            {(esAdmin ? veterinarios : veterinarios.filter((v) => v.id === currentUser.id)).map((v) => (
              <option key={v.id} value={v.id}>{v.nombre} {v.apellidos}</option>
            ))}
            {!esAdmin && !veterinarios.some((v) => v.id === currentUser.id) && (
              <option value={currentUser.id}>{currentUser.nombre} {currentUser.apellidos}</option>
            )}
          </select>
        </div>

        <ErrorFormulario texto={errorHorario} />

        {franjas !== null && franjas.length === 0 && (
          <p id="aviso-sin-horario" className="mp-aviso mp-aviso--info">
            Sin franjas declaradas: no se le pueden agendar citas hasta que tenga horario.
          </p>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
          {DIAS.map((nombre, d) => (
            <div key={d} id={`dia-horario-${d}`} className="mp-panel p-3 space-y-2">
              <div className="text-sm font-semibold">{nombre}</div>
              {franjas === null ? (
                <div className="text-xs text-white/50">…</div>
              ) : franjasDelDia(d).length === 0 ? (
                <div className="text-xs text-white/65">No atiende</div>
              ) : (
                franjasDelDia(d).map((f) => (
                  <div key={f.id} className="flex items-center justify-between gap-1 text-xs font-semibold text-[#1d4f60] bg-white rounded-lg px-2 py-1">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-[#1d95c8]" />
                      {hhmm(f.hora_inicio)}–{hhmm(f.hora_fin)}
                    </span>
                    <button
                      id={`btn-quitar-franja-${f.id}`}
                      onClick={() => quitarFranja(f)}
                      className="text-slate-400 hover:text-[#dc3545]"
                      title="Quitar franja"
                      aria-label={`Quitar la franja ${hhmm(f.hora_inicio)}–${hhmm(f.hora_fin)}`}
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          ))}
        </div>

        <form onSubmit={agregarFranja} className="mp-papel-blanco p-4 flex flex-col sm:flex-row sm:items-end gap-3">
          <div className="flex-1">
            <label className="mp-etiqueta" htmlFor="select-franja-dia">Día</label>
            <select id="select-franja-dia" value={dia} onChange={(e) => setDia(Number(e.target.value))} className="mp-campo">
              {DIAS.map((nombre, d) => <option key={d} value={d}>{nombre}</option>)}
            </select>
          </div>
          <div>
            <label className="mp-etiqueta" htmlFor="input-franja-inicio">Desde</label>
            <input id="input-franja-inicio" type="time" required value={inicio} onChange={(e) => setInicio(e.target.value)} className="mp-campo" />
          </div>
          <div>
            <label className="mp-etiqueta" htmlFor="input-franja-fin">Hasta</label>
            <input id="input-franja-fin" type="time" required value={fin} onChange={(e) => setFin(e.target.value)} className="mp-campo" />
          </div>
          <button
            id="btn-agregar-franja"
            type="submit"
            disabled={agregando || !vetHorario}
            className="mp-btn mp-btn--azul"
          >
            <Plus className="w-4 h-4" />
            {agregando ? 'Añadiendo…' : 'Añadir franja'}
          </button>
        </form>
      </section>

      {/* ------------------------------ Modal servicio ------------------------------ */}
      {editando && (
        <Modal
          titulo={editando === 'nuevo' ? 'Nuevo servicio' : `Editar ${editando.nombre}`}
          icono={<Stethoscope className="w-5 h-5 text-[#ff9f43]" />}
          onCerrar={() => setEditando(null)}
        >

            <form onSubmit={guardarServicio} className="p-6 space-y-4">
              <ErrorFormulario texto={errorModal} />

              <div>
                <label className="mp-etiqueta" htmlFor="input-servicio-nombre">Nombre *</label>
                <input
                  id="input-servicio-nombre"
                  type="text"
                  required
                  minLength={3}
                  maxLength={100}
                  value={formulario.nombre}
                  onChange={(e) => setFormulario({ ...formulario, nombre: e.target.value })}
                  className="mp-campo"
                />
              </div>

              <div>
                <label className="mp-etiqueta" htmlFor="textarea-servicio-descripcion">Descripción</label>
                <textarea
                  id="textarea-servicio-descripcion"
                  rows={2}
                  value={formulario.descripcion || ''}
                  onChange={(e) => setFormulario({ ...formulario, descripcion: e.target.value })}
                  className={`mp-campo resize-none`}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mp-etiqueta" htmlFor="input-servicio-precio">Precio ($ CLP)</label>
                  <input
                    id="input-servicio-precio"
                    type="number"
                    min="0"
                    placeholder="Sin precio"
                    value={precioTexto}
                    onChange={(e) => setPrecioTexto(e.target.value)}
                    className="mp-campo"
                  />
                </div>
                <div>
                  <label className="mp-etiqueta" htmlFor="input-servicio-duracion">Duración (min) *</label>
                  <input
                    id="input-servicio-duracion"
                    type="number"
                    required
                    min="5"
                    max="480"
                    step="5"
                    value={formulario.duracion_min}
                    onChange={(e) => setFormulario({ ...formulario, duracion_min: Number(e.target.value) })}
                    className="mp-campo"
                  />
                </div>
              </div>

              <fieldset>
                <legend className="mp-etiqueta">Lo prestan</legend>
                <p className="mp-ayuda mt-0 mb-2">Si no marcas ninguno, lo puede prestar cualquier veterinario.</p>
                <div className="grid grid-cols-2 gap-2">
                  {veterinarios.map((v) => (
                    <label key={v.id} className="flex items-center gap-2 text-xs text-slate-700">
                      <input
                        id={`check-servicio-vet-${v.id}`}
                        type="checkbox"
                        checked={formulario.veterinarios_ids.includes(v.id)}
                        onChange={() => alternarVet(v.id)}
                        className="w-4 h-4 accent-[#1d95c8]"
                      />
                      {v.nombre} {v.apellidos}
                    </label>
                  ))}
                </div>
              </fieldset>

              <label className="flex items-center gap-2 text-sm font-medium">
                <input
                  id="check-servicio-activo"
                  type="checkbox"
                  checked={formulario.activo}
                  onChange={(e) => setFormulario({ ...formulario, activo: e.target.checked })}
                  className="w-4 h-4 accent-[#1d95c8]"
                />
                Activo (se puede agendar)
              </label>

              <PieModal>
                <button type="button" onClick={() => setEditando(null)} className="mp-btn mp-btn--borde">
                  Cancelar
                </button>
                <button id="btn-guardar-servicio" type="submit" disabled={guardando} className="mp-btn mp-btn--primario">
                  {guardando ? 'Guardando…' : 'Guardar servicio'}
                </button>
              </PieModal>
            </form>
        </Modal>
      )}
    </div>
  );
};
