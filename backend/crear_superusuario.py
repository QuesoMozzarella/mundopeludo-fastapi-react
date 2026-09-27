"""Crea una cuenta de administrador desde la consola.

Es el equivalente a `python manage.py createsuperuser`: con la API cerrada, el
registro público sólo crea clientes, así que el primer administrador nace aquí.
Desde él se crean después, por la API, las cuentas de veterinario y de otros
administradores.

    python backend/crear_superusuario.py
    python backend/crear_superusuario.py --email admin@mundopeludo.com --nombre Ana --apellidos Ruiz

La contraseña siempre se pide sin eco. Para scripts se puede pasar en la
variable MP_SUPERUSER_PASSWORD junto con --no-interactivo.
"""
from __future__ import annotations

import argparse
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.entorno import cargar_env  # noqa: E402

cargar_env()  # antes de importar la configuración

from app.application.use_cases.autenticacion import RegistrarUsuario  # noqa: E402
from app.config import config  # noqa: E402
from app.domain.errors import DomainError  # noqa: E402
from app.domain.value_objects import TipoUsuario  # noqa: E402
from app.interfaces.http.deps import Contenedor  # noqa: E402


def _preguntar(etiqueta: str, valor: str | None) -> str:
    while not valor:
        valor = input(f"{etiqueta}: ").strip()
    return valor


def _password(interactivo: bool) -> str:
    if not interactivo:
        password = os.getenv("MP_SUPERUSER_PASSWORD", "")
        if not password:
            sys.exit("Falta MP_SUPERUSER_PASSWORD para el modo no interactivo.")
        return password
    while True:
        password = getpass.getpass("Contraseña: ")
        if password != getpass.getpass("Contraseña (otra vez): "):
            print("Las contraseñas no coinciden.\n")
            continue
        return password


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea un administrador de MundoPeludo.")
    parser.add_argument("--email")
    parser.add_argument("--nombre")
    parser.add_argument("--apellidos")
    parser.add_argument(
        "--no-interactivo",
        action="store_true",
        help="No pregunta nada; la contraseña sale de MP_SUPERUSER_PASSWORD",
    )
    args = parser.parse_args()
    interactivo = not args.no_interactivo

    if interactivo:
        email = _preguntar("Correo", args.email)
        nombre = _preguntar("Nombre", args.nombre)
        apellidos = _preguntar("Apellidos", args.apellidos)
    else:
        if not (args.email and args.nombre and args.apellidos):
            sys.exit("En modo no interactivo hacen falta --email, --nombre y --apellidos.")
        email, nombre, apellidos = args.email, args.nombre, args.apellidos
    password = _password(interactivo)

    contenedor = Contenedor(config)
    contenedor.preparar()
    try:
        with contenedor.db.unidad_de_trabajo() as conexion:
            repos = contenedor.repositorios(conexion)
            usuario = RegistrarUsuario(
                repos.usuarios,
                repos.perfiles_cliente,
                repos.perfiles_veterinario,
                contenedor.servicios.hasher,
                contenedor.servicios.reloj,
                repos.actividades,
            ).ejecutar(
                email=email,
                password=password,
                nombre=nombre,
                apellidos=apellidos,
                tipo=TipoUsuario.ADMINISTRADOR,
            )
    except DomainError as exc:
        print(f"No se creó el administrador: {exc.mensaje}", file=sys.stderr)
        return 1

    print(f"Administrador creado: {usuario.email} (id {usuario.id})")
    print(f"Base de datos: {config.descripcion_bd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
