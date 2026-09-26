"""Casos de uso transversales: bitácora de actividad y panel de indicadores."""
from __future__ import annotations

from ...domain.model.sistema import ActividadSistema
from ...domain.ports.repositories import (
    ActividadSistemaRepository,
    CitaRepository,
    EstadoCitaRepository,
    HistorialMedicoRepository,
    MascotaRepository,
    PedidoRepository,
    ProductoRepository,
    SolicitudAdopcionRepository,
    UsuarioRepository,
)
from ...domain.ports.services import Clock
from ...domain.value_objects import EstadoAdopcion, EstadoSolicitud, TipoUsuario
from ..read_models import EstadisticasDashboard

# Estados de cita que cuentan como "activas" en el panel.
ESTADOS_ACTIVOS = ("Pendiente", "Confirmada")


class RegistrarActividad:
    def __init__(self, actividades: ActividadSistemaRepository, reloj: Clock):
        self.actividades = actividades
        self.reloj = reloj

    def ejecutar(self, usuario: str, tipo: str, descripcion: str) -> ActividadSistema:
        return self.actividades.registrar(
            ActividadSistema(
                usuario=usuario, tipo=tipo, descripcion=descripcion, fecha=self.reloj.ahora()
            )
        )


class ConsultarActividad:
    def __init__(self, actividades: ActividadSistemaRepository):
        self.actividades = actividades

    def listar(self, limite: int = 50, tipo: str | None = None) -> list[ActividadSistema]:
        return self.actividades.listar(limite, tipo)


class ObtenerEstadisticas:
    """Indicadores del dashboard, calculados con contadores, no cargando tablas."""

    def __init__(
        self,
        usuarios: UsuarioRepository,
        mascotas: MascotaRepository,
        solicitudes: SolicitudAdopcionRepository,
        citas: CitaRepository,
        historiales: HistorialMedicoRepository,
        productos: ProductoRepository,
        pedidos: PedidoRepository,
        estados: EstadoCitaRepository,
        reloj: Clock,
    ):
        self.usuarios = usuarios
        self.mascotas = mascotas
        self.solicitudes = solicitudes
        self.citas = citas
        self.historiales = historiales
        self.productos = productos
        self.pedidos = pedidos
        self.estados = estados
        self.reloj = reloj

    def ejecutar(self) -> EstadisticasDashboard:
        catalogo = self.productos.listar(solo_activos=True)
        return EstadisticasDashboard(
            total_usuarios=self.usuarios.contar(),
            total_clientes=self.usuarios.contar(TipoUsuario.CLIENTE),
            total_veterinarios=self.usuarios.contar(TipoUsuario.VETERINARIO),
            total_mascotas=self.mascotas.contar(activo=True),
            mascotas_en_adopcion=len(
                self.mascotas.listar(estado_adopcion=EstadoAdopcion.EN_ADOPCION)
            ),
            solicitudes_pendientes=len(
                self.solicitudes.listar(estado=EstadoSolicitud.PENDIENTE)
            ),
            citas_hoy=self.citas.contar(dia=self.reloj.hoy()),
            citas_totales=self.citas.contar(),
            citas_activas=self._citas_activas(),
            total_productos=len(catalogo),
            productos_stock_bajo=sum(1 for p in catalogo if p.stock_bajo),
            productos_por_vencer=sum(1 for p in catalogo if p.proximo_a_vencer(self.reloj.hoy())),
            historiales_registrados=len(self.historiales.listar()),
            ingresos_totales=self.pedidos.total_ingresos(),
        )

    def _citas_activas(self) -> int:
        """Citas que aún van a ocurrir: pendientes o confirmadas."""
        total = 0
        for nombre in ESTADOS_ACTIVOS:
            estado = self.estados.obtener_por_nombre(nombre)
            if estado is not None:
                total += self.citas.contar(estado_id=estado.id)
        return total
