import React, { useState, useEffect } from 'react';
import { 
  User, 
  Mascota, 
  Especie, 
  Servicio, 
  Cita, 
  Producto, 
  HistorialMedico, 
  SolicitudAdopcion, 
  DashboardStats, 
  CartItem 
} from './types';
import { apiService } from './api';
import { Navbar } from './components/Navbar';
import { HomeView } from './components/HomeView';
import { CitasView } from './components/CitasView';
import { MascotasView } from './components/MascotasView';
import { AdopcionesView } from './components/AdopcionesView';
import { TiendaView } from './components/TiendaView';
import { HistorialView } from './components/HistorialView';
import { InventarioView } from './components/InventarioView';
import { DashboardView } from './components/DashboardView';
import { CartModal } from './components/CartModal';
import { AlertCircle, RefreshCw } from 'lucide-react';
import {
  INITIAL_USERS,
  INITIAL_ESPECIES,
  INITIAL_SERVICIOS,
  INITIAL_MASCOTAS,
  INITIAL_CITAS,
  INITIAL_PRODUCTOS,
  INITIAL_HISTORIALES,
  INITIAL_SOLICITUDES,
  INITIAL_STATS
} from './data/seedData';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('inicio');
  const [loading, setLoading] = useState<boolean>(false);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  // User State
  const [allUsers, setAllUsers] = useState<User[]>(INITIAL_USERS);
  const [currentUser, setCurrentUser] = useState<User>(INITIAL_USERS[0]);

  // Domain Entities
  const [mascotas, setMascotas] = useState<Mascota[]>(INITIAL_MASCOTAS);
  const [especies, setEspecies] = useState<Especie[]>(INITIAL_ESPECIES);
  const [servicios, setServicios] = useState<Servicio[]>(INITIAL_SERVICIOS);
  const [citas, setCitas] = useState<Cita[]>(INITIAL_CITAS);
  const [adopciones, setAdopciones] = useState<Mascota[]>(() => INITIAL_MASCOTAS.filter(m => m.estado_adopcion === 'en_adopcion'));
  const [solicitudes, setSolicitudes] = useState<SolicitudAdopcion[]>(INITIAL_SOLICITUDES);
  const [productos, setProductos] = useState<Producto[]>(INITIAL_PRODUCTOS);
  const [historiales, setHistoriales] = useState<HistorialMedico[]>(INITIAL_HISTORIALES);
  const [stats, setStats] = useState<DashboardStats | null>(INITIAL_STATS);

  // Modals & Navigation Context
  const [cartModalOpen, setCartModalOpen] = useState(false);
  const [selectedPetForHistorial, setSelectedPetForHistorial] = useState<Mascota | null>(null);
  const [preselectedServicioId, setPreselectedServicioId] = useState<number | null>(null);

  // Shopping Cart
  const [cartItems, setCartItems] = useState<CartItem[]>(() => {
    try {
      const saved = localStorage.getItem('mundopeludo_cart');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('mundopeludo_cart', JSON.stringify(cartItems));
    } catch (e) {
      console.error(e);
    }
  }, [cartItems]);

  // Load all initial data from FastAPI backend with automatic retry and graceful fallback
  const loadData = async (showLoadingSpinner = false) => {
    try {
      if (showLoadingSpinner) {
        setLoading(true);
      }
      setErrorBanner(null);

      // Check health safely (does not throw thanks to fallback)
      const health = await apiService.getHealth();
      const isHealthy = health.status === 'ok';

      const [
        usersData,
        especiesData,
        serviciosData,
        mascotasData,
        citasData,
        adopcionesData,
        solicitudesData,
        productosData,
        historialesData,
        statsData
      ] = await Promise.all([
        apiService.getUsuarios().catch(() => null),
        apiService.getEspecies().catch(() => null),
        apiService.getServicios().catch(() => null),
        apiService.getMascotas().catch(() => null),
        apiService.getCitas().catch(() => null),
        apiService.getAdopciones().catch(() => null),
        apiService.getSolicitudesAdopcion().catch(() => null),
        apiService.getProductos().catch(() => null),
        apiService.getHistoriales().catch(() => null),
        apiService.getStats().catch(() => null)
      ]);

      if (usersData && usersData.length > 0) {
        setAllUsers(usersData);
        if (!usersData.some(u => u.id === currentUser.id)) {
          setCurrentUser(usersData[0]);
        }
      }
      if (especiesData && especiesData.length > 0) setEspecies(especiesData);
      if (serviciosData && serviciosData.length > 0) setServicios(serviciosData);
      if (mascotasData && mascotasData.length > 0) setMascotas(mascotasData);
      if (citasData && citasData.length > 0) setCitas(citasData);
      if (adopcionesData && adopcionesData.length > 0) setAdopciones(adopcionesData);
      if (solicitudesData && solicitudesData.length > 0) setSolicitudes(solicitudesData);
      if (productosData && productosData.length > 0) setProductos(productosData);
      if (historialesData && historialesData.length > 0) setHistoriales(historialesData);
      if (statsData) setStats(statsData);

      if (isHealthy) {
        setErrorBanner(null);
      } else if (!usersData && !mascotasData) {
        // Only show banner if neither health nor data could connect
        setErrorBanner('Conectando con el backend FastAPI de Mundo Peludo...');
      }
    } catch (err: any) {
      console.warn('Backend synchronization notice:', err?.message || err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Re-verify connection after 3 seconds in case backend was finishing cold start
    const timer = setTimeout(() => {
      loadData();
    }, 3000);
    return () => clearTimeout(timer);
  }, []);

  // Cart operations
  const handleAddToCart = (producto: Producto) => {
    setCartItems(prev => {
      const existing = prev.find(item => item.producto.id === producto.id);
      if (existing) {
        return prev.map(item =>
          item.producto.id === producto.id
            ? { ...item, cantidad: item.cantidad + 1 }
            : item
        );
      }
      return [...prev, { producto, cantidad: 1 }];
    });
  };

  const handleUpdateCartQuantity = (productoId: number, delta: number) => {
    setCartItems(prev =>
      prev
        .map(item => {
          if (item.producto.id === productoId) {
            const newQty = item.cantidad + delta;
            return newQty > 0 ? { ...item, cantidad: newQty } : null;
          }
          return item;
        })
        .filter(Boolean) as CartItem[]
    );
  };

  const handleRemoveCartItem = (productoId: number) => {
    setCartItems(prev => prev.filter(item => item.producto.id !== productoId));
  };

  const handleClearCart = () => {
    setCartItems([]);
  };

  const handleCheckout = async (data: {
    items: { producto_id: number; cantidad: number }[];
    direccion_envio: string;
    metodo_pago: string;
  }) => {
    const res = await apiService.createPedido({
      cliente_id: currentUser.id,
      items: data.items,
      direccion_envio: data.direccion_envio,
      metodo_pago: data.metodo_pago
    });

    // Refresh products and stats
    const [prods, s] = await Promise.all([
      apiService.getProductos(),
      apiService.getStats()
    ]);
    setProductos(prods);
    setStats(s);

    return res;
  };

  // Citas operations
  const handleBookCita = async (data: any) => {
    await apiService.createCita(data);
    const updatedCitas = await apiService.getCitas();
    setCitas(updatedCitas);
    const updatedStats = await apiService.getStats();
    setStats(updatedStats);
  };

  const handleUpdateCitaEstado = async (id: number, estado: string) => {
    await apiService.updateCitaEstado(id, estado);
    const updatedCitas = await apiService.getCitas();
    setCitas(updatedCitas);
    const updatedStats = await apiService.getStats();
    setStats(updatedStats);
  };

  // Mascotas operations
  const handleCreateMascota = async (data: Partial<Mascota>) => {
    await apiService.createMascota(data);
    const updatedMascotas = await apiService.getMascotas();
    setMascotas(updatedMascotas);
    const updatedStats = await apiService.getStats();
    setStats(updatedStats);
  };

  // Adopciones operations
  const handleApplyAdopcion = async (mascotaId: number, clienteId: number, notas: string) => {
    await apiService.solicitarAdopcion({
      mascota_id: mascotaId,
      cliente_id: clienteId,
      notas_cliente: notas
    });
    const updatedSols = await apiService.getSolicitudesAdopcion();
    setSolicitudes(updatedSols);
  };

  const handleAprobarSolicitud = async (solicitudId: number, revisorId: number, notas?: string) => {
    await apiService.revisarSolicitudAdopcion(solicitudId, {
      estado: 'aprobada',
      revisor_id: revisorId,
      notas_revisor: notas
    });
    const [sols, adops, mascs, s] = await Promise.all([
      apiService.getSolicitudesAdopcion(),
      apiService.getAdopciones(),
      apiService.getMascotas(),
      apiService.getStats()
    ]);
    setSolicitudes(sols);
    setAdopciones(adops);
    setMascotas(mascs);
    setStats(s);
  };

  const handleRechazarSolicitud = async (solicitudId: number, revisorId: number, notas?: string) => {
    await apiService.revisarSolicitudAdopcion(solicitudId, {
      estado: 'rechazada',
      revisor_id: revisorId,
      notas_revisor: notas
    });
    const sols = await apiService.getSolicitudesAdopcion();
    setSolicitudes(sols);
  };

  // Historial operations
  const handleCreateHistorial = async (data: any) => {
    await apiService.createHistorial(data);
    const updatedHists = await apiService.getHistoriales();
    setHistoriales(updatedHists);

    // If linked to an appointment, mark appointment completed
    if (data.cita_id) {
      await handleUpdateCitaEstado(data.cita_id, 'Completada');
    }
  };

  // Inventory operations
  const handleCreateProducto = async (data: Partial<Producto>) => {
    await apiService.createProducto(data);
    const prods = await apiService.getProductos();
    setProductos(prods);
  };

  const handleUpdateProducto = async (id: number, data: Partial<Producto>) => {
    await apiService.updateProducto(id, data);
    const prods = await apiService.getProductos();
    setProductos(prods);
  };

  const handleDeleteProducto = async (id: number) => {
    await apiService.deleteProducto(id);
    const prods = await apiService.getProductos();
    setProductos(prods);
  };

  // Quick navigation helper
  const handleNavigate = (tab: string, context?: any) => {
    if (context?.servicioId) {
      setPreselectedServicioId(context.servicioId);
    }
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const veterinarios = allUsers.filter(u => u.tipo === 'veterinario' || u.tipo === 'administrador');

  return (
    <div className="min-h-screen bg-[#f7fbfe] text-[#333333] flex flex-col antialiased">
      {/* Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={(t) => {
          setActiveTab(t);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        currentUser={currentUser}
        onSwitchUser={setCurrentUser}
        allUsers={allUsers}
        cartCount={cartItems.reduce((acc, i) => acc + i.cantidad, 0)}
        onOpenCart={() => setCartModalOpen(true)}
      />

      {/* Error alert banner if any */}
      {errorBanner && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2.5 text-xs text-red-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorBanner}</span>
          </div>
          <button
            onClick={() => loadData(true)}
            className="font-bold underline hover:text-red-900"
          >
            Reintentar
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && mascotas.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 space-y-4">
            <RefreshCw className="w-10 h-10 text-[#1d95c8] animate-spin" />
            <h3 className="text-base font-bold text-[#156a8e]">Cargando datos de Mundo Peludo...</h3>
            <p className="text-xs text-slate-500">Conectando con el backend FastAPI y base de datos</p>
          </div>
        ) : (
          <>
            {activeTab === 'inicio' && (
              <HomeView
                onNavigate={handleNavigate}
                servicios={servicios}
                mascotasAdopcion={adopciones}
                productos={productos}
                stats={stats}
                onAddToCart={handleAddToCart}
              />
            )}

            {activeTab === 'citas' && (
              <CitasView
                citas={citas}
                mascotas={mascotas}
                servicios={servicios}
                veterinarios={veterinarios}
                currentUser={currentUser}
                onBookCita={handleBookCita}
                onUpdateEstado={handleUpdateCitaEstado}
                onOpenHistorialModal={(cita) => {
                  const pet = mascotas.find(m => m.id === cita.mascota_id) || null;
                  setSelectedPetForHistorial(pet);
                  setActiveTab('historial');
                }}
                preselectedServicioId={preselectedServicioId}
              />
            )}

            {activeTab === 'mascotas' && (
              <MascotasView
                mascotas={mascotas}
                especies={especies}
                currentUser={currentUser}
                onCreateMascota={handleCreateMascota}
                onOpenHistorialModalWithPet={(pet) => {
                  setSelectedPetForHistorial(pet);
                  setActiveTab('historial');
                }}
              />
            )}

            {activeTab === 'adopciones' && (
              <AdopcionesView
                adopciones={adopciones}
                solicitudes={solicitudes}
                currentUser={currentUser}
                onApplyAdopcion={handleApplyAdopcion}
                onAprobarSolicitud={handleAprobarSolicitud}
                onRechazarSolicitud={handleRechazarSolicitud}
              />
            )}

            {activeTab === 'tienda' && (
              <TiendaView
                productos={productos}
                onAddToCart={handleAddToCart}
                currentUser={currentUser}
                onOpenCart={() => setCartModalOpen(true)}
              />
            )}

            {activeTab === 'historial' && (
              <HistorialView
                historiales={historiales}
                mascotas={mascotas}
                citas={citas}
                currentUser={currentUser}
                onCreateHistorial={handleCreateHistorial}
                initialSelectedPet={selectedPetForHistorial}
              />
            )}

            {activeTab === 'inventario' && (
              <InventarioView
                productos={productos}
                currentUser={currentUser}
                onCreateProducto={handleCreateProducto}
                onUpdateProducto={handleUpdateProducto}
                onDeleteProducto={handleDeleteProducto}
              />
            )}

            {activeTab === 'dashboard' && (
              <DashboardView
                stats={stats}
                currentUser={currentUser}
                citas={citas}
                mascotas={mascotas}
                onNavigate={handleNavigate}
              />
            )}
          </>
        )}
      </main>

      {/* Footer (Legacy Primary Darker #1d4f60) */}
      <footer className="bg-[#1d4f60] text-sky-100 text-xs border-t border-[#156a8e] py-10 px-4 mt-auto">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <img 
                src="/img/logo.jpg" 
                alt="Logo Mundo Peludo" 
                className="w-8 h-8 rounded-full border border-white/60 object-cover"
                onError={(e) => {
                  (e.currentTarget as HTMLElement).style.display = 'none';
                }}
              />
              <span className="font-extrabold text-base text-white tracking-wide">Mundo Peludo</span>
            </div>
            <p className="text-sky-200/80 leading-relaxed text-xs">
              Clínica veterinaria dedicada al cuidado integral, salud y felicidad de tus mascotas con atención profesional 24/7.
            </p>
          </div>

          <div>
            <h4 className="font-bold text-white uppercase tracking-wider text-[11px] mb-3">Contacto & Ubicación</h4>
            <ul className="space-y-2 text-sky-200/90 text-xs">
              <li>📍 Bello, Antioquia, Colombia</li>
              <li>💬 WhatsApp: +57 3243806941</li>
              <li>✉️ andres_ramirez23232@elpoli.edu.co</li>
              <li>⏰ Urgencias: Atención Médica 24 Horas</li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-white uppercase tracking-wider text-[11px] mb-3">Arquitectura Técnica</h4>
            <p className="text-sky-200/80 leading-relaxed mb-3">
              Nueva versión moderna desarrollada con FastAPI v2.0 (Python), Node.js Express y React + Tailwind.
            </p>
          </div>
        </div>

        <div className="max-w-7xl mx-auto pt-6 border-t border-[#156a8e]/60 flex flex-col sm:flex-row items-center justify-between gap-3 text-sky-200/60 text-[11px]">
          <div>
            © {new Date().getFullYear()} Mundo Peludo. Todos los derechos reservados.
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setActiveTab('inicio')}
              className="hover:text-white transition-colors"
            >
              Inicio
            </button>
            <span>•</span>
            <button
              onClick={() => setActiveTab('citas')}
              className="hover:text-white transition-colors"
            >
              Agendar Cita
            </button>
            <span>•</span>
            <button
              onClick={() => setActiveTab('tienda')}
              className="hover:text-white transition-colors"
            >
              Tienda
            </button>
          </div>
        </div>
      </footer>

      {/* Cart Modal */}
      <CartModal
        isOpen={cartModalOpen}
        onClose={() => setCartModalOpen(false)}
        cartItems={cartItems}
        onUpdateQuantity={handleUpdateCartQuantity}
        onRemoveItem={handleRemoveCartItem}
        onClearCart={handleClearCart}
        currentUser={currentUser}
        onCheckout={handleCheckout}
      />
    </div>
  );
}

export default App;
