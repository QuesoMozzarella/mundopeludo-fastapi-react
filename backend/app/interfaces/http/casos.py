"""Proveedores de casos de uso para FastAPI (composition root de la aplicación).

Aquí —y sólo aquí— se decide con qué repositorios y servicios se construye
cada caso de uso. Los routers declaran qué caso necesitan (`AgendarCitaDep`) y
FastAPI lo inyecta: no conocen sus dependencias ni el orden de sus argumentos.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from ...application.use_cases.autenticacion import (
    AutenticarUsuario,
    CambiarPassword,
    RegistrarUsuario,
    RestablecerPassword,
    SolicitarCodigoRecuperacion,
)
from ...application.use_cases.usuarios import (
    ActualizarEspecialidad,
    ActualizarUsuario,
    ConsultarEspecialidades,
    ConsultarUsuarios,
    CrearEspecialidad,
    DesactivarUsuario,
    EliminarEspecialidad,
    GuardarPerfilCliente,
    GuardarPerfilVeterinario,
)
from ...application.use_cases.mascotas import (
    ActualizarMascota,
    ConsultarEspecies,
    ConsultarMascotas,
    CrearEspecie,
    DarDeBajaMascota,
    EliminarEspecie,
    RegistrarMascota,
    RenombrarEspecie,
)
from ...application.use_cases.adopciones import (
    CancelarSolicitudAdopcion,
    ConsultarSolicitudesAdopcion,
    PublicarMascotaEnAdopcion,
    ResolverSolicitudAdopcion,
    SolicitarAdopcion,
)
from ...application.use_cases.citas import (
    ActualizarCita,
    ActualizarServicio,
    AgendarCita,
    AvisosDeCita,
    CambiarEstadoCita,
    ConsultarAgendaDia,
    ConsultarCitas,
    ConsultarDisponibilidad,
    ConsultarEstadosCita,
    ConsultarServicios,
    CrearEstadoCita,
    CrearServicio,
    DeclararDisponibilidad,
    EliminarCita,
    EliminarDisponibilidad,
    EliminarEstadoCita,
    EliminarServicio,
    ReglasDeAgenda,
)
from ...application.use_cases.historiales import (
    ActualizarHistorial,
    ConsultarHistoriales,
    EliminarHistorial,
    RegistrarHistorial,
)
from ...application.use_cases.inventario import (
    ActualizarProducto,
    AjustarStock,
    ConsultarImagenesProducto,
    ConsultarProductos,
    CrearProducto,
    DesactivarProducto,
    EliminarImagenProducto,
    GeneradorSku,
    SubirImagenProducto,
)
from ...application.use_cases.carrito import (
    ConsultarPedidos,
    GestionarCarrito,
    ProcesarCheckout,
)
from ...application.use_cases.sistema import (
    ConsultarActividad,
    ObtenerEstadisticas,
    RegistrarActividad,
)
from .deps import AvisosDep, ReposDep, ServiciosDep

# ------------------------------ autenticacion ---------------------------


def autenticar_usuario(repos: ReposDep, servicios: ServiciosDep) -> AutenticarUsuario:
    return AutenticarUsuario(
        repos.usuarios,
        servicios.hasher,
        servicios.tokens,
        servicios.reloj,
        repos.actividades,
    )


AutenticarUsuarioDep = Annotated[AutenticarUsuario, Depends(autenticar_usuario)]


def cambiar_password(repos: ReposDep, servicios: ServiciosDep) -> CambiarPassword:
    return CambiarPassword(repos.usuarios, servicios.hasher)


CambiarPasswordDep = Annotated[CambiarPassword, Depends(cambiar_password)]


def registrar_usuario(repos: ReposDep, servicios: ServiciosDep) -> RegistrarUsuario:
    return RegistrarUsuario(
        repos.usuarios,
        repos.perfiles_cliente,
        repos.perfiles_veterinario,
        servicios.hasher,
        servicios.reloj,
        repos.actividades,
    )


RegistrarUsuarioDep = Annotated[RegistrarUsuario, Depends(registrar_usuario)]


def restablecer_password(repos: ReposDep, servicios: ServiciosDep) -> RestablecerPassword:
    return RestablecerPassword(repos.usuarios, repos.codigos, servicios.hasher, servicios.reloj)


RestablecerPasswordDep = Annotated[RestablecerPassword, Depends(restablecer_password)]


def solicitar_codigo_recuperacion(
    repos: ReposDep,
    servicios: ServiciosDep,
) -> SolicitarCodigoRecuperacion:
    return SolicitarCodigoRecuperacion(
        repos.usuarios,
        repos.codigos,
        servicios.generador,
        servicios.reloj,
        servicios.notificaciones,
    )


SolicitarCodigoRecuperacionDep = Annotated[
    SolicitarCodigoRecuperacion, Depends(solicitar_codigo_recuperacion)
]


# ------------------------------ usuarios --------------------------------


def actualizar_especialidad(repos: ReposDep) -> ActualizarEspecialidad:
    return ActualizarEspecialidad(repos.especialidades)


ActualizarEspecialidadDep = Annotated[ActualizarEspecialidad, Depends(actualizar_especialidad)]


def actualizar_usuario(repos: ReposDep, servicios: ServiciosDep) -> ActualizarUsuario:
    return ActualizarUsuario(
        repos.usuarios,
        repos.perfiles_cliente,
        repos.perfiles_veterinario,
        servicios.reloj,
    )


ActualizarUsuarioDep = Annotated[ActualizarUsuario, Depends(actualizar_usuario)]


def consultar_especialidades(repos: ReposDep) -> ConsultarEspecialidades:
    return ConsultarEspecialidades(repos.especialidades)


ConsultarEspecialidadesDep = Annotated[ConsultarEspecialidades, Depends(consultar_especialidades)]


def consultar_usuarios(repos: ReposDep) -> ConsultarUsuarios:
    return ConsultarUsuarios(
        repos.usuarios,
        repos.perfiles_cliente,
        repos.perfiles_veterinario,
        repos.especialidades,
    )


ConsultarUsuariosDep = Annotated[ConsultarUsuarios, Depends(consultar_usuarios)]


def crear_especialidad(repos: ReposDep) -> CrearEspecialidad:
    return CrearEspecialidad(repos.especialidades)


CrearEspecialidadDep = Annotated[CrearEspecialidad, Depends(crear_especialidad)]


def desactivar_usuario(repos: ReposDep) -> DesactivarUsuario:
    return DesactivarUsuario(repos.usuarios)


DesactivarUsuarioDep = Annotated[DesactivarUsuario, Depends(desactivar_usuario)]


def eliminar_especialidad(repos: ReposDep) -> EliminarEspecialidad:
    return EliminarEspecialidad(repos.especialidades)


EliminarEspecialidadDep = Annotated[EliminarEspecialidad, Depends(eliminar_especialidad)]


def guardar_perfil_cliente(repos: ReposDep, servicios: ServiciosDep) -> GuardarPerfilCliente:
    return GuardarPerfilCliente(repos.usuarios, repos.perfiles_cliente, servicios.reloj)


GuardarPerfilClienteDep = Annotated[GuardarPerfilCliente, Depends(guardar_perfil_cliente)]


def guardar_perfil_veterinario(
    repos: ReposDep,
    servicios: ServiciosDep,
) -> GuardarPerfilVeterinario:
    return GuardarPerfilVeterinario(
        repos.usuarios,
        repos.perfiles_veterinario,
        repos.especialidades,
        servicios.reloj,
    )


GuardarPerfilVeterinarioDep = Annotated[
    GuardarPerfilVeterinario, Depends(guardar_perfil_veterinario)
]


# ------------------------------ mascotas --------------------------------


def actualizar_mascota(repos: ReposDep) -> ActualizarMascota:
    return ActualizarMascota(repos.mascotas, repos.especies, repos.usuarios)


ActualizarMascotaDep = Annotated[ActualizarMascota, Depends(actualizar_mascota)]


def consultar_especies(repos: ReposDep) -> ConsultarEspecies:
    return ConsultarEspecies(repos.especies)


ConsultarEspeciesDep = Annotated[ConsultarEspecies, Depends(consultar_especies)]


def consultar_mascotas(repos: ReposDep) -> ConsultarMascotas:
    return ConsultarMascotas(repos.mascotas, repos.especies, repos.usuarios)


ConsultarMascotasDep = Annotated[ConsultarMascotas, Depends(consultar_mascotas)]


def crear_especie(repos: ReposDep) -> CrearEspecie:
    return CrearEspecie(repos.especies)


CrearEspecieDep = Annotated[CrearEspecie, Depends(crear_especie)]


def dar_de_baja_mascota(repos: ReposDep) -> DarDeBajaMascota:
    return DarDeBajaMascota(repos.mascotas)


DarDeBajaMascotaDep = Annotated[DarDeBajaMascota, Depends(dar_de_baja_mascota)]


def eliminar_especie(repos: ReposDep) -> EliminarEspecie:
    return EliminarEspecie(repos.especies, repos.mascotas)


EliminarEspecieDep = Annotated[EliminarEspecie, Depends(eliminar_especie)]


def registrar_mascota(repos: ReposDep, servicios: ServiciosDep) -> RegistrarMascota:
    return RegistrarMascota(repos.mascotas, repos.especies, repos.usuarios, servicios.reloj)


RegistrarMascotaDep = Annotated[RegistrarMascota, Depends(registrar_mascota)]


def renombrar_especie(repos: ReposDep) -> RenombrarEspecie:
    return RenombrarEspecie(repos.especies)


RenombrarEspecieDep = Annotated[RenombrarEspecie, Depends(renombrar_especie)]


# ------------------------------ adopciones ------------------------------


def cancelar_solicitud_adopcion(
    repos: ReposDep,
    servicios: ServiciosDep,
) -> CancelarSolicitudAdopcion:
    return CancelarSolicitudAdopcion(repos.solicitudes, repos.mascotas, servicios.reloj)


CancelarSolicitudAdopcionDep = Annotated[
    CancelarSolicitudAdopcion, Depends(cancelar_solicitud_adopcion)
]


def consultar_solicitudes_adopcion(repos: ReposDep) -> ConsultarSolicitudesAdopcion:
    return ConsultarSolicitudesAdopcion(repos.solicitudes, repos.mascotas, repos.usuarios)


ConsultarSolicitudesAdopcionDep = Annotated[
    ConsultarSolicitudesAdopcion, Depends(consultar_solicitudes_adopcion)
]


def publicar_mascota_en_adopcion(repos: ReposDep) -> PublicarMascotaEnAdopcion:
    return PublicarMascotaEnAdopcion(repos.mascotas)


PublicarMascotaEnAdopcionDep = Annotated[
    PublicarMascotaEnAdopcion, Depends(publicar_mascota_en_adopcion)
]


def resolver_solicitud_adopcion(
    repos: ReposDep,
    servicios: ServiciosDep,
) -> ResolverSolicitudAdopcion:
    return ResolverSolicitudAdopcion(
        repos.solicitudes,
        repos.mascotas,
        repos.usuarios,
        servicios.reloj,
        repos.actividades,
    )


ResolverSolicitudAdopcionDep = Annotated[
    ResolverSolicitudAdopcion, Depends(resolver_solicitud_adopcion)
]


def solicitar_adopcion(repos: ReposDep, servicios: ServiciosDep) -> SolicitarAdopcion:
    return SolicitarAdopcion(
        repos.solicitudes,
        repos.mascotas,
        repos.usuarios,
        servicios.reloj,
        repos.actividades,
    )


SolicitarAdopcionDep = Annotated[SolicitarAdopcion, Depends(solicitar_adopcion)]


# ------------------------------ citas -----------------------------------


def reglas_de_agenda(repos: ReposDep, servicios: ServiciosDep) -> ReglasDeAgenda:
    return ReglasDeAgenda(
        repos.citas,
        repos.usuarios,
        repos.servicios,
        repos.disponibilidades,
        servicios.reloj,
    )


def avisos_de_cita(repos: ReposDep, avisos: AvisosDep) -> AvisosDeCita:
    return AvisosDeCita(
        repos.mascotas, repos.usuarios, repos.servicios, repos.estados_cita, avisos
    )


def actualizar_cita(
    repos: ReposDep, servicios: ServiciosDep, avisos: AvisosDep
) -> ActualizarCita:
    return ActualizarCita(
        repos.citas,
        repos.estados_cita,
        reglas_de_agenda(repos, servicios),
        avisos_de_cita(repos, avisos),
    )


ActualizarCitaDep = Annotated[ActualizarCita, Depends(actualizar_cita)]


def actualizar_servicio(repos: ReposDep) -> ActualizarServicio:
    return ActualizarServicio(repos.servicios, repos.usuarios, repos.especialidades)


ActualizarServicioDep = Annotated[ActualizarServicio, Depends(actualizar_servicio)]


def agendar_cita(repos: ReposDep, servicios: ServiciosDep, avisos: AvisosDep) -> AgendarCita:
    return AgendarCita(
        repos.citas,
        repos.mascotas,
        repos.estados_cita,
        reglas_de_agenda(repos, servicios),
        avisos_de_cita(repos, avisos),
    )


AgendarCitaDep = Annotated[AgendarCita, Depends(agendar_cita)]


def cambiar_estado_cita(repos: ReposDep, avisos: AvisosDep) -> CambiarEstadoCita:
    return CambiarEstadoCita(repos.citas, repos.estados_cita, avisos_de_cita(repos, avisos))


CambiarEstadoCitaDep = Annotated[CambiarEstadoCita, Depends(cambiar_estado_cita)]


def consultar_agenda_dia(repos: ReposDep) -> ConsultarAgendaDia:
    return ConsultarAgendaDia(repos.citas, repos.disponibilidades, repos.usuarios)


ConsultarAgendaDiaDep = Annotated[ConsultarAgendaDia, Depends(consultar_agenda_dia)]


def consultar_citas(repos: ReposDep) -> ConsultarCitas:
    return ConsultarCitas(
        repos.citas,
        repos.mascotas,
        repos.usuarios,
        repos.servicios,
        repos.estados_cita,
        repos.historiales,
    )


ConsultarCitasDep = Annotated[ConsultarCitas, Depends(consultar_citas)]


def consultar_disponibilidad(repos: ReposDep) -> ConsultarDisponibilidad:
    return ConsultarDisponibilidad(repos.disponibilidades, repos.usuarios)


ConsultarDisponibilidadDep = Annotated[ConsultarDisponibilidad, Depends(consultar_disponibilidad)]


def consultar_estados_cita(repos: ReposDep) -> ConsultarEstadosCita:
    return ConsultarEstadosCita(repos.estados_cita)


ConsultarEstadosCitaDep = Annotated[ConsultarEstadosCita, Depends(consultar_estados_cita)]


def consultar_servicios(repos: ReposDep) -> ConsultarServicios:
    return ConsultarServicios(repos.servicios, repos.usuarios, repos.especialidades)


ConsultarServiciosDep = Annotated[ConsultarServicios, Depends(consultar_servicios)]


def crear_estado_cita(repos: ReposDep) -> CrearEstadoCita:
    return CrearEstadoCita(repos.estados_cita)


CrearEstadoCitaDep = Annotated[CrearEstadoCita, Depends(crear_estado_cita)]


def crear_servicio(repos: ReposDep) -> CrearServicio:
    return CrearServicio(repos.servicios, repos.usuarios, repos.especialidades)


CrearServicioDep = Annotated[CrearServicio, Depends(crear_servicio)]


def declarar_disponibilidad(repos: ReposDep) -> DeclararDisponibilidad:
    return DeclararDisponibilidad(repos.disponibilidades, repos.usuarios)


DeclararDisponibilidadDep = Annotated[DeclararDisponibilidad, Depends(declarar_disponibilidad)]


def eliminar_cita(repos: ReposDep) -> EliminarCita:
    return EliminarCita(repos.citas)


EliminarCitaDep = Annotated[EliminarCita, Depends(eliminar_cita)]


def eliminar_disponibilidad(repos: ReposDep) -> EliminarDisponibilidad:
    return EliminarDisponibilidad(repos.disponibilidades)


EliminarDisponibilidadDep = Annotated[EliminarDisponibilidad, Depends(eliminar_disponibilidad)]


def eliminar_estado_cita(repos: ReposDep) -> EliminarEstadoCita:
    return EliminarEstadoCita(repos.estados_cita, repos.citas)


EliminarEstadoCitaDep = Annotated[EliminarEstadoCita, Depends(eliminar_estado_cita)]


def eliminar_servicio(repos: ReposDep) -> EliminarServicio:
    return EliminarServicio(repos.servicios, repos.citas)


EliminarServicioDep = Annotated[EliminarServicio, Depends(eliminar_servicio)]


# ------------------------------ historiales -----------------------------


def actualizar_historial(repos: ReposDep) -> ActualizarHistorial:
    return ActualizarHistorial(repos.historiales)


ActualizarHistorialDep = Annotated[ActualizarHistorial, Depends(actualizar_historial)]


def consultar_historiales(repos: ReposDep) -> ConsultarHistoriales:
    return ConsultarHistoriales(repos.historiales, repos.citas, repos.mascotas, repos.usuarios)


ConsultarHistorialesDep = Annotated[ConsultarHistoriales, Depends(consultar_historiales)]


def eliminar_historial(repos: ReposDep) -> EliminarHistorial:
    return EliminarHistorial(repos.historiales)


EliminarHistorialDep = Annotated[EliminarHistorial, Depends(eliminar_historial)]


def registrar_historial(
    repos: ReposDep, servicios: ServiciosDep, avisos: AvisosDep
) -> RegistrarHistorial:
    return RegistrarHistorial(
        repos.historiales,
        repos.citas,
        repos.mascotas,
        repos.usuarios,
        repos.estados_cita,
        servicios.reloj,
        avisos,
    )


RegistrarHistorialDep = Annotated[RegistrarHistorial, Depends(registrar_historial)]


# ------------------------------ inventario ------------------------------


def actualizar_producto(repos: ReposDep, servicios: ServiciosDep) -> ActualizarProducto:
    return ActualizarProducto(repos.productos, GeneradorSku(repos.productos), servicios.reloj)


ActualizarProductoDep = Annotated[ActualizarProducto, Depends(actualizar_producto)]


def ajustar_stock(repos: ReposDep, servicios: ServiciosDep) -> AjustarStock:
    return AjustarStock(repos.productos, servicios.reloj)


AjustarStockDep = Annotated[AjustarStock, Depends(ajustar_stock)]


def consultar_imagenes_producto(repos: ReposDep) -> ConsultarImagenesProducto:
    return ConsultarImagenesProducto(repos.imagenes, repos.productos)


ConsultarImagenesProductoDep = Annotated[
    ConsultarImagenesProducto, Depends(consultar_imagenes_producto)
]


def consultar_productos(repos: ReposDep, servicios: ServiciosDep) -> ConsultarProductos:
    return ConsultarProductos(repos.productos, repos.imagenes, servicios.reloj)


ConsultarProductosDep = Annotated[ConsultarProductos, Depends(consultar_productos)]


def crear_producto(repos: ReposDep, servicios: ServiciosDep) -> CrearProducto:
    return CrearProducto(repos.productos, GeneradorSku(repos.productos), servicios.reloj)


CrearProductoDep = Annotated[CrearProducto, Depends(crear_producto)]


def desactivar_producto(repos: ReposDep, servicios: ServiciosDep) -> DesactivarProducto:
    return DesactivarProducto(repos.productos, servicios.reloj)


DesactivarProductoDep = Annotated[DesactivarProducto, Depends(desactivar_producto)]


def eliminar_imagen_producto(repos: ReposDep) -> EliminarImagenProducto:
    return EliminarImagenProducto(repos.imagenes)


EliminarImagenProductoDep = Annotated[EliminarImagenProducto, Depends(eliminar_imagen_producto)]


def subir_imagen_producto(repos: ReposDep, servicios: ServiciosDep) -> SubirImagenProducto:
    return SubirImagenProducto(repos.imagenes, repos.productos, servicios.reloj)


SubirImagenProductoDep = Annotated[SubirImagenProducto, Depends(subir_imagen_producto)]


# ------------------------------ carrito ---------------------------------


def consultar_pedidos(repos: ReposDep) -> ConsultarPedidos:
    return ConsultarPedidos(repos.pedidos)


ConsultarPedidosDep = Annotated[ConsultarPedidos, Depends(consultar_pedidos)]


def gestionar_carrito(repos: ReposDep, servicios: ServiciosDep) -> GestionarCarrito:
    return GestionarCarrito(repos.carritos, repos.productos, repos.usuarios, servicios.reloj)


GestionarCarritoDep = Annotated[GestionarCarrito, Depends(gestionar_carrito)]


def procesar_checkout(repos: ReposDep, servicios: ServiciosDep) -> ProcesarCheckout:
    return ProcesarCheckout(
        repos.carritos,
        repos.productos,
        repos.pedidos,
        repos.usuarios,
        servicios.reloj,
        repos.actividades,
    )


ProcesarCheckoutDep = Annotated[ProcesarCheckout, Depends(procesar_checkout)]


# ------------------------------ sistema ---------------------------------


def consultar_actividad(repos: ReposDep) -> ConsultarActividad:
    return ConsultarActividad(repos.actividades)


ConsultarActividadDep = Annotated[ConsultarActividad, Depends(consultar_actividad)]


def obtener_estadisticas(repos: ReposDep, servicios: ServiciosDep) -> ObtenerEstadisticas:
    return ObtenerEstadisticas(
        repos.usuarios,
        repos.mascotas,
        repos.solicitudes,
        repos.citas,
        repos.historiales,
        repos.productos,
        repos.pedidos,
        repos.estados_cita,
        servicios.reloj,
    )


ObtenerEstadisticasDep = Annotated[ObtenerEstadisticas, Depends(obtener_estadisticas)]


def registrar_actividad(repos: ReposDep, servicios: ServiciosDep) -> RegistrarActividad:
    return RegistrarActividad(repos.actividades, servicios.reloj)


RegistrarActividadDep = Annotated[RegistrarActividad, Depends(registrar_actividad)]
