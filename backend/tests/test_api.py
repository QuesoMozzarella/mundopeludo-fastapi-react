"""Pruebas de extremo a extremo de la API sobre una base SQLite temporal.

Se ejecutan con `python backend/tests/test_api.py` (sin pytest) o con
`pytest backend/tests` si está instalado.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import date, datetime, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.application.use_cases.autenticacion import RegistrarUsuario  # noqa: E402
from app.bootstrap import create_app  # noqa: E402
from app.config import SECRETO_DESARROLLO, Config  # noqa: E402
from cliente import crear_cliente  # noqa: E402

PASSWORD = "mundopeludo2025"


def nuevo_cliente():
    ruta = os.path.join(tempfile.mkdtemp(prefix="mundopeludo-test-"), "prueba.db")
    app = create_app(
        Config(ruta_bd=ruta, secreto_jwt="secreto-de-prueba", exigir_auth=False, correo_host="")
    )
    return crear_cliente(app)


def cliente_con_auth():
    """App con `MP_REQUIRE_AUTH=1`; devuelve también la app para sembrar datos."""
    ruta = os.path.join(tempfile.mkdtemp(prefix="mundopeludo-auth-"), "prueba.db")
    app = create_app(
        Config(ruta_bd=ruta, secreto_jwt="secreto", exigir_auth=True, correo_host="")
    )
    return app, crear_cliente(app)


def _crear_directo(app, email, tipo):
    """Alta sin pasar por HTTP, como `seed.py`: con auth activa, el registro
    público no permite crear personal."""
    contenedor = app.state.contenedor
    with contenedor.db.unidad_de_trabajo() as conexion:
        repos = contenedor.repositorios(conexion)
        usuario = RegistrarUsuario(
            repos.usuarios,
            repos.perfiles_cliente,
            repos.perfiles_veterinario,
            contenedor.servicios.hasher,
            contenedor.servicios.reloj,
        ).ejecutar(email=email, password=PASSWORD, nombre="Nombre", apellidos="Apellido", tipo=tipo)
    return usuario.id


def _token(cli, email):
    r = cli.post("/api/auth/login", {"email": email, "password": PASSWORD})
    assert r.status == 200, r
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _crear(cli, email, tipo="cliente", **extra):
    datos = {
        "email": email,
        "password": PASSWORD,
        "nombre": extra.pop("nombre", "Nombre"),
        "apellidos": extra.pop("apellidos", "Apellido"),
        "tipo": tipo,
        **extra,
    }
    r = cli.post("/api/auth/register", datos)
    assert r.status == 201, r
    return r.json()["usuario"]


# --------------------------------------------------------------------------
def test_salud_y_catalogos():
    cli = nuevo_cliente()
    r = cli.get("/api/health")
    assert r.status == 200 and r.json()["status"] == "ok", r

    especies = cli.get("/api/especies").json()
    assert len(especies) >= 5, especies
    estados = cli.get("/api/estados-cita").json()
    assert {e["nombre"] for e in estados} >= {"Pendiente", "Confirmada", "Completada"}, estados


def test_registro_login_y_token():
    cli = nuevo_cliente()
    usuario = _crear(cli, "cliente1@test.com", documento="12345678")
    assert usuario["tipo"] == "cliente" and usuario["documento"] == "12345678"

    duplicado = cli.post(
        "/api/auth/register",
        {"email": "cliente1@test.com", "password": PASSWORD, "nombre": "Otro", "apellidos": "Mas"},
    )
    assert duplicado.status == 409, duplicado

    malo = cli.post("/api/auth/login", {"email": "cliente1@test.com", "password": "incorrecta"})
    assert malo.status == 401, malo

    sesion = cli.post("/api/auth/login", {"email": "cliente1@test.com", "password": PASSWORD})
    assert sesion.status == 200, sesion
    token = sesion.json()["access_token"]

    yo = cli.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert yo.status == 200 and yo.json()["email"] == "cliente1@test.com", yo
    assert cli.get("/api/auth/me").status == 401


def test_recuperacion_de_password():
    cli = nuevo_cliente()
    _crear(cli, "olvidadizo@test.com")

    r = cli.post("/api/auth/password/recuperar", {"email": "olvidadizo@test.com"})
    assert r.status == 200 and "codigo_debug" in r.json(), r
    codigo = r.json()["codigo_debug"]

    erroneo = cli.post(
        "/api/auth/password/restablecer",
        {"email": "olvidadizo@test.com", "codigo": "000000", "password_nueva": "otraClave123"},
    )
    assert erroneo.status == 401, erroneo

    ok = cli.post(
        "/api/auth/password/restablecer",
        {"email": "olvidadizo@test.com", "codigo": codigo, "password_nueva": "otraClave123"},
    )
    assert ok.status == 200, ok
    assert cli.post("/api/auth/login", {"email": "olvidadizo@test.com", "password": "otraClave123"}).status == 200
    # El código se consume: no sirve dos veces.
    repetido = cli.post(
        "/api/auth/password/restablecer",
        {"email": "olvidadizo@test.com", "codigo": codigo, "password_nueva": "terceraClave1"},
    )
    assert repetido.status == 401, repetido


def test_validaciones_de_mascota():
    cli = nuevo_cliente()
    cliente = _crear(cli, "tutor@test.com")
    especie = cli.get("/api/especies").json()[0]

    base = {
        "cliente_id": cliente["id"],
        "especie_id": especie["id"],
        "nombre": "  luna  ",
        "sexo": "Hembra",
        "color": "  DORADO ",
        "peso": 28.5,
        "edad_anos": 3,
        "raza": "golden retriever",
    }
    r = cli.post("/api/mascotas", base)
    assert r.status == 201, r
    mascota = r.json()
    # Normalización heredada de Mascota.save(): title() y lower().
    assert mascota["nombre"] == "Luna" and mascota["color"] == "dorado", mascota
    assert mascota["raza"] == "Golden Retriever" and mascota["especie"] == especie["nombre"]
    assert mascota["cliente_nombre"] == cliente["nombre_completo"]

    con_numeros = cli.post("/api/mascotas", {**base, "nombre": "Luna2"})
    assert con_numeros.status == 422 and con_numeros.json()["campo"] == "nombre", con_numeros

    especie_mala = cli.post("/api/mascotas", {**base, "especie_id": 9999})
    assert especie_mala.status == 404, especie_mala

    edad_mala = cli.post("/api/mascotas", {**base, "edad_anos": 99})
    assert edad_mala.status == 422, edad_mala

    baja = cli.delete(f"/api/mascotas/{mascota['id']}")
    assert baja.status == 200 and baja.json()["activo"] is False, baja
    assert all(m["id"] != mascota["id"] for m in cli.get("/api/mascotas").json())


def test_flujo_de_adopcion():
    cli = nuevo_cliente()
    admin = _crear(cli, "admin@test.com", "administrador")
    tutor = _crear(cli, "adoptante@test.com")
    especie = cli.get("/api/especies").json()[0]

    mascota = cli.post(
        "/api/mascotas",
        {
            "especie_id": especie["id"],
            "nombre": "Rocky",
            "sexo": "Macho",
            "color": "negro",
            "peso": 12.0,
        },
    ).json()

    # Sin publicar todavía, no se puede solicitar.
    prematura = cli.post(
        "/api/adopciones/solicitudes", {"mascota_id": mascota["id"], "cliente_id": tutor["id"]}
    )
    assert prematura.status == 409, prematura

    publicada = cli.put(f"/api/adopciones/mascotas/{mascota['id']}/publicar")
    assert publicada.status == 200 and publicada.json()["estado_adopcion"] == "en_adopcion"
    assert len(cli.get("/api/adopciones").json()) == 1

    solicitud = cli.post(
        "/api/adopciones/solicitudes",
        {"mascota_id": mascota["id"], "cliente_id": tutor["id"], "notas_cliente": "Tengo patio"},
    )
    assert solicitud.status == 201, solicitud
    solicitud_id = solicitud.json()["id"]

    repetida = cli.post(
        "/api/adopciones/solicitudes", {"mascota_id": mascota["id"], "cliente_id": tutor["id"]}
    )
    assert repetida.status == 409, repetida

    aprobada = cli.put(
        f"/api/adopciones/solicitudes/{solicitud_id}/aprobar",
        {"revisor_id": admin["id"], "notas": "Aprobada tras entrevista"},
    )
    assert aprobada.status == 200 and aprobada.json()["estado"] == "aprobada", aprobada

    # La mascota queda transferida al adoptante y fuera del listado de adopción.
    final = cli.get(f"/api/mascotas/{mascota['id']}").json()
    assert final["cliente_id"] == tutor["id"] and final["estado_adopcion"] == "normal", final
    assert cli.get("/api/adopciones").json() == []

    # No se puede volver a resolver una solicitud ya resuelta.
    otra_vez = cli.put(
        f"/api/adopciones/solicitudes/{solicitud_id}/rechazar", {"revisor_id": admin["id"]}
    )
    assert otra_vez.status == 409, otra_vez


def test_agenda_citas_e_historial():
    cli = nuevo_cliente()
    vet = _crear(cli, "vet@test.com", "veterinario", documento="9876543")
    tutor = _crear(cli, "tutor2@test.com")
    especie = cli.get("/api/especies").json()[0]

    mascota = cli.post(
        "/api/mascotas",
        {
            "cliente_id": tutor["id"],
            "especie_id": especie["id"],
            "nombre": "Michi",
            "sexo": "Macho",
            "color": "gris",
            "peso": 4.2,
        },
    ).json()

    especialidad = cli.post(
        "/api/especialidades", {"codigo": "cirugia", "nombre": "Cirugía"}
    ).json()
    servicio = cli.post(
        "/api/servicios",
        {
            "nombre": "Consulta General",
            "descripcion": "Evaluación clínica",
            "veterinarios_ids": [vet["id"]],
            "especialidades_ids": [especialidad["id"]],
        },
    )
    assert servicio.status == 201, servicio
    servicio = servicio.json()
    assert servicio["veterinarios"] == [vet["nombre_completo"]], servicio

    manana = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    cita = cli.post(
        "/api/citas",
        {
            "mascota_id": mascota["id"],
            "veterinario_id": vet["id"],
            "servicio_id": servicio["id"],
            "fecha_hora": manana.isoformat(),
            "motivo": "Control anual",
        },
    )
    assert cita.status == 201, cita
    cita = cita.json()
    assert cita["estado"] == "Pendiente" and cita["veterinario_nombre"] == vet["nombre_completo"]

    pasado = cli.post(
        "/api/citas",
        {
            "mascota_id": mascota["id"],
            "veterinario_id": vet["id"],
            "servicio_id": servicio["id"],
            "fecha_hora": (datetime.now() - timedelta(days=1)).isoformat(),
            "motivo": "Control atrasado",
        },
    )
    assert pasado.status == 409, pasado

    solapada = cli.post(
        "/api/citas",
        {
            "mascota_id": mascota["id"],
            "veterinario_id": vet["id"],
            "servicio_id": servicio["id"],
            "fecha_hora": (manana + timedelta(minutes=10)).isoformat(),
            "motivo": "Otra consulta",
        },
    )
    assert solapada.status == 409, solapada

    confirmada = cli.put(f"/api/citas/{cita['id']}/estado", {"estado": "Confirmada"})
    assert confirmada.status == 200 and confirmada.json()["estado"] == "Confirmada", confirmada

    historial = cli.post(
        "/api/historiales-medicos",
        {
            "cita_id": cita["id"],
            "diagnostico": "Paciente sano",
            "tratamiento": "Refuerzo de vacuna",
            "observaciones": "Control en 12 meses",
        },
    )
    assert historial.status == 201, historial
    assert historial.json()["mascota_nombre"] == "Michi"

    duplicado = cli.post(
        "/api/historiales-medicos",
        {"cita_id": cita["id"], "diagnostico": "Otro", "tratamiento": "Otro"},
    )
    assert duplicado.status == 409, duplicado

    assert cli.get(f"/api/citas/{cita['id']}").json()["tiene_historial"] is True
    por_cliente = cli.get("/api/historiales-medicos", params={"cliente_id": tutor["id"]}).json()
    assert len(por_cliente) == 1, por_cliente


def test_disponibilidad_restringe_horario():
    cli = nuevo_cliente()
    vet = _crear(cli, "vet2@test.com", "veterinario")
    tutor = _crear(cli, "tutor3@test.com")
    especie = cli.get("/api/especies").json()[0]
    mascota = cli.post(
        "/api/mascotas",
        {
            "cliente_id": tutor["id"],
            "especie_id": especie["id"],
            "nombre": "Kira",
            "sexo": "Hembra",
            "color": "blanco",
            "peso": 8.0,
        },
    ).json()
    servicio = cli.post("/api/servicios", {"nombre": "Vacunación"}).json()

    manana = (datetime.now() + timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
    franja = cli.post(
        "/api/disponibilidades",
        {
            "veterinario_id": vet["id"],
            "dia_semana": manana.weekday(),
            "hora_inicio": "09:00:00",
            "hora_fin": "12:00:00",
        },
    )
    assert franja.status == 201, franja
    assert franja.json()["dia"] in (
        "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"
    )

    solapada = cli.post(
        "/api/disponibilidades",
        {
            "veterinario_id": vet["id"],
            "dia_semana": manana.weekday(),
            "hora_inicio": "11:00:00",
            "hora_fin": "13:00:00",
        },
    )
    assert solapada.status == 409, solapada

    fuera = cli.post(
        "/api/citas",
        {
            "mascota_id": mascota["id"],
            "veterinario_id": vet["id"],
            "servicio_id": servicio["id"],
            "fecha_hora": manana.isoformat(),
            "motivo": "Fuera de horario",
        },
    )
    assert fuera.status == 409, fuera

    dentro = cli.post(
        "/api/citas",
        {
            "mascota_id": mascota["id"],
            "veterinario_id": vet["id"],
            "servicio_id": servicio["id"],
            "fecha_hora": manana.replace(hour=10).isoformat(),
            "motivo": "Dentro de horario",
        },
    )
    assert dentro.status == 201, dentro

    libres = cli.get(
        f"/api/veterinarios/{vet['id']}/agenda", params={"dia": manana.date().isoformat()}
    ).json()
    assert "09:00" in libres and "10:00" not in libres, libres


def test_productos_sku_y_stock():
    cli = nuevo_cliente()
    primero = cli.post(
        "/api/productos",
        {
            "nombre": "Alimento Premium Perros",
            "categoria": "alimento",
            "precio": "85000",
            "descuento_porcentaje": "10",
            "stock": 45,
            "tipo_animal": "perro",
            "unidad_medida": "kg",
        },
    )
    assert primero.status == 201, primero
    producto = primero.json()
    assert producto["sku"] == "ALI-ALIPRE", producto
    assert producto["precio_final"] == 76500.0, producto
    assert producto["categoria_nombre"] == "Alimento"

    # Mismo nombre y categoría: el SKU se desambigua con un sufijo.
    segundo = cli.post(
        "/api/productos",
        {"nombre": "Alimento Premium Perros", "categoria": "alimento", "precio": "90000",
         "stock": 20},
    ).json()
    assert segundo["sku"] == "ALI-ALIPRE-001", segundo

    categoria_mala = cli.post(
        "/api/productos", {"nombre": "Algo", "categoria": "inventada", "precio": "100"}
    )
    assert categoria_mala.status == 422, categoria_mala

    bajo = cli.post(
        "/api/productos",
        {"nombre": "Amoxicilina 500", "categoria": "medicamento", "precio": "7500",
         "stock": 3, "stock_minimo": 10,
         "fecha_vencimiento": (date.today() + timedelta(days=20)).isoformat()},
    ).json()
    assert bajo["stock_bajo"] is True and bajo["proximo_a_vencer"] is True, bajo

    solo_bajos = cli.get("/api/productos", params={"stock_bajo": "true"}).json()
    assert [p["id"] for p in solo_bajos] == [bajo["id"]], solo_bajos

    ajustado = cli.post(f"/api/productos/{bajo['id']}/stock", {"cantidad": 20}).json()
    assert ajustado["stock"] == 23 and ajustado["stock_bajo"] is False, ajustado

    exceso = cli.post(f"/api/productos/{bajo['id']}/stock", {"cantidad": -1000})
    assert exceso.status == 409, exceso

    buscados = cli.get("/api/productos", params={"buscar": "amoxi"}).json()
    assert len(buscados) == 1 and buscados[0]["id"] == bajo["id"], buscados


def test_imagen_de_producto():
    cli = nuevo_cliente()
    producto = cli.post(
        "/api/productos", {"nombre": "Juguete Hueso", "categoria": "juguete", "precio": "4990"}
    ).json()

    # PNG de 1x1 px en base64.
    png = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    subida = cli.post(
        f"/api/productos/{producto['id']}/imagenes",
        {"imagen_base64": png, "nombre_archivo": "hueso.png", "tipo_contenido": "image/png"},
    )
    assert subida.status == 201, subida
    imagen = subida.json()
    assert imagen["tamano_bytes"] > 0 and imagen["url"] == f"/api/imagenes/{imagen['id']}"

    binario = cli.get(f"/api/imagenes/{imagen['id']}")
    assert binario.status == 200 and binario.cuerpo.startswith(b"\x89PNG"), binario
    assert binario.headers["content-type"].startswith("image/png")

    mala = cli.post(
        f"/api/productos/{producto['id']}/imagenes", {"imagen_base64": "no-es-base64!!"}
    )
    assert mala.status == 422, mala

    assert cli.get(f"/api/productos/{producto['id']}").json()["imagenes_ids"] == [imagen["id"]]
    assert cli.delete(f"/api/imagenes/{imagen['id']}").status == 204
    assert cli.get(f"/api/imagenes/{imagen['id']}").status == 404


def test_carrito_y_checkout():
    cli = nuevo_cliente()
    comprador = _crear(cli, "comprador@test.com", direccion="Av. Siempre Viva 742")
    producto = cli.post(
        "/api/productos",
        {"nombre": "Shampoo Hipoalergénico", "categoria": "higiene", "precio": "8990", "stock": 10},
    ).json()

    vacio = cli.get(f"/api/carrito/{comprador['id']}").json()
    assert vacio["items"] == [] and vacio["total"] == 0.0, vacio

    agregado = cli.post(
        f"/api/carrito/{comprador['id']}", {"producto_id": producto["id"], "cantidad": 2}
    )
    assert agregado.status == 200, agregado
    assert agregado.json()["total"] == 17980.0, agregado.json()

    sin_stock = cli.post(
        f"/api/carrito/{comprador['id']}", {"producto_id": producto["id"], "cantidad": 50}
    )
    assert sin_stock.status == 409, sin_stock

    ajustado = cli.put(
        f"/api/carrito/{comprador['id']}/{producto['id']}", {"cantidad": 3}
    ).json()
    assert ajustado["total_items"] == 3, ajustado

    pedido = cli.post(
        "/api/checkout", {"usuario_id": comprador["id"], "metodo_pago": "tarjeta"}
    )
    assert pedido.status == 201, pedido
    pedido = pedido.json()
    assert pedido["total"] == 26970.0 and pedido["direccion"] == "Av. Siempre Viva 742"
    assert len(pedido["items"]) == 1 and pedido["items"][0]["cantidad"] == 3

    # El stock bajó, el carrito quedó vacío y el pedido quedó registrado.
    assert cli.get(f"/api/productos/{producto['id']}").json()["stock"] == 7
    assert cli.get(f"/api/carrito/{comprador['id']}").json()["items"] == []
    assert cli.post("/api/checkout", {"usuario_id": comprador["id"]}).status == 422
    assert len(cli.get("/api/pedidos", params={"usuario_id": comprador["id"]}).json()) == 1


def test_checkout_es_transaccional():
    """Si un producto no tiene stock, no se descuenta ninguno de los otros."""
    cli = nuevo_cliente()
    comprador = _crear(cli, "transaccion@test.com")
    bueno = cli.post(
        "/api/productos", {"nombre": "Collar Reflectante", "categoria": "accesorio",
                           "precio": "5000", "stock": 10}
    ).json()
    escaso = cli.post(
        "/api/productos", {"nombre": "Correa Retráctil", "categoria": "accesorio",
                           "precio": "9000", "stock": 5}
    ).json()

    cli.post(f"/api/carrito/{comprador['id']}", {"producto_id": bueno["id"], "cantidad": 2})
    cli.post(f"/api/carrito/{comprador['id']}", {"producto_id": escaso["id"], "cantidad": 5})
    # El stock del segundo desaparece entre el carrito y el pago.
    cli.post(f"/api/productos/{escaso['id']}/stock", {"cantidad": -4})

    fallido = cli.post("/api/checkout", {"usuario_id": comprador["id"]})
    assert fallido.status == 409, fallido
    assert cli.get(f"/api/productos/{bueno['id']}").json()["stock"] == 10
    assert cli.get(f"/api/carrito/{comprador['id']}").json()["total_items"] == 7
    assert cli.get("/api/pedidos").json() == []


def test_autorizacion_por_rol():
    app, cli = cliente_con_auth()
    _crear_directo(app, "admin@test.com", "administrador")
    cli.post(
        "/api/auth/register",
        {"email": "cliente@test.com", "password": PASSWORD, "nombre": "Ceci", "apellidos": "Cliente"},
    )
    token_admin = cli.post(
        "/api/auth/login", {"email": "admin@test.com", "password": PASSWORD}
    ).json()["access_token"]
    token_cliente = cli.post(
        "/api/auth/login", {"email": "cliente@test.com", "password": PASSWORD}
    ).json()["access_token"]

    cuerpo = {"codigo": "cardiologia", "nombre": "Cardiología"}
    assert cli.post("/api/especialidades", cuerpo).status == 401
    assert cli.post(
        "/api/especialidades", cuerpo, headers={"Authorization": f"Bearer {token_cliente}"}
    ).status == 403
    assert cli.post(
        "/api/especialidades", cuerpo, headers={"Authorization": f"Bearer {token_admin}"}
    ).status == 201
    # Las lecturas públicas siguen abiertas.
    assert cli.get("/api/especialidades").status == 200


def test_estadisticas_del_panel():
    cli = nuevo_cliente()
    admin = _crear(cli, "stats@test.com", "administrador")
    tutor = _crear(cli, "stats-cliente@test.com")
    especie = cli.get("/api/especies").json()[0]
    cli.post(
        "/api/mascotas",
        {"cliente_id": tutor["id"], "especie_id": especie["id"], "nombre": "Nube",
         "sexo": "Hembra", "color": "blanco", "peso": 5.0},
    )
    cli.post("/api/productos", {"nombre": "Arena Sanitaria", "categoria": "higiene",
                                "precio": "6990", "stock": 2, "stock_minimo": 5})

    stats = cli.get("/api/dashboard/stats")
    assert stats.status == 200, stats
    datos = stats.json()
    assert datos["total_usuarios"] == 2 and datos["total_clientes"] == 1
    assert datos["total_mascotas"] == 1 and datos["productos_stock_bajo"] == 1
    assert datos["ingresos_totales"] == 0.0

    # El registro de usuarios deja rastro en la bitácora del sistema.
    actividad = cli.get("/api/actividad").json()
    assert any(a["tipo"] == "registro" for a in actividad), actividad
    assert admin["tipo"] == "administrador"


def test_especialidades_y_perfil_veterinario():
    cli = nuevo_cliente()
    vet = _crear(cli, "perfil-vet@test.com", "veterinario", documento="1122334")
    cirugia = cli.post("/api/especialidades", {"codigo": "cirugia", "nombre": "Cirugía"}).json()
    derma = cli.post("/api/especialidades", {"codigo": "derma", "nombre": "Dermatología"}).json()

    repetida = cli.post("/api/especialidades", {"codigo": "cirugia", "nombre": "Otra"})
    assert repetida.status == 409, repetida

    perfil = cli.put(
        f"/api/users/{vet['id']}/perfil-veterinario",
        {"activo": True, "especialidades_ids": [cirugia["id"], derma["id"]]},
    )
    assert perfil.status == 200, perfil
    assert perfil.json()["activo"] is True

    ficha = cli.get(f"/api/users/{vet['id']}").json()
    assert sorted(ficha["especialidades"]) == ["Cirugía", "Dermatología"], ficha

    inexistente = cli.put(
        f"/api/users/{vet['id']}/perfil-veterinario", {"especialidades_ids": [999]}
    )
    assert inexistente.status == 404, inexistente


# --------------------------------------------------------------------------
# Regresiones de la auditoría de la API
# --------------------------------------------------------------------------
def test_recuperacion_resiste_fuerza_bruta():
    cli = nuevo_cliente()
    _crear(cli, "bruta@test.com")
    real = cli.post("/api/auth/password/recuperar", {"email": "bruta@test.com"}).json()[
        "codigo_debug"
    ]
    erroneos = [f"{(int(real) + i) % 1_000_000:06d}" for i in range(1, 6)]
    for codigo in erroneos:
        r = cli.post(
            "/api/auth/password/restablecer",
            {"email": "bruta@test.com", "codigo": codigo, "password_nueva": "otraClave123"},
        )
        assert r.status == 401, r

    # Cada fallo quedó guardado pese al rollback: el código real ya no sirve.
    bloqueado = cli.post(
        "/api/auth/password/restablecer",
        {"email": "bruta@test.com", "codigo": real, "password_nueva": "otraClave123"},
    )
    assert bloqueado.status == 401, bloqueado


def test_autorizacion_por_propietario():
    app, cli = cliente_con_auth()
    _crear_directo(app, "jefa@test.com", "administrador")
    vet_id = _crear_directo(app, "doc@test.com", "veterinario")
    ana = _crear(cli, "ana@test.com")
    beto = _crear(cli, "beto@test.com")
    h_admin, h_vet = _token(cli, "jefa@test.com"), _token(cli, "doc@test.com")
    h_ana, h_beto = _token(cli, "ana@test.com"), _token(cli, "beto@test.com")

    # Registro: el público sólo crea clientes; el personal lo crea un admin.
    datos_vet = {"email": "nuevo-vet@test.com", "password": PASSWORD, "nombre": "Vera",
                 "apellidos": "Vet", "tipo": "veterinario"}
    assert cli.post("/api/auth/register", datos_vet).status == 401
    assert cli.post("/api/auth/register", datos_vet, headers=h_ana).status == 403
    assert cli.post("/api/auth/register", datos_vet, headers=h_admin).status == 201

    # Usuarios: cada uno edita lo suyo, y el rol sólo lo cambia un admin.
    assert cli.put(f"/api/users/{ana['id']}", {"telefono": "555"}).status == 401
    assert cli.put(f"/api/users/{ana['id']}", {"telefono": "555"}, headers=h_beto).status == 403
    assert cli.put(f"/api/users/{ana['id']}", {"telefono": "555"}, headers=h_ana).status == 200
    assert cli.put(f"/api/users/{ana['id']}", {"tipo": "administrador"}, headers=h_ana).status == 403
    assert cli.get("/api/users", headers=h_ana).status == 403
    assert cli.get("/api/users", headers=h_vet).status == 200
    assert cli.get(f"/api/users/{beto['id']}", headers=h_ana).status == 403
    assert cli.put(
        f"/api/users/{vet_id}/perfil-veterinario", {"documento": "1"}, headers=h_ana
    ).status == 403

    # Carrito y pedidos: sólo el dueño (o el personal).
    assert cli.get(f"/api/carrito/{beto['id']}", headers=h_ana).status == 403
    assert cli.get(f"/api/carrito/{ana['id']}", headers=h_ana).status == 200
    assert cli.get(f"/api/carrito/{ana['id']}", headers=h_vet).status == 200
    assert cli.get("/api/pedidos", params={"usuario_id": beto["id"]}, headers=h_ana).status == 403
    assert cli.get("/api/pedidos", headers=h_ana).status == 200
    assert cli.post(
        "/api/checkout", {"usuario_id": beto["id"], "items": []}, headers=h_ana
    ).status == 403

    # Mascotas: un cliente sólo registra y ve las suyas.
    especie = cli.get("/api/especies").json()[0]
    mascota = {"especie_id": especie["id"], "nombre": "Pelusa", "sexo": "Hembra", "color": "blanco"}
    assert cli.post("/api/mascotas", {**mascota, "cliente_id": beto["id"]}, headers=h_ana).status == 403
    propia = cli.post("/api/mascotas", {**mascota, "cliente_id": ana["id"]}, headers=h_ana)
    assert propia.status == 201, propia
    assert cli.get(f"/api/mascotas/{propia.json()['id']}", headers=h_beto).status == 403
    assert cli.get("/api/mascotas", headers=h_beto).json() == []
    assert cli.put(
        f"/api/mascotas/{propia.json()['id']}", {"cliente_id": beto["id"]}, headers=h_ana
    ).status == 403

    # Datos clínicos y del panel: nada sin sesión.
    for ruta in ("/api/historiales-medicos", "/api/citas", "/api/adopciones/solicitudes"):
        assert cli.get(ruta).status == 401, ruta
        assert cli.get(ruta, params={"cliente_id": beto["id"]}, headers=h_ana).status == 403, ruta
    assert cli.get("/api/dashboard/stats", headers=h_ana).status == 403
    assert cli.get("/api/dashboard/stats", headers=h_admin).status == 200
    assert cli.get("/api/actividad", headers=h_ana).status == 403


def _agenda_basica(cli):
    vet = _crear(cli, "agenda-vet@test.com", "veterinario")
    tutor = _crear(cli, "agenda-tutor@test.com")
    especie = cli.get("/api/especies").json()[0]
    mascota = cli.post(
        "/api/mascotas",
        {"cliente_id": tutor["id"], "especie_id": especie["id"], "nombre": "Kira",
         "sexo": "Hembra", "color": "canela"},
    ).json()
    servicio = cli.post(
        "/api/servicios",
        {"nombre": "Vacunación", "descripcion": "Vacunas", "veterinarios_ids": [vet["id"]]},
    ).json()
    base = {"mascota_id": mascota["id"], "veterinario_id": vet["id"],
            "servicio_id": servicio["id"], "motivo": "Vacuna anual"}
    return vet, tutor, base


def test_reprogramar_cita_respeta_la_agenda():
    cli = nuevo_cliente()
    _vet, tutor, base = _agenda_basica(cli)
    manana = (datetime.now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    primera = cli.post("/api/citas", {**base, "fecha_hora": manana.isoformat()}).json()
    segunda = cli.post(
        "/api/citas", {**base, "fecha_hora": (manana + timedelta(hours=2)).isoformat()}
    ).json()
    ruta = f"/api/citas/{segunda['id']}"

    assert cli.put(ruta, {"fecha_hora": manana.isoformat()}).status == 409
    pasado = (datetime.now() - timedelta(days=2)).isoformat()
    assert cli.put(ruta, {"fecha_hora": pasado}).status == 409
    assert cli.put(ruta, {"veterinario_id": tutor["id"]}).status == 422

    # Cambiar sólo las notas no revalida la agenda y moverla a un hueco libre sí vale.
    assert cli.put(ruta, {"notas": "Traer cartilla"}).status == 200
    libre = (manana + timedelta(hours=4)).isoformat()
    movida = cli.put(ruta, {"fecha_hora": libre})
    assert movida.status == 200 and movida.json()["fecha_hora"].startswith(libre[:16]), movida
    assert cli.get(f"/api/citas/{primera['id']}").json()["fecha_hora"].startswith(
        manana.isoformat()[:16]
    )


def test_cita_con_zona_horaria():
    cli = nuevo_cliente()
    _vet, _tutor, base = _agenda_basica(cli)
    local = (datetime.now() + timedelta(days=2)).replace(hour=11, minute=0, second=0, microsecond=0)
    con_zona = local.astimezone().isoformat()  # p. ej. 2026-09-28T11:00:00-05:00
    creada = cli.post("/api/citas", {**base, "fecha_hora": con_zona})
    assert creada.status == 201, creada
    assert creada.json()["fecha_hora"].startswith(local.isoformat()[:16]), creada.json()

    utc = cli.post("/api/citas", {**base, "fecha_hora": "2099-01-01T15:00:00Z"})
    assert utc.status == 201, utc


def test_contrato_del_cliente_spa():
    cli = nuevo_cliente()
    vet = _crear(cli, "spa-vet@test.com", "veterinario")
    tutor = _crear(cli, "spa-tutor@test.com")
    especie = cli.get("/api/especies").json()[0]

    # Las notas del revisor llegan como `notas_revisor`.
    mascota = cli.post(
        "/api/mascotas",
        {"especie_id": especie["id"], "nombre": "Bruno", "sexo": "Macho", "color": "gris"},
    ).json()
    cli.put(f"/api/adopciones/mascotas/{mascota['id']}/publicar")
    solicitud = cli.post(
        "/api/adopciones/solicitudes", {"mascota_id": mascota["id"], "cliente_id": tutor["id"]}
    ).json()
    rechazada = cli.put(
        f"/api/adopciones/solicitudes/{solicitud['id']}/rechazar",
        {"revisor_id": vet["id"], "notas_revisor": "Falta visita domiciliaria"},
    )
    assert rechazada.json()["notas_revisor"] == "Falta visita domiciliaria", rechazada.json()

    # Checkout con los items en el cuerpo: el carrito del SPA vive en el navegador.
    pienso = cli.post(
        "/api/productos",
        {"nombre": "Pienso Gato", "categoria": "alimento", "precio": 20, "stock": 3,
         "tipo_animal": "gato"},
    ).json()
    collar = cli.post(
        "/api/productos",
        {"nombre": "Collar Azul", "categoria": "accesorio", "precio": 8, "stock": 3,
         "tipo_animal": "perro"},
    ).json()
    cli.post(f"/api/carrito/{tutor['id']}", {"producto_id": collar["id"], "cantidad": 1})
    pedido = cli.post(
        "/api/checkout",
        {"usuario_id": tutor["id"], "metodo_pago": "tarjeta", "direccion": "Calle 2",
         "items": [{"producto_id": pienso["id"], "cantidad": 2}]},
    )
    assert pedido.status == 201, pedido
    assert pedido.json()["pedido_id"] == pedido.json()["id"]
    assert pedido.json()["total"] == 40.0, pedido.json()
    assert cli.get(f"/api/productos/{pienso['id']}").json()["stock"] == 1
    # La compra directa no toca el carrito guardado.
    assert cli.get(f"/api/carrito/{tutor['id']}").json()["total_items"] == 1

    # Filtros de la API anterior: `search` y `tipo_animal`.
    buscados = cli.get("/api/productos", params={"search": "collar"}).json()
    assert [p["nombre"] for p in buscados] == ["Collar Azul"], buscados
    para_gato = cli.get("/api/productos", params={"tipo_animal": "gato"}).json()
    assert [p["nombre"] for p in para_gato] == ["Pienso Gato"], para_gato


def test_produccion_exige_clave_propia():
    try:
        create_app(Config(ruta_bd=":memory:", entorno="produccion", secreto_jwt=SECRETO_DESARROLLO))
    except RuntimeError:
        pass
    else:
        raise AssertionError("arrancó en producción con la clave JWT de desarrollo")
    create_app(Config(ruta_bd=":memory:", entorno="produccion", secreto_jwt="clave-propia"))


def test_historial_sin_cita():
    cli = nuevo_cliente()
    vet = _crear(cli, "hist-vet@test.com", "veterinario")
    tutor = _crear(cli, "hist-tutor@test.com")
    especie = cli.get("/api/especies").json()[0]
    mascota = cli.post(
        "/api/mascotas",
        {"cliente_id": tutor["id"], "especie_id": especie["id"], "nombre": "Lola",
         "sexo": "Hembra", "color": "blanco"},
    ).json()
    ficha = {"diagnostico": "Otitis leve", "tratamiento": "Gotas óticas 7 días"}

    # Urgencia sin cita previa: como la manda el frontend (cita_id null).
    sin_cita = cli.post(
        "/api/historiales-medicos",
        {**ficha, "cita_id": None, "mascota_id": mascota["id"], "veterinario_id": vet["id"]},
    )
    assert sin_cita.status == 201, sin_cita
    assert sin_cita.json()["cita_id"] is None
    assert sin_cita.json()["mascota_nombre"] == "Lola"
    por_mascota = cli.get("/api/historiales-medicos", params={"mascota_id": mascota["id"]})
    assert [h["id"] for h in por_mascota.json()] == [sin_cita.json()["id"]]
    por_cliente = cli.get("/api/historiales-medicos", params={"cliente_id": tutor["id"]})
    assert len(por_cliente.json()) == 1

    # Sin cita hacen falta la mascota y quien firma.
    assert cli.post("/api/historiales-medicos", {**ficha, "veterinario_id": vet["id"]}).status == 422
    assert cli.post("/api/historiales-medicos", {**ficha, "mascota_id": mascota["id"]}).status == 422
    assert cli.post(
        "/api/historiales-medicos",
        {**ficha, "mascota_id": 9999, "veterinario_id": vet["id"]},
    ).status == 404

    # Con cita: la mascota sale de ella y la cita queda Completada.
    servicio = cli.post(
        "/api/servicios", {"nombre": "Otología", "descripcion": "Oídos", "veterinarios_ids": [vet["id"]]}
    ).json()
    manana = (datetime.now() + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
    cita = cli.post(
        "/api/citas",
        {"mascota_id": mascota["id"], "veterinario_id": vet["id"], "servicio_id": servicio["id"],
         "fecha_hora": manana.isoformat(), "motivo": "Revisión de oídos"},
    ).json()
    con_cita = cli.post("/api/historiales-medicos", {**ficha, "cita_id": cita["id"]})
    assert con_cita.status == 201, con_cita
    assert con_cita.json()["mascota_id"] == mascota["id"]
    assert cli.get(f"/api/citas/{cita['id']}").json()["estado"] == "Completada"

    otra = cli.post(
        "/api/mascotas",
        {"cliente_id": tutor["id"], "especie_id": especie["id"], "nombre": "Nala",
         "sexo": "Hembra", "color": "negro"},
    ).json()
    cruzada = cli.post(
        "/api/historiales-medicos", {**ficha, "cita_id": cita["id"], "mascota_id": otra["id"]}
    )
    assert cruzada.status in (409, 422), cruzada

    # Borrar la cita no borra la ficha clínica.
    cli.delete(f"/api/citas/{cita['id']}")
    ficha_guardada = cli.get(f"/api/historiales-medicos/{con_cita.json()['id']}")
    assert ficha_guardada.status == 200 and ficha_guardada.json()["cita_id"] is None


class _BuzonFalso:
    """Adaptador de prueba del puerto `Notificaciones`."""

    def __init__(self, falla: bool = False):
        self.enviados = []
        self.falla = falla

    def codigo_recuperacion(self, usuario, codigo):
        if self.falla:
            from app.domain.errors import ServicioNoDisponibleError

            raise ServicioNoDisponibleError("SMTP caído")
        self.enviados.append((usuario.email, codigo.codigo))


def test_recuperacion_envia_el_codigo_por_correo():
    ruta = os.path.join(tempfile.mkdtemp(prefix="mundopeludo-correo-"), "prueba.db")
    configuracion = Config(
        ruta_bd=ruta, secreto_jwt="s", exigir_auth=True, correo_host="smtp.ejemplo.com"
    )
    app = create_app(configuracion)
    buzon = _BuzonFalso()
    app.state.contenedor.servicios.notificaciones = buzon
    cli = crear_cliente(app)
    _crear(cli, "olvido@test.com")

    r = cli.post("/api/auth/password/recuperar", {"email": "olvido@test.com"})
    assert r.status == 200, r
    # Con correo configurado el código NO viaja en la respuesta.
    assert "codigo_debug" not in r.json(), r.json()
    assert len(buzon.enviados) == 1 and buzon.enviados[0][0] == "olvido@test.com"
    codigo = buzon.enviados[0][1]
    restablecida = cli.post(
        "/api/auth/password/restablecer",
        {"email": "olvido@test.com", "codigo": codigo, "password_nueva": "nuevaClave123"},
    )
    assert restablecida.status == 200, restablecida

    # Correo inexistente: misma respuesta y ningún envío.
    r = cli.post("/api/auth/password/recuperar", {"email": "nadie@test.com"})
    assert r.status == 200 and len(buzon.enviados) == 1

    # Si el SMTP falla: 503 y no queda un código activo que nadie recibió.
    app.state.contenedor.servicios.notificaciones = _BuzonFalso(falla=True)
    fallo = cli.post("/api/auth/password/recuperar", {"email": "olvido@test.com"})
    assert fallo.status == 503, fallo


def test_correo_smtp_arma_el_mensaje():
    import smtplib

    from app.domain.model.sistema import CodigoRecuperacion
    from app.domain.model.usuario import Usuario
    from app.infrastructure.notificaciones.adaptadores import CorreoSmtp

    llamadas = {}

    class SmtpFalso:
        def __init__(self, host, puerto, timeout=None):
            llamadas["servidor"] = (host, puerto)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def starttls(self, context=None):
            llamadas["tls"] = True

        def login(self, usuario, password):
            llamadas["login"] = (usuario, password)

        def send_message(self, mensaje):
            llamadas["mensaje"] = mensaje

    original = smtplib.SMTP
    smtplib.SMTP = SmtpFalso
    try:
        CorreoSmtp(
            "smtp.gmail.com", 587, "sistema@test.com", "clave",
            "MundoPeludo <sistema@test.com>",
        ).codigo_recuperacion(
            Usuario(email="ana@test.com", nombre="Ana", apellidos="Pérez"),
            CodigoRecuperacion(usuario_id=1, codigo="123456"),
        )
    finally:
        smtplib.SMTP = original

    assert llamadas["servidor"] == ("smtp.gmail.com", 587)
    assert llamadas["tls"] is True and llamadas["login"] == ("sistema@test.com", "clave")
    mensaje = llamadas["mensaje"]
    assert mensaje["To"] == "ana@test.com" and mensaje["From"] == "MundoPeludo <sistema@test.com>"
    assert "Recuperación" in mensaje["Subject"]
    partes = {p.get_content_type(): p.get_content() for p in mensaje.iter_parts()}
    assert "123456" in partes["text/plain"] and "123456" in partes["text/html"]
    assert "Ana Pérez" in partes["text/plain"]


def test_api_cerrada_por_defecto():
    anterior = os.environ.pop("MP_REQUIRE_AUTH", None)
    try:
        assert Config().exigir_auth is True
    finally:
        if anterior is not None:
            os.environ["MP_REQUIRE_AUTH"] = anterior


def test_crear_superusuario_por_consola():
    import subprocess

    ruta = os.path.join(tempfile.mkdtemp(prefix="mundopeludo-su-"), "prueba.db")
    entorno = {**os.environ, "MP_DB_PATH": ruta, "MP_SUPERUSER_PASSWORD": PASSWORD,
               "PYTHONIOENCODING": "utf-8"}
    script = os.path.join(RAIZ, "crear_superusuario.py")
    argumentos = [sys.executable, script, "--no-interactivo", "--email", "raiz@test.com",
                  "--nombre", "Rita", "--apellidos", "Raíz"]
    creado = subprocess.run(argumentos, env=entorno, capture_output=True, text=True, encoding="utf-8")
    assert creado.returncode == 0, creado.stderr
    repetido = subprocess.run(argumentos, env=entorno, capture_output=True, text=True, encoding="utf-8")
    assert repetido.returncode == 1 and "Ya existe" in repetido.stderr, repetido.stderr

    app = create_app(Config(ruta_bd=ruta, secreto_jwt="s", exigir_auth=True, correo_host=""))
    cli = crear_cliente(app)
    sesion = _token(cli, "raiz@test.com")
    assert cli.get("/api/users", headers=sesion).status == 200


def test_null_en_actualizacion_no_borra_datos():
    cli = nuevo_cliente()
    producto = cli.post(
        "/api/productos",
        {"nombre": "Arena Gato", "categoria": "higiene", "precio": 12, "stock": 8,
         "descuento_porcentaje": 10},
    ).json()
    r = cli.put(
        f"/api/productos/{producto['id']}",
        {"precio": None, "descuento_porcentaje": None, "stock": None, "disponible_online": None,
         "activo": None},
    )
    assert r.status == 200, r
    assert r.json()["precio"] == 12.0 and r.json()["stock"] == 8, r.json()

    usuario = _crear(cli, "nulos@test.com")
    r = cli.put(f"/api/users/{usuario['id']}", {"is_active": None, "nombre": None})
    assert r.status == 200 and r.json()["activo"] is True, r

    especie = cli.get("/api/especies").json()[0]
    mascota = cli.post(
        "/api/mascotas",
        {"especie_id": especie["id"], "nombre": "Nieve", "sexo": "Hembra", "color": "blanco",
         "peso": 6, "edad_anos": 3},
    ).json()
    r = cli.put(f"/api/mascotas/{mascota['id']}", {"peso": None, "edad_anos": None, "activo": None})
    assert r.status == 200 and r.json()["peso"] == 6 and r.json()["edad_anos"] == 3, r


def test_entradas_fuera_de_rango_no_dan_500():
    cli = nuevo_cliente()
    enorme = 10**20
    assert cli.get(f"/api/mascotas/{enorme}").status in (404, 422)
    assert cli.get("/api/mascotas", params={"cliente_id": str(enorme)}).status == 422
    assert cli.get("/api/citas", params={"desde": "-1"}).status == 422
    for token in ("ñññ.b.c", "a.ñ.c", "a" * 5000):
        r = cli.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status == 401, (token[:10], r)


def test_checkout_concurrente_no_sobrevende():
    import threading

    cli = nuevo_cliente()
    producto = cli.post(
        "/api/productos", {"nombre": "Última Pelota", "categoria": "juguete", "precio": 4, "stock": 1}
    ).json()
    compradores = [_crear(cli, f"prisa{i}@test.com")["id"] for i in range(8)]
    barrera = threading.Barrier(len(compradores))
    estados = []

    def comprar(usuario_id):
        barrera.wait()
        r = cli.post(
            "/api/checkout",
            {"usuario_id": usuario_id, "items": [{"producto_id": producto["id"], "cantidad": 1}]},
        )
        estados.append(r.status)

    hilos = [threading.Thread(target=comprar, args=(u,)) for u in compradores]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    assert sorted(estados) == [201] + [409] * (len(compradores) - 1), estados
    assert cli.get(f"/api/productos/{producto['id']}").json()["stock"] == 0
    assert len(cli.get("/api/pedidos").json()) == 1


def test_bajas_bloquean_nuevas_operaciones():
    cli = nuevo_cliente()
    vet = _crear(cli, "baja-vet@test.com", "veterinario")
    tutor = _crear(cli, "baja-tutor@test.com")
    especie = cli.get("/api/especies").json()[0]
    servicio = cli.post(
        "/api/servicios", {"nombre": "Chequeo", "descripcion": "x", "veterinarios_ids": [vet["id"]]}
    ).json()
    mascota = cli.post(
        "/api/mascotas",
        {"cliente_id": tutor["id"], "especie_id": especie["id"], "nombre": "Coco",
         "sexo": "Macho", "color": "marrón"},
    ).json()
    manana = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    cita = {"mascota_id": mascota["id"], "veterinario_id": vet["id"], "servicio_id": servicio["id"],
            "fecha_hora": manana.isoformat(), "motivo": "Chequeo general"}

    cli.delete(f"/api/mascotas/{mascota['id']}")
    assert cli.post("/api/citas", cita).status == 409
    ficha = {"mascota_id": mascota["id"], "veterinario_id": vet["id"],
             "diagnostico": "Sano", "tratamiento": "Ninguno"}
    assert cli.post("/api/historiales-medicos", ficha).status == 409

    otra = cli.post(
        "/api/mascotas",
        {"cliente_id": tutor["id"], "especie_id": especie["id"], "nombre": "Luna",
         "sexo": "Hembra", "color": "gris"},
    ).json()
    cli.delete(f"/api/users/{vet['id']}")
    assert cli.post("/api/citas", {**cita, "mascota_id": otra["id"]}).status == 409

    refugio = cli.post(
        "/api/mascotas", {"especie_id": especie["id"], "nombre": "Sol", "sexo": "Macho", "color": "negro"}
    ).json()
    cli.put(f"/api/adopciones/mascotas/{refugio['id']}/publicar")
    cli.delete(f"/api/mascotas/{refugio['id']}")
    solicitud = cli.post(
        "/api/adopciones/solicitudes", {"mascota_id": refugio["id"], "cliente_id": tutor["id"]}
    )
    assert solicitud.status == 409, solicitud


def _ejecutar_todo() -> int:
    pruebas = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fallos = 0
    for prueba in pruebas:
        try:
            prueba()
            print(f"  OK    {prueba.__name__}")
        except AssertionError as exc:
            fallos += 1
            print(f"  FALLO {prueba.__name__}: {exc}")
        except Exception as exc:  # pragma: no cover
            fallos += 1
            print(f"  ERROR {prueba.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(pruebas) - fallos}/{len(pruebas)} pruebas correctas")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(_ejecutar_todo())
