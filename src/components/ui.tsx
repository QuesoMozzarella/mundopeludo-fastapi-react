import React, { createContext, useCallback, useContext, useEffect, useId, useRef, useState } from 'react';
import {
  AlertCircle,
  Bird,
  Bone,
  Bug,
  Cat,
  CheckCircle2,
  Dog,
  Fish,
  Info,
  Package,
  PawPrint,
  Pill,
  Rabbit,
  ShoppingBag,
  Sparkles,
  ToyBrick,
  Turtle,
  X
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Encabezado de página: título blanco sobre el lienzo azul y sus acciones.
// ---------------------------------------------------------------------------
export function Encabezado({
  titulo,
  descripcion,
  children
}: {
  titulo: string;
  descripcion?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
      <div className="space-y-1.5">
        <h1 className="mp-titulo">{titulo}</h1>
        {descripcion && <p className="mp-descripcion">{descripcion}</p>}
      </div>
      {children && <div className="flex flex-wrap gap-2 shrink-0">{children}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Modal accesible: Escape y el botón cierran, el foco entra y vuelve.
// ---------------------------------------------------------------------------
const ANCHOS = { sm: 'max-w-md', md: 'max-w-lg', lg: 'max-w-2xl' } as const;

export function Modal({
  titulo,
  icono,
  onCerrar,
  children,
  ancho = 'md',
  idCerrar
}: {
  titulo: string;
  icono?: React.ReactNode;
  onCerrar: () => void;
  children: React.ReactNode;
  ancho?: keyof typeof ANCHOS;
  /** id del botón de cerrar, para las pruebas. */
  idCerrar?: string;
}) {
  const idTitulo = useId();
  const caja = useRef<HTMLDivElement>(null);
  const alCerrar = useRef(onCerrar);
  alCerrar.current = onCerrar;

  useEffect(() => {
    const previo = document.activeElement as HTMLElement | null;
    const primero = caja.current?.querySelector<HTMLElement>(
      'input:not([type="hidden"]):not([disabled]), select:not([disabled]), textarea:not([disabled])'
    );
    (primero ?? caja.current)?.focus();
    const alTeclear = (e: KeyboardEvent) => {
      if (e.key === 'Escape') alCerrar.current();
    };
    document.addEventListener('keydown', alTeclear);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', alTeclear);
      document.body.style.overflow = '';
      previo?.focus?.();
    };
  }, []);

  return (
    <div
      className="mp-modal-fondo"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onCerrar();
      }}
    >
      <div
        ref={caja}
        role="dialog"
        aria-modal="true"
        aria-labelledby={idTitulo}
        tabIndex={-1}
        className={`mp-modal ${ANCHOS[ancho]}`}
      >
        <div className="mp-modal-cabecera">
          <div className="flex items-center gap-2 min-w-0">
            {icono}
            <h2 id={idTitulo} className="truncate">{titulo}</h2>
          </div>
          <button
            type="button"
            id={idCerrar}
            onClick={onCerrar}
            aria-label="Cerrar"
            className="p-1 rounded-lg text-white/70 hover:text-white hover:bg-white/10"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

/** Pie de un formulario dentro de un modal: acciones a la derecha. */
export function PieModal({ children }: { children: React.ReactNode }) {
  return <div className="flex items-center justify-end gap-3 pt-4 mt-2 border-t border-slate-200">{children}</div>;
}

// ---------------------------------------------------------------------------
// Avisos y confirmaciones propias (en lugar de alert() y confirm()).
// ---------------------------------------------------------------------------
type TipoAviso = 'exito' | 'error' | 'info';
interface Aviso {
  id: number;
  tipo: TipoAviso;
  texto: string;
}
interface PeticionConfirmar {
  titulo: string;
  mensaje: string;
  confirmar: string;
  peligro?: boolean;
  resolver: (ok: boolean) => void;
}

interface Interfaz {
  avisar: (texto: string, tipo?: TipoAviso) => void;
  confirmar: (opciones: { titulo: string; mensaje: string; confirmar: string; peligro?: boolean }) => Promise<boolean>;
}

const ContextoInterfaz = createContext<Interfaz | null>(null);

export function useInterfaz(): Interfaz {
  const ctx = useContext(ContextoInterfaz);
  if (!ctx) throw new Error('useInterfaz fuera de <InterfazProvider>');
  return ctx;
}

const ICONO_AVISO = { exito: CheckCircle2, error: AlertCircle, info: Info };

export function InterfazProvider({ children }: { children: React.ReactNode }) {
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const [pregunta, setPregunta] = useState<PeticionConfirmar | null>(null);
  const siguiente = useRef(1);

  const avisar = useCallback((texto: string, tipo: TipoAviso = 'exito') => {
    const id = siguiente.current++;
    setAvisos((lista) => [...lista, { id, tipo, texto }]);
    window.setTimeout(() => setAvisos((lista) => lista.filter((a) => a.id !== id)), tipo === 'error' ? 8000 : 4500);
  }, []);

  const confirmar = useCallback<Interfaz['confirmar']>(
    (opciones) => new Promise((resolver) => setPregunta({ ...opciones, resolver })),
    []
  );

  const responder = (ok: boolean) => {
    pregunta?.resolver(ok);
    setPregunta(null);
  };

  return (
    <ContextoInterfaz.Provider value={{ avisar, confirmar }}>
      {children}

      <div aria-live="polite" className="fixed bottom-4 right-4 left-4 sm:left-auto z-[60] flex flex-col gap-2 sm:w-96">
        {avisos.map((a) => {
          const Icono = ICONO_AVISO[a.tipo];
          return (
            <div key={a.id} role={a.tipo === 'error' ? 'alert' : 'status'} className={`mp-aviso mp-aviso--${a.tipo} shadow-lg`}>
              <Icono className="w-4 h-4 shrink-0 mt-0.5" />
              <span className="flex-1">{a.texto}</span>
              <button
                type="button"
                aria-label="Cerrar aviso"
                onClick={() => setAvisos((lista) => lista.filter((x) => x.id !== a.id))}
                className="opacity-60 hover:opacity-100"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>

      {pregunta && (
        <Modal titulo={pregunta.titulo} ancho="sm" onCerrar={() => responder(false)}>
          <div className="p-6 space-y-2">
            <p className="text-sm text-slate-700">{pregunta.mensaje}</p>
            <PieModal>
              <button type="button" className="mp-btn mp-btn--borde" onClick={() => responder(false)}>
                Cancelar
              </button>
              <button
                type="button"
                id="btn-confirmar-dialogo"
                className={`mp-btn ${pregunta.peligro ? 'mp-btn--peligro' : 'mp-btn--azul'}`}
                onClick={() => responder(true)}
              >
                {pregunta.confirmar}
              </button>
            </PieModal>
          </div>
        </Modal>
      )}
    </ContextoInterfaz.Provider>
  );
}

/** Mensaje de error dentro de un formulario. */
export function ErrorFormulario({ texto }: { texto: string | null }) {
  if (!texto) return null;
  return (
    <div role="alert" className="mp-aviso mp-aviso--error">
      <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
      <span>{texto}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Estados.
// ---------------------------------------------------------------------------
const PILL_CITA: Record<string, string> = {
  Pendiente: 'mp-pill--pendiente',
  Confirmada: 'mp-pill--exito',
  Completada: 'mp-pill--info',
  Cancelada: 'mp-pill--peligro'
};

export function EstadoCita({ estado }: { estado: string }) {
  return <span className={`mp-pill ${PILL_CITA[estado] ?? 'mp-pill--neutro'}`}>{estado}</span>;
}

/** Pantalla vacía: dice qué falta y, si se puede, cómo empezar. */
export function Vacio({
  icono: Icono,
  titulo,
  texto,
  children
}: {
  icono: React.ComponentType<{ className?: string }>;
  titulo: string;
  texto?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="mp-panel text-center py-12 px-6">
      <Icono className="w-10 h-10 mx-auto mb-3 text-[#9dddf5]" />
      <h2 className="text-lg font-semibold">{titulo}</h2>
      {texto && <p className="text-sm text-white/80 mt-1 max-w-md mx-auto">{texto}</p>}
      {children && <div className="mt-5 flex justify-center">{children}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Imágenes: la foto real o una ilustración de la especie / categoría. Nunca
// una foto de otro animal.
// ---------------------------------------------------------------------------
function iconoEspecie(especie?: string) {
  const e = (especie || '').toLowerCase();
  if (e.includes('perro') || e.includes('canino')) return { Icono: Dog, fondo: '#1d4f60' };
  if (e.includes('gato') || e.includes('felino')) return { Icono: Cat, fondo: '#1d4f60' };
  if (e.includes('ave') || e.includes('pájaro') || e.includes('pajaro')) return { Icono: Bird, fondo: '#0f7f9c' };
  if (e.includes('roedor') || e.includes('conejo')) return { Icono: Rabbit, fondo: '#2a6f86' };
  if (e.includes('reptil') || e.includes('tortuga')) return { Icono: Turtle, fondo: '#256a5a' };
  if (e.includes('pez')) return { Icono: Fish, fondo: '#12708f' };
  return { Icono: PawPrint, fondo: '#156a8e' };
}

export function FotoMascota({
  nombre,
  imagen,
  especie,
  className = '',
  tamanoIcono = 'w-1/3 h-1/3'
}: {
  nombre: string;
  imagen?: string | null;
  especie?: string;
  className?: string;
  tamanoIcono?: string;
}) {
  const [fallo, setFallo] = useState(false);
  if (imagen && !fallo) {
    return <img src={imagen} alt={nombre} className={`object-cover ${className}`} onError={() => setFallo(true)} />;
  }
  const { Icono, fondo } = iconoEspecie(especie);
  return (
    <div role="img" aria-label={nombre} className={`flex items-center justify-center ${className}`} style={{ backgroundColor: fondo }}>
      <Icono className={`${tamanoIcono} text-[#9dddf5]`} />
    </div>
  );
}

const ICONO_CATEGORIA: Record<string, React.ComponentType<{ className?: string }>> = {
  medicamento: Pill,
  suplemento: Pill,
  alimento: Bone,
  accesorio: ShoppingBag,
  juguete: ToyBrick,
  higiene: Sparkles,
  antipulgas: Bug,
  desparasitante: Pill
};

export function ImagenProducto({
  nombre,
  imagen,
  categoria,
  className = '',
  tamanoIcono = 'w-1/3 h-1/3'
}: {
  nombre: string;
  imagen?: string | null;
  categoria?: string;
  className?: string;
  tamanoIcono?: string;
}) {
  const [fallo, setFallo] = useState(false);
  if (imagen && !fallo) {
    return <img src={imagen} alt={nombre} className={`object-cover ${className}`} onError={() => setFallo(true)} />;
  }
  const Icono = ICONO_CATEGORIA[(categoria || '').toLowerCase()] ?? Package;
  return (
    <div role="img" aria-label={nombre} className={`flex items-center justify-center bg-[#e8f6fc] ${className}`}>
      <Icono className={`${tamanoIcono} text-[#1d95c8]`} />
    </div>
  );
}
