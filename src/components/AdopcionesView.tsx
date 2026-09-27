import React, { useState } from 'react';
import { Mascota, SolicitudAdopcion, User } from '../types';
import { formatearFecha } from '../formato';
import { Encabezado, ErrorFormulario, FotoMascota, Modal, PieModal, Vacio, useInterfaz } from './ui';
import { Check, FileText, HeartHandshake, X } from 'lucide-react';

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

const ESTADO_SOLICITUD: Record<string, { texto: string; clase: string }> = {
  pendiente: { texto: 'En revisión', clase: 'mp-pill--pendiente' },
  aprobada: { texto: 'Aprobada', clase: 'mp-pill--exito' },
  rechazada: { texto: 'Rechazada', clase: 'mp-pill--peligro' },
  cancelada: { texto: 'Cancelada', clase: 'mp-pill--neutro' }
};

const edad = (anos: number) => `${anos} ${anos === 1 ? 'año' : 'años'}`;

export const AdopcionesView: React.FC<AdopcionesViewProps> = ({
  adopciones,
  solicitudes,
  currentUser,
  onRequiereLogin,
  onApplyAdopcion,
  onAprobarSolicitud,
  onRechazarSolicitud
}) => {
  const { avisar, confirmar } = useInterfaz();
  const esPersonal = currentUser?.tipo === 'veterinario' || currentUser?.tipo === 'administrador';
  const [activeSubTab, setActiveSubTab] = useState<'catalogo' | 'solicitudes'>('catalogo');
  const [selectedPetForAdoption, setSelectedPetForAdoption] = useState<Mascota | null>(null);
  const [notasCliente, setNotasCliente] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reviewNotes, setReviewNotes] = useState<{ [id: number]: string }>({});
  const pendientes = solicitudes.filter((s) => s.estado === 'pendiente').length;

  const handleApplySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPetForAdoption || !currentUser) return;
    if (!notasCliente.trim()) {
      setErrorMsg('Cuéntanos cómo es tu hogar y por qué quieres adoptar.');
      return;
    }
    try {
      setIsSubmitting(true);
      await onApplyAdopcion(selectedPetForAdoption.id, currentUser.id, notasCliente.trim());
      avisar(`Solicitud enviada. Te avisaremos cuando la revisemos.`);
      setSelectedPetForAdoption(null);
      setNotasCliente('');
      setActiveSubTab('solicitudes');
    } catch (err: any) {
      setErrorMsg(err.message || 'No se pudo enviar la solicitud.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const revisar = async (sol: SolicitudAdopcion, aprobar: boolean) => {
    if (!currentUser) return;
    const ok = await confirmar(
      aprobar
        ? {
            titulo: `Aprobar la adopción de ${sol.mascota_nombre}`,
            mensaje: `${sol.mascota_nombre} pasará a ser de ${sol.cliente_nombre} y las demás solicitudes por esta mascota se rechazarán.`,
            confirmar: 'Aprobar adopción'
          }
        : {
            titulo: 'Rechazar la solicitud',
            mensaje: `${sol.mascota_nombre} seguirá disponible para adopción.`,
            confirmar: 'Rechazar',
            peligro: true
          }
    );
    if (!ok) return;
    try {
      if (aprobar) await onAprobarSolicitud(sol.id, currentUser.id, reviewNotes[sol.id]);
      else await onRechazarSolicitud(sol.id, currentUser.id, reviewNotes[sol.id]);
      avisar(aprobar ? `Adopción de ${sol.mascota_nombre} aprobada.` : 'Solicitud rechazada.');
    } catch (err: any) {
      avisar(err.message || 'No se pudo revisar la solicitud.', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <Encabezado
        titulo="Adopciones"
        descripcion="Mascotas rescatadas que buscan familia. Postula y el equipo de la clínica revisará tu solicitud."
      />

      {currentUser && (
        <div role="tablist" aria-label="Adopciones" className="mp-tabs">
          <button
            role="tab"
            id="subtab-catalogo-adopciones"
            aria-selected={activeSubTab === 'catalogo'}
            onClick={() => setActiveSubTab('catalogo')}
            className="mp-tab"
          >
            En adopción ({adopciones.length})
          </button>
          <button
            role="tab"
            id="subtab-solicitudes-adopciones"
            aria-selected={activeSubTab === 'solicitudes'}
            onClick={() => setActiveSubTab('solicitudes')}
            className="mp-tab"
          >
            {esPersonal ? 'Solicitudes' : 'Mis solicitudes'} ({solicitudes.length})
            {esPersonal && pendientes > 0 && <span className="mp-pill mp-pill--pendiente">{pendientes} por revisar</span>}
          </button>
        </div>
      )}

      {activeSubTab === 'catalogo' ? (
        adopciones.length === 0 ? (
          <Vacio icono={HeartHandshake} titulo="Ahora mismo no hay mascotas en adopción" texto="Vuelve pronto: publicamos cada mascota rescatada en cuanto está lista para un hogar." />
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {adopciones.map((pet) => (
              <article key={pet.id} className="mp-papel-blanco overflow-hidden flex flex-col">
                <div className="relative">
                  <FotoMascota nombre={pet.nombre} imagen={pet.imagen_url} especie={pet.especie_nombre} className="w-full h-52" tamanoIcono="w-16 h-16" />
                  <span className="mp-pill mp-pill--info absolute top-3 left-3">{pet.especie_nombre}</span>
                </div>
                <div className="p-5 flex-1 flex flex-col gap-3">
                  <div>
                    <h2 className="font-titulo text-xl font-semibold text-[#1d4f60]">{pet.nombre}</h2>
                    <p className="text-sm text-slate-500">{[pet.raza || 'Mestizo', pet.sexo, edad(pet.edad_anos)].join(', ')}</p>
                  </div>
                  {pet.descripcion && <p className="text-sm text-slate-600">{pet.descripcion}</p>}
                  <dl className="flex flex-wrap gap-x-5 gap-y-1 text-sm">
                    <div className="flex gap-1.5"><dt className="text-slate-500">Peso</dt><dd className="font-semibold">{pet.peso} kg</dd></div>
                    <div className="flex gap-1.5"><dt className="text-slate-500">Esterilizado</dt><dd className="font-semibold">{pet.esta_esterilizado ? 'Sí' : 'No'}</dd></div>
                  </dl>
                  <button
                    id={`btn-solicitar-adopcion-${pet.id}`}
                    onClick={() => {
                      if (!currentUser) return onRequiereLogin();
                      setErrorMsg(null);
                      setSelectedPetForAdoption(pet);
                    }}
                    className="mp-btn mp-btn--primario mt-auto"
                  >
                    <HeartHandshake className="w-4 h-4" />
                    Quiero adoptar a {pet.nombre}
                  </button>
                </div>
              </article>
            ))}
          </div>
        )
      ) : solicitudes.length === 0 ? (
        <Vacio
          icono={FileText}
          titulo={esPersonal ? 'No hay solicitudes' : 'Todavía no has postulado'}
          texto={esPersonal ? 'Cuando alguien postule a una adopción, aparecerá aquí para revisarla.' : 'Elige una mascota en adopción y cuéntanos cómo es tu hogar.'}
        />
      ) : (
        <div className="space-y-4">
          {solicitudes.map((sol) => {
            const estado = ESTADO_SOLICITUD[sol.estado] ?? { texto: sol.estado, clase: 'mp-pill--neutro' };
            return (
              <article key={sol.id} className="mp-papel-blanco p-5 flex flex-col lg:flex-row lg:items-start gap-5">
                <FotoMascota nombre={sol.mascota_nombre} imagen={sol.mascota_imagen} className="w-16 h-16 rounded-xl shrink-0" tamanoIcono="w-8 h-8" />
                <div className="flex-1 min-w-0 space-y-2">
                  <div className="flex flex-wrap items-center gap-3">
                    <h3 className="font-titulo text-lg font-semibold text-[#1d4f60]">Postulación por {sol.mascota_nombre}</h3>
                    <span className={`mp-pill ${estado.clase}`}>{estado.texto}</span>
                  </div>
                  <p className="text-sm text-slate-600 flex flex-wrap gap-x-4 gap-y-1">
                    <span className="font-semibold text-[#2c3e50]">{sol.cliente_nombre} {sol.cliente_apellidos}</span>
                    <span>{sol.cliente_email}</span>
                    <span>Tel: {sol.cliente_telefono || 'sin teléfono'}</span>
                    <span>{formatearFecha(sol.fecha_solicitud)}</span>
                  </p>
                  <blockquote className="text-sm bg-[#f3f7fa] rounded-lg p-3 text-slate-700">{sol.notas_cliente}</blockquote>
                  {sol.notas_revisor && (
                    <p className="text-sm bg-[#fff5e6] border-l-4 border-[#ff9f43] rounded-r-lg p-2.5">
                      <strong>Nota de la clínica:</strong> {sol.notas_revisor}
                    </p>
                  )}
                </div>

                {esPersonal && sol.estado === 'pendiente' && (
                  <div className="flex flex-col gap-2 lg:w-64 shrink-0">
                    <label htmlFor={`nota-revision-${sol.id}`} className="sr-only">Nota para el solicitante</label>
                    <input
                      id={`nota-revision-${sol.id}`}
                      type="text"
                      placeholder="Nota para el solicitante (opcional)"
                      value={reviewNotes[sol.id] || ''}
                      onChange={(e) => setReviewNotes({ ...reviewNotes, [sol.id]: e.target.value })}
                      className="mp-campo"
                    />
                    <div className="flex gap-2">
                      <button id={`btn-aprobar-solicitud-${sol.id}`} onClick={() => revisar(sol, true)} className="mp-btn mp-btn--exito mp-btn--sm flex-1">
                        <Check className="w-4 h-4" />
                        Aprobar
                      </button>
                      <button id={`btn-rechazar-solicitud-${sol.id}`} onClick={() => revisar(sol, false)} className="mp-btn mp-btn--borde mp-btn--sm flex-1">
                        <X className="w-4 h-4" />
                        Rechazar
                      </button>
                    </div>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}

      {selectedPetForAdoption && currentUser && (
        <Modal
          titulo={`Adoptar a ${selectedPetForAdoption.nombre}`}
          icono={<HeartHandshake className="w-5 h-5 text-[#ff9f43]" />}
          onCerrar={() => setSelectedPetForAdoption(null)}
        >
          <form onSubmit={handleApplySubmit} className="p-6 space-y-4">
            <ErrorFormulario texto={errorMsg} />
            <div className="flex items-center gap-4 p-3 bg-[#f3f7fa] rounded-xl">
              <FotoMascota
                nombre={selectedPetForAdoption.nombre}
                imagen={selectedPetForAdoption.imagen_url}
                especie={selectedPetForAdoption.especie_nombre}
                className="w-14 h-14 rounded-xl"
                tamanoIcono="w-7 h-7"
              />
              <div>
                <p className="font-semibold">{selectedPetForAdoption.nombre}</p>
                <p className="text-sm text-slate-500">{selectedPetForAdoption.especie_nombre}, {edad(selectedPetForAdoption.edad_anos)}</p>
              </div>
            </div>

            <div className="text-sm">
              <p className="mp-etiqueta">Te contactaremos en</p>
              <p>{currentUser.email}{currentUser.telefono ? ` · ${currentUser.telefono}` : ''}</p>
            </div>

            <div>
              <label htmlFor="textarea-motivo-adopcion" className="mp-etiqueta">¿Cómo es tu hogar y por qué quieres adoptar?</label>
              <textarea
                id="textarea-motivo-adopcion"
                rows={4}
                placeholder="Casa o apartamento, patio, otras mascotas, tiempo para paseos…"
                value={notasCliente}
                onChange={(e) => setNotasCliente(e.target.value)}
                className="mp-campo resize-none"
                required
              />
            </div>

            <PieModal>
              <button type="button" onClick={() => setSelectedPetForAdoption(null)} className="mp-btn mp-btn--borde">Cancelar</button>
              <button type="submit" id="btn-enviar-solicitud-adopcion" disabled={isSubmitting} className="mp-btn mp-btn--primario">
                {isSubmitting ? 'Enviando…' : 'Enviar solicitud'}
              </button>
            </PieModal>
          </form>
        </Modal>
      )}
    </div>
  );
};
