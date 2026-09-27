import React, { useEffect, useState } from 'react';
import { Producto, User } from '../types';
import { TIPOS_IMAGEN, validarImagen } from '../api';
import { formatearPrecio } from '../formato';
import { Encabezado, ErrorFormulario, ImagenProducto, Modal, PieModal, Vacio, useInterfaz } from './ui';
import { AlertTriangle, ImagePlus, Package, Pencil, Plus, Search, Trash2 } from 'lucide-react';

const CATEGORIAS: [string, string][] = [
  ['medicamento', 'Medicamento'],
  ['alimento', 'Alimento'],
  ['antipulgas', 'Antipulgas'],
  ['desparasitante', 'Desparasitante'],
  ['suplemento', 'Suplemento'],
  ['higiene', 'Higiene'],
  ['accesorio', 'Accesorio'],
  ['juguete', 'Juguete']
];
const ANIMALES: [string, string][] = [
  ['ambos', 'Perros y gatos'],
  ['perro', 'Perros'],
  ['gato', 'Gatos'],
  ['ave', 'Aves'],
  ['roedor', 'Roedores'],
  ['reptil', 'Reptiles'],
  ['todos', 'Todas las especies']
];
const UNIDADES: [string, string][] = [
  ['unidad', 'Unidad'],
  ['caja', 'Caja'],
  ['sobre', 'Sobre'],
  ['kg', 'Kilogramos'],
  ['gr', 'Gramos'],
  ['lt', 'Litros'],
  ['ml', 'Mililitros']
];

// ---------------------------------------------------------------------------
// Foto del producto: archivo validado como en la API, con vista previa.
// ---------------------------------------------------------------------------
interface SelectorImagenProps {
  id: string;
  /** Imagen que ya tiene el producto (al editar). */
  actual?: string;
  archivo: File | null;
  onCambio: (archivo: File | null) => void;
}

