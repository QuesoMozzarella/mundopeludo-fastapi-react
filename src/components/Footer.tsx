import React from 'react';

interface FooterProps {
  onNavigate: (tab: string) => void;
}

/** Pie común a la página pública y a la app con sesión. */
export const Footer: React.FC<FooterProps> = ({ onNavigate }) => (
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
          onClick={() => onNavigate('inicio')}
          className="hover:text-white transition-colors"
        >
          Inicio
        </button>
        <span>•</span>
        <button
          onClick={() => onNavigate('citas')}
          className="hover:text-white transition-colors"
        >
          Agendar Cita
        </button>
        <span>•</span>
        <button
          onClick={() => onNavigate('tienda')}
          className="hover:text-white transition-colors"
        >
          Tienda
        </button>
      </div>
    </div>
  </footer>
);
