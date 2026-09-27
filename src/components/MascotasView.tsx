import React, { useState } from 'react';
import { Mascota, Especie, User } from '../types';
import { Encabezado, ErrorFormulario, FotoMascota, Modal, PieModal, Vacio, useInterfaz } from './ui';
import { ClipboardPlus, Dog, Plus, Search } from 'lucide-react';

interface MascotasViewProps {
  mascotas: Mascota[];
  especies: Especie[];
  currentUser: User;
  onCreateMascota: (data: Partial<Mascota>) => Promise<void>;
  onOpenHistorialModalWithPet: (mascota: Mascota) => void;
}

const edad = (anos: number) => `${anos} ${anos === 1 ? 'año' : 'años'}`;

export const MascotasView: React.FC<MascotasViewProps> = ({
  mascotas,
  especies,
  currentUser,
  onCreateMascota,
  onOpenHistorialModalWithPet
}) => {
  const { avisar } = useInterfaz();
  const esPersonal = currentUser.tipo !== 'cliente';
  const [search, setSearch] = useState('');
  const [selectedEspecie, setSelectedEspecie] = useState<string>('todas');
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalPet, setDetailModalPet] = useState<Mascota | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Formulario de alta
  const [nombre, setNombre] = useState('');
  const [especieId, setEspecieId] = useState<number>(especies[0]?.id || 1);
  const [raza, setRaza] = useState('');
  const [edadAnos, setEdadAnos] = useState<number>(1);
  const [sexo, setSexo] = useState<'Macho' | 'Hembra'>('Macho');
  const [color, setColor] = useState('');
  const [peso, setPeso] = useState<number>(5);
  const [estaEsterilizado, setEstaEsterilizado] = useState(false);
  const [descripcion, setDescripcion] = useState('');
  const [imagenUrl, setImagenUrl] = useState('');

  // Sólo las especies que tienen alguna mascota, para no llenar de filtros vacíos.
  const especiesConMascotas = especies.filter((e) => mascotas.some((m) => m.especie_id === e.id));

  const filteredMascotas = mascotas.filter((m) => {
    if (selectedEspecie !== 'todas' && String(m.especie_id) !== selectedEspecie) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      m.nombre.toLowerCase().includes(q) ||
      (m.raza || '').toLowerCase().includes(q) ||
      (m.tutor_nombre || '').toLowerCase().includes(q)
    );
  });

  const abrirAlta = () => {
    setErrorMsg(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    // Las mismas reglas que el modelo Mascota del Django.
    if (/\d/.test(nombre)) return setErrorMsg('El nombre no puede tener números.');
    if (nombre.trim().length < 2) return setErrorMsg('El nombre necesita al menos 2 letras.');
    if (color && /\d/.test(color)) return setErrorMsg('El color no puede tener números.');
    if (peso <= 0) return setErrorMsg('El peso tiene que ser mayor que 0 kg.');

    try {
      setIsSubmitting(true);
      await onCreateMascota({
        cliente_id: currentUser.tipo === 'cliente' ? currentUser.id : null,
        especie_id: Number(especieId),
        nombre: nombre.trim(),
        raza: raza.trim(),
        edad_anos: Number(edadAnos),
        sexo,
        color: color.trim(),
        peso: Number(peso),
        esta_esterilizado: estaEsterilizado,
        estado_adopcion: 'normal',
        descripcion: descripcion.trim(),
        imagen_url: imagenUrl.trim() || undefined
      });
      avisar(`${nombre.trim()} quedó registrada.`);
      setModalOpen(false);
      setNombre('');
      setRaza('');
      setColor('');
      setDescripcion('');
      setImagenUrl('');
    } catch (err: any) {
      setErrorMsg(err.message || 'No se pudo registrar la mascota.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Encabezado
        titulo={esPersonal ? 'Pacientes' : 'Mis mascotas'}
        descripcion={esPersonal ? 'Todas las mascotas registradas en la clínica y sus tutores.' : 'Los datos de tus mascotas y su ficha clínica.'}
      >
        <button id="btn-registrar-mascota" onClick={abrirAlta} className="mp-btn mp-btn--primario">
          <Plus className="w-4 h-4" />
          Registrar mascota
        </button>
      </Encabezado>

      <div className="flex flex-col lg:flex-row lg:items-center gap-3">
        <div className="mp-buscador w-full lg:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" aria-hidden />
          <label htmlFor="input-search-mascotas" className="sr-only">Buscar mascota</label>
          <input
            type="search"
            id="input-search-mascotas"
            placeholder={esPersonal ? 'Nombre, raza o tutor' : 'Nombre o raza'}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="mp-campo"
          />
        </div>
        {especiesConMascotas.length > 1 && (
          <div role="group" aria-label="Filtrar por especie" className="flex flex-wrap gap-2">
            <button onClick={() => setSelectedEspecie('todas')} aria-pressed={selectedEspecie === 'todas'} className="mp-filtro">
              Todas
            </button>
            {especiesConMascotas.map((esp) => (
              <button
                key={esp.id}
                onClick={() => setSelectedEspecie(String(esp.id))}
                aria-pressed={selectedEspecie === String(esp.id)}
                className="mp-filtro"
              >
                {esp.nombre}
              </button>
            ))}
          </div>
        )}
      </div>

      {filteredMascotas.length === 0 ? (
        <Vacio
          icono={Dog}
          titulo={mascotas.length === 0 ? 'Todavía no hay mascotas' : 'Ninguna mascota coincide'}
          texto={mascotas.length === 0 ? 'Registra la primera para poder pedirle citas.' : 'Prueba con otro nombre o quita el filtro de especie.'}
        >
          {mascotas.length === 0 && (
            <button onClick={abrirAlta} className="mp-btn mp-btn--claro">
              <Plus className="w-4 h-4" />
              Registrar mascota
            </button>
          )}
        </Vacio>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredMascotas.map((m) => (
            <article key={m.id} className="mp-papel-blanco overflow-hidden flex flex-col">
              <div className="relative">
                <FotoMascota nombre={m.nombre} imagen={m.imagen_url} especie={m.especie_nombre} className="w-full h-44" tamanoIcono="w-16 h-16" />
                <span className="mp-pill mp-pill--info absolute top-3 left-3">{m.especie_nombre || 'Mascota'}</span>
              </div>

              <div className="p-5 flex-1 flex flex-col gap-3">
                <div>
                  <h2 className="font-titulo text-xl font-semibold text-[#1d4f60]">{m.nombre}</h2>
                  <p className="text-sm text-slate-500">
                    {[m.raza || 'Mestizo', m.sexo, edad(m.edad_anos)].join(', ')}
                  </p>
                </div>

                <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                  <div className="flex gap-1.5"><dt className="text-slate-500">Peso</dt><dd className="font-semibold">{m.peso} kg</dd></div>
                  <div className="flex gap-1.5"><dt className="text-slate-500">Esterilizado</dt><dd className="font-semibold">{m.esta_esterilizado ? 'Sí' : 'No'}</dd></div>
                  {esPersonal && (
                    <div className="col-span-2 flex gap-1.5">
                      <dt className="text-slate-500">Tutor</dt>
                      <dd className="font-semibold truncate">{m.tutor_nombre || 'Sin tutor (clínica)'}</dd>
                    </div>
                  )}
                </dl>

                {m.descripcion && <p className="text-sm text-slate-600 line-clamp-2">{m.descripcion}</p>}

                <div className="mt-auto pt-2 flex gap-2">
                  <button id={`btn-ver-ficha-${m.id}`} onClick={() => setDetailModalPet(m)} className="mp-btn mp-btn--azul mp-btn--sm flex-1">
                    Ver ficha
                  </button>
                  {esPersonal && (
                    <button id={`btn-historial-pet-${m.id}`} onClick={() => onOpenHistorialModalWithPet(m)} className="mp-btn mp-btn--borde mp-btn--sm">
                      <ClipboardPlus className="w-4 h-4" />
                      Historia
                    </button>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Ficha */}
      {detailModalPet && (
        <Modal titulo={`Ficha de ${detailModalPet.nombre}`} onCerrar={() => setDetailModalPet(null)}>
          <FotoMascota
            nombre={detailModalPet.nombre}
            imagen={detailModalPet.imagen_url}
            especie={detailModalPet.especie_nombre}
            className="w-full h-52"
            tamanoIcono="w-20 h-20"
          />
          <div className="p-6 space-y-4">
            <p className="text-sm text-slate-500">
              {[detailModalPet.especie_nombre, detailModalPet.raza || 'Mestizo', detailModalPet.color].filter(Boolean).join(' · ')}
            </p>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              {[
                ['Edad', edad(detailModalPet.edad_anos)],
                ['Sexo', detailModalPet.sexo],
                ['Peso', `${detailModalPet.peso} kg`],
                ['Esterilizado', detailModalPet.esta_esterilizado ? 'Sí' : 'No']
              ].map(([k, v]) => (
                <div key={k} className="bg-[#f3f7fa] rounded-lg p-3">
                  <dt className="text-slate-500 text-xs">{k}</dt>
                  <dd className="font-semibold">{v}</dd>
                </div>
              ))}
            </dl>
            {detailModalPet.descripcion && (
              <p className="text-sm bg-[#fff5e6] border-l-4 border-[#ff9f43] rounded-r-lg p-3">
                <strong>Notas:</strong> {detailModalPet.descripcion}
              </p>
            )}
            {detailModalPet.tutor_nombre && (
              <div className="text-sm border-t border-slate-200 pt-3">
                <p className="font-semibold">Tutor: {detailModalPet.tutor_nombre} {detailModalPet.tutor_apellidos}</p>
                <p className="text-slate-500">
                  {[detailModalPet.tutor_telefono, detailModalPet.tutor_email].filter(Boolean).join(' · ') || 'Sin datos de contacto'}
                </p>
              </div>
            )}
            <PieModal>
              <button onClick={() => setDetailModalPet(null)} className="mp-btn mp-btn--azul">Cerrar</button>
            </PieModal>
          </div>
        </Modal>
      )}

      {/* Alta */}
      {modalOpen && (
        <Modal titulo="Registrar mascota" icono={<Dog className="w-5 h-5 text-[#ff9f43]" />} onCerrar={() => setModalOpen(false)}>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <ErrorFormulario texto={errorMsg} />
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <label htmlFor="input-mascota-nombre" className="mp-etiqueta">Nombre</label>
                <input id="input-mascota-nombre" type="text" value={nombre} onChange={(e) => setNombre(e.target.value)} className="mp-campo" required />
              </div>
              <div>
                <label htmlFor="select-mascota-especie" className="mp-etiqueta">Especie</label>
                <select id="select-mascota-especie" value={especieId} onChange={(e) => setEspecieId(Number(e.target.value))} className="mp-campo">
                  {especies.map((esp) => <option key={esp.id} value={esp.id}>{esp.nombre}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="input-mascota-raza" className="mp-etiqueta">Raza</label>
                <input id="input-mascota-raza" type="text" placeholder="Mestizo" value={raza} onChange={(e) => setRaza(e.target.value)} className="mp-campo" />
              </div>
              <div>
                <label htmlFor="select-mascota-sexo" className="mp-etiqueta">Sexo</label>
                <select id="select-mascota-sexo" value={sexo} onChange={(e) => setSexo(e.target.value as 'Macho' | 'Hembra')} className="mp-campo">
                  <option value="Macho">Macho</option>
                  <option value="Hembra">Hembra</option>
                </select>
              </div>
              <div>
                <label htmlFor="input-mascota-edad" className="mp-etiqueta">Edad (años)</label>
                <input id="input-mascota-edad" type="number" min="0" max="40" value={edadAnos} onChange={(e) => setEdadAnos(parseInt(e.target.value))} className="mp-campo" required />
              </div>
              <div>
                <label htmlFor="input-mascota-peso" className="mp-etiqueta">Peso (kg)</label>
                <input id="input-mascota-peso" type="number" step="0.1" min="0.1" value={peso} onChange={(e) => setPeso(parseFloat(e.target.value))} className="mp-campo" required />
              </div>
              <div>
                <label htmlFor="input-mascota-color" className="mp-etiqueta">Color</label>
                <input id="input-mascota-color" type="text" value={color} onChange={(e) => setColor(e.target.value)} className="mp-campo" required />
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm font-medium">
              <input id="check-mascota-esterilizado" type="checkbox" checked={estaEsterilizado} onChange={(e) => setEstaEsterilizado(e.target.checked)} className="w-4 h-4 accent-[#1d95c8]" />
              Está esterilizada
            </label>

            <div>
              <label htmlFor="input-mascota-foto" className="mp-etiqueta">Foto (enlace, opcional)</label>
              <input id="input-mascota-foto" type="url" placeholder="https://…" value={imagenUrl} onChange={(e) => setImagenUrl(e.target.value)} className="mp-campo" />
              <p className="mp-ayuda">Sin foto se muestra una ilustración de su especie.</p>
            </div>

            <div>
              <label htmlFor="textarea-mascota-descripcion" className="mp-etiqueta">Notas (opcional)</label>
              <textarea
                id="textarea-mascota-descripcion"
                rows={2}
                placeholder="Alergias, carácter, hábitos…"
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
                className="mp-campo resize-none"
              />
            </div>

            <PieModal>
              <button type="button" onClick={() => setModalOpen(false)} className="mp-btn mp-btn--borde">Cancelar</button>
              <button type="submit" id="btn-submit-mascota" disabled={isSubmitting} className="mp-btn mp-btn--primario">
                {isSubmitting ? 'Registrando…' : 'Registrar mascota'}
              </button>
            </PieModal>
          </form>
        </Modal>
      )}
    </div>
  );
};
