import React, { useState } from 'react';
import { 
  Terminal, 
  CheckCircle2, 
  ExternalLink, 
  Play, 
  Code, 
  Layers, 
  Server, 
  X, 
  RefreshCw 
} from 'lucide-react';

interface FastApiModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiConnected: boolean;
}

export const FastApiModal: React.FC<FastApiModalProps> = ({
  isOpen,
  onClose,
  apiConnected
}) => {
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>('/api/health');
  const [responseOutput, setResponseOutput] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [latency, setLatency] = useState<number | null>(null);

  if (!isOpen) return null;

  const endpoints = [
    { method: 'GET', path: '/api/health', desc: 'Verifica estado del servicio y conexión a SQLite' },
    { method: 'GET', path: '/api/stats', desc: 'Métricas agregadas para el dashboard administrativo' },
    { method: 'GET', path: '/api/mascotas', desc: 'Listado completo de pacientes registrados y tutores' },
    { method: 'GET', path: '/api/servicios', desc: 'Catálogo de servicios médicos, duraciones y aranceles' },
    { method: 'GET', path: '/api/citas', desc: 'Agenda médica de consultas, cirugías y vacunaciones' },
    { method: 'GET', path: '/api/adopciones', desc: 'Mascotas rescatadas disponibles para adopción' },
    { method: 'GET', path: '/api/productos', desc: 'Catálogo de medicamentos, insumos y alimentos' },
    { method: 'GET', path: '/api/historiales', desc: 'Fichas clínicas, diagnósticos y tratamientos' },
    { method: 'GET', path: '/openapi.json', desc: 'Especificación estándar OpenAPI v3 generada por FastAPI' }
  ];

  const handleTestEndpoint = async (path: string) => {
    try {
      setIsLoading(true);
      const start = performance.now();
      const res = await fetch(path);
      const end = performance.now();
      setLatency(Math.round(end - start));
      const data = await res.json();
      setResponseOutput(data);
    } catch (err: any) {
      setResponseOutput({ error: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="bg-slate-900 text-slate-100 rounded-3xl shadow-2xl border border-slate-700 w-full max-w-4xl overflow-hidden my-8 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-slate-950 border-b border-slate-800 px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold font-mono">
              ⚡
            </div>
            <div>
              <h3 className="font-bold text-base flex items-center gap-2">
                <span>FastAPI Backend + Node.js + React</span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono ${apiConnected ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-red-500/20 text-red-400'}`}>
                  {apiConnected ? 'ONLINE (Port 8001)' : 'OFFLINE'}
                </span>
              </h3>
              <p className="text-xs text-slate-400">Arquitectura de migración de Django a Microservicios Modernos</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a
              href="/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-lg bg-sky-500/20 text-sky-300 hover:bg-sky-500/30 text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <span>Swagger UI</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>

            <button 
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1 rounded-lg"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Stack Architecture Highlights */}
        <div className="bg-slate-900/80 px-6 py-3 border-b border-slate-800 grid sm:grid-cols-3 gap-3 text-xs">
          <div className="flex items-center gap-2 bg-slate-800/60 p-2 rounded-xl border border-slate-700/50">
            <Server className="w-4 h-4 text-emerald-400 shrink-0" />
            <div>
              <div className="font-bold text-slate-200">FastAPI (Python 3.11)</div>
              <div className="text-[10px] text-slate-400">REST API, Pydantic, SQLite</div>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-slate-800/60 p-2 rounded-xl border border-slate-700/50">
            <Layers className="w-4 h-4 text-amber-400 shrink-0" />
            <div>
              <div className="font-bold text-slate-200">Node.js Express Proxy</div>
              <div className="text-[10px] text-slate-400">Reverse Proxy puerto 3000</div>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-slate-800/60 p-2 rounded-xl border border-slate-700/50">
            <Code className="w-4 h-4 text-sky-400 shrink-0" />
            <div>
              <div className="font-bold text-slate-200">React 18 + TypeScript</div>
              <div className="text-[10px] text-slate-400">Tailwind CSS, Single-Page App</div>
            </div>
          </div>
        </div>

        {/* Body: Endpoint Selector and Live Runner */}
        <div className="p-6 overflow-y-auto flex-1 grid md:grid-cols-2 gap-6">
          {/* Left Column: Endpoints List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-slate-400 font-semibold uppercase tracking-wider">
              <span>Endpoints FastAPI Disponibles</span>
              <span>REST JSON</span>
            </div>

            <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
              {endpoints.map((ep) => (
                <div
                  key={ep.path}
                  onClick={() => {
                    setSelectedEndpoint(ep.path);
                    handleTestEndpoint(ep.path);
                  }}
                  className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                    selectedEndpoint === ep.path
                      ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-200 shadow-sm'
                      : 'bg-slate-800/50 border-slate-700/60 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono font-bold text-emerald-400">{ep.method}</span>
                    <span className="font-mono text-[11px] text-slate-300 font-semibold">{ep.path}</span>
                  </div>
                  <p className="text-[11px] text-slate-400">{ep.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Live Console Output */}
          <div className="flex flex-col bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden">
            <div className="px-4 py-2.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                <span className="font-mono font-bold text-slate-300">{selectedEndpoint}</span>
              </div>
              <div className="flex items-center gap-3">
                {latency !== null && (
                  <span className="font-mono text-[10px] text-emerald-400">⚡ {latency} ms</span>
                )}
                <button
                  onClick={() => handleTestEndpoint(selectedEndpoint)}
                  disabled={isLoading}
                  className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[10px] flex items-center gap-1 transition-colors disabled:opacity-50"
                >
                  <Play className="w-2.5 h-2.5" />
                  <span>{isLoading ? 'Ejecutando...' : 'Ejecutar'}</span>
                </button>
              </div>
            </div>

            <div className="p-4 font-mono text-xs overflow-auto flex-1 max-h-[380px] text-slate-200">
              {isLoading ? (
                <div className="flex items-center gap-2 text-slate-400">
                  <RefreshCw className="w-4 h-4 animate-spin text-emerald-400" />
                  <span>Consultando FastAPI a través de Node.js proxy...</span>
                </div>
              ) : responseOutput ? (
                <pre className="whitespace-pre-wrap leading-relaxed text-[11px] text-emerald-300">
                  {JSON.stringify(responseOutput, null, 2)}
                </pre>
              ) : (
                <div className="text-slate-500 text-center py-12">
                  <p>Haz clic en cualquier endpoint a la izquierda o en "Ejecutar" para probar la respuesta en tiempo real de FastAPI.</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-slate-950 px-6 py-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            <span>MundoPeludo v2.0 • Stack Python FastAPI & Node.js</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};
