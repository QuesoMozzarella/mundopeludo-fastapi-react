import React from 'react';
import { Servicio, Mascota, Producto, DashboardStats } from '../types';
import { CLINICA, enlaceTelefono, hayContacto } from '../clinica';
import { formatearPrecio } from '../formato';
import { FotoMascota, ImagenProducto, useInterfaz } from './ui';
import { CalendarPlus, Clock, HeartHandshake, Mail, MapPin, Phone, Plus, ShoppingBag, Siren, Stethoscope } from 'lucide-react';

interface HomeViewProps {
  onNavigate: (tab: string, context?: any) => void;
  servicios: Servicio[];
  mascotasAdopcion: Mascota[];
  productos: Producto[];
  stats: DashboardStats | null;
  onAddToCart: (producto: Producto) => void;
}

// Fotos de servicio que traía el proyecto Django (public/img).
function fotoServicio(nombre: string): string | null {
  const n = nombre.toLowerCase();
  if (n.includes('consulta')) return '/img/servicio-general.jpg';
  if (n.includes('vacun')) return '/img/servicio-vacunacion.jpg';
  if (n.includes('cirug')) return '/img/servicio-cirugua.jpg';
  if (n.includes('peluq') || n.includes('estétic') || n.includes('baño')) return '/img/servicio-peluqueria.jpg';
  return null;
}

function Seccion({ id, titulo, texto, accion, children }: {
  id?: string;
  titulo: string;
  texto?: string;
  accion?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="space-y-5 scroll-mt-28">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div className="space-y-1">
          <h2 className="font-titulo text-2xl sm:text-3xl font-semibold">{titulo}</h2>
          {texto && <p className="mp-descripcion">{texto}</p>}
        </div>
        {accion}
      </div>
      {children}
    </section>
  );
}

