import React, { useEffect, useRef, useState } from 'react';
import { User } from '../types';
import { CLINICA } from '../clinica';
import {
  CalendarClock,
  ChevronDown,
  ClipboardList,
  Dog,
  HeartHandshake,
  Home,
  LayoutDashboard,
  LogIn,
  LogOut,
  Menu,
  Package,
  ShoppingBag,
  ShoppingCart,
  Stethoscope,
  X
} from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  /** null en la página pública: se muestra "Iniciar sesión" en vez del menú. */
  currentUser: User | null;
  onCerrarSesion?: () => void;
  onIniciarSesion?: () => void;
  cartCount: number;
  onOpenCart: () => void;
}

interface Seccion {
  id: string;
  nombre: string;
  Icono: React.ComponentType<{ className?: string }>;
}

// Lo que ve cualquiera, como el index del Django.
const PUBLICAS: Seccion[] = [
  { id: 'inicio', nombre: 'Inicio', Icono: Home },
  { id: 'adopciones', nombre: 'Adopciones', Icono: HeartHandshake },
  { id: 'tienda', nombre: 'Tienda', Icono: ShoppingBag }
];

// La barra de gestión, como las pestañas de los dashboards del Django.
function seccionesPrivadas(usuario: User | null): Seccion[] {
  const comunes: Seccion[] = [
    { id: 'dashboard', nombre: 'Panel', Icono: LayoutDashboard },
    { id: 'citas', nombre: 'Citas', Icono: Stethoscope },
    { id: 'mascotas', nombre: usuario?.tipo === 'cliente' ? 'Mis mascotas' : 'Mascotas', Icono: Dog },
    { id: 'historial', nombre: 'Historial', Icono: ClipboardList }
  ];
  if (!usuario || usuario.tipo === 'cliente') return comunes;
  return [
    ...comunes,
    { id: 'inventario', nombre: 'Inventario', Icono: Package },
    { id: 'servicios', nombre: 'Servicios', Icono: CalendarClock }
  ];
}

