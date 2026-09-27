import React, { useState } from 'react';
import { CartItem, User } from '../types';
import { formatearPrecio } from '../formato';
import { ErrorFormulario, ImagenProducto, Modal } from './ui';
import { Banknote, Building2, CheckCircle2, CreditCard, Minus, Plus, ShoppingBag, Trash2 } from 'lucide-react';

interface CartModalProps {
  isOpen: boolean;
  onClose: () => void;
  cartItems: CartItem[];
  onUpdateQuantity: (productoId: number, delta: number) => void;
  onRemoveItem: (productoId: number) => void;
  onClearCart: () => void;
  /** null = visitante: puede llenar el carrito, pagar pide iniciar sesión. */
  currentUser: User | null;
  onRequiereLogin: () => void;
  onCheckout: (data: {
    items: { producto_id: number; cantidad: number }[];
    direccion_envio: string;
    metodo_pago: string;
  }) => Promise<any>;
}

const METODOS = [
  { id: 'tarjeta', nombre: 'Tarjeta', Icono: CreditCard },
  { id: 'efectivo', nombre: 'Efectivo', Icono: Banknote },
  { id: 'transferencia', nombre: 'Transferencia', Icono: Building2 }
];

export const CartModal: React.FC<CartModalProps> = ({
  isOpen,
  onClose,
  cartItems,
  onUpdateQuantity,
  onRemoveItem,
  onClearCart,
  currentUser,
  onRequiereLogin,
  onCheckout
}) => {
  const [metodoPago, setMetodoPago] = useState<string>('tarjeta');
  const [direccion, setDireccion] = useState<string>(currentUser?.direccion || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pedido, setPedido] = useState<{ pedido_id: number; total: number } | null>(null);

  if (!isOpen) return null;

  const total = cartItems.reduce((acc, item) => acc + item.producto.precio_final * item.cantidad, 0);
  const unidades = cartItems.reduce((acc, item) => acc + item.cantidad, 0);

  const cerrar = () => {
    setPedido(null);
    setError(null);
    onClose();
  };

  const pagar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (cartItems.length === 0) return;
    if (!currentUser) return onRequiereLogin();
    setError(null);
    try {
      setIsSubmitting(true);
      const res = await onCheckout({
        items: cartItems.map((item) => ({ producto_id: item.producto.id, cantidad: item.cantidad })),
        direccion_envio: direccion.trim(),
        metodo_pago: metodoPago
      });
      setPedido(res);
      onClearCart();
    } catch (err: any) {
      setError(err.message || 'No se pudo completar la compra.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal titulo={pedido ? 'Pedido confirmado' : 'Tu carrito'} icono={<ShoppingBag className="w-5 h-5 text-[#ff9f43]" />} onCerrar={cerrar} ancho="lg">
      {pedido ? (
        <div className="p-8 text-center space-y-4">
          <CheckCircle2 className="w-14 h-14 text-[#3aa76d] mx-auto" />
          <h3 className="font-titulo text-2xl font-semibold text-[#1d4f60]">Pedido #PED-{pedido.pedido_id} registrado</h3>
          <p className="text-sm text-slate-600 max-w-sm mx-auto">
            Lo verás en la clínica con tu nombre. Total: <strong>{formatearPrecio(pedido.total)}</strong>, pago con{' '}
            {METODOS.find((m) => m.id === metodoPago)?.nombre.toLowerCase()}.
          </p>
          <button onClick={cerrar} className="mp-btn mp-btn--azul">Seguir comprando</button>
        </div>
      ) : cartItems.length === 0 ? (
        <div className="p-10 text-center space-y-3">
          <ShoppingBag className="w-12 h-12 text-[#1d95c8] mx-auto" />
          <p className="font-semibold">Tu carrito está vacío</p>
          <p className="text-sm text-slate-500">Añade productos desde la tienda.</p>
          <button onClick={cerrar} className="mp-btn mp-btn--azul">Ir a la tienda</button>
        </div>
      ) : (
        <form onSubmit={pagar} className="p-6 space-y-5">
          <ErrorFormulario texto={error} />
          <ul className="divide-y divide-slate-200 max-h-72 overflow-y-auto -mx-2 px-2">
            {cartItems.map((item) => (
              <li key={item.producto.id} className="py-3 flex items-center gap-3">
                <ImagenProducto
                  nombre={item.producto.nombre}
                  imagen={item.producto.imagen_url}
                  categoria={item.producto.categoria}
                  className="w-14 h-14 rounded-lg shrink-0"
                  tamanoIcono="w-6 h-6"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold truncate">{item.producto.nombre}</p>
                  <p className="text-xs text-slate-500">{formatearPrecio(item.producto.precio_final)} c/u</p>
                </div>
                <div className="flex items-center gap-1" role="group" aria-label={`Cantidad de ${item.producto.nombre}`}>
                  <button type="button" onClick={() => onUpdateQuantity(item.producto.id, -1)} aria-label="Quitar uno" className="mp-accion mp-accion--neutro w-7 h-7">
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <span className="w-7 text-center text-sm font-semibold" aria-live="polite">{item.cantidad}</span>
                  <button
                    type="button"
                    onClick={() => onUpdateQuantity(item.producto.id, 1)}
                    disabled={item.cantidad >= item.producto.stock}
                    aria-label="Añadir uno"
                    className="mp-accion w-7 h-7 disabled:opacity-40"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
                <span className="w-20 text-right text-sm font-bold">{formatearPrecio(item.producto.precio_final * item.cantidad)}</span>
                <button type="button" onClick={() => onRemoveItem(item.producto.id)} aria-label={`Quitar ${item.producto.nombre}`} className="p-1.5 text-slate-400 hover:text-[#dc3545]">
                  <Trash2 className="w-4 h-4" />
                </button>
              </li>
            ))}
          </ul>

          <div>
            <label htmlFor="input-cart-direccion" className="mp-etiqueta">Dirección de entrega</label>
            <input
              id="input-cart-direccion"
              type="text"
              placeholder="Calle y número, o «Retiro en la clínica»"
              value={direccion}
              onChange={(e) => setDireccion(e.target.value)}
              className="mp-campo"
              required={Boolean(currentUser)}
            />
          </div>

          <fieldset>
            <legend className="mp-etiqueta">Forma de pago</legend>
            <div className="grid grid-cols-3 gap-2">
              {METODOS.map(({ id, nombre, Icono }) => (
                <label
                  key={id}
                  className={`flex flex-col items-center gap-1 p-3 rounded-lg border text-sm font-semibold cursor-pointer ${
                    metodoPago === id ? 'border-[#1d95c8] bg-[#e8f6fc] text-[#156a8e]' : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <input type="radio" name="metodo-pago" value={id} checked={metodoPago === id} onChange={() => setMetodoPago(id)} className="sr-only" />
                  <Icono className="w-5 h-5" />
                  {nombre}
                </label>
              ))}
            </div>
          </fieldset>

          <div className="flex items-center justify-between border-t border-slate-200 pt-4">
            <span className="text-sm text-slate-600">{unidades} {unidades === 1 ? 'producto' : 'productos'}</span>
            <span className="text-xl font-bold">Total {formatearPrecio(total)}</span>
          </div>

          <button type="submit" id="btn-confirmar-compra" disabled={isSubmitting} className="mp-btn mp-btn--primario w-full">
            {!currentUser ? 'Inicia sesión para pagar' : isSubmitting ? 'Procesando…' : `Confirmar compra por ${formatearPrecio(total)}`}
          </button>
        </form>
      )}
    </Modal>
  );
};