export const HomeView: React.FC<HomeViewProps> = ({ onNavigate, servicios, mascotasAdopcion, productos, onAddToCart }) => {
  const { avisar } = useInterfaz();
  const destacados = productos.filter((p) => p.stock > 0).slice(0, 4);
  const telefono = enlaceTelefono();

  const verServicios = () => document.getElementById('servicios')?.scrollIntoView({ behavior: 'smooth' });

  return (
    <div className="space-y-16 pb-8">
      {/* Portada: el logo del Django sobre el azul de la clínica */}
      <section className="grid lg:grid-cols-12 gap-10 items-center pt-4">
        <div className="lg:col-span-7 space-y-6">
          <h1 className="font-titulo text-4xl sm:text-6xl font-bold leading-[1.05]">Bienvenido a {CLINICA.nombre}</h1>
          <p className="text-lg text-white/85 max-w-xl leading-relaxed">
            Consultas, vacunación y cirugía para tu mascota. Pide la cita en línea con las horas libres de cada
            veterinario, adopta a un rescatado o compra su alimento y sus medicamentos.
          </p>
          <div className="flex flex-wrap gap-3">
            <button id="btn-hero-agendar" onClick={() => onNavigate('citas')} className="mp-btn mp-btn--primario text-base px-6 py-3">
              <CalendarPlus className="w-5 h-5" />
              Pedir una cita
            </button>
            <button id="btn-hero-servicios" onClick={verServicios} className="mp-btn mp-btn--fantasma text-base px-6 py-3">
              <Stethoscope className="w-5 h-5" />
              Ver servicios y precios
            </button>
          </div>
        </div>
        <div className="lg:col-span-5 flex justify-center">
          <div className="w-64 h-64 sm:w-80 sm:h-80 rounded-full bg-white p-5 shadow-[0_20px_50px_rgba(29,79,96,0.35)] ring-8 ring-white/15">
            <img src="/img/logo.jpg" alt={`Logo de ${CLINICA.nombre}`} className="w-full h-full object-contain rounded-full" />
          </div>
        </div>
      </section>

      {/* Servicios reales de la API */}
      {servicios.length > 0 && (
        <Seccion id="servicios" titulo="Servicios" texto="Duración y precio de cada consulta. Al pedir la cita te mostramos las horas libres.">
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {servicios.map((s) => {
              const foto = fotoServicio(s.nombre);
              return (
                <article key={s.id} className="mp-papel-blanco overflow-hidden flex flex-col">
                  {foto ? (
                    <img src={foto} alt="" className="w-full h-36 object-cover" />
                  ) : (
                    <div className="w-full h-36 bg-[#156a8e] flex items-center justify-center">
                      <Stethoscope className="w-12 h-12 text-[#9dddf5]" />
                    </div>
                  )}
                  <div className="p-5 flex-1 flex flex-col gap-2">
                    <h3 className="font-titulo text-lg font-semibold text-[#1d4f60]">{s.nombre}</h3>
                    {s.descripcion && <p className="text-sm text-slate-600">{s.descripcion}</p>}
                    <p className="mt-auto pt-2 flex items-center justify-between text-sm">
                      <span className="flex items-center gap-1.5 text-slate-500">
                        <Clock className="w-4 h-4" />
                        {s.duracion_min} min
                      </span>
                      {s.precio != null && <span className="font-bold text-[#2c3e50]">{formatearPrecio(s.precio)}</span>}
                    </p>
                    <button
                      id={`btn-servicio-agendar-${s.id}`}
                      onClick={() => onNavigate('citas', { servicioId: s.id })}
                      className="mp-btn mp-btn--azul mp-btn--sm mt-2"
                    >
                      Pedir esta cita
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </Seccion>
      )}

      {/* Adopción: mascotas reales en adopción */}
      {mascotasAdopcion.length > 0 && (
        <section className="mp-panel p-6 sm:p-8 grid lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-4 space-y-4">
            <h2 className="font-titulo text-2xl sm:text-3xl font-semibold">
              {mascotasAdopcion.length === 1
                ? `${mascotasAdopcion[0].nombre} busca familia`
                : `${mascotasAdopcion.length} mascotas buscan familia`}
            </h2>
            <p className="text-white/85">Rescatadas por la clínica y listas para un hogar. Postula y el equipo revisará tu solicitud.</p>
            <button id="btn-adoptar-banner" onClick={() => onNavigate('adopciones')} className="mp-btn mp-btn--claro">
              <HeartHandshake className="w-4 h-4" />
              Conocerlas
            </button>
          </div>
          <ul className="lg:col-span-8 grid grid-cols-2 sm:grid-cols-3 gap-4">
            {mascotasAdopcion.slice(0, 3).map((m) => (
              <li key={m.id}>
                <button onClick={() => onNavigate('adopciones')} className="w-full text-left rounded-xl bg-white/10 hover:bg-white/15 border border-white/15 p-2.5 group">
                  <FotoMascota nombre={m.nombre} imagen={m.imagen_url} especie={m.especie_nombre} className="w-full aspect-[4/3] rounded-lg" tamanoIcono="w-1/3 h-1/3" />
                  <span className="block mt-2 px-1 font-semibold group-hover:underline underline-offset-2">{m.nombre}</span>
                  <span className="block px-1 pb-1 text-sm text-white/75">{m.especie_nombre}, {m.edad_anos} {m.edad_anos === 1 ? 'año' : 'años'}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Tienda */}
      {destacados.length > 0 && (
        <Seccion
          titulo="De la farmacia y la tienda"
          texto="Alimentos, antiparasitarios y medicamentos con stock en la clínica."
          accion={
            <button onClick={() => onNavigate('tienda')} className="mp-btn mp-btn--fantasma mp-btn--sm self-start sm:self-auto">
              <ShoppingBag className="w-4 h-4" />
              Ver toda la tienda
            </button>
          }
        >
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {destacados.map((p) => (
              <article key={p.id} className="mp-papel-blanco overflow-hidden flex flex-col">
                <ImagenProducto nombre={p.nombre} imagen={p.imagen_url} categoria={p.categoria} className="w-full h-32 sm:h-40" tamanoIcono="w-12 h-12" />
                <div className="p-4 flex-1 flex flex-col gap-2">
                  <h3 className="text-sm sm:text-base font-semibold text-[#1d4f60] leading-snug">{p.nombre}</h3>
                  <p className="mt-auto flex items-baseline gap-2">
                    <span className="font-bold text-[#2c3e50]">{formatearPrecio(p.precio_final)}</span>
                    {p.descuento_porcentaje > 0 && <span className="text-xs text-slate-400 line-through">{formatearPrecio(p.precio)}</span>}
                  </p>
                  <button
                    id={`btn-add-cart-home-${p.id}`}
                    onClick={() => {
                      onAddToCart(p);
                      avisar(`${p.nombre} añadido al carrito.`);
                    }}
                    className="mp-btn mp-btn--primario mp-btn--sm"
                  >
                    <Plus className="w-4 h-4" />
                    Añadir al carrito
                  </button>
                </div>
              </article>
            ))}
          </div>
        </Seccion>
      )}

      {/* Contacto: sólo lo que esté rellenado en src/clinica.ts */}
      {hayContacto && (
        <section className="mp-panel grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {CLINICA.direccion && (
            <div className="flex gap-3"><MapPin className="w-5 h-5 text-[#9dddf5] shrink-0" /><div><h2 className="font-semibold">Dónde estamos</h2><p className="text-sm text-white/80">{CLINICA.direccion}</p></div></div>
          )}
          {CLINICA.horario && (
            <div className="flex gap-3"><Clock className="w-5 h-5 text-[#9dddf5] shrink-0" /><div><h2 className="font-semibold">Horario</h2><p className="text-sm text-white/80">{CLINICA.horario}</p></div></div>
          )}
          {(CLINICA.telefono || CLINICA.correo) && (
            <div className="flex gap-3">
              {CLINICA.telefono ? <Phone className="w-5 h-5 text-[#9dddf5] shrink-0" /> : <Mail className="w-5 h-5 text-[#9dddf5] shrink-0" />}
              <div>
                <h2 className="font-semibold">Contacto</h2>
                {CLINICA.telefono && <a href={telefono!} className="block text-sm text-white/80 hover:text-white underline-offset-2 hover:underline">{CLINICA.telefono}</a>}
                {CLINICA.correo && <a href={`mailto:${CLINICA.correo}`} className="block text-sm text-white/80 hover:text-white underline-offset-2 hover:underline">{CLINICA.correo}</a>}
              </div>
            </div>
          )}
          {CLINICA.urgencias && (
            <div className="flex gap-3"><Siren className="w-5 h-5 text-[#ff9f43] shrink-0" /><div><h2 className="font-semibold">Urgencias</h2><p className="text-sm text-white/80">{CLINICA.urgencias}</p></div></div>
          )}
        </section>
      )}
    </div>
  );
};
