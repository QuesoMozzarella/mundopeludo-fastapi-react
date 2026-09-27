import React from 'react';
import { DashboardStats, User, Cita, Mascota } from '../types';
import { formatearFechaHora, formatearPrecio } from '../formato';
import { EstadoCita, FotoMascota } from './ui';
import { CalendarPlus, ClipboardList, Dog, HeartHandshake, Mail, Package, Phone, ShieldCheck, Stethoscope } from 'lucide-react';

interface DashboardViewProps {
  stats: DashboardStats | null;
  currentUser: User;
  citas: Cita[];
  mascotas: Mascota[];
  onNavigate: (tab: string) => void;
}

const AVATAR: Record<string, string> = {
  administrador: '/img/admin.png',
  veterinario: '/img/veterinario.png',
  cliente: '/img/cliente.png'
};

const ROL: Record<string, string> = {
  administrador: 'Administrador',
  veterinario: 'Veterinario',
  cliente: 'Cliente'
};

const hoyLargo = new Intl.DateTimeFormat('es-CO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

function Estadistica({ valor, etiqueta, detalle, Icono }: {
  valor: React.ReactNode;
  etiqueta: string;
  detalle?: React.ReactNode;
  Icono: React.ComponentType<{ className?: string }>;
}) {
  return (
    <div className="mp-stat">
      <Icono className="w-5 h-5 text-[#9dddf5] mb-2" />
      <div className="mp-stat-valor">{valor}</div>
      <div className="text-sm text-white/90 mt-1">{etiqueta}</div>
      {detalle && <div className="text-xs text-white/70 mt-0.5">{detalle}</div>}
    </div>
  );
}

export const DashboardView: React.FC<DashboardViewProps> = ({ stats, currentUser, citas, mascotas, onNavigate }) => {
  const esCliente = currentUser.tipo === 'cliente';
  const ahora = Date.now();
  const proximas = citas
    .filter((c) => (c.estado === 'Pendiente' || c.estado === 'Confirmada') && new Date(c.fecha_hora).getTime() >= ahora)
    .sort((a, b) => a.fecha_hora.localeCompare(b.fecha_hora));
  const activas = citas.filter((c) => c.estado === 'Pendiente' || c.estado === 'Confirmada').length;

  const accesos = esCliente
    ? [
        { tab: 'citas', texto: 'Pedir una cita', Icono: CalendarPlus },
        { tab: 'mascotas', texto: 'Registrar una mascota', Icono: Dog },
        { tab: 'historial', texto: 'Ver el historial', Icono: ClipboardList },
        { tab: 'adopciones', texto: 'Adoptar', Icono: HeartHandshake }
      ]
    : [
        { tab: 'citas', texto: 'Agenda de citas', Icono: Stethoscope },
        { tab: 'historial', texto: 'Historias clínicas', Icono: ClipboardList },
        { tab: 'adopciones', texto: 'Solicitudes de adopción', Icono: HeartHandshake },
        { tab: 'inventario', texto: 'Inventario', Icono: Package }
      ];

  return (
    <div className="space-y-8">
      {/* Bienvenida: perfil, resumen e información, como en el dashboard del Django */}
      <section className="mp-panel grid gap-6 lg:grid-cols-12">
        <div className="lg:col-span-3 flex lg:flex-col items-center gap-4 lg:text-center">
          <img
            src={AVATAR[currentUser.tipo] ?? AVATAR.cliente}
            alt=""
            className="w-24 h-24 lg:w-32 lg:h-32 rounded-full object-cover bg-white/90 border-[3px] border-white/25 shrink-0"
          />
          <div>
            <h1 className="font-titulo text-2xl font-bold leading-tight">¡Bienvenido/a, {currentUser.nombre}!</h1>
            <p className="text-sm text-white/75 mt-1 first-letter:uppercase">{hoyLargo.format(new Date())}</p>
            <span className="mp-pill mp-pill--suave mt-2">{ROL[currentUser.tipo]}</span>
          </div>
        </div>

        <div className="lg:col-span-5 lg:border-l lg:border-white/15 lg:pl-6">
          <h2 className="mp-panel-titulo">{esCliente ? 'Tu resumen' : 'Resumen de la clínica'}</h2>
          <div className="grid grid-cols-2 gap-3">
            {esCliente ? (
              <>
                <Estadistica Icono={Dog} valor={mascotas.length} etiqueta="Mascotas" />
                <Estadistica Icono={Stethoscope} valor={citas.length} etiqueta="Citas" detalle={`${activas} activas`} />
                <Estadistica
                  Icono={CalendarPlus}
                  valor={proximas.length}
                  etiqueta="Próximas"
                  detalle={proximas[0] ? formatearFechaHora(proximas[0].fecha_hora) : 'Sin citas por venir'}
                />
                <Estadistica Icono={HeartHandshake} valor={stats?.solicitudes_pendientes ?? 0} etiqueta="Solicitudes de adopción" />
              </>
            ) : (
              <>
                <Estadistica Icono={Dog} valor={stats?.total_mascotas ?? mascotas.length} etiqueta="Pacientes" />
                <Estadistica
                  Icono={Stethoscope}
                  valor={stats?.total_citas ?? citas.length}
                  etiqueta="Citas"
                  detalle={`${stats?.citas_activas ?? activas} activas · ${stats?.citas_hoy ?? 0} hoy`}
                />
                <Estadistica
                  Icono={HeartHandshake}
                  valor={stats?.mascotas_adopcion ?? 0}
                  etiqueta="En adopción"
                  detalle={`${stats?.solicitudes_pendientes ?? 0} solicitudes por revisar`}
                />
                <Estadistica
                  Icono={Package}
                  valor={formatearPrecio(stats?.ingresos_totales ?? stats?.total_ventas ?? 0)}
                  etiqueta="Ventas de la tienda"
                  detalle={stats?.stock_bajo ? `${stats.stock_bajo} ${stats.stock_bajo === 1 ? 'producto' : 'productos'} con stock bajo` : undefined}
                />
              </>
            )}
          </div>
        </div>

        <div className="lg:col-span-4 lg:border-l lg:border-white/15 lg:pl-6">
          <h2 className="mp-panel-titulo">Tu cuenta</h2>
          <ul className="space-y-2 text-sm text-white/90 mb-5">
            <li className="font-semibold">{currentUser.nombre} {currentUser.apellidos}</li>
            <li className="flex items-center gap-2"><Mail className="w-4 h-4 text-[#9dddf5]" />{currentUser.email}</li>
            {currentUser.telefono && (
              <li className="flex items-center gap-2"><Phone className="w-4 h-4 text-[#9dddf5]" />{currentUser.telefono}</li>
            )}
            {currentUser.especialidad && (
              <li className="flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-[#9dddf5]" />{currentUser.especialidad}</li>
            )}
          </ul>
          <div className="grid grid-cols-2 gap-2">
            {accesos.map(({ tab, texto, Icono }) => (
              <button key={tab} onClick={() => onNavigate(tab)} className="mp-btn mp-btn--fantasma mp-btn--sm justify-start whitespace-normal text-left">
                <Icono className="w-4 h-4 shrink-0" />
                {texto}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Próximas citas */}
      <section className="space-y-3">
        <div className="flex items-end justify-between gap-4">
          <h2 className="font-titulo text-xl font-semibold">Próximas citas</h2>
          <button onClick={() => onNavigate('citas')} className="mp-btn mp-btn--fantasma mp-btn--sm">
            Ver todas las citas
          </button>
        </div>

        {proximas.length === 0 ? (
          <div className="mp-panel text-sm text-white/85">
            {esCliente ? 'No tienes citas por venir.' : 'No hay citas por venir.'}{' '}
            <button onClick={() => onNavigate('citas')} className="font-semibold underline underline-offset-2">
              Pedir una cita
            </button>
          </div>
        ) : (
          <div className="mp-papel overflow-hidden">
            <div className="mp-desplazable">
              <table className="mp-tabla">
                <thead>
                  <tr>
                    <th>Mascota</th>
                    <th>Servicio</th>
                    <th>Veterinario</th>
                    <th>Fecha y hora</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {proximas.slice(0, 6).map((c) => (
                    <tr key={c.id}>
                      <td>
                        <div className="flex items-center gap-3">
                          <FotoMascota
                            nombre={c.mascota_nombre}
                            imagen={c.mascota_imagen}
                            especie={mascotas.find((m) => m.id === c.mascota_id)?.especie_nombre}
                            className="w-9 h-9 rounded-full shrink-0"
                            tamanoIcono="w-5 h-5"
                          />
                          <span className="font-semibold">{c.mascota_nombre}</span>
                        </div>
                      </td>
                      <td>{c.servicio_nombre}</td>
                      <td>{c.vet_nombre}</td>
                      <td className="whitespace-nowrap">{formatearFechaHora(c.fecha_hora)}</td>
                      <td><EstadoCita estado={c.estado} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </div>
  );
};
