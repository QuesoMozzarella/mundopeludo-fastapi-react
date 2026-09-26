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

from app.bootstrap import create_app  # noqa: E402
from app.config import Config  # noqa: E402
from cliente import crear_cliente  # noqa: E402

PASSWORD = "mundopeludo2025"


def nuevo_cliente():
    ruta = os.path.join(tempfile.mkdtemp(prefix="mundopeludo-test-"), "prueba.db")
    app = create_app(Config(ruta_bd=ruta, secreto_jwt="secreto-de-prueba", exigir_auth=False))
    return crear_cliente(app)


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
    ruta = os.path.join(tempfile.mkdtemp(prefix="mundopeludo-auth-"), "prueba.db")
    app = create_app(Config(ruta_bd=ruta, secreto_jwt="secreto", exigir_auth=True))
    cli = crear_cliente(app)

    cli.post(
        "/api/auth/register",
        {"email": "admin@test.com", "password": PASSWORD, "nombre": "Ada", "apellidos": "Admin",
         "tipo": "administrador"},
    )
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
