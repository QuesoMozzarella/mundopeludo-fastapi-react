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
  CartItem,
  Sesion
} from './types';
import {
  apiService,
  alCaducarSesion,
  ApiError,
  fetchMe,
  guardarSesion,
  obtenerSesion
} from './api';
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
import { LoginView } from './components/LoginView';
import { Footer } from './components/Footer';
import { AlertCircle, RefreshCw } from 'lucide-react';

const CLAVE_CARRITO = 'mundopeludo_cart';

interface Destino {
  tab: string;
  context?: any;
}

// Lo mismo que era público en el Django (index, adopciones, tienda): se ve sin
// sesión. El resto pide iniciar sesión y, al entrar, abre la sección pedida.
const SECCIONES_PUBLICAS = new Set(['inicio', 'adopciones', 'tienda']);

/** Puerta de entrada: decide entre la app (con o sin sesión) y el login. */
export function App() {
  const [sesion, setSesion] = useState<Sesion | null>(() => obtenerSesion());
  const [aviso, setAviso] = useState<string | null>(null);
  const [pidiendoLogin, setPidiendoLogin] = useState(false);
  const [destino, setDestino] = useState<Destino>({ tab: 'inicio' });

  const cerrarSesion = (mensaje: string | null = null) => {
    guardarSesion(null);
    try {
      // El carrito vive en el navegador: no debe pasar de un usuario a otro.
      localStorage.removeItem(CLAVE_CARRITO);
    } catch {
      /* sin almacenamiento */
    }
    setAviso(mensaje);
    setDestino({ tab: 'inicio' });
    // Si caducó, se muestra el login con el aviso; si cerró sesión, el inicio.
    setPidiendoLogin(mensaje !== null);
    setSesion(null);
  };

  useEffect(() => {
    alCaducarSesion(() => cerrarSesion('Tu sesión expiró. Vuelve a iniciar sesión.'));
    return () => alCaducarSesion(null);
  }, []);

  // Una sesión guardada puede estar caducada o el usuario pudo cambiar de rol.
  useEffect(() => {
    if (!sesion) return;
    fetchMe()
      .then((usuario) => {
        const actualizada = { ...sesion, usuario };
        guardarSesion(actualizada);
        setSesion(actualizada);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          cerrarSesion('Tu sesión expiró. Vuelve a iniciar sesión.');
        }
      });
    // Sólo al arrancar: después la sesión cambia por login/logout explícitos.
  }, []);

  if (!sesion && pidiendoLogin) {
    return (
      <LoginView
        aviso={aviso}
        onVolver={() => {
          setDestino({ tab: 'inicio' });
          setPidiendoLogin(false);
        }}
        onSesionIniciada={(nueva) => {
          guardarSesion(nueva);
          setAviso(null);
          setPidiendoLogin(false);
          setSesion(nueva);
        }}
      />
    );
  }

  return (
    <Clinica
      // Montaje nuevo al entrar o salir: estado y datos del usuario anterior no se arrastran.
      key={sesion?.usuario.id ?? 'publico'}
      currentUser={sesion?.usuario ?? null}
      destinoInicial={destino}
      onRequiereLogin={(tab, context) => {
        setDestino({ tab, context });
        setAviso(null);
        setPidiendoLogin(true);
      }}
      onCerrarSesion={() => cerrarSesion()}
    />
  );
}

interface ClinicaProps {
  /** null = visitante: sólo secciones públicas y datos públicos de la API. */
  currentUser: User | null;
  /** Sección que el usuario pidió antes de iniciar sesión. */
  destinoInicial: Destino;
  onRequiereLogin: (tab: string, context?: any) => void;
  onCerrarSesion: () => void;
}