const SelectorImagen: React.FC<SelectorImagenProps> = ({ id, actual, archivo, onCambio }) => {
  const [error, setError] = useState<string | null>(null);
  const [previa, setPrevia] = useState<string | null>(null);

  useEffect(() => {
    if (!archivo) {
      setPrevia(null);
      return;
    }
    const url = URL.createObjectURL(archivo);
    setPrevia(url);
    return () => URL.revokeObjectURL(url);
  }, [archivo]);

  const alElegir = (e: React.ChangeEvent<HTMLInputElement>) => {
    const elegido = e.target.files?.[0] ?? null;
    e.target.value = ''; // permite volver a elegir el mismo archivo
    if (!elegido) return;
    const problema = validarImagen(elegido);
    setError(problema);
    onCambio(problema ? null : elegido);
  };

  const mostrada = previa || actual;

  return (
    <div>
      <p className="mp-etiqueta">Foto (opcional)</p>
      <div className="flex items-center gap-3">
        <div className="w-16 h-16 rounded-lg border border-slate-200 bg-[#f3f7fa] overflow-hidden shrink-0 flex items-center justify-center">
          {mostrada ? (
            <img id={`${id}-previa`} src={mostrada} alt="Vista previa" className="w-full h-full object-cover" />
          ) : (
            <ImagePlus className="w-6 h-6 text-slate-400" />
          )}
        </div>
        <div className="flex-1 min-w-0 space-y-1">
          <label htmlFor={id} className="mp-btn mp-btn--borde mp-btn--sm cursor-pointer">
            <ImagePlus className="w-4 h-4" />
            {mostrada ? 'Cambiar foto' : 'Elegir foto'}
          </label>
          <input type="file" id={id} accept={TIPOS_IMAGEN.join(',')} onChange={alElegir} className="sr-only" />
          {archivo ? (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="truncate">{archivo.name}</span>
              <button type="button" onClick={() => onCambio(null)} className="font-semibold hover:text-[#b92b39] shrink-0">
                Quitar
              </button>
            </div>
          ) : (
            <p className="mp-ayuda mt-0">JPG, PNG, WEBP o GIF, hasta 5 MB.</p>
          )}
          {error && <p role="alert" className="text-xs font-semibold text-[#b92b39]">{error}</p>}
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Campos comunes al alta y a la edición.
// ---------------------------------------------------------------------------
type DatosProducto = {
  nombre: string;
  categoria: string;
  marca: string;
  precio: number;
  descuento_porcentaje: number;
  stock: number;
  stock_minimo: number;
  tipo_animal: string;
  unidad_medida: string;
  descripcion: string;
};

const VACIO: DatosProducto = {
  nombre: '',
  categoria: 'medicamento',
  marca: '',
  precio: 10000,
  descuento_porcentaje: 0,
  stock: 10,
  stock_minimo: 5,
  tipo_animal: 'ambos',
  unidad_medida: 'unidad',
  descripcion: ''
};

function aDatos(p: Producto): DatosProducto {
  return {
    nombre: p.nombre,
    categoria: p.categoria,
    marca: p.marca || '',
    precio: p.precio,
    descuento_porcentaje: p.descuento_porcentaje,
    stock: p.stock,
    stock_minimo: p.stock_minimo,
    tipo_animal: p.tipo_animal,
    unidad_medida: p.unidad_medida,
    descripcion: p.descripcion || ''
  };
}

function CamposProducto({ datos, cambiar, prefijo }: {
  datos: DatosProducto;
  cambiar: (parcial: Partial<DatosProducto>) => void;
  /** "prod" en el alta, "edit-prod" en la edición (ids de las pruebas). */
  prefijo: 'prod' | 'edit-prod';
}) {
  const num = (v: string) => (v === '' ? 0 : Number(v));
  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="col-span-2">
        <label htmlFor={`input-${prefijo}-nombre`} className="mp-etiqueta">Nombre</label>
        <input id={`input-${prefijo}-nombre`} type="text" required minLength={2} placeholder="Alimento perro adulto 15 kg" value={datos.nombre} onChange={(e) => cambiar({ nombre: e.target.value })} className="mp-campo" />
      </div>
      <div>
        <label htmlFor={`select-${prefijo}-categoria`} className="mp-etiqueta">Categoría</label>
        <select id={`select-${prefijo}-categoria`} value={datos.categoria} onChange={(e) => cambiar({ categoria: e.target.value })} className="mp-campo">
          {CATEGORIAS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
        </select>
      </div>
      <div>
        <label htmlFor={`input-${prefijo}-marca`} className="mp-etiqueta">Marca</label>
        <input id={`input-${prefijo}-marca`} type="text" value={datos.marca} onChange={(e) => cambiar({ marca: e.target.value })} className="mp-campo" />
      </div>
      <div>
        <label htmlFor={`input-${prefijo}-precio`} className="mp-etiqueta">Precio ($)</label>
        <input id={`input-${prefijo}-precio`} type="number" min="0" required value={datos.precio} onChange={(e) => cambiar({ precio: num(e.target.value) })} className="mp-campo" />
      </div>
      <div>
        <label htmlFor={`input-${prefijo}-descuento`} className="mp-etiqueta">Descuento (%)</label>
        <input id={`input-${prefijo}-descuento`} type="number" min="0" max="90" value={datos.descuento_porcentaje} onChange={(e) => cambiar({ descuento_porcentaje: num(e.target.value) })} className="mp-campo" />
      </div>
      <div>
        <label htmlFor={`input-${prefijo}-stock`} className="mp-etiqueta">Stock</label>
        <input id={`input-${prefijo}-stock`} type="number" min="0" required value={datos.stock} onChange={(e) => cambiar({ stock: num(e.target.value) })} className="mp-campo" />
      </div>
      <div>
        <label htmlFor={`input-${prefijo}-stock-minimo`} className="mp-etiqueta">Avisar con menos de</label>
        <input id={`input-${prefijo}-stock-minimo`} type="number" min="0" required value={datos.stock_minimo} onChange={(e) => cambiar({ stock_minimo: num(e.target.value) })} className="mp-campo" />
      </div>
      <div>
        <label htmlFor={`select-${prefijo}-animal`} className="mp-etiqueta">Para</label>
        <select id={`select-${prefijo}-animal`} value={datos.tipo_animal} onChange={(e) => cambiar({ tipo_animal: e.target.value })} className="mp-campo">
          {ANIMALES.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
        </select>
      </div>
      <div>
        <label htmlFor={`select-${prefijo}-unidad`} className="mp-etiqueta">Presentación</label>
        <select id={`select-${prefijo}-unidad`} value={datos.unidad_medida} onChange={(e) => cambiar({ unidad_medida: e.target.value })} className="mp-campo">
          {UNIDADES.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
        </select>
      </div>
      <div className="col-span-2">
        <label htmlFor={`textarea-${prefijo}-descripcion`} className="mp-etiqueta">Descripción</label>
        <textarea id={`textarea-${prefijo}-descripcion`} rows={2} placeholder="Dosis, composición o modo de uso" value={datos.descripcion} onChange={(e) => cambiar({ descripcion: e.target.value })} className="mp-campo resize-none" />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
interface InventarioViewProps {
  productos: Producto[];
  currentUser: User;
  onCreateProducto: (data: Partial<Producto>) => Promise<Producto>;
  onUpdateProducto: (id: number, data: Partial<Producto>) => Promise<void>;
  onDeleteProducto: (id: number) => Promise<void>;
  /** Sube `archivo` como imagen del producto y retira las `anteriores`. */
  onCambiarImagen: (id: number, archivo: File, anteriores: number[]) => Promise<void>;
}

function EstadoStock({ p }: { p: Producto }) {
  if (p.stock === 0) return <span className="mp-pill mp-pill--peligro">Agotado</span>;
  if (p.stock <= p.stock_minimo) return <span className="mp-pill mp-pill--pendiente">Stock bajo</span>;
  return <span className="mp-pill mp-pill--exito">Disponible</span>;
}

export const InventarioView: React.FC<InventarioViewProps> = ({
  productos,
  onCreateProducto,
  onUpdateProducto,
  onDeleteProducto,
  onCambiarImagen
}) => {
  const { avisar, confirmar } = useInterfaz();
  const [search, setSearch] = useState('');
  const [soloStockBajo, setSoloStockBajo] = useState(false);
  // null: cerrado; 'nuevo': alta; un producto: edición.
  const [editando, setEditando] = useState<Producto | 'nuevo' | null>(null);
  const [datos, setDatos] = useState<DatosProducto>(VACIO);
  const [imagen, setImagen] = useState<File | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const stockBajo = productos.filter((p) => p.stock > 0 && p.stock <= p.stock_minimo).length;
  const agotados = productos.filter((p) => p.stock === 0).length;
  const vendidos = productos.reduce((acc, p) => acc + (p.total_vendidos || 0), 0);

  const filtrados = productos.filter((p) => {
    if (soloStockBajo && p.stock > p.stock_minimo) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return [p.nombre, p.sku, p.categoria, p.marca].some((t) => (t || '').toLowerCase().includes(q));
  });

  const abrir = (p: Producto | 'nuevo') => {
    setDatos(p === 'nuevo' ? VACIO : aDatos(p));
    setImagen(null);
    setErrorMsg(null);
    setEditando(p);
  };

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editando) return;
    setErrorMsg(null);
    const cuerpo = { ...datos, nombre: datos.nombre.trim(), marca: datos.marca.trim(), descripcion: datos.descripcion.trim() };
    try {
      setIsSubmitting(true);
      if (editando === 'nuevo') {
        const creado = await onCreateProducto(cuerpo);
        // El producto ya existe: si la foto falla, se avisa y se cierra igual
        // para no crearlo dos veces al reintentar.
        if (imagen) {
          try {
            await onCambiarImagen(creado.id, imagen, []);
          } catch (err: any) {
            avisar(`El producto se creó, pero la foto no se pudo subir (${err.message}). Súbela desde «Editar».`, 'error');
          }
        }
        avisar(`${cuerpo.nombre} añadido al inventario.`);
      } else {
        await onUpdateProducto(editando.id, cuerpo);
        if (imagen) await onCambiarImagen(editando.id, imagen, editando.imagenes_ids);
        avisar('Cambios guardados.');
      }
      setEditando(null);
    } catch (err: any) {
      setErrorMsg(err.message || 'No se pudo guardar el producto.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const retirar = async (p: Producto) => {
    const ok = await confirmar({
      titulo: 'Retirar del inventario',
      mensaje: `«${p.nombre}» dejará de aparecer en la tienda y en el inventario. Sus ventas se conservan.`,
      confirmar: 'Retirar producto',
      peligro: true
    });
    if (!ok) return;
    try {
      await onDeleteProducto(p.id);
      avisar(`${p.nombre} retirado del inventario.`);
    } catch (err: any) {
      avisar(err.message || 'No se pudo retirar el producto.', 'error');
    }
  };

  return (
    <div className="space-y-6">
      <Encabezado titulo="Inventario y farmacia" descripcion="Stock, precios y fotos de los productos que se venden en la tienda.">
        <button id="btn-agregar-producto-inv" onClick={() => abrir('nuevo')} className="mp-btn mp-btn--primario">
          <Plus className="w-4 h-4" />
          Nuevo producto
        </button>
      </Encabezado>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="mp-stat"><div className="mp-stat-valor">{productos.length}</div><div className="text-sm mt-1">Productos</div></div>
        <div className="mp-stat"><div className="mp-stat-valor">{stockBajo}</div><div className="text-sm mt-1">Con stock bajo</div></div>
        <div className="mp-stat"><div className="mp-stat-valor">{agotados}</div><div className="text-sm mt-1">Agotados</div></div>
        <div className="mp-stat"><div className="mp-stat-valor">{vendidos}</div><div className="text-sm mt-1">Unidades vendidas</div></div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="mp-buscador w-full sm:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" aria-hidden />
          <label htmlFor="input-search-inventario" className="sr-only">Buscar en el inventario</label>
          <input type="search" id="input-search-inventario" placeholder="Nombre, SKU o marca" value={search} onChange={(e) => setSearch(e.target.value)} className="mp-campo" />
        </div>
        <button onClick={() => setSoloStockBajo((v) => !v)} aria-pressed={soloStockBajo} className="mp-filtro self-start sm:self-auto">
          <AlertTriangle className="w-3.5 h-3.5 inline mr-1 -mt-0.5" />
          Sólo stock bajo o agotado
        </button>
      </div>

      {filtrados.length === 0 ? (
        <Vacio
          icono={Package}
          titulo={productos.length === 0 ? 'El inventario está vacío' : 'Ningún producto coincide'}
          texto={productos.length === 0 ? 'Añade el primer producto para venderlo en la tienda.' : 'Prueba con otra búsqueda o quita el filtro.'}
        />
      ) : (
        <div className="mp-papel overflow-hidden">
          <div className="mp-desplazable">
            <table className="mp-tabla">
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>SKU</th>
                  <th>Categoría</th>
                  <th className="text-right">Precio</th>
                  <th className="text-right">Stock</th>
                  <th>Estado</th>
                  <th className="text-right"><span className="sr-only">Acciones</span></th>
                </tr>
              </thead>
              <tbody>
                {filtrados.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <div className="flex items-center gap-3 min-w-[14rem]">
                        <ImagenProducto nombre={p.nombre} imagen={p.imagen_url} categoria={p.categoria} className="w-10 h-10 rounded-lg shrink-0" tamanoIcono="w-5 h-5" />
                        <div>
                          <div className="font-semibold">{p.nombre}</div>
                          <div className="text-xs text-slate-500">{p.marca || 'Sin marca'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="font-mono text-xs text-slate-500">{p.sku}</td>
                    <td className="capitalize">{p.categoria}</td>
                    <td className="text-right whitespace-nowrap">
                      <div className="font-semibold">{formatearPrecio(p.precio_final)}</div>
                      {p.descuento_porcentaje > 0 && <div className="text-xs text-[#b92b39]">-{p.descuento_porcentaje}%</div>}
                    </td>
                    <td className="text-right">
                      <div className="font-semibold">{p.stock}</div>
                      <div className="text-xs text-slate-500">mín. {p.stock_minimo}</div>
                    </td>
                    <td><EstadoStock p={p} /></td>
                    <td>
                      <div className="flex justify-end gap-2">
                        <button id={`btn-edit-prod-${p.id}`} onClick={() => abrir(p)} className="mp-accion" aria-label={`Editar ${p.nombre}`} title="Editar">
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button id={`btn-delete-prod-${p.id}`} onClick={() => retirar(p)} className="mp-accion mp-accion--peligro" aria-label={`Retirar ${p.nombre}`} title="Retirar">
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
      )}

      {editando && (
        <Modal
          titulo={editando === 'nuevo' ? 'Nuevo producto' : `Editar ${editando.nombre}`}
          icono={<Package className="w-5 h-5 text-[#ff9f43]" />}
          onCerrar={() => setEditando(null)}
        >
          <form onSubmit={guardar} className="p-6 space-y-4">
            <ErrorFormulario texto={errorMsg} />
            {editando !== 'nuevo' && <p className="text-xs text-slate-500 font-mono">SKU {editando.sku}</p>}
            <CamposProducto datos={datos} cambiar={(parcial) => setDatos((d) => ({ ...d, ...parcial }))} prefijo={editando === 'nuevo' ? 'prod' : 'edit-prod'} />
            <SelectorImagen
              id={editando === 'nuevo' ? 'input-prod-imagen' : 'input-edit-prod-imagen'}
              actual={editando === 'nuevo' ? undefined : editando.imagen_url}
              archivo={imagen}
              onCambio={setImagen}
            />
            <PieModal>
              <button type="button" onClick={() => setEditando(null)} className="mp-btn mp-btn--borde">Cancelar</button>
              <button
                type="submit"
                id={editando === 'nuevo' ? 'btn-submit-nuevo-prod' : 'btn-submit-editar-prod'}
                disabled={isSubmitting}
                className="mp-btn mp-btn--primario"
              >
                {isSubmitting ? 'Guardando…' : editando === 'nuevo' ? 'Añadir producto' : 'Guardar cambios'}
              </button>
            </PieModal>
          </form>
        </Modal>
      )}
    </div>
  );
};
