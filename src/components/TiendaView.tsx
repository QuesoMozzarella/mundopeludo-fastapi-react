import React, { useState } from 'react';
import { Producto, User } from '../types';
import { 
  ShoppingBag, 
  Search, 
  Filter, 
  Plus, 
  Check, 
  Tag, 
  Info, 
  AlertTriangle,
  X 
} from 'lucide-react';

interface TiendaViewProps {
  productos: Producto[];
  onAddToCart: (producto: Producto) => void;
  currentUser: User | null;
  onOpenCart: () => void;
}

export const TiendaView: React.FC<TiendaViewProps> = ({
  productos,
  onAddToCart,
  currentUser,
  onOpenCart
}) => {
  const [categoria, setCategoria] = useState<string>('todas');
  const [tipoAnimal, setTipoAnimal] = useState<string>('todos');
  const [search, setSearch] = useState<string>('');
  const [selectedProduct, setSelectedProduct] = useState<Producto | null>(null);
  const [addedItemMap, setAddedItemMap] = useState<{ [id: number]: boolean }>({});

  const categorias = [
    { id: 'todas', label: 'Todos' },
    { id: 'alimento', label: 'Alimentos' },
    { id: 'medicamento', label: 'Medicamentos' },
    { id: 'antipulgas', label: 'Antipulgas' },
    { id: 'suplemento', label: 'Suplementos' },
    { id: 'higiene', label: 'Higiene & Cuidado' },
    { id: 'accesorio', label: 'Accesorios' },
    { id: 'juguete', label: 'Juguetes' }
  ];

  const filteredProductos = productos.filter((p) => {
    if (categoria !== 'todas' && p.categoria !== categoria) {
      return false;
    }
    if (tipoAnimal !== 'todos' && p.tipo_animal !== tipoAnimal && p.tipo_animal !== 'ambos' && p.tipo_animal !== 'todos') {
      return false;
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      return (
        p.nombre.toLowerCase().includes(q) ||
        (p.descripcion && p.descripcion.toLowerCase().includes(q)) ||
        (p.marca && p.marca.toLowerCase().includes(q)) ||
        p.sku.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const handleAddClick = (p: Producto) => {
    onAddToCart(p);
    setAddedItemMap({ ...addedItemMap, [p.id]: true });
    setTimeout(() => {
      setAddedItemMap(prev => ({ ...prev, [p.id]: false }));
    }, 1200);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Farmacia y Tienda Veterinaria
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Alimentos terapéuticos certificados, antiparasitarios, medicamentos y accesorios de alta calidad.
          </p>
        </div>

        <button
          id="btn-ver-carrito-tienda"
          onClick={onOpenCart}
          className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm shadow-xs flex items-center justify-center gap-2 transition-colors self-start sm:self-auto"
        >
          <ShoppingBag className="w-4 h-4 text-amber-400" />
          <span>Abrir Carrito</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative w-full sm:w-96">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              id="input-search-tienda"
              placeholder="Buscar por nombre, principio activo, marca o SKU..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider shrink-0">Especie:</span>
            {['todos', 'perro', 'gato'].map((animal) => (
              <button
                key={animal}
                onClick={() => setTipoAnimal(animal)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold capitalize transition-colors ${tipoAnimal === animal ? 'bg-amber-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}
              >
                {animal}
              </button>
            ))}
          </div>
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar">
          {categorias.map((cat) => (
            <button
              key={cat.id}
              id={`filter-cat-${cat.id}`}
              onClick={() => setCategoria(cat.id)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${categoria === cat.id ? 'bg-slate-900 text-white shadow-2xs' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'}`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Products Grid */}
      {filteredProductos.length === 0 ? (
        <div className="bg-white rounded-3xl border border-dashed border-slate-300 p-16 text-center">
          <ShoppingBag className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">No encontramos productos en esta búsqueda</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-4">
            Intenta cambiar los términos de búsqueda o seleccionar otra categoría de productos.
          </p>
          <button
            onClick={() => { setCategoria('todas'); setTipoAnimal('todos'); setSearch(''); }}
            className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold"
          >
            Restablecer Filtros
          </button>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filteredProductos.map((p) => {
            const isAdded = addedItemMap[p.id];
            const isOutOfStock = p.stock <= 0;

            return (
              <div 
                key={p.id}
                className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between"
              >
                <div>
                  <div 
                    onClick={() => setSelectedProduct(p)}
                    className="w-full h-48 rounded-xl overflow-hidden bg-slate-100 mb-3 relative cursor-pointer group"
                  >
                    <img 
                      src={p.imagen_url || "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=500&auto=format&fit=crop&q=80"} 
                      alt={p.nombre} 
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    {p.descuento_porcentaje > 0 && (
                      <span className="absolute top-2.5 left-2.5 bg-rose-600 text-white text-[10px] font-extrabold px-2.5 py-0.5 rounded-full shadow-xs">
                        -{p.descuento_porcentaje}%
                      </span>
                    )}
                    <span className="absolute bottom-2.5 right-2.5 bg-slate-900/80 backdrop-blur-xs text-white text-[10px] font-mono px-2 py-0.5 rounded-md">
                      SKU: {p.sku}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                    <span>{p.marca || p.categoria}</span>
                    <span className={p.stock <= 3 ? 'text-amber-600 font-bold' : 'text-emerald-600'}>
                      {isOutOfStock ? 'Agotado' : p.stock <= 3 ? `¡Quedan ${p.stock}!` : `Stock: ${p.stock}`}
                    </span>
                  </div>

                  <h3 
                    onClick={() => setSelectedProduct(p)}
                    className="text-sm font-bold text-slate-900 line-clamp-2 mb-2 hover:text-amber-600 cursor-pointer transition-colors"
                  >
                    {p.nombre}
                  </h3>

                  <p className="text-xs text-slate-500 line-clamp-2 mb-4 leading-relaxed">
                    {p.descripcion}
                  </p>
                </div>

                <div>
                  <div className="flex items-baseline gap-2 mb-3">
                    <span className="text-lg font-extrabold text-slate-900">
                      ${p.precio_final.toLocaleString('es-CL')}
                    </span>
                    {p.descuento_porcentaje > 0 && (
                      <span className="text-xs text-slate-400 line-through">
                        ${p.precio.toLocaleString('es-CL')}
                      </span>
                    )}
                  </div>

                  <button
                    id={`btn-add-cart-${p.id}`}
                    disabled={isOutOfStock}
                    onClick={() => handleAddClick(p)}
                    className={`w-full py-2.5 px-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                      isOutOfStock 
                        ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                        : isAdded
                        ? 'bg-emerald-600 text-white shadow-xs'
                        : 'bg-amber-600 hover:bg-amber-700 text-white shadow-sm'
                    }`}
                  >
                    {isAdded ? (
                      <>
                        <Check className="w-4 h-4" />
                        <span>¡Agregado al Carrito!</span>
                      </>
                    ) : (
                      <>
                        <Plus className="w-4 h-4" />
                        <span>{isOutOfStock ? 'Sin Stock' : 'Añadir al Carrito'}</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal Detalle de Producto */}
      {selectedProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl shadow-2xl border border-slate-200 w-full max-w-lg overflow-hidden my-8">
            <div className="relative h-60 bg-slate-100">
              <img 
                src={selectedProduct.imagen_url || "https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=500&auto=format&fit=crop&q=80"} 
                alt={selectedProduct.nombre} 
                className="w-full h-full object-cover"
              />
              <button 
                onClick={() => setSelectedProduct(null)}
                className="absolute top-4 right-4 bg-black/60 text-white hover:bg-black/90 p-1.5 rounded-full"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold uppercase tracking-wider text-amber-600 bg-amber-50 px-2 py-0.5 rounded-md">
                    {selectedProduct.categoria}
                  </span>
                  <span className="text-xs text-slate-400 font-mono">SKU: {selectedProduct.sku}</span>
                </div>
                <h3 className="text-xl font-bold text-slate-900">{selectedProduct.nombre}</h3>
                <p className="text-xs text-slate-500 mt-0.5">Marca: <strong>{selectedProduct.marca || 'Genérica'}</strong></p>
              </div>

              <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-3.5 rounded-2xl border border-slate-100">
                {selectedProduct.descripcion}
              </p>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-50 p-2.5 rounded-xl">
                  <span className="text-slate-400 block font-medium">Tipo de Animal:</span>
                  <strong className="capitalize text-slate-800">{selectedProduct.tipo_animal}</strong>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-xl">
                  <span className="text-slate-400 block font-medium">Unidad de Medida:</span>
                  <strong className="capitalize text-slate-800">{selectedProduct.unidad_medida} ({selectedProduct.peso || 0} g/kg)</strong>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <div>
                  <span className="text-xs text-slate-400 block font-medium">Precio final:</span>
                  <span className="text-2xl font-extrabold text-slate-900">
                    ${selectedProduct.precio_final.toLocaleString('es-CL')}
                  </span>
                </div>

                <button
                  onClick={() => {
                    onAddToCart(selectedProduct);
                    setSelectedProduct(null);
                  }}
                  disabled={selectedProduct.stock <= 0}
                  className="px-6 py-3 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-sm font-bold shadow-md transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  <span>Añadir al Carrito</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
