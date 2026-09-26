import React, { useState } from 'react';
import { AlertCircle, ArrowLeft, CheckCircle2, KeyRound, LogIn, UserPlus } from 'lucide-react';
import { Sesion } from '../types';
import {
  loginUser,
  registerUser,
  restablecerPassword,
  solicitarCodigoRecuperacion
} from '../api';

type Modo = 'acceso' | 'registro' | 'recuperar' | 'restablecer';

interface LoginViewProps {
  onSesionIniciada: (sesion: Sesion) => void;
  /** Mensaje al volver aquí por una sesión caducada. */
  aviso?: string | null;
  /** Vuelve a la página de inicio pública. */
  onVolver?: () => void;
}

const estiloCampo =
  'w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#1d95c8] bg-white';
const estiloEtiqueta = 'block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5';
const estiloBoton =
  'w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[#ff9f43] hover:bg-[#f08e30] text-white text-sm font-bold shadow-sm transition-all active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed';

export const LoginView: React.FC<LoginViewProps> = ({ onSesionIniciada, aviso, onVolver }) => {
  const [modo, setModo] = useState<Modo>('acceso');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmacion, setConfirmacion] = useState('');
  const [nombre, setNombre] = useState('');
  const [apellidos, setApellidos] = useState('');
  const [telefono, setTelefono] = useState('');
  const [codigo, setCodigo] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [exito, setExito] = useState<string | null>(aviso ?? null);
  const [enviando, setEnviando] = useState(false);

  const cambiarModo = (nuevo: Modo) => {
    setModo(nuevo);
    setError(null);
    setExito(null);
    setPassword('');
    setConfirmacion('');
  };

  const ejecutar = async (accion: () => Promise<void>) => {
    setError(null);
    setEnviando(true);
    try {
      await accion();
    } catch (err: any) {
      setError(err?.message || 'No se pudo completar la operación');
    } finally {
      setEnviando(false);
    }
  };

  const enviarAcceso = (e: React.FormEvent) => {
    e.preventDefault();
    ejecutar(async () => {
      onSesionIniciada(await loginUser(email.trim(), password));
    });
  };

  const enviarRegistro = (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmacion) {
      setError('Las contraseñas no coinciden');
      return;
    }
    ejecutar(async () => {
      onSesionIniciada(
        await registerUser({
          email: email.trim(),
          password,
          nombre: nombre.trim(),
          apellidos: apellidos.trim(),
          telefono: telefono.trim() || undefined
        })
      );
    });
  };

  const enviarRecuperacion = (e: React.FormEvent) => {
    e.preventDefault();
    ejecutar(async () => {
      const r = await solicitarCodigoRecuperacion(email.trim());
      setModo('restablecer');
      // `codigo_debug` sólo llega en desarrollo, cuando no hay correo configurado.
      setExito(
        r.codigo_debug
          ? `${r.detail}. Código (modo desarrollo): ${r.codigo_debug}`
          : `${r.detail}. Revisa tu bandeja de entrada.`
      );
    });
  };

  const enviarRestablecimiento = (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmacion) {
      setError('Las contraseñas no coinciden');
      return;
    }
    ejecutar(async () => {
      await restablecerPassword(email.trim(), codigo.trim(), password);
      cambiarModo('acceso');
      setExito('Contraseña actualizada. Ya puedes iniciar sesión.');
    });
  };

  const titulos: Record<Modo, string> = {
    acceso: 'Iniciar sesión',
    registro: 'Crear una cuenta',
    recuperar: 'Recuperar contraseña',
    restablecer: 'Nueva contraseña'
  };

  return (
    <div className="min-h-screen bg-[#f7fbfe] flex flex-col items-center justify-center px-4 py-10">
      <div className="flex items-center gap-3 mb-6 select-none">
        <img
          src="/img/logo.jpg"
          alt="Logo Mundo Peludo"
          className="w-12 h-12 rounded-full border-2 border-[#1d95c8] object-cover shadow-sm"
          onError={(e) => {
            (e.currentTarget as HTMLElement).style.display = 'none';
          }}
        />
        <div>
          <div className="text-2xl font-extrabold tracking-tight text-[#156a8e]">
            Mundo <span className="text-[#1d95c8]">Peludo</span>
          </div>
          <p className="text-xs font-medium text-slate-500 -mt-1 tracking-wide">Clínica Veterinaria</p>
        </div>
      </div>

      <div className="w-full max-w-md bg-white rounded-2xl shadow-md border border-slate-200 overflow-hidden">
        {(modo === 'acceso' || modo === 'registro') && (
          <div className="grid grid-cols-2 border-b border-slate-200 text-sm font-bold">
            <button
              id="tab-acceso"
              type="button"
              onClick={() => cambiarModo('acceso')}
              className={`py-3 transition-colors ${modo === 'acceso' ? 'text-[#156a8e] border-b-2 border-[#1d95c8] bg-sky-50/60' : 'text-slate-500 hover:text-[#156a8e]'}`}
            >
              Iniciar sesión
            </button>
            <button
              id="tab-registro"
              type="button"
              onClick={() => cambiarModo('registro')}
              className={`py-3 transition-colors ${modo === 'registro' ? 'text-[#156a8e] border-b-2 border-[#1d95c8] bg-sky-50/60' : 'text-slate-500 hover:text-[#156a8e]'}`}
            >
              Crear cuenta
            </button>
          </div>
        )}

        <div className="p-6 space-y-4">
          <h1 className="text-lg font-extrabold text-[#1d4f60]">{titulos[modo]}</h1>

          {exito && (
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-px" />
              <span>{exito}</span>
            </div>
          )}
          {error && (
            <div role="alert" className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-px" />
              <span>{error}</span>
            </div>
          )}

          {modo === 'acceso' && (
            <form onSubmit={enviarAcceso} className="space-y-4">
              <div>
                <label htmlFor="login-email" className={estiloEtiqueta}>Correo</label>
                <input id="login-email" type="email" autoComplete="email" required
                  value={email} onChange={(e) => setEmail(e.target.value)} className={estiloCampo} />
              </div>
              <div>
                <label htmlFor="login-password" className={estiloEtiqueta}>Contraseña</label>
                <input id="login-password" type="password" autoComplete="current-password" required
                  value={password} onChange={(e) => setPassword(e.target.value)} className={estiloCampo} />
              </div>
              <button id="btn-login" type="submit" disabled={enviando} className={estiloBoton}>
                <LogIn className="w-4 h-4" />
                {enviando ? 'Entrando…' : 'Entrar'}
              </button>
              <button type="button" onClick={() => cambiarModo('recuperar')}
                className="w-full text-xs font-semibold text-[#1d95c8] hover:text-[#156a8e] hover:underline">
                ¿Olvidaste tu contraseña?
              </button>
            </form>
          )}

          {modo === 'registro' && (
            <form onSubmit={enviarRegistro} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="reg-nombre" className={estiloEtiqueta}>Nombre</label>
                  <input id="reg-nombre" type="text" autoComplete="given-name" required minLength={2}
                    value={nombre} onChange={(e) => setNombre(e.target.value)} className={estiloCampo} />
                </div>
                <div>
                  <label htmlFor="reg-apellidos" className={estiloEtiqueta}>Apellidos</label>
                  <input id="reg-apellidos" type="text" autoComplete="family-name" required minLength={2}
                    value={apellidos} onChange={(e) => setApellidos(e.target.value)} className={estiloCampo} />
                </div>
              </div>
              <div>
                <label htmlFor="reg-email" className={estiloEtiqueta}>Correo</label>
                <input id="reg-email" type="email" autoComplete="email" required
                  value={email} onChange={(e) => setEmail(e.target.value)} className={estiloCampo} />
              </div>
              <div>
                <label htmlFor="reg-telefono" className={estiloEtiqueta}>Teléfono (opcional)</label>
                <input id="reg-telefono" type="tel" autoComplete="tel"
                  value={telefono} onChange={(e) => setTelefono(e.target.value)} className={estiloCampo} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="reg-password" className={estiloEtiqueta}>Contraseña</label>
                  <input id="reg-password" type="password" autoComplete="new-password" required minLength={8}
                    value={password} onChange={(e) => setPassword(e.target.value)} className={estiloCampo} />
                </div>
                <div>
                  <label htmlFor="reg-confirmacion" className={estiloEtiqueta}>Repetir</label>
                  <input id="reg-confirmacion" type="password" autoComplete="new-password" required minLength={8}
                    value={confirmacion} onChange={(e) => setConfirmacion(e.target.value)} className={estiloCampo} />
                </div>
              </div>
              <p className="text-[11px] text-slate-500">Mínimo 8 caracteres y no sólo números.</p>
              <button id="btn-registro" type="submit" disabled={enviando} className={estiloBoton}>
                <UserPlus className="w-4 h-4" />
                {enviando ? 'Creando cuenta…' : 'Crear cuenta'}
              </button>
            </form>
          )}

          {modo === 'recuperar' && (
            <form onSubmit={enviarRecuperacion} className="space-y-4">
              <p className="text-xs text-slate-600">
                Te enviaremos un código de 6 dígitos al correo de tu cuenta. Caduca en 1 hora.
              </p>
              <div>
                <label htmlFor="rec-email" className={estiloEtiqueta}>Correo</label>
                <input id="rec-email" type="email" autoComplete="email" required
                  value={email} onChange={(e) => setEmail(e.target.value)} className={estiloCampo} />
              </div>
              <button type="submit" disabled={enviando} className={estiloBoton}>
                <KeyRound className="w-4 h-4" />
                {enviando ? 'Enviando…' : 'Enviar código'}
              </button>
              <button type="button" onClick={() => cambiarModo('acceso')}
                className="w-full text-xs font-semibold text-slate-500 hover:text-[#156a8e]">
                Volver a iniciar sesión
              </button>
            </form>
          )}

          {modo === 'restablecer' && (
            <form onSubmit={enviarRestablecimiento} className="space-y-4">
              <div>
                <label htmlFor="res-codigo" className={estiloEtiqueta}>Código de 6 dígitos</label>
                <input id="res-codigo" type="text" inputMode="numeric" autoComplete="one-time-code"
                  required pattern="\d{6}" maxLength={6}
                  value={codigo} onChange={(e) => setCodigo(e.target.value)}
                  className={`${estiloCampo} tracking-[0.4em] font-mono text-center`} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="res-password" className={estiloEtiqueta}>Nueva contraseña</label>
                  <input id="res-password" type="password" autoComplete="new-password" required minLength={8}
                    value={password} onChange={(e) => setPassword(e.target.value)} className={estiloCampo} />
                </div>
                <div>
                  <label htmlFor="res-confirmacion" className={estiloEtiqueta}>Repetir</label>
                  <input id="res-confirmacion" type="password" autoComplete="new-password" required minLength={8}
                    value={confirmacion} onChange={(e) => setConfirmacion(e.target.value)} className={estiloCampo} />
                </div>
              </div>
              <button type="submit" disabled={enviando} className={estiloBoton}>
                <KeyRound className="w-4 h-4" />
                {enviando ? 'Guardando…' : 'Cambiar contraseña'}
              </button>
              <button type="button" onClick={() => cambiarModo('recuperar')}
                className="w-full text-xs font-semibold text-slate-500 hover:text-[#156a8e]">
                Pedir otro código
              </button>
            </form>
          )}
        </div>
      </div>

      {onVolver && (
        <button
          id="btn-volver-inicio"
          type="button"
          onClick={onVolver}
          className="mt-5 inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-[#156a8e]"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Volver al inicio
        </button>
      )}
    </div>
  );
};
