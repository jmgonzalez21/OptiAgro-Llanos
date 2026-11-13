"""Arranque con datos demo (OPTIAGRO_CARGAR_DEMO=true): crea usuarios y datos FICTICIOS SOLO si no existen."""
import os

from django.core.management.base import BaseCommand, CommandError

from cuentas.models import Rol, Usuario
from red.demo import AVISO, cargar_datos_demo, demo_cargado


class Command(BaseCommand):
    help = (
        "Crea los usuarios demo (admin y analista) que no existan y carga los datos demo FICTICIOS si aún no hay "
        "ninguno. Nunca modifica usuarios ni datos existentes. Las contraseñas SOLO vienen de DEMO_ADMIN_PASSWORD y "
        "DEMO_ANALISTA_PASSWORD (entorno); si falta alguna, no se crea el usuario correspondiente y el comando falla."
    )

    def handle(self, *args, **opciones):
        definiciones = [
            (os.environ.get("DEMO_ADMIN_USERNAME") or "admin_demo", "DEMO_ADMIN_PASSWORD", Rol.ADMINISTRADOR),
            (os.environ.get("DEMO_ANALISTA_USERNAME") or "analista_demo", "DEMO_ANALISTA_PASSWORD", Rol.ANALISTA),
        ]
        faltantes = []
        for username, variable, rol in definiciones:
            if Usuario.objects.filter(username=username).exists():
                self.stdout.write(f"Usuario '{username}' ya existe: sin cambios.")
                continue
            clave = os.environ.get(variable)
            if not clave:
                faltantes.append(variable)
                continue
            es_admin = rol == Rol.ADMINISTRADOR
            usuario = Usuario(username=username, rol=rol, is_staff=es_admin, is_superuser=es_admin, email=f"{username}@ejemplo.invalid")
            usuario.set_password(clave)
            usuario.save()
            self.stdout.write(self.style.SUCCESS(f"Usuario demo creado: {username} (rol {rol})."))
        if demo_cargado():
            self.stdout.write("Los datos demo ya existen: sin cambios.")
        else:
            self.stdout.write(self.style.WARNING(AVISO))
            r = cargar_datos_demo()
            self.stdout.write(self.style.SUCCESS(f"Datos demo FICTICIOS cargados: {r['empresas']} empresas, {r['plantas']} plantas, {r['rutas']} rutas."))
        if faltantes:
            raise CommandError(f"Faltan variables de entorno para crear usuarios demo: {', '.join(faltantes)}.")
