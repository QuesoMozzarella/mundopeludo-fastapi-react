import React, { useState } from 'react';
import { Producto, User } from '../types';
import { 
  Package, 
  Plus, 
  AlertTriangle, 
  TrendingUp, 
  Search, 
  Edit3, 
  Trash2, 
  CheckCircle, 
  X, 
  RefreshCw 
} from 'lucide-react';

interface InventarioViewProps {
  productos: Producto[];
  currentUser: User;
  onCreateProducto: (data: Partial<Producto>) => Promise<void>;
  onUpdateProducto: (id: number, data: Partial<Producto>) => Promise<void>;
  onDeleteProducto: (id: number) => Promise<void>;
}

export const InventarioView: React.FC<InventarioViewProps> = ({
  productos,
  currentUser,
  onCreateProducto,
  onUpdateProducto,
  onDeleteProducto
}) => {
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editProduct, setEditProduct] = useState<Producto | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // New product state
  const [nombre, setNombre] = useState('');
  const [categoria, setCategoria] = useState('medicamento');
  const [marca, setMarca] = useState('');
  const [precio, setPrecio] = useState<number>(10000);
  const [descuento, setDescuento] = useState<number>(0);
  const [stock, setStock] = useState<number>(10);
  const [stockMinimo, setStockMinimo] = useState<number>(5);
  const [tipoAnimal, setTipoAnimal] = useState('ambos');
  const [unidadMedida, setUnidadMedida] = useState('unidad');
  const [peso, setPeso] = useState<number>(1);
  const [descripcion, setDescripcion] = useState('');
  const [imagenUrl, setImagenUrl] = useState('');

  const filteredProductos = productos.filter((p) => {
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        p.nombre.toLowerCase().includes(q) ||
        p.sku.toLowerCase().includes(q) ||
        p.categoria.toLowerCase().includes(q) ||
        (p.marca && p.marca.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const lowStockCount = productos.filter(p => p.stock <= p.stock_minimo).length;
  const outOfStockCount = productos.filter(p => p.stock === 0).length;

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      await onCreateProducto({
        nombre,
        categoria,
        marca,
        precio: Number(precio),
        descuento_porcentaje: Number(descuento),
        stock: Number(stock),
        stock_minimo: Number(stockMinimo),
        tipo_animal: tipoAnimal,
        unidad_medida: unidadMedida,
        peso: Number(peso),
        descripcion,
        imagen_url: imagenUrl || undefined
      });

      setModalOpen(false);
      setNombre('');
      setMarca('');
      setDescripcion('');
      setImagenUrl('');
    } catch (err: any) {
      alert(err.message || 'Error al guardar el producto');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editProduct) return;

    try {
      setIsSubmitting(true);
      await onUpdateProducto(editProduct.id, {
        nombre: editProduct.nombre,
        categoria: editProduct.categoria,
        marca: editProduct.marca,
        precio: Number(editProduct.precio),
        descuento_porcentaje: Number(editProduct.descuento_porcentaje),
        stock: Number(editProduct.stock),
        stock_minimo: Number(editProduct.stock_minimo),
        tipo_animal: editProduct.tipo_animal,
        unidad_medida: editProduct.unidad_medida,
        peso: Number(editProduct.peso),
        descripcion: editProduct.descripcion
      });

      setEditProduct(null);
    } catch (err: any) {
      alert(err.message || 'Error al actualizar el producto');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Control de Inventario y Farmacia
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Gestión de stock en tiempo real, alertas de abastecimiento y catálogo médico.
          </p>
        </div>

        <button
          id="btn-agregar-producto-inv"
          onClick={() => setModalOpen(true)}
          className="px-5 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-sm shadow-sm flex items-center justify-center gap-2 transition-colors self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Nuevo Producto</span>
        </button>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Total de Productos</div>
          <div className="text-3xl font-extrabold text-slate-900">{productos.length}</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Stock Bajo</div>
          <div className={`text-3xl font-extrabold ${lowStockCount > 0 ? 'text-amber-600' : 'text-slate-900'}`}>
            {lowStockCount}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Sin Stock (Agotados)</div>
          <div className={`text-3xl font-extrabold ${outOfStockCount > 0 ? 'text-red-600' : 'text-slate-900'}`}>
            {outOfStockCount}
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Unidades Vendidas</div>
          <div className="text-3xl font-extrabold text-emerald-600">
            {productos.reduce((acc, p) => acc + (p.total_vendidos || 0), 0)}
          </div>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          id="input-search-inventario"
          placeholder="Buscar producto por SKU, nombre o marca..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">SKU</th>
                <th className="px-4 py-3">Producto</th>
                <th className="px-4 py-3">Categoría</th>
                <th className="px-4 py-3">Precio</th>
                <th className="px-4 py-3">Stock Actual</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredProductos.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50/70 transition-colors">
                  <td className="px-4 py-3.5 font-mono font-bold text-slate-500">{p.sku}</td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-3">
                      <img 
                        src={p.imagen_url || "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=100&auto=format&fit=crop&q=80"} 
                        alt={p.nombre} 
                        className="w-8 h-8 rounded-lg object-cover border border-slate-200 shrink-0"
                      />
                      <div>
                        <div className="font-bold text-slate-900">{p.nombre}</div>
                        <div className="text-[11px] text-slate-400">{p.marca || 'Marca genérica'}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3.5 capitalize font-medium">{p.categoria}</td>
                  <td className="px-4 py-3.5 font-bold text-slate-900">
                    ${p.precio_final.toLocaleString('es-CL')}
                    {p.descuento_porcentaje > 0 && (
                      <span className="text-[10px] text-rose-600 block">-{p.descuento_porcentaje}%</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="font-bold text-sm">{p.stock}</span>
                    <span className="text-slate-400 text-[10px] block">Mínimo: {p.stock_minimo}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    {p.stock === 0 ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-100 text-red-800">
                        Agotado
                      </span>
                    ) : p.stock <= p.stock_minimo ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                        Bajo Stock
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                        Óptimo
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        id={`btn-edit-prod-${p.id}`}
                        onClick={() => setEditProduct(p)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100"
                        title="Editar Producto"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button
                        id={`btn-delete-prod-${p.id}`}
                        onClick={() => {
                          if (confirm(`¿Eliminar del inventario "${p.nombre}"?`)) {
                            onDeleteProducto(p.id);
                          }
                        }}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50"
                        title="Eliminar"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Nuevo Producto */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden my-8">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Package className="w-5 h-5 text-amber-400" />
                <h3 className="font-bold text-lg">Agregar Producto al Inventario</h3>
              </div>
              <button onClick={() => setModalOpen(false)} className="text-slate-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Nombre del Producto *
                  </label>
                  <input
                    type="text"
                    id="input-prod-nombre"
                    placeholder="Ej: Alimento Perro Adulto 15kg"
                    value={nombre}
                    onChange={(e) => setNombre(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Categoría *
                  </label>
                  <select
                    id="select-prod-categoria"
                    value={categoria}
                    onChange={(e) => setCategoria(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
                  >
                    <option value="medicamento">Medicamento</option>
                    <option value="alimento">Alimento</option>
                    <option value="accesorio">Accesorio</option>
                    <option value="juguete">Juguete</option>
                    <option value="higiene">Higiene</option>
                    <option value="suplemento">Suplemento</option>
                    <option value="antipulgas">Antipulgas</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Marca
                  </label>
                  <input
                    type="text"
                    id="input-prod-marca"
                    placeholder="Ej: Royal Canin, MSD..."
                    value={marca}
                    onChange={(e) => setMarca(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Precio ($ CLP) *
                  </label>
                  <input
                    type="number"
                    id="input-prod-precio"
                    min="1"
                    value={precio}
                    onChange={(e) => setPrecio(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Descuento (%)
                  </label>
                  <input
                    type="number"
                    id="input-prod-descuento"
                    min="0"
                    max="90"
                    value={descuento}
                    onChange={(e) => setDescuento(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Stock Inicial *
                  </label>
                  <input
                    type="number"
                    id="input-prod-stock"
                    min="0"
                    value={stock}
                    onChange={(e) => setStock(parseInt(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Stock Mínimo Alerta *
                  </label>
                  <input
                    type="number"
                    id="input-prod-stock-minimo"
                    min="1"
                    value={stockMinimo}
                    onChange={(e) => setStockMinimo(parseInt(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Descripción
                </label>
                <textarea
                  id="textarea-prod-descripcion"
                  rows={2}
                  placeholder="Detalles sobre dosis, composición, raza o modo de uso..."
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 resize-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  URL de Imagen (Opcional)
                </label>
                <input
                  type="url"
                  id="input-prod-imagen"
                  placeholder="https://..."
                  value={imagenUrl}
                  onChange={(e) => setImagenUrl(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-sm font-semibold hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  id="btn-submit-nuevo-prod"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-sm font-bold shadow-md disabled:opacity-50"
                >
                  {isSubmitting ? 'Guardando...' : 'Crear Producto'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Editar Producto */}
      {editProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden my-8">
            <div className="bg-slate-900 text-white px-6 py-4 flex items-center justify-between">
              <h3 className="font-bold text-lg">Actualizar Stock y Precio</h3>
              <button onClick={() => setEditProduct(null)} className="text-slate-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleEditSubmit} className="p-6 space-y-4">
              <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl">
                <div className="font-bold text-slate-900">{editProduct.nombre}</div>
                <div className="font-mono text-slate-500">SKU: {editProduct.sku}</div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Precio ($ CLP)
                  </label>
                  <input
                    type="number"
                    value={editProduct.precio}
                    onChange={(e) => setEditProduct({ ...editProduct, precio: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Descuento (%)
                  </label>
                  <input
                    type="number"
                    value={editProduct.descuento_porcentaje}
                    onChange={(e) => setEditProduct({ ...editProduct, descuento_porcentaje: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Stock Físico
                  </label>
                  <input
                    type="number"
                    value={editProduct.stock}
                    onChange={(e) => setEditProduct({ ...editProduct, stock: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Stock Mínimo
                  </label>
                  <input
                    type="number"
                    value={editProduct.stock_minimo}
                    onChange={(e) => setEditProduct({ ...editProduct, stock_minimo: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl border border-slate-300 text-sm"
                    required
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditProduct(null)}
                  className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-sm font-semibold hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-sm font-bold shadow-md disabled:opacity-50"
                >
                  {isSubmitting ? 'Guardando...' : 'Actualizar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
