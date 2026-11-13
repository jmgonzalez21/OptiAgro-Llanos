"""Crea un administrador y un analista de demostración. Las contraseñas SOLO vienen del entorno."""
import os

from django.core.management.base import BaseCommand, CommandError

from cuentas.models import Rol, Usuario


class Command(BaseCommand):
    help = (
        "Crea/actualiza un administrador y un analista de demostración. Requiere las variables de entorno "
        "DEMO_ADMIN_PASSWORD y DEMO_ANALISTA_PASSWORD (y opcionalmente DEMO_ADMIN_USERNAME, "
        "DEMO_ANALISTA_USERNAME). Las contraseñas nunca se imprimen ni se guardan en el repositorio."
    )

    def handle(self, *args, **opciones):
        definiciones = [
            (os.environ.get("DEMO_ADMIN_USERNAME") or "admin_demo", "DEMO_ADMIN_PASSWORD", Rol.ADMINISTRADOR, True),
            (os.environ.get("DEMO_ANALISTA_USERNAME") or "analista_demo", "DEMO_ANALISTA_PASSWORD", Rol.ANALISTA, False),
        ]
        faltantes = [var for _, var, _, _ in definiciones if not os.environ.get(var)]
        if faltantes:
            raise CommandError(f"Defina las variables de entorno: {', '.join(faltantes)} (vea .env.example).")
        for username, variable, rol, es_admin in definiciones:
            usuario, creado = Usuario.objects.get_or_create(username=username)
            usuario.rol = rol
            usuario.is_staff = es_admin
            usuario.is_superuser = es_admin
            usuario.is_active = True
            usuario.email = usuario.email or f"{username}@ejemplo.invalid"
            usuario.set_password(os.environ[variable])
            usuario.save()
            self.stdout.write(self.style.SUCCESS(f"{'Creado' if creado else 'Actualizado'}: {username} (rol {rol})."))
