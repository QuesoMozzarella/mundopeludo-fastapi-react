import React from 'react';
import { User } from '../types';
import { 
  HeartHandshake, 
  Calendar, 
  Dog, 
  ShoppingBag, 
  ClipboardList, 
  Package, 
  ShieldCheck, 
  Stethoscope, 
  UserCheck, 
  ShoppingCart,
  ChevronDown,
  LogIn,
  LogOut,
  CalendarClock
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

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  currentUser,
  onCerrarSesion,
  onIniciarSesion,
  cartCount,
  onOpenCart
}) => {
  const [userDropdownOpen, setUserDropdownOpen] = React.useState(false);
  const esPersonal = currentUser?.tipo === 'administrador' || currentUser?.tipo === 'veterinario';

  const getRoleBadge = (tipo: string) => {
    switch (tipo) {
      case 'administrador':
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-[#1d4f60] text-white">Admin</span>;
      case 'veterinario':
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-[#5dca88] text-white">Veterinario</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-[#ff9f43] text-white">Cliente</span>;
    }
  };

  return (
    <header className="sticky top-0 z-40 shadow-md">
      {/* Top Banner: Quick Switch (Legacy Primary Darker #1d4f60) */}
      <div className="bg-[#1d4f60] text-white text-xs px-4 py-1.5 flex flex-wrap items-center justify-between gap-2 border-b border-[#156a8e]/40">
        <span className="text-sky-100/80 hidden sm:inline">Mundo Peludo • Clínica Veterinaria</span>

        <div className="flex items-center gap-3">
          {!currentUser && (
            <button
              id="btn-iniciar-sesion"
              onClick={onIniciarSesion}
              className="flex items-center gap-1.5 text-white hover:bg-[#156a8e] bg-[#156a8e]/80 px-2 py-0.5 rounded-md border border-white/20 transition-colors font-medium"
            >
              <LogIn className="w-3.5 h-3.5 text-[#ff9f43]" />
              Iniciar sesión
            </button>
          )}

          {/* Menú de la sesión */}
          {currentUser && (
            <div className="relative">
              <button
                id="btn-user-role-menu"
                onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                className="flex items-center gap-1.5 text-white hover:bg-[#156a8e] bg-[#156a8e]/80 px-2 py-0.5 rounded-md border border-white/20 transition-colors"
              >
                <UserCheck className="w-3.5 h-3.5 text-[#ff9f43]" />
                <span className="font-medium truncate max-w-[120px] sm:max-w-none">{currentUser.nombre}</span>
                <span className="text-sky-200 text-[10px] uppercase hidden sm:inline">({currentUser.tipo})</span>
                <ChevronDown className="w-3 h-3 text-sky-200" />
              </button>

              {userDropdownOpen && (
                <div className="absolute right-0 mt-1 w-64 bg-white text-[#333333] rounded-lg shadow-xl border border-slate-200 py-1.5 z-50 text-xs">
                  <div className="px-3 py-2 border-b border-slate-100 flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <div className="font-semibold text-[#156a8e] truncate">
                        {currentUser.nombre} {currentUser.apellidos}
                      </div>
                      <div className="text-[11px] text-slate-500 truncate">{currentUser.email}</div>
                    </div>
                    {getRoleBadge(currentUser.tipo)}
                  </div>
                  <button
                    id="btn-cerrar-sesion"
                    onClick={() => {
                      setUserDropdownOpen(false);
                      onCerrarSesion?.();
                    }}
                    className="w-full text-left px-3 py-2 flex items-center gap-2 text-red-600 hover:bg-red-50 transition-colors font-medium"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    Cerrar sesión
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Main Navbar (Legacy Primary Blue #1d95c8) */}
      <div className="bg-[#1d95c8] text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Brand Logo with Official Image */}
            <div 
              id="brand-logo"
              onClick={() => setActiveTab('inicio')}
              className="flex items-center gap-3 cursor-pointer group select-none"
            >
              <img 
                src="/img/logo.jpg" 
                alt="Logo Mundo Peludo" 
                className="w-10 h-10 rounded-full border-2 border-white/80 object-cover shadow-sm group-hover:scale-105 transition-transform" 
                onError={(e) => {
                  (e.currentTarget as HTMLElement).style.display = 'none';
                }}
              />
              <div>
                <div className="text-xl font-extrabold tracking-tight text-white flex items-center gap-1">
                  Mundo <span className="text-[#fff5e6] drop-shadow-xs">Peludo</span>
                </div>
                <p className="text-[11px] font-medium text-sky-100 -mt-1 tracking-wide">Clínica Veterinaria</p>
              </div>
            </div>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center gap-1">
              <button
                id="nav-inicio"
                onClick={() => setActiveTab('inicio')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === 'inicio' ? 'bg-white/20 text-white font-bold shadow-xs' : 'text-white/90 hover:text-white hover:bg-white/10'}`}
              >
                Inicio
              </button>

              <button
                id="nav-citas"
                onClick={() => setActiveTab('citas')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${activeTab === 'citas' ? 'bg-white/20 text-white font-bold shadow-xs' : 'text-white/90 hover:text-white hover:bg-white/10'}`}
              >
                <Calendar className="w-4 h-4 text-[#ff9f43]" />
                <span>Citas</span>
              </button>

              <button
                id="nav-mascotas"
                onClick={() => setActiveTab('mascotas')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${activeTab === 'mascotas' ? 'bg-white/20 text-white font-bold shadow-xs' : 'text-white/90 hover:text-white hover:bg-white/10'}`}
              >
                <Dog className="w-4 h-4 text-[#ff9f43]" />
                <span>Mascotas</span>
              </button>

              <button
                id="nav-adopciones"
                onClick={() => setActiveTab('adopciones')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${activeTab === 'adopciones' ? 'bg-white/20 text-white font-bold shadow-xs' : 'text-white/90 hover:text-white hover:bg-white/10'}`}
              >
                <HeartHandshake className="w-4 h-4 text-pink-300" />
                <span>Adopciones</span>
              </button>

              <button
                id="nav-tienda"
                onClick={() => setActiveTab('tienda')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${activeTab === 'tienda' ? 'bg-white/20 text-white font-bold shadow-xs' : 'text-white/90 hover:text-white hover:bg-white/10'}`}
              >
                <ShoppingBag className="w-4 h-4 text-[#ff9f43]" />
                <span>Tienda</span>
              </button>

              <button
                id="nav-historial"
                onClick={() => setActiveTab('historial')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${activeTab === 'historial' ? 'bg-white/20 text-white font-bold shadow-xs' : 'text-white/90 hover:text-white hover:bg-white/10'}`}
              >
                <ClipboardList className="w-4 h-4 text-sky-200" />
                <span>Historial</span>
              </button>

              {esPersonal && (
                <button
                  id="nav-inventario"
                  onClick={() => setActiveTab('inventario')}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${activeTab === 'inventario' ? 'bg-white/20 text-white font-bold shadow-xs' : 'text-white/90 hover:text-white hover:bg-white/10'}`}
                >
                  <Package className="w-4 h-4 text-yellow-300" />
                  <span>Inventario</span>
                </button>
              )}

              {esPersonal && (
                <button
                  id="nav-servicios"
                  onClick={() => setActiveTab('servicios')}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${activeTab === 'servicios' ? 'bg-white/20 text-white font-bold shadow-xs' : 'text-white/90 hover:text-white hover:bg-white/10'}`}
                >
                  <CalendarClock className="w-4 h-4 text-sky-200" />
                  <span>Servicios</span>
                </button>
              )}

              <button
                id="nav-dashboard"
                onClick={() => setActiveTab('dashboard')}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${activeTab === 'dashboard' ? 'bg-white/20 text-white font-bold shadow-xs' : 'text-white/90 hover:text-white hover:bg-white/10'}`}
              >
                <ShieldCheck className="w-4 h-4 text-[#5dca88]" />
                <span>Panel</span>
              </button>
            </nav>

            {/* Action buttons (Cart & Quick Book in signature paw orange #ff9f43) */}
            <div className="flex items-center gap-3">
              <button
                id="btn-open-cart"
                onClick={onOpenCart}
                className="relative p-2.5 rounded-xl text-white hover:bg-white/15 transition-colors"
                title="Ver Carrito de Compras"
              >
                <ShoppingCart className="w-5 h-5 text-white" />
                {cartCount > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#ff9f43] text-white text-[11px] font-extrabold flex items-center justify-center border-2 border-[#1d95c8] shadow-sm">
                    {cartCount}
                  </span>
                )}
              </button>

              <button
                id="btn-quick-appointment"
                onClick={() => setActiveTab('citas')}
                className="hidden sm:inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#ff9f43] hover:bg-[#f08e30] text-white text-sm font-bold shadow-sm hover:shadow-md transition-all active:scale-95"
              >
                <Stethoscope className="w-4 h-4" />
                <span>Agendar Cita</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile navigation tab strip (Legacy primary dark #156a8e) */}
      <div className="md:hidden overflow-x-auto bg-[#156a8e] border-t border-white/10 px-4 py-2 flex items-center gap-2 no-scrollbar">
        <button
          onClick={() => setActiveTab('inicio')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${activeTab === 'inicio' ? 'bg-[#ff9f43] text-white font-bold' : 'bg-white/10 text-white'}`}
        >
          Inicio
        </button>
        <button
          onClick={() => setActiveTab('citas')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${activeTab === 'citas' ? 'bg-[#ff9f43] text-white font-bold' : 'bg-white/10 text-white'}`}
        >
          Citas
        </button>
        <button
          onClick={() => setActiveTab('mascotas')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${activeTab === 'mascotas' ? 'bg-[#ff9f43] text-white font-bold' : 'bg-white/10 text-white'}`}
        >
          Mascotas
        </button>
        <button
          onClick={() => setActiveTab('adopciones')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${activeTab === 'adopciones' ? 'bg-[#ff9f43] text-white font-bold' : 'bg-white/10 text-white'}`}
        >
          Adopciones
        </button>
        <button
          onClick={() => setActiveTab('tienda')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${activeTab === 'tienda' ? 'bg-[#ff9f43] text-white font-bold' : 'bg-white/10 text-white'}`}
        >
          Tienda
        </button>
        <button
          onClick={() => setActiveTab('historial')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${activeTab === 'historial' ? 'bg-[#ff9f43] text-white font-bold' : 'bg-white/10 text-white'}`}
        >
          Historial
        </button>
        {esPersonal && (
          <button
            onClick={() => setActiveTab('inventario')}
            className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${activeTab === 'inventario' ? 'bg-[#ff9f43] text-white font-bold' : 'bg-white/10 text-white'}`}
          >
            Inventario
          </button>
        )}
        {esPersonal && (
          <button
            onClick={() => setActiveTab('servicios')}
            className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${activeTab === 'servicios' ? 'bg-[#ff9f43] text-white font-bold' : 'bg-white/10 text-white'}`}
          >
            Servicios
          </button>
        )}
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap ${activeTab === 'dashboard' ? 'bg-[#ff9f43] text-white font-bold' : 'bg-white/10 text-white'}`}
        >
          Panel
        </button>
      </div>
    </header>
  );
};

