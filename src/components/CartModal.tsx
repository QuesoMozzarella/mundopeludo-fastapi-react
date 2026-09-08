import React, { useState } from 'react';
import { CartItem, User } from '../types';
import { 
  ShoppingBag, 
  Trash2, 
  Plus, 
  Minus, 
  CreditCard, 
  Banknote, 
  Building2, 
  CheckCircle2, 
  X, 
  ArrowRight,
  ShieldCheck
} from 'lucide-react';

interface CartModalProps {
  isOpen: boolean;
  onClose: () => void;
  cartItems: CartItem[];
  onUpdateQuantity: (productoId: number, delta: number) => void;
  onRemoveItem: (productoId: number) => void;
  onClearCart: () => void;
  currentUser: User;
  onCheckout: (data: {
    items: { producto_id: number; cantidad: number }[];
    direccion_envio: string;
    metodo_pago: string;
  }) => Promise<any>;
}

export const CartModal: React.FC<CartModalProps> = ({
  isOpen,
  onClose,
  cartItems,
  onUpdateQuantity,
  onRemoveItem,
  onClearCart,
  currentUser,
  onCheckout
}) => {
  const [metodoPago, setMetodoPago] = useState<string>('tarjeta');
  const [direccion, setDireccion] = useState<string>(currentUser.direccion || 'Av. Providencia 1234, Santiago');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [orderCompleted, setOrderCompleted] = useState<any | null>(null);

  if (!isOpen) return null;

  const total = cartItems.reduce(
    (acc, item) => acc + item.producto.precio_final * item.cantidad, 
    0
  );

  const handlePay = async (e: React.FormEvent) => {
    e.preventDefault();
    if (cartItems.length === 0) return;

    try {
      setIsSubmitting(true);
      const itemsPayload = cartItems.map(item => ({
        producto_id: item.producto.id,
        cantidad: item.cantidad
      }));

      const res = await onCheckout({
        items: itemsPayload,
        direccion_envio: direccion,
        metodo_pago: metodoPago
      });

      setOrderCompleted(res);
      onClearCart();
    } catch (err: any) {
      alert(err.message || 'Error al procesar la compra.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-xl overflow-hidden my-8 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-[#1d4f60] text-white px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <ShoppingBag className="w-5 h-5 text-[#ff9f43]" />
            <h3 className="font-bold text-lg">Carrito de Compras</h3>
          </div>
          <button 
            onClick={onClose}
            className="text-sky-200 hover:text-white p-1 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {orderCompleted ? (
          /* Order Confirmation Screen */
          <div className="p-8 text-center space-y-4 my-auto">
            <div className="w-16 h-16 rounded-full bg-[#5dca88]/20 text-[#5dca88] flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-10 h-10" />
            </div>
            <h3 className="text-2xl font-extrabold text-[#156a8e]">¡Pedido Confirmado con Éxito!</h3>
            <p className="text-sm text-slate-600 max-w-md mx-auto">
              Tu orden ha sido registrada en el sistema de Mundo Peludo y descontada del inventario clínico en tiempo real.
            </p>
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 text-left text-xs max-w-md mx-auto space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">ID de Pedido:</span>
                <span className="font-mono font-bold">#PED-{orderCompleted.pedido_id || Math.floor(1000 + Math.random() * 9000)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Cliente:</span>
                <span className="font-semibold">{currentUser.nombre} {currentUser.apellidos}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Total Pagado:</span>
                <span className="font-bold text-[#1d95c8]">${orderCompleted.total?.toLocaleString('es-CL') || total.toLocaleString('es-CL')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Método de Pago:</span>
                <span className="capitalize font-medium">{metodoPago}</span>
              </div>
            </div>
            <button
              onClick={() => {
                setOrderCompleted(null);
                onClose();
              }}
              className="px-6 py-2.5 rounded-xl bg-[#1d95c8] hover:bg-[#156a8e] text-white font-bold text-xs transition-colors shadow-sm"
            >
              Cerrar y Continuar
            </button>
          </div>
        ) : (
          /* Cart Content */
          <div className="p-6 overflow-y-auto flex-1 space-y-6">
            {cartItems.length === 0 ? (
              <div className="text-center py-12">
                <ShoppingBag className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <h4 className="text-base font-bold text-slate-700">Tu carrito está vacío</h4>
                <p className="text-xs text-slate-400 mt-1">Explora nuestra farmacia y tienda de alimentos para añadir productos.</p>
              </div>
            ) : (
              <>
                {/* Items List */}
                <div className="divide-y divide-slate-100">
                  {cartItems.map((item) => (
                    <div key={item.producto.id} className="py-3 flex items-center justify-between gap-3">
                      <img 
                        src={item.producto.imagen_url || "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=100&auto=format&fit=crop&q=80"} 
                        alt={item.producto.nombre} 
                        className="w-12 h-12 rounded-xl object-cover border border-slate-200 shrink-0"
                      />
                      <div className="flex-1 min-w-0">
                        <h4 className="text-xs font-bold text-slate-900 truncate">{item.producto.nombre}</h4>
                        <div className="text-[11px] text-slate-500">
                          ${item.producto.precio_final.toLocaleString('es-CL')} c/u
                        </div>
                      </div>

                      {/* Quantity buttons */}
                      <div className="flex items-center gap-2 border border-slate-200 rounded-lg p-1">
                        <button
                          onClick={() => onUpdateQuantity(item.producto.id, -1)}
                          className="p-1 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded"
                        >
                          <Minus className="w-3 h-3" />
                        </button>
                        <span className="text-xs font-bold px-1">{item.cantidad}</span>
                        <button
                          onClick={() => onUpdateQuantity(item.producto.id, 1)}
                          className="p-1 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded"
                        >
                          <Plus className="w-3 h-3" />
                        </button>
                      </div>

                      {/* Item Total */}
                      <div className="text-right min-w-[70px]">
                        <span className="text-xs font-bold text-slate-900">
                          ${(item.producto.precio_final * item.cantidad).toLocaleString('es-CL')}
                        </span>
                      </div>

                      {/* Remove button */}
                      <button
                        onClick={() => onRemoveItem(item.producto.id)}
                        className="p-1.5 text-slate-400 hover:text-red-600 rounded-lg hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>

                {/* Shipping & Payment Form */}
                <form onSubmit={handlePay} className="space-y-4 pt-4 border-t border-slate-200">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Dirección de Despacho o Retiro en Clínica
                    </label>
                    <input
                      type="text"
                      id="input-cart-direccion"
                      value={direccion}
                      onChange={(e) => setDireccion(e.target.value)}
                      placeholder="Calle, número, depto / Retiro en clínica"
                      className="w-full px-3 py-2 rounded-xl border border-slate-300 text-xs focus:outline-none focus:ring-2 focus:ring-amber-500"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Método de Pago
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      <button
                        type="button"
                        onClick={() => setMetodoPago('tarjeta')}
                        className={`p-2.5 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 transition-all ${metodoPago === 'tarjeta' ? 'border-[#1d95c8] bg-[#e8f4f9] text-[#156a8e] shadow-2xs' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`}
                      >
                        <CreditCard className="w-4 h-4 text-[#1d95c8]" />
                        <span>Tarjeta</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setMetodoPago('efectivo')}
                        className={`p-2.5 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 transition-all ${metodoPago === 'efectivo' ? 'border-[#1d95c8] bg-[#e8f4f9] text-[#156a8e] shadow-2xs' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`}
                      >
                        <Banknote className="w-4 h-4 text-[#5dca88]" />
                        <span>Efectivo</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => setMetodoPago('transferencia')}
                        className={`p-2.5 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 transition-all ${metodoPago === 'transferencia' ? 'border-[#1d95c8] bg-[#e8f4f9] text-[#156a8e] shadow-2xs' : 'border-slate-200 text-slate-600 hover:bg-slate-50'}`}
                      >
                        <Building2 className="w-4 h-4 text-[#156a8e]" />
                        <span>Transferencia</span>
                      </button>
                    </div>
                  </div>

                  {/* Summary */}
                  <div className="bg-slate-50 p-4 rounded-2xl space-y-2 text-xs">
                    <div className="flex justify-between text-slate-600">
                      <span>Subtotal</span>
                      <span>${total.toLocaleString('es-CL')}</span>
                    </div>
                    <div className="flex justify-between text-slate-600">
                      <span>Despacho</span>
                      <span className="text-[#5dca88] font-semibold">Gratis</span>
                    </div>
                    <div className="flex justify-between text-base font-extrabold text-slate-900 pt-2 border-t border-slate-200">
                      <span>Total a Pagar</span>
                      <span>${total.toLocaleString('es-CL')}</span>
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    id="btn-confirmar-compra"
                    disabled={isSubmitting}
                    className="w-full py-3 rounded-xl bg-[#ff9f43] hover:bg-[#f08e30] text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2 disabled:opacity-50 active:scale-98"
                  >
                    <ShieldCheck className="w-4 h-4" />
                    <span>{isSubmitting ? 'Procesando Pago...' : `Pagar $${total.toLocaleString('es-CL')}`}</span>
                  </button>
                </form>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