function Clinica({ currentUser, destinoInicial, onRequiereLogin, onCerrarSesion }: ClinicaProps) {
  const esPersonal = currentUser?.tipo === 'veterinario' || currentUser?.tipo === 'administrador';
  const [activeTab, setActiveTab] = useState<string>(destinoInicial.tab);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  // Domain Entities (sin datos de demostración: sólo lo que devuelve la API)
  const [veterinarios, setVeterinarios] = useState<User[]>([]);
  const [mascotas, setMascotas] = useState<Mascota[]>([]);
  const [especies, setEspecies] = useState<Especie[]>([]);
  const [servicios, setServicios] = useState<Servicio[]>([]);
  const [citas, setCitas] = useState<Cita[]>([]);
  const [adopciones, setAdopciones] = useState<Mascota[]>([]);
  const [solicitudes, setSolicitudes] = useState<SolicitudAdopcion[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [historiales, setHistoriales] = useState<HistorialMedico[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);

  // Modals & Navigation Context
  const [cartModalOpen, setCartModalOpen] = useState(false);
  const [selectedPetForHistorial, setSelectedPetForHistorial] = useState<Mascota | null>(null);
  const [preselectedServicioId, setPreselectedServicioId] = useState<number | null>(
    destinoInicial.context?.servicioId ?? null
  );

  // Shopping Cart
  const [cartItems, setCartItems] = useState<CartItem[]>(() => {
    try {
      const saved = localStorage.getItem(CLAVE_CARRITO);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(CLAVE_CARRITO, JSON.stringify(cartItems));
    } catch (e) {
      console.error(e);
    }
  }, [cartItems]);

  // El panel de indicadores es sólo para el personal: a un cliente la API le
  // responde 403, así que ni se pide.
  const refrescarStats = async () => {
    if (!esPersonal) return;
    try {
      setStats(await apiService.getStats());
    } catch (err) {
      console.warn('No se pudieron cargar los indicadores:', err);
    }
  };

  // La API ya filtra por usuario: un cliente recibe sólo sus mascotas, citas,
  // historiales y solicitudes; el personal, todo. Un visitante, sólo lo público.
  const loadData = async (showLoadingSpinner = false) => {
    if (showLoadingSpinner) setLoading(true);
    setErrorBanner(null);
    try {
      const health = await apiService.getHealth();
      if (health.status !== 'ok') {
        setErrorBanner('No se pudo conectar con el backend de Mundo Peludo.');
        return;
      }

      const intentar = <T,>(p: Promise<T>) => p.catch((err) => {
        console.warn('Carga parcial:', err?.message || err);
        return null;
      });
      const privado = <T,>(cargar: () => Promise<T>) =>
        currentUser ? intentar(cargar()) : Promise.resolve(null);
      const [
        vetsData,
        especiesData,
        serviciosData,
        mascotasData,
        citasData,
        adopcionesData,
        solicitudesData,
        productosData,
        historialesData
      ] = await Promise.all([
        intentar(apiService.getVeterinarios()),
        intentar(apiService.getEspecies()),
        intentar(apiService.getServicios()),
        privado(() => apiService.getMascotas()),
        privado(() => apiService.getCitas()),
        intentar(apiService.getAdopciones()),
        privado(() => apiService.getSolicitudesAdopcion()),
        intentar(apiService.getProductos()),
        privado(() => apiService.getHistoriales())
      ]);

      if (vetsData) setVeterinarios(vetsData);
      if (especiesData) setEspecies(especiesData);
      if (serviciosData) setServicios(serviciosData);
      if (mascotasData) setMascotas(mascotasData);
      if (citasData) setCitas(citasData);
      if (adopcionesData) setAdopciones(adopcionesData);
      if (solicitudesData) setSolicitudes(solicitudesData);
      if (productosData) setProductos(productosData);
      if (historialesData) setHistoriales(historialesData);
      await refrescarStats();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(true);
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
    if (!currentUser) throw new Error('Inicia sesión para completar la compra');
    const res = await apiService.createPedido({
      cliente_id: currentUser.id,
      items: data.items,
      direccion_envio: data.direccion_envio,
      metodo_pago: data.metodo_pago
    });

    setProductos(await apiService.getProductos());
    await refrescarStats();
    return res;
  };

  // Citas operations
  const handleBookCita = async (data: any) => {
    await apiService.createCita(data);
    setCitas(await apiService.getCitas());
    await refrescarStats();
  };

  const handleUpdateCitaEstado = async (id: number, estado: string) => {
    await apiService.updateCitaEstado(id, estado);
    setCitas(await apiService.getCitas());
    await refrescarStats();
  };

  // Mascotas operations
  const handleCreateMascota = async (data: Partial<Mascota>) => {
    await apiService.createMascota(data);
    setMascotas(await apiService.getMascotas());
    await refrescarStats();
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
    const [sols, adops, mascs] = await Promise.all([
      apiService.getSolicitudesAdopcion(),
      apiService.getAdopciones(),
      apiService.getMascotas()
    ]);
    setSolicitudes(sols);
    setAdopciones(adops);
    setMascotas(mascs);
    await refrescarStats();
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
    setHistoriales(await apiService.getHistoriales());
    // Con cita, el backend ya la marca como Completada: sólo hay que refrescarla.
    if (data.cita_id) {
      setCitas(await apiService.getCitas());
    }
  };

  // Inventory operations
  const handleCreateProducto = async (data: Partial<Producto>) => {
    const creado = await apiService.createProducto(data);
    const prods = await apiService.getProductos();
    setProductos(prods);
    return creado;
  };

  // Sube la nueva imagen y después retira las anteriores: el producto se
  // queda con una sola. Si falla un borrado, la nueva ya es la que se muestra.
  const handleCambiarImagenProducto = async (id: number, archivo: File, anteriores: number[]) => {
    try {
      await apiService.subirImagenProducto(id, archivo);
      await Promise.allSettled(anteriores.map((imagenId) => apiService.eliminarImagenProducto(imagenId)));
    } finally {
      setProductos(await apiService.getProductos());
    }
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
    if (!currentUser && !SECCIONES_PUBLICAS.has(tab)) {
      onRequiereLogin(tab, context);
      return;
    }
    if (context?.servicioId) {
      setPreselectedServicioId(context.servicioId);
    }
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#f7fbfe] text-[#333333] flex flex-col antialiased">
      {/* Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={(t) => handleNavigate(t)}
        currentUser={currentUser}
        onCerrarSesion={onCerrarSesion}
        onIniciarSesion={() => onRequiereLogin(activeTab)}
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
        {loading ? (
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

            {activeTab === 'citas' && currentUser && (
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

            {activeTab === 'mascotas' && currentUser && (
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
                onRequiereLogin={() => onRequiereLogin('adopciones')}
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

            {activeTab === 'historial' && currentUser && (
              <HistorialView
                historiales={historiales}
                mascotas={mascotas}
                citas={citas}
                currentUser={currentUser}
                onCreateHistorial={handleCreateHistorial}
                initialSelectedPet={selectedPetForHistorial}
              />
            )}

            {activeTab === 'inventario' && currentUser && (
              <InventarioView
                productos={productos}
                currentUser={currentUser}
                onCreateProducto={handleCreateProducto}
                onUpdateProducto={handleUpdateProducto}
                onDeleteProducto={handleDeleteProducto}
                onCambiarImagen={handleCambiarImagenProducto}
              />
            )}

            {activeTab === 'dashboard' && currentUser && (
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

      <Footer onNavigate={handleNavigate} />

      {/* Cart Modal */}
      <CartModal
        isOpen={cartModalOpen}
        onClose={() => setCartModalOpen(false)}
        cartItems={cartItems}
        onUpdateQuantity={handleUpdateCartQuantity}
        onRemoveItem={handleRemoveCartItem}
        onClearCart={handleClearCart}
        currentUser={currentUser}
        onRequiereLogin={() => {
          setCartModalOpen(false);
          onRequiereLogin('tienda');
        }}
        onCheckout={handleCheckout}
      />
    </div>
  );
}

export default App;
