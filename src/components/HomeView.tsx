import React from 'react';
import { Servicio, Mascota, Producto, DashboardStats } from '../types';
import { 
  Calendar, 
  Heart, 
  ShoppingBag, 
  Shield, 
  Clock, 
  Phone, 
  MapPin, 
  Award, 
  CheckCircle2, 
  ArrowRight,
  Sparkles,
  Stethoscope
} from 'lucide-react';

interface HomeViewProps {
  onNavigate: (tab: string, context?: any) => void;
  servicios: Servicio[];
  mascotasAdopcion: Mascota[];
  productos: Producto[];
  stats: DashboardStats | null;
  onAddToCart: (producto: Producto) => void;
}

export const HomeView: React.FC<HomeViewProps> = ({
  onNavigate,
  servicios,
  mascotasAdopcion,
  productos,
  stats,
  onAddToCart
}) => {
  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section (Legacy MundoPeludo Blue #1d95c8) */}
      <section className="relative overflow-hidden rounded-3xl bg-[#1d95c8] text-white shadow-xl">
        <div className="absolute inset-0 z-0 opacity-15 pointer-events-none">
          <div className="absolute top-0 right-0 w-96 h-96 bg-white/20 rounded-full blur-3xl" />
          <div className="absolute bottom-0 left-0 w-96 h-96 bg-[#1d4f60]/30 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10 max-w-7xl mx-auto px-6 py-12 sm:px-12 sm:py-16 grid lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-white/20 backdrop-blur-xs border border-white/30 text-white text-xs font-bold tracking-wide uppercase">
              <Sparkles className="w-3.5 h-3.5 text-[#ff9f43]" />
              <span>Te ayudamos a cuidar a tu mascota</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
              Bienvenido a <span className="text-[#fff5e6] drop-shadow-sm">Mundo Peludo</span>
            </h1>

            <p className="text-base sm:text-lg text-sky-100 max-w-2xl leading-relaxed">
              Tu clínica veterinaria de confianza. Ofrecemos atención médica personalizada,
              quirófano equipado, agenda digital de citas, adopciones responsables y farmacia completa.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                id="btn-hero-agendar"
                onClick={() => onNavigate('citas')}
                className="px-6 py-3.5 rounded-xl bg-[#ff9f43] hover:bg-[#f08e30] text-white font-bold text-sm sm:text-base shadow-lg shadow-black/10 transition-all flex items-center gap-2 hover:scale-[1.02] active:scale-95"
              >
                <Calendar className="w-5 h-5 text-white" />
                <span>Agendar Cita Médica</span>
              </button>

              <button
                id="btn-hero-servicios"
                onClick={() => onNavigate('citas')}
                className="px-6 py-3.5 rounded-xl bg-white text-[#156a8e] hover:bg-sky-50 font-bold text-sm sm:text-base shadow-sm transition-all flex items-center gap-2"
              >
                <Stethoscope className="w-5 h-5 text-[#1d95c8]" />
                <span>Nuestros Servicios</span>
              </button>

              <button
                id="btn-hero-adopciones"
                onClick={() => onNavigate('adopciones')}
                className="px-6 py-3.5 rounded-xl bg-white/15 hover:bg-white/25 text-white font-semibold text-sm sm:text-base backdrop-blur-xs border border-white/20 transition-all flex items-center gap-2"
              >
                <Heart className="w-5 h-5 text-pink-200" />
                <span>Adopciones</span>
              </button>
            </div>
          </div>

          <div className="lg:col-span-5 flex justify-center">
            <div className="relative">
              <div className="w-64 h-64 sm:w-80 sm:h-80 rounded-3xl bg-white/10 p-4 backdrop-blur-xs border border-white/20 shadow-2xl flex items-center justify-center">
                <img 
                  src="/img/logo.jpg" 
                  alt="Mundo Peludo Clínica" 
                  className="w-full h-full object-cover rounded-2xl shadow-md"
                  onError={(e) => {
                    // Fallback to cat or pet image if needed
                    (e.currentTarget as HTMLImageElement).src = '/img/cuidado-mascota.jpg';
                  }}
                />
              </div>
              <div className="absolute -bottom-4 -right-4 bg-white text-[#156a8e] px-4 py-2 rounded-2xl shadow-xl border border-sky-100 flex items-center gap-2 font-bold text-xs sm:text-sm">
                <span className="w-3 h-3 rounded-full bg-[#5dca88] animate-ping" />
                <span>Atención y Emergencias 24/7</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Sección: Cuidado Profesional para tu Mascota (From Legacy index.html) */}
      <section className="bg-white rounded-3xl p-8 sm:p-12 border border-sky-100 shadow-sm">
        <div className="grid lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-6">
            <img 
              src="/img/cuidado-mascota.jpg" 
              alt="Cuidado profesional veterinario" 
              className="w-full h-80 sm:h-96 object-cover rounded-2xl shadow-md border-4 border-[#e2f5fc]"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).src = 'https://images.unsplash.com/photo-1576201836106-db1758fd1c97?w=800&auto=format&fit=crop&q=80';
              }}
            />
          </div>

          <div className="lg:col-span-6 space-y-6">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#ff9f43]">Atención Especializada</span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-[#156a8e] mt-1">
                Cuidado Profesional para tu Mascota
              </h2>
              <p className="text-slate-600 mt-2 text-base leading-relaxed">
                Entendemos que tu mascota es parte esencial de tu familia. Por eso brindamos atención
                veterinaria de la más alta calidad con calidez humana y tecnología de punta.
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="w-11 h-11 rounded-xl bg-[#1d95c8] text-white flex items-center justify-center shrink-0 shadow-sm shadow-[#1d95c8]/30">
                  <Award className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-800 text-base">Atención Personalizada</h3>
                  <p className="text-sm text-slate-600">Cada paciente recibe un diagnóstico y tratamiento adaptado a su edad y especie.</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-11 h-11 rounded-xl bg-[#1d95c8] text-white flex items-center justify-center shrink-0 shadow-sm shadow-[#1d95c8]/30">
                  <Stethoscope className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-800 text-base">Equipo Médico Calificado</h3>
                  <p className="text-sm text-slate-600">Profesionales certificados con amplia trayectoria en cirugías y medicina interna.</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="w-11 h-11 rounded-xl bg-[#5dca88] text-white flex items-center justify-center shrink-0 shadow-sm shadow-[#5dca88]/30">
                  <Heart className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-800 text-base">Amor por los Animales</h3>
                  <p className="text-sm text-slate-600">Nos apasiona el bienestar animal y se nota en la dedicación de cada consulta.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Sección: Nuestro Impacto (From Legacy index.html) */}
      <section className="bg-[#f7fbfe] rounded-3xl p-8 sm:p-12 border border-[#9dddf5]/50 shadow-sm">
        <div className="grid lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-7 space-y-6">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-[#1d95c8]">Confianza Comprobada</span>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-[#156a8e] mt-1">
                Nuestro Impacto
              </h2>
              <p className="text-slate-600 mt-2 text-base leading-relaxed">
                Nuestra pasión por los animales se traduce en resultados y sonrisas de familias satisfechas.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white p-5 rounded-2xl border-t-4 border-[#1d95c8] shadow-xs text-center">
                <div className="text-3xl sm:text-4xl font-extrabold text-[#1d95c8] mb-1">
                  {stats ? stats.total_mascotas + 1000 : '1000'}+
                </div>
                <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Mascotas Atendidas</p>
              </div>

              <div className="bg-white p-5 rounded-2xl border-t-4 border-[#ff9f43] shadow-xs text-center">
                <div className="text-3xl sm:text-4xl font-extrabold text-[#ff9f43] mb-1">98%</div>
                <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Clientes Satisfechos</p>
              </div>

              <div className="bg-white p-5 rounded-2xl border-t-4 border-[#5dca88] shadow-xs text-center">
                <div className="text-3xl sm:text-4xl font-extrabold text-[#5dca88] mb-1">24/7</div>
                <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Urgencias Médicas</p>
              </div>

              <div className="bg-white p-5 rounded-2xl border-t-4 border-[#1d4f60] shadow-xs text-center">
                <div className="text-3xl sm:text-4xl font-extrabold text-[#1d4f60] mb-1">5+</div>
                <p className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Años de Experiencia</p>
              </div>
            </div>
          </div>

          <div className="lg:col-span-5 flex justify-center">
            <img 
              src="/img/gato.jpg" 
              alt="Mascota feliz en Mundo Peludo" 
              className="w-full max-w-sm h-80 object-cover rounded-2xl shadow-lg border-4 border-white"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).src = 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=800&auto=format&fit=crop&q=80';
              }}
            />
          </div>
        </div>
      </section>

      {/* Servicios Médicos Destacados */}
      <section className="space-y-6">
        <div className="flex items-end justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#1d95c8]">Servicios Médicos</span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#156a8e]">Especialidades de Nuestra Clínica</h2>
          </div>
          <button
            onClick={() => onNavigate('citas')}
            className="text-sm font-bold text-[#1d95c8] hover:text-[#156a8e] flex items-center gap-1 group"
          >
            <span>Ver todos los servicios</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {servicios.map((s) => (
            <div 
              key={s.id} 
              className="card-mundo p-6 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-[#e2f5fc] text-[#156a8e]">
                    ⏱️ {s.duracion_min} minutos
                  </span>
                  <span className="text-base font-extrabold text-[#ff9f43]">
                    ${s.precio.toLocaleString('es-CL')}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-800 mb-2">{s.nombre}</h3>
                <p className="text-sm text-slate-600 leading-relaxed mb-4">{s.descripcion}</p>
              </div>

              <button
                id={`btn-servicio-agendar-${s.id}`}
                onClick={() => onNavigate('citas', { servicioId: s.id })}
                className="w-full py-2.5 px-4 rounded-xl bg-[#1d95c8] hover:bg-[#156a8e] text-white text-xs font-bold transition-colors flex items-center justify-center gap-1.5 shadow-sm active:scale-95"
              >
                <Calendar className="w-3.5 h-3.5" />
                <span>Agendar este servicio</span>
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Adopción Urgente Banner */}
      {mascotasAdopcion.length > 0 && (
        <section className="bg-gradient-to-r from-[#1d95c8] via-[#156a8e] to-[#1d4f60] rounded-3xl p-8 sm:p-10 text-white shadow-lg flex flex-col lg:flex-row items-center justify-between gap-8">
          <div className="max-w-xl space-y-3">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#5dca88] text-white text-xs font-bold uppercase tracking-wider">
              <Heart className="w-3.5 h-3.5 text-white" />
              <span>Adopta con Amor</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              {mascotasAdopcion[0].nombre} busca una familia que lo llene de amor
            </h2>
            <p className="text-sky-100 text-sm sm:text-base leading-relaxed">
              {mascotasAdopcion[0].descripcion}
            </p>
            <div className="pt-2 flex flex-wrap gap-4">
              <button
                id="btn-adoptar-banner"
                onClick={() => onNavigate('adopciones')}
                className="px-6 py-3 rounded-xl bg-[#ff9f43] hover:bg-[#f08e30] text-white font-bold text-sm shadow-md transition-all active:scale-95"
              >
                Conocer a {mascotasAdopcion[0].nombre} y otros
              </button>
            </div>
          </div>

          <div className="w-48 h-48 sm:w-64 sm:h-64 rounded-2xl overflow-hidden shadow-2xl border-4 border-white/40 shrink-0 bg-white">
            <img 
              src={mascotasAdopcion[0].imagen_url} 
              alt={mascotasAdopcion[0].nombre} 
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.currentTarget as HTMLImageElement).src = '/img/default-pet.jpg';
              }}
            />
          </div>
        </section>
      )}

      {/* Tienda & Farmacia Highlights */}
      <section className="space-y-6">
        <div className="flex items-end justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#1d95c8]">Farmacia y Nutrición</span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#156a8e]">Productos Populares en la Tienda</h2>
          </div>
          <button
            onClick={() => onNavigate('tienda')}
            className="text-sm font-bold text-[#1d95c8] hover:text-[#156a8e] flex items-center gap-1 group"
          >
            <span>Ir a la tienda</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>

        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-6">
          {productos.slice(0, 4).map((p) => (
            <div 
              key={p.id}
              className="card-mundo p-4 flex flex-col justify-between"
            >
              <div>
                <div className="w-full h-44 rounded-xl overflow-hidden bg-slate-100 mb-3 relative">
                  <img 
                    src={p.imagen_url} 
                    alt={p.nombre} 
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.currentTarget as HTMLImageElement).src = '/img/producto-default.jpg';
                    }}
                  />
                  {p.descuento_porcentaje > 0 && (
                    <span className="absolute top-2 left-2 bg-[#ff9f43] text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-xs">
                      -{p.descuento_porcentaje}% OFF
                    </span>
                  )}
                </div>

                <div className="text-[11px] font-bold text-[#1d95c8] uppercase tracking-wider mb-1">
                  {p.marca || p.categoria}
                </div>
                <h4 className="text-sm font-bold text-slate-800 line-clamp-2 mb-2">{p.nombre}</h4>
              </div>

              <div>
                <div className="flex items-baseline gap-2 mb-3">
                  <span className="text-base font-extrabold text-[#1d4f60]">
                    ${p.precio_final.toLocaleString('es-CL')}
                  </span>
                  {p.descuento_porcentaje > 0 && (
                    <span className="text-xs text-slate-400 line-through">
                      ${p.precio.toLocaleString('es-CL')}
                    </span>
                  )}
                </div>

                <button
                  id={`btn-add-cart-home-${p.id}`}
                  onClick={() => onAddToCart(p)}
                  className="w-full py-2 px-3 rounded-xl bg-[#ff9f43] hover:bg-[#f08e30] text-white text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-sm active:scale-95"
                >
                  <ShoppingBag className="w-3.5 h-3.5" />
                  <span>Añadir al Carrito</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Info & Contact Cards (Legacy details) */}
      <section className="bg-white rounded-3xl p-8 sm:p-12 border border-[#9dddf5]/60 shadow-sm">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-[#e2f5fc] text-[#1d95c8] shadow-xs flex items-center justify-center shrink-0">
              <MapPin className="w-6 h-6" />
            </div>
            <div>
              <h4 className="font-bold text-[#156a8e] mb-1">Ubicación</h4>
              <p className="text-sm text-slate-600">Bello, Antioquia, Colombia</p>
              <p className="text-xs text-slate-400 mt-1">Sede principal Mundo Peludo</p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-[#e2f5fc] text-[#5dca88] shadow-xs flex items-center justify-center shrink-0">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <h4 className="font-bold text-[#156a8e] mb-1">Horarios de Atención</h4>
              <p className="text-sm text-slate-600">Lunes a Sábado: 08:00 - 20:00</p>
              <p className="text-xs text-[#5dca88] font-bold mt-1">Urgencias Médicas: 24 Horas</p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-[#fff5e6] text-[#ff9f43] shadow-xs flex items-center justify-center shrink-0">
              <Phone className="w-6 h-6" />
            </div>
            <div>
              <h4 className="font-bold text-[#156a8e] mb-1">Contacto</h4>
              <p className="text-sm text-slate-600">WhatsApp: +57 3243806941</p>
              <p className="text-xs text-slate-500 mt-1">andres_ramirez23232@elpoli.edu.co</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
