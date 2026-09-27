import React from 'react';
import { Clock, Mail, MapPin, Phone, Siren } from 'lucide-react';
import { CLINICA, enlaceTelefono, hayContacto } from '../clinica';

interface FooterProps {
  onNavigate: (tab: string) => void;
}

/** Pie común: la marca, el contacto de `clinica.ts` y accesos directos. */
export const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  const telefono = enlaceTelefono();
  return (
    <footer className="bg-[#1d4f60] text-white/85 text-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 grid gap-8 md:grid-cols-3">
        <div className="space-y-3">
          <div className="flex items-center gap-2.5">
            <img
              src="/img/logo.jpg"
              alt=""
              className="w-9 h-9 rounded-full border border-white/60 object-cover bg-white"
              onError={(e) => ((e.currentTarget as HTMLElement).style.display = 'none')}
            />
            <span className="font-titulo text-lg font-semibold text-white">{CLINICA.nombre}</span>
          </div>
          <p className="text-white/70 max-w-xs">{CLINICA.presentacion}</p>
        </div>

        {hayContacto && (
          <div>
            <h2 className="font-titulo text-base font-semibold text-white mb-3">Contacto</h2>
            <ul className="space-y-2 text-white/75">
              {CLINICA.direccion && (
                <li className="flex gap-2"><MapPin className="w-4 h-4 mt-0.5 text-[#9dddf5] shrink-0" />{CLINICA.direccion}</li>
              )}
              {CLINICA.telefono && (
                <li className="flex gap-2">
                  <Phone className="w-4 h-4 mt-0.5 text-[#9dddf5] shrink-0" />
                  <a href={telefono!} className="hover:text-white underline-offset-2 hover:underline">{CLINICA.telefono}</a>
                </li>
              )}
              {CLINICA.correo && (
                <li className="flex gap-2">
                  <Mail className="w-4 h-4 mt-0.5 text-[#9dddf5] shrink-0" />
                  <a href={`mailto:${CLINICA.correo}`} className="hover:text-white underline-offset-2 hover:underline">{CLINICA.correo}</a>
                </li>
              )}
              {CLINICA.horario && (
                <li className="flex gap-2"><Clock className="w-4 h-4 mt-0.5 text-[#9dddf5] shrink-0" />{CLINICA.horario}</li>
              )}
              {CLINICA.urgencias && (
                <li className="flex gap-2"><Siren className="w-4 h-4 mt-0.5 text-[#9dddf5] shrink-0" />{CLINICA.urgencias}</li>
              )}
            </ul>
          </div>
        )}

        <nav aria-label="Accesos directos" className={hayContacto ? '' : 'md:col-start-3'}>
          <h2 className="font-titulo text-base font-semibold text-white mb-3">Accesos</h2>
          <ul className="space-y-2">
            {[
              ['citas', 'Pedir una cita'],
              ['adopciones', 'Adoptar una mascota'],
              ['tienda', 'Ir a la tienda']
            ].map(([tab, texto]) => (
              <li key={tab}>
                <button onClick={() => onNavigate(tab)} className="text-white/75 hover:text-white hover:underline underline-offset-2">
                  {texto}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </div>

      <div className="border-t border-white/10">
        <p className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 text-xs text-white/55">
          © {new Date().getFullYear()} {CLINICA.nombre}
        </p>
      </div>
    </footer>
  );
};
