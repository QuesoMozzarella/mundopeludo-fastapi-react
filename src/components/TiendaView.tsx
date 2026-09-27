import React, { useState } from 'react';
import { Producto, User } from '../types';
import { formatearPrecio } from '../formato';
import { Encabezado, ImagenProducto, Modal, Vacio, useInterfaz } from './ui';
import { Check, Plus, Search, ShoppingBag, ShoppingCart } from 'lucide-react';

interface TiendaViewProps {
  productos: Producto[];
  onAddToCart: (producto: Producto) => void;
  currentUser: User | null;
  onOpenCart: () => void;
}

const CATEGORIAS: Record<string, string> = {
  alimento: 'Alimentos',
  medicamento: 'Medicamentos',
  antipulgas: 'Antipulgas',
  desparasitante: 'Desparasitantes',
  suplemento: 'Suplementos',
  higiene: 'Higiene',
  accesorio: 'Accesorios',
  juguete: 'Juguetes'
};

const ANIMALES = [
  { id: 'todos', nombre: 'Todas las especies' },
  { id: 'perro', nombre: 'Perros' },
  { id: 'gato', nombre: 'Gatos' }
];

export const TiendaView: React.FC<TiendaViewProps> = ({ productos, onAddToCart, onOpenCart }) => {
  const { avisar } = useInterfaz();
  const [categoria, setCategoria] = useState<string>('todas');
  const [tipoAnimal, setTipoAnimal] = useState<string>('todos');
  const [search, setSearch] = useState<string>('');
  const [seleccionado, setSeleccionado] = useState<Producto | null>(null);
  const [recienAnadidos, setRecienAnadidos] = useState<{ [id: number]: boolean }>({});

  const categoriasConProductos = Object.keys(CATEGORIAS).filter((c) => productos.some((p) => p.categoria === c));

  const filtrados = productos.filter((p) => {
    if (categoria !== 'todas' && p.categoria !== categoria) return false;
    if (tipoAnimal !== 'todos' && ![tipoAnimal, 'ambos', 'todos'].includes(p.tipo_animal)) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return [p.nombre, p.descripcion, p.marca].some((t) => (t || '').toLowerCase().includes(q));
  });

  const anadir = (p: Producto) => {
    onAddToCart(p);
    avisar(`${p.nombre} añadido al carrito.`);
    setRecienAnadidos((m) => ({ ...m, [p.id]: true }));
    window.setTimeout(() => setRecienAnadidos((m) => ({ ...m, [p.id]: false })), 1500);
  };

  const limpiarFiltros = () => {
    setCategoria('todas');
    setTipoAnimal('todos');
    setSearch('');
  };

  return (
    <div className="space-y-6">
      <Encabezado
        titulo="Farmacia y tienda"
        descripcion="Alimentos, antiparasitarios, medicamentos y accesorios para tu mascota."
      >
        <button id="btn-ver-carrito-tienda" onClick={onOpenCart} className="mp-btn mp-btn--claro">
          <ShoppingCart className="w-4 h-4" />
          Ver carrito
        </button>
      </Encabezado>

      <div className="space-y-3">
        <div className="flex flex-col md:flex-row md:items-center gap-3">
          <div className="mp-buscador w-full md:w-96">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" aria-hidden />
            <label htmlFor="input-search-tienda" className="sr-only">Buscar productos</label>
            <input
              type="search"
              id="input-search-tienda"
              placeholder="Nombre o marca"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="mp-campo"
            />
          </div>
          <div role="group" aria-label="Especie" className="flex flex-wrap gap-2">
            {ANIMALES.map((a) => (
              <button key={a.id} onClick={() => setTipoAnimal(a.id)} aria-pressed={tipoAnimal === a.id} className="mp-filtro">
                {a.nombre}
              </button>
            ))}
          </div>
        </div>
        {categoriasConProductos.length > 1 && (
          <div role="group" aria-label="Categoría" className="flex flex-wrap gap-2">
            <button id="filter-cat-todas" onClick={() => setCategoria('todas')} aria-pressed={categoria === 'todas'} className="mp-filtro">
              Todo
            </button>
            {categoriasConProductos.map((c) => (
              <button key={c} id={`filter-cat-${c}`} onClick={() => setCategoria(c)} aria-pressed={categoria === c} className="mp-filtro">
                {CATEGORIAS[c]}
              </button>
            ))}
          </div>
        )}
      </div>

      {productos.length === 0 ? (
        <Vacio icono={ShoppingBag} titulo="La tienda todavía no tiene productos" texto="Pronto podrás comprar aquí alimentos, antiparasitarios y medicamentos." />
      ) : filtrados.length === 0 ? (
        <Vacio icono={ShoppingBag} titulo="Ningún producto coincide" texto="Prueba con otra búsqueda o quita los filtros.">
          <button onClick={limpiarFiltros} className="mp-btn mp-btn--claro">Quitar filtros</button>
        </Vacio>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {filtrados.map((p) => {
            const agotado = p.stock <= 0;
            const anadido = recienAnadidos[p.id];
            return (
              <article key={p.id} className="mp-papel-blanco overflow-hidden flex flex-col">
                <button onClick={() => setSeleccionado(p)} className="relative block text-left" aria-label={`Ver detalles de ${p.nombre}`}>
                  <ImagenProducto nombre={p.nombre} imagen={p.imagen_url} categoria={p.categoria} className="w-full h-36 sm:h-44" tamanoIcono="w-12 h-12" />
                  {p.descuento_porcentaje > 0 && (
                    <span className="mp-pill mp-pill--peligro absolute top-2.5 left-2.5">-{p.descuento_porcentaje}%</span>
                  )}
                </button>
                <div className="p-4 flex-1 flex flex-col gap-2">
                  <p className="text-xs text-slate-500">{p.marca || CATEGORIAS[p.categoria] || p.categoria}</p>
                  <h2 className="text-sm sm:text-base font-semibold text-[#1d4f60] leading-snug line-clamp-2">
                    <button onClick={() => setSeleccionado(p)} className="text-left hover:underline underline-offset-2">{p.nombre}</button>
                  </h2>
                  <div className="mt-auto flex items-baseline gap-2 flex-wrap">
                    <span className="text-lg font-bold text-[#2c3e50]">{formatearPrecio(p.precio_final)}</span>
                    {p.descuento_porcentaje > 0 && <span className="text-xs text-slate-400 line-through">{formatearPrecio(p.precio)}</span>}
                  </div>
                  <p className={`text-xs ${agotado ? 'text-[#b92b39]' : p.stock <= 3 ? 'text-[#b8650f]' : 'text-slate-500'}`}>
                    {agotado ? 'Agotado' : p.stock <= 3 ? `Quedan ${p.stock}` : 'Disponible'}
                  </p>
                  <button
                    id={`btn-add-cart-${p.id}`}
                    disabled={agotado}
                    onClick={() => anadir(p)}
                    className={`mp-btn mp-btn--sm w-full ${anadido ? 'mp-btn--exito' : 'mp-btn--primario'}`}
                  >
                    {anadido ? <Check className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                    {agotado ? 'Agotado' : anadido ? 'Añadido' : 'Añadir al carrito'}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {seleccionado && (
        <Modal titulo={seleccionado.nombre} onCerrar={() => setSeleccionado(null)}>
          <ImagenProducto nombre={seleccionado.nombre} imagen={seleccionado.imagen_url} categoria={seleccionado.categoria} className="w-full h-56" tamanoIcono="w-20 h-20" />
          <div className="p-6 space-y-4">
            <p className="text-sm text-slate-500">
              {[CATEGORIAS[seleccionado.categoria] || seleccionado.categoria, seleccionado.marca].filter(Boolean).join(' · ')}
            </p>
            {seleccionado.descripcion && <p className="text-sm text-slate-700 leading-relaxed">{seleccionado.descripcion}</p>}
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-[#f3f7fa] rounded-lg p-3">
                <dt className="text-xs text-slate-500">Para</dt>
                <dd className="font-semibold capitalize">{['ambos', 'todos'].includes(seleccionado.tipo_animal) ? 'Perros y gatos' : seleccionado.tipo_animal}</dd>
              </div>
              <div className="bg-[#f3f7fa] rounded-lg p-3">
                <dt className="text-xs text-slate-500">Presentación</dt>
                <dd className="font-semibold capitalize">{seleccionado.unidad_medida}</dd>
              </div>
            </dl>
            <div className="flex items-center justify-between gap-4 pt-4 border-t border-slate-200">
              <div>
                <p className="text-2xl font-bold">{formatearPrecio(seleccionado.precio_final)}</p>
                {seleccionado.descuento_porcentaje > 0 && (
                  <p className="text-xs text-slate-500">Antes {formatearPrecio(seleccionado.precio)}</p>
                )}
              </div>
              <button
                onClick={() => {
                  anadir(seleccionado);
                  setSeleccionado(null);
                }}
                disabled={seleccionado.stock <= 0}
                className="mp-btn mp-btn--primario"
              >
                <Plus className="w-4 h-4" />
                Añadir al carrito
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