const ROL: Record<string, string> = {
  administrador: 'Administrador',
  veterinario: 'Veterinario',
  cliente: 'Cliente'
};

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  currentUser,
  onCerrarSesion,
  onIniciarSesion,
  cartCount,
  onOpenCart
}) => {
  const [menuCuenta, setMenuCuenta] = useState(false);
  const [menuMovil, setMenuMovil] = useState(false);
  const cuenta = useRef<HTMLDivElement>(null);
  const privadas = seccionesPrivadas(currentUser);

  // El menú de la cuenta se cierra al pulsar fuera o con Escape.
  useEffect(() => {
    if (!menuCuenta) return;
    const fuera = (e: MouseEvent) => {
      if (!cuenta.current?.contains(e.target as Node)) setMenuCuenta(false);
    };
    const escape = (e: KeyboardEvent) => e.key === 'Escape' && setMenuCuenta(false);
    document.addEventListener('mousedown', fuera);
    document.addEventListener('keydown', escape);
    return () => {
      document.removeEventListener('mousedown', fuera);
      document.removeEventListener('keydown', escape);
    };
  }, [menuCuenta]);

  const ir = (tab: string) => {
    setMenuMovil(false);
    setActiveTab(tab);
  };

  const enlacePublico = (s: Seccion) => (
    <button
      key={s.id}
      id={`nav-${s.id}`}
      onClick={() => ir(s.id)}
      aria-current={activeTab === s.id ? 'page' : undefined}
      className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
        activeTab === s.id ? 'bg-white/15 text-white' : 'text-white/80 hover:text-white hover:bg-white/10'
      }`}
    >
      {s.nombre}
    </button>
  );

  return (
    <header className="sticky top-0 z-40">
      {/* Barra principal (petróleo, como el navbar del Django al hacer scroll) */}
      <div className="bg-[#1d4f60] text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center gap-4">
          <button
            id="brand-logo"
            onClick={() => ir('inicio')}
            className="flex items-center gap-3 shrink-0 rounded-lg"
            aria-label={`${CLINICA.nombre}, ir al inicio`}
          >
            <img
              src="/img/logo.jpg"
              alt=""
              className="w-10 h-10 rounded-full border-2 border-white/80 object-cover bg-white"
              onError={(e) => ((e.currentTarget as HTMLElement).style.display = 'none')}
            />
            <span className="text-left leading-tight">
              <span className="block font-titulo text-lg font-bold">{CLINICA.nombre}</span>
              <span className="block text-[11px] text-[#9dddf5]">{CLINICA.lema}</span>
            </span>
          </button>

          <nav aria-label="Secciones públicas" className="hidden md:flex items-center gap-1 ml-4">
            {PUBLICAS.map(enlacePublico)}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <button
              id="btn-open-cart"
              onClick={onOpenCart}
              aria-label={`Carrito, ${cartCount} ${cartCount === 1 ? 'producto' : 'productos'}`}
              className="relative p-2 rounded-lg text-white/90 hover:text-white hover:bg-white/10"
            >
              <ShoppingCart className="w-5 h-5" />
              {cartCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] px-1 rounded-full bg-[#ff9f43] text-white text-[10px] font-bold flex items-center justify-center">
                  {cartCount}
                </span>
              )}
            </button>

            {!currentUser && (
              <button
                id="btn-iniciar-sesion"
                onClick={onIniciarSesion}
                aria-label="Iniciar sesión"
                className="mp-btn mp-btn--fantasma mp-btn--sm"
              >
                <LogIn className="w-4 h-4" />
                {/* En móvil sólo el icono: con el carrito y el menú no cabe el texto. */}
                <span className="hidden sm:inline">Iniciar sesión</span>
              </button>
            )}

            {currentUser && (
              <div className="relative" ref={cuenta}>
                <button
                  id="btn-user-role-menu"
                  onClick={() => setMenuCuenta((v) => !v)}
                  aria-expanded={menuCuenta}
                  aria-haspopup="menu"
                  className="flex items-center gap-2 pl-1.5 pr-2.5 py-1 rounded-full bg-white/10 hover:bg-white/15 border border-white/20"
                >
                  <span className="w-7 h-7 rounded-full bg-[#1d95c8] flex items-center justify-center text-xs font-bold">
                    {currentUser.nombre.charAt(0)}
                  </span>
                  <span className="text-left leading-tight hidden sm:block">
                    <span className="block text-sm font-semibold">{currentUser.nombre}</span>
                    <span className="block text-[11px] text-[#9dddf5]">{ROL[currentUser.tipo] ?? currentUser.tipo}</span>
                  </span>
                  <ChevronDown className="w-4 h-4 text-white/70" />
                </button>

                {menuCuenta && (
                  <div role="menu" className="absolute right-0 mt-2 w-64 mp-papel-blanco shadow-xl border border-slate-200 py-1.5 z-50 text-sm">
                    <div className="px-4 py-2.5 border-b border-slate-100">
                      <div className="font-semibold text-[#156a8e] truncate">
                        {currentUser.nombre} {currentUser.apellidos}
                      </div>
                      <div className="text-xs text-slate-500 truncate">{currentUser.email}</div>
                      <div className="text-xs text-slate-500 mt-0.5">{ROL[currentUser.tipo]}</div>
                    </div>
                    <button
                      role="menuitem"
                      id="btn-cerrar-sesion"
                      onClick={() => {
                        setMenuCuenta(false);
                        onCerrarSesion?.();
                      }}
                      className="w-full text-left px-4 py-2 flex items-center gap-2 text-[#b92b39] hover:bg-red-50 font-medium"
                    >
                      <LogOut className="w-4 h-4" />
                      Cerrar sesión
                    </button>
                  </div>
                )}
              </div>
            )}

            <button
              id="btn-menu-movil"
              onClick={() => setMenuMovil((v) => !v)}
              aria-expanded={menuMovil}
              aria-controls="menu-movil"
              aria-label={menuMovil ? 'Cerrar menú' : 'Abrir menú'}
              className="md:hidden p-2 rounded-lg hover:bg-white/10"
            >
              {menuMovil ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Menú móvil: todas las secciones en una lista */}
        {menuMovil && (
          <nav id="menu-movil" aria-label="Menú" className="md:hidden border-t border-white/10 px-4 py-3 space-y-3">
            <ul className="grid grid-cols-2 gap-1">
              {PUBLICAS.map((s) => (
                <li key={s.id}>
                  <button
                    id={`nav-movil-${s.id}`}
                    onClick={() => ir(s.id)}
                    aria-current={activeTab === s.id ? 'page' : undefined}
                    className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm ${activeTab === s.id ? 'bg-white/15 font-semibold' : 'hover:bg-white/10'}`}
                  >
                    <s.Icono className="w-4 h-4 text-[#9dddf5]" />
                    {s.nombre}
                  </button>
                </li>
              ))}
            </ul>
            <div className="border-t border-white/10 pt-3">
              <p className="px-3 pb-1 text-xs text-[#9dddf5]">{currentUser ? 'Gestión' : 'Con tu cuenta'}</p>
              <ul className="grid grid-cols-2 gap-1">
                {privadas.map((s) => (
                  <li key={s.id}>
                    <button
                      id={`nav-movil-${s.id}`}
                      onClick={() => ir(s.id)}
                      aria-current={activeTab === s.id ? 'page' : undefined}
                      className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm ${activeTab === s.id ? 'bg-white/15 font-semibold' : 'hover:bg-white/10'}`}
                    >
                      <s.Icono className="w-4 h-4 text-[#9dddf5]" />
                      {s.nombre}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </nav>
        )}
      </div>

      {/* Barra de gestión: las pestañas del dashboard del Django */}
      <div className="hidden md:block bg-[#1d95c8]">
        <nav aria-label="Gestión" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-3">
          <div className="mp-tabs">
            {privadas.map((s) => (
              <button
                key={s.id}
                id={`nav-${s.id}`}
                onClick={() => ir(s.id)}
                aria-current={activeTab === s.id ? 'page' : undefined}
                className="mp-tab"
              >
                <s.Icono className="w-4 h-4" />
                {s.nombre}
              </button>
            ))}
          </div>
        </nav>
      </div>
    </header>
  );
};
