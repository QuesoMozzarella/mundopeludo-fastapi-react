"""Carga de datos de ejemplo: `python backend/seed.py`.

Escribe a través de los casos de uso y repositorios, no con SQL suelto: así los
datos de prueba pasan por las mismas validaciones que la API.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.entorno import cargar_env  # noqa: E402

cargar_env()  # antes de importar la configuración

from app.application.use_cases.autenticacion import RegistrarUsuario  # noqa: E402
from app.application.use_cases.citas import (  # noqa: E402
    AgendarCita,
    AgendarCitaCmd,
    ReglasDeAgenda,
)
from app.application.use_cases.historiales import (  # noqa: E402
    RegistrarHistorial,
    RegistrarHistorialCmd,
)
from app.application.use_cases.inventario import (  # noqa: E402
    CrearProducto,
    CrearProductoCmd,
    GeneradorSku,
)
from app.application.use_cases.mascotas import (  # noqa: E402
    RegistrarMascota,
    RegistrarMascotaCmd,
)
from app.domain.model.cita import Servicio  # noqa: E402
from app.domain.model.usuario import Especialidad  # noqa: E402
from app.interfaces.http.deps import Contenedor  # noqa: E402

PASSWORD_DEMO = "mundopeludo2025"


def poblar() -> None:
    contenedor = Contenedor()
    contenedor.preparar()

    with contenedor.db.unidad_de_trabajo() as conexion:
        repos = contenedor.repositorios(conexion)
        servicios_tec = contenedor.servicios

        if repos.usuarios.listar():
            print("La base ya tiene usuarios: no se vuelve a poblar.")
            return

        print("Poblando MundoPeludo...")

        # 1. Especialidades
        especialidades = {}
        for codigo, nombre in [
            ("medicina_interna", "Medicina Interna"),
            ("cirugia", "Cirugía"),
            ("dermatologia", "Dermatología"),
            ("cardiologia", "Cardiología"),
            ("exoticos", "Medicina de Animales Exóticos"),
        ]:
            especialidad = repos.especialidades.crear(Especialidad(codigo=codigo, nombre=nombre))
            especialidades[codigo] = especialidad.id

        # 2. Usuarios
        registrar = RegistrarUsuario(
            repos.usuarios,
            repos.perfiles_cliente,
            repos.perfiles_veterinario,
            servicios_tec.hasher,
            servicios_tec.reloj,
            repos.actividades,
        )
        admin = registrar.ejecutar(
            email="admin@mundopeludo.com",
            password=PASSWORD_DEMO,
            nombre="Maurizio",
            apellidos="Ramírez",
            telefono="+56 9 8765 4321",
            direccion="Av. Providencia 1234, Santiago",
            tipo="administrador",
            documento="18234567",
        )
        vet_garcia = registrar.ejecutar(
            email="vet.garcia@mundopeludo.com",
            password=PASSWORD_DEMO,
            nombre="Andrea",
            apellidos="García Morales",
            telefono="+56 9 7654 3210",
            direccion="Calle Los Leones 540, Santiago",
            tipo="veterinario",
            documento="16890123",
            especialidades_ids=[especialidades["cirugia"], especialidades["medicina_interna"]],
        )
        vet_martinez = registrar.ejecutar(
            email="vet.martinez@mundopeludo.com",
            password=PASSWORD_DEMO,
            nombre="Felipe",
            apellidos="Martínez Soto",
            telefono="+56 9 6543 2109",
            direccion="Av. Vitacura 2300, Santiago",
            tipo="veterinario",
            documento="17456789",
            especialidades_ids=[especialidades["dermatologia"], especialidades["exoticos"]],
        )
        for perfil_id in (vet_garcia.id, vet_martinez.id):
            perfil = repos.perfiles_veterinario.obtener_por_usuario(perfil_id)
            perfil.activar()
            repos.perfiles_veterinario.guardar(perfil)

        maria = registrar.ejecutar(
            email="maria.gonzalez@example.com",
            password=PASSWORD_DEMO,
            nombre="María",
            apellidos="González Rojas",
            telefono="+56 9 5432 1098",
            direccion="Pasaje Miraflores 88, Las Condes",
            documento="19345678",
        )
        carlos = registrar.ejecutar(
            email="carlos.ramirez@example.com",
            password=PASSWORD_DEMO,
            nombre="Carlos",
            apellidos="Ramírez Vega",
            telefono="+56 9 4321 0987",
            direccion="Av. Apoquindo 4500, Santiago",
            documento="20123456",
        )

        # 3. Servicios (los estados de cita y las especies vienen del esquema)
        servicios = {}
        for nombre, descripcion, vets, esps in [
            ("Consulta General", "Evaluación clínica integral", [vet_garcia.id, vet_martinez.id], ["medicina_interna"]),
            ("Vacunación", "Aplicación de vacunas y refuerzos", [vet_garcia.id, vet_martinez.id], []),
            ("Cirugía", "Procedimientos quirúrgicos programados", [vet_garcia.id], ["cirugia"]),
            ("Dermatología", "Tratamiento de afecciones de la piel", [vet_martinez.id], ["dermatologia"]),
        ]:
            servicio = repos.servicios.crear(
                Servicio(
                    nombre=nombre,
                    descripcion=descripcion,
                    veterinarios_ids=vets,
                    especialidades_ids=[especialidades[e] for e in esps],
                )
            )
            servicios[nombre] = servicio.id

        # 4. Mascotas
        especies = {e.nombre: e.id for e in repos.especies.listar()}
        registrar_mascota = RegistrarMascota(
            repos.mascotas, repos.especies, repos.usuarios, servicios_tec.reloj
        )
        luna = registrar_mascota.ejecutar(
            RegistrarMascotaCmd(
                cliente_id=maria.id,
                especie_id=especies["Canino (Perro)"],
                nombre="Luna",
                raza="Golden Retriever",
                edad_anos=3,
                sexo="Hembra",
                color="dorado",
                peso=28.5,
                esta_esterilizado=True,
            )
        )
        registrar_mascota.ejecutar(
            RegistrarMascotaCmd(
                cliente_id=carlos.id,
                especie_id=especies["Felino (Gato)"],
                nombre="Michi",
                raza="Siamés",
                edad_anos=2,
                sexo="Macho",
                color="gris",
                peso=4.2,
            )
        )
        registrar_mascota.ejecutar(
            RegistrarMascotaCmd(
                especie_id=especies["Canino (Perro)"],
                nombre="Rocky",
                raza="Mestizo",
                edad_anos=1,
                sexo="Macho",
                color="negro",
                peso=12.0,
                estado_adopcion="en_adopcion",
            )
        )

        # 5. Una cita con su historial
        reglas = ReglasDeAgenda(
            repos.citas,
            repos.usuarios,
            repos.servicios,
            repos.disponibilidades,
            servicios_tec.reloj,
        )
        agendar = AgendarCita(repos.citas, repos.mascotas, repos.estados_cita, reglas)
        cita = agendar.ejecutar(
            AgendarCitaCmd(
                mascota_id=luna.id,
                veterinario_id=vet_garcia.id,
                servicio_id=servicios["Consulta General"],
                fecha_hora=datetime.now() + timedelta(days=1, hours=2),
                motivo="Control anual y refuerzo de vacunas",
                estado="Confirmada",
            )
        )
        RegistrarHistorial(
            repos.historiales,
            repos.citas,
            repos.mascotas,
            repos.usuarios,
            repos.estados_cita,
            servicios_tec.reloj,
        ).ejecutar(
            RegistrarHistorialCmd(
                cita_id=cita.id,
                diagnostico="Paciente sano, peso adecuado para la raza",
                tratamiento="Refuerzo de vacuna séxtuple y antiparasitario oral",
                observaciones="Control en 12 meses",
            )
        )

        # 6. Productos
        crear_producto = CrearProducto(
            repos.productos, GeneradorSku(repos.productos), servicios_tec.reloj
        )
        for datos in [
            {
                "nombre": "Alimento Premium para Perros 15kg",
                "descripcion": "Alimento balanceado de alta calidad",
                "categoria": "alimento",
                "marca": "Royal Canin",
                "precio": Decimal("85000"),
                "descuento_porcentaje": Decimal("10"),
                "stock": 45,
                "tipo_animal": "perro",
                "unidad_medida": "kg",
            },
            {
                "nombre": "Antipulgas Spot On Gatos",
                "categoria": "antipulgas",
                "marca": "Frontline",
                "precio": Decimal("12990"),
                "stock": 30,
                "tipo_animal": "gato",
                "unidad_medida": "unidad",
            },
            {
                "nombre": "Amoxicilina 500mg",
                "categoria": "medicamento",
                "marca": "Genfar",
                "precio": Decimal("7500"),
                "stock": 3,
                "stock_minimo": 10,
                "unidad_medida": "caja",
                "fecha_vencimiento": (datetime.now() + timedelta(days=20)).date(),
            },
            {
                "nombre": "Juguete Mordedor Hueso",
                "categoria": "juguete",
                "precio": Decimal("4990"),
                "stock": 60,
                "tipo_animal": "perro",
            },
            {
                "nombre": "Shampoo Hipoalergénico 500ml",
                "categoria": "higiene",
                "precio": Decimal("8990"),
                "stock": 25,
                "tipo_animal": "ambos",
                "unidad_medida": "ml",
            },
        ]:
            crear_producto.ejecutar(CrearProductoCmd(**datos))

    print("Listo.")
    print(f"  Base de datos : {contenedor.config.ruta_bd}")
    print(f"  Administrador : {admin.email} / {PASSWORD_DEMO}")
    print(f"  Veterinario   : vet.garcia@mundopeludo.com / {PASSWORD_DEMO}")
    print(f"  Cliente       : maria.gonzalez@example.com / {PASSWORD_DEMO}")


if __name__ == "__main__":
    poblar()
