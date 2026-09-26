import React, { useEffect, useState } from 'react';
import { Mascota, Producto, Servicio } from '../types';
import { apiService } from '../api';
import { Navbar } from './Navbar';
import { HomeView } from './HomeView';
import { Footer } from './Footer';

interface InicioPublicoProps {
  /** Cualquier sección que no sea el inicio pide iniciar sesión primero. */
  onRequiereLogin: (tab: string, context?: any) => void;
}

/**
 * Landing visible sin sesión. Sólo usa endpoints públicos de la API
 * (servicios, mascotas en adopción y productos); el resto de la app queda
 * detrás del login.
 */
export const InicioPublico: React.FC<InicioPublicoProps> = ({ onRequiereLogin }) => {
  const [servicios, setServicios] = useState<Servicio[]>([]);
  const [adopciones, setAdopciones] = useState<Mascota[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);

  useEffect(() => {
    const avisar = (err: any) => {
      console.warn('Carga parcial de la página de inicio:', err?.message || err);
      return null;
    };
    apiService.getServicios().then(setServicios).catch(avisar);
    apiService.getAdopciones().then(setAdopciones).catch(avisar);
    apiService.getProductos().then(setProductos).catch(avisar);
  }, []);

  const navegar = (tab: string, context?: any) => {
    if (tab === 'inicio') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    onRequiereLogin(tab, context);
  };

  return (
    <div className="min-h-screen bg-[#f7fbfe] text-[#333333] flex flex-col antialiased">
      <Navbar
        activeTab="inicio"
        setActiveTab={navegar}
        currentUser={null}
        onIniciarSesion={() => onRequiereLogin('inicio')}
        cartCount={0}
        onOpenCart={() => onRequiereLogin('tienda')}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <HomeView
          onNavigate={navegar}
          servicios={servicios}
          mascotasAdopcion={adopciones}
          productos={productos}
          stats={null}
          onAddToCart={() => onRequiereLogin('tienda')}
        />
      </main>

      <Footer onNavigate={navegar} />
    </div>
  );
};
