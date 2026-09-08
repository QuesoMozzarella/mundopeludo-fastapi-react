import React, { useState } from 'react';
import { Mascota, Especie, User } from '../types';
import { 
  Dog, 
  Plus, 
  Search, 
  Activity, 
  Calendar, 
  User as UserIcon, 
  FileText, 
  CheckCircle2, 
  X, 
  AlertCircle 
} from 'lucide-react';

interface MascotasViewProps {
  mascotas: Mascota[];
  especies: Especie[];
  currentUser: User;
  onCreateMascota: (data: Partial<Mascota>) => Promise<void>;
  onOpenHistorialModalWithPet: (mascota: Mascota) => void;
}

export const MascotasView: React.FC<MascotasViewProps> = ({
  mascotas,
  especies,
  currentUser,
  onCreateMascota,
  onOpenHistorialModalWithPet
}) => {
  const [search, setSearch] = useState('');
  const [selectedEspecie, setSelectedEspecie] = useState<string>('todas');
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalPet, setDetailModalPet] = useState<Mascota | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // New pet form state
  const [nombre, setNombre] = useState('');
  const [especieId, setEspecieId] = useState<number>(especies[0]?.id || 1);
  const [raza, setRaza] = useState('');
  const [edadAnos, setEdadAnos] = useState<number>(2);
  const [sexo, setSexo] = useState<'Macho' | 'Hembra'>('Macho');
  const [color, setColor] = useState('');
  const [peso, setPeso] = useState<number>(10.0);
  const [estaEsterilizado, setEstaEsterilizado] = useState(false);
  const [descripcion, setDescripcion] = useState('');
  const [imagenUrl, setImagenUrl] = useState('');

  const filteredMascotas = mascotas.filter((m) => {
    // Si es cliente, ver sus mascotas y las de la clínica
    if (currentUser.tipo === 'cliente' && m.cliente_id && m.cliente_id !== currentUser.id) {
      return false;
    }
    if (selectedEspecie !== 'todas' && String(m.especie_id) !== selectedEspecie) {
      return false;
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        m.nombre.toLowerCase().includes(q) ||
        (m.raza && m.raza.toLowerCase().includes(q)) ||
        (m.tutor_nombre && m.tutor_nombre.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    // Validaciones estrictas del modelo Django MundoPeludo
    if (/\d/.test(nombre)) {
      setErrorMsg('El nombre de la mascota no puede contener números.');
      return;
    }
    if (nombre.trim().length < 2) {
      setErrorMsg('El nombre debe tener al menos 2 caracteres.');
      return;
    }
    if (color && /\d/.test(color)) {
      setErrorMsg('El color no puede contener números.');
      return;
    }
    if (peso <= 0) {
      setErrorMsg('El peso debe ser mayor a 0 kg.');
      return;
    }

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

      setModalOpen(false);
      // Reset form
      setNombre('');
      setRaza('');
      setColor('');
      setDescripcion('');
      setImagenUrl('');
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al registrar la mascota.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#156a8e] tracking-tight">
            Pacientes & Mascotas
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Registro clínico completo, carnet veterinario y seguimiento preventivo.
          </p>
        </div>

        <button
          id="btn-registrar-mascota"
          onClick={() => setModalOpen(true)}
          className="px-5 py-2.5 rounded-xl bg-[#ff9f43] hover:bg-[#f08e30] text-white font-bold text-sm shadow-sm flex items-center justify-center gap-2 transition-all self-start sm:self-auto active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>Registrar Mascota</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            id="input-search-mascotas"
            placeholder="Buscar por nombre, raza o tutor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#1d95c8] bg-white"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto no-scrollbar">
          <button
            onClick={() => setSelectedEspecie('todas')}
            className={`px-3 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors ${selectedEspecie === 'todas' ? 'bg-[#1d95c8] text-white shadow-xs' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
          >
            Todas las especies
          </button>
          {especies.map((esp) => (
            <button
              key={esp.id}
              onClick={() => setSelectedEspecie(String(esp.id))}
              className={`px-3 py-2 rounded-xl text-xs font-bold whitespace-nowrap transition-colors ${selectedEspecie === String(esp.id) ? 'bg-[#1d95c8] text-white shadow-xs' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
            >
              {esp.nombre}
            </button>
          ))}
        </div>
      </div>

      {/* Pet Cards Grid */}
      {filteredMascotas.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-12 text-center">
          <Dog className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-700">No se encontraron mascotas</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
            No hay pacientes registrados que coincidan con la búsqueda o filtro aplicado.
          </p>
          <button
            onClick={() => setModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-[#ff9f43] text-white text-xs font-bold hover:bg-[#f08e30]"
          >
            Registrar Mascota
          </button>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMascotas.map((m) => (
            <div 
              key={m.id}
              className="card-mundo overflow-hidden flex flex-col justify-between"
            >
              <div>
                <div className="relative h-48 bg-slate-100">
                  <img 
                    src={m.imagen_url || "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=600&auto=format&fit=crop&q=80"} 
                    alt={m.nombre} 
                    className="w-full h-full object-cover"
                  />
                  <span className="absolute top-3 right-3 px-2.5 py-1 rounded-full text-[11px] font-bold bg-white/90 backdrop-blur-xs text-slate-800 shadow-2xs">
                    {m.especie_nombre || 'Mascota'}
                  </span>
                </div>

                <div className="p-5">
                  <div className="flex items-baseline justify-between mb-1">
                    <h3 className="text-lg font-bold text-slate-900">{m.nombre}</h3>
                    <span className="text-xs font-semibold text-slate-500">{m.raza || 'Mestizo'}</span>
                  </div>

                  <p className="text-xs text-slate-500 mb-4 line-clamp-2">
                    {m.descripcion || 'Paciente regular de la clínica MundoPeludo.'}
                  </p>

                  <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-xl border border-slate-100 mb-4">
                    <div>
                      <span className="text-slate-400 font-medium">Edad:</span>{' '}
                      <span className="font-bold text-slate-800">{m.edad_anos} {m.edad_anos === 1 ? 'año' : 'años'}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-medium">Sexo:</span>{' '}
                      <span className="font-bold text-slate-800">{m.sexo}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-medium">Peso:</span>{' '}
                      <span className="font-bold text-slate-800">{m.peso} kg</span>
                    </div>
                    <div>
                      <span className="text-slate-400 font-medium">Esterilizado:</span>{' '}
                      <span className={`font-bold ${m.esta_esterilizado ? 'text-emerald-600' : 'text-slate-600'}`}>
                        {m.esta_esterilizado ? 'Sí' : 'No'}
                      </span>
                    </div>
                  </div>

                  {m.tutor_nombre && (
                    <div className="flex items-center gap-1.5 text-xs text-slate-600">
                      <UserIcon className="w-3.5 h-3.5 text-amber-500" />
                      <span>Tutor: <strong>{m.tutor_nombre} {m.tutor_apellidos}</strong></span>
                    </div>
                  )}
                </div>
              </div>

              <div className="p-5 pt-0 flex gap-2">
                <button
                  id={`btn-ver-ficha-${m.id}`}
                  onClick={() => setDetailModalPet(m)}
                  className="flex-1 py-2 px-3 rounded-xl bg-[#1d95c8] hover:bg-[#156a8e] text-white text-xs font-bold transition-colors text-center shadow-xs"
                >
                  Ficha Médica
                </button>

                {(currentUser.tipo === 'veterinario' || currentUser.tipo === 'administrador') && (
                  <button
                    id={`btn-historial-pet-${m.id}`}
                    onClick={() => onOpenHistorialModalWithPet(m)}
                    className="py-2 px-3 rounded-xl bg-[#fff5e6] hover:bg-[#ffeed4] text-[#ff9f43] text-xs font-bold transition-colors flex items-center gap-1 border border-[#ff9f43]/30"
                    title="Registrar Consulta / Historial"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>+ Historial</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal Ficha Médica de Mascota */}
      {detailModalPet && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden my-8">
            <div className="relative h-48 bg-slate-900">
              <img 
                src={detailModalPet.imagen_url || "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=600&auto=format&fit=crop&q=80"} 
                alt={detailModalPet.nombre} 
                className="w-full h-full object-cover opacity-80"
              />
              <button 
                onClick={() => setDetailModalPet(null)}
                className="absolute top-4 right-4 bg-black/50 text-white hover:bg-black/80 p-1.5 rounded-full backdrop-blur-xs"
              >
                <X className="w-5 h-5" />
              </button>
              <div className="absolute bottom-4 left-4 text-white">
                <h3 className="text-2xl font-extrabold drop-shadow-md">{detailModalPet.nombre}</h3>
                <p className="text-xs text-slate-200 drop-shadow-md">{detailModalPet.especie_nombre} • {detailModalPet.raza}</p>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-slate-50 p-3 rounded-xl">
                  <span className="text-xs text-slate-400 font-medium">Edad:</span>
                  <p className="font-bold text-slate-900">{detailModalPet.edad_anos} años</p>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl">
                  <span className="text-xs text-slate-400 font-medium">Sexo:</span>
                  <p className="font-bold text-slate-900">{detailModalPet.sexo}</p>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl">
                  <span className="text-xs text-slate-400 font-medium">Peso Actual:</span>
                  <p className="font-bold text-slate-900">{detailModalPet.peso} kg</p>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl">
                  <span className="text-xs text-slate-400 font-medium">Esterilización:</span>
                  <p className="font-bold text-emerald-600">{detailModalPet.esta_esterilizado ? 'Esterilizado/a' : 'No esterilizado'}</p>
                </div>
              </div>

              {detailModalPet.descripcion && (
                <div className="text-xs text-slate-600 bg-amber-50/50 p-3 rounded-xl border border-amber-100">
                  <strong>Observaciones de la Mascota:</strong> {detailModalPet.descripcion}
                </div>
              )}

              {detailModalPet.tutor_nombre && (
                <div className="border-t border-slate-200 pt-3 text-xs text-slate-700">
                  <span className="font-bold block mb-1">Información del Tutor:</span>
                  <p>{detailModalPet.tutor_nombre} {detailModalPet.tutor_apellidos}</p>
                  <p className="text-slate-500">Tel: {detailModalPet.tutor_telefono || 'No registrado'} | {detailModalPet.tutor_email}</p>
                </div>
              )}

              <div className="flex justify-end pt-2">
                <button
                  onClick={() => setDetailModalPet(null)}
                  className="px-5 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800"
                >
                  Cerrar Ficha
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Registrar Mascota */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden my-8">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Dog className="w-5 h-5 text-amber-400" />
                <h3 className="font-bold text-lg">Registrar Nueva Mascota</h3>
              </div>
              <button 
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

              {/* Nombre y Especie */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Nombre (sin números) *
                  </label>
                  <input
                    type="text"
                    id="input-mascota-nombre"
                    placeholder="Ej: Max, Luna, Toby"
                    value={nombre}
                    onChange={(e) => setNombre(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Especie *
                  </label>
                  <select
                    id="select-mascota-especie"
                    value={especieId}
                    onChange={(e) => setEspecieId(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
                  >
                    {especies.map((esp) => (
                      <option key={esp.id} value={esp.id}>{esp.nombre}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Raza y Sexo */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Raza (Opcional)
                  </label>
                  <input
                    type="text"
                    id="input-mascota-raza"
                    placeholder="Ej: Labrador, Siamés, Mestizo"
                    value={raza}
                    onChange={(e) => setRaza(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Sexo *
                  </label>
                  <select
                    id="select-mascota-sexo"
                    value={sexo}
                    onChange={(e) => setSexo(e.target.value as 'Macho' | 'Hembra')}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
                  >
                    <option value="Macho">Macho</option>
                    <option value="Hembra">Hembra</option>
                  </select>
                </div>
              </div>

              {/* Edad, Peso y Color */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Edad (años) *
                  </label>
                  <input
                    type="number"
                    id="input-mascota-edad"
                    min="0"
                    max="30"
                    value={edadAnos}
                    onChange={(e) => setEdadAnos(parseInt(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Peso (kg) *
                  </label>
                  <input
                    type="number"
                    id="input-mascota-peso"
                    step="0.1"
                    min="0.1"
                    max="120"
                    value={peso}
                    onChange={(e) => setPeso(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Color *
                  </label>
                  <input
                    type="text"
                    id="input-mascota-color"
                    placeholder="Café, Blanco..."
                    value={color}
                    onChange={(e) => setColor(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    required
                  />
                </div>
              </div>

              {/* Checkbox Esterilizado */}
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="check-mascota-esterilizado"
                  checked={estaEsterilizado}
                  onChange={(e) => setEstaEsterilizado(e.target.checked)}
                  className="w-4 h-4 rounded text-amber-600 focus:ring-amber-500 border-slate-300"
                />
                <label htmlFor="check-mascota-esterilizado" className="text-xs font-medium text-slate-700 cursor-pointer">
                  Mascota esterilizada / castrada
                </label>
              </div>

              {/* URL Foto (Opcional) */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Foto de la Mascota (URL Opcional)
                </label>
                <input
                  type="url"
                  id="input-mascota-foto"
                  placeholder="https://images.unsplash.com/..."
                  value={imagenUrl}
                  onChange={(e) => setImagenUrl(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              {/* Descripción */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Notas sobre comportamiento o salud (Opcional)
                </label>
                <textarea
                  id="textarea-mascota-descripcion"
                  rows={2}
                  placeholder="Alergias conocidas, personalidad, hábitos..."
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
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
                  id="btn-submit-mascota"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-[#ff9f43] hover:bg-[#f08e30] text-white text-sm font-bold shadow-sm transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? 'Guardando...' : 'Registrar Paciente'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
