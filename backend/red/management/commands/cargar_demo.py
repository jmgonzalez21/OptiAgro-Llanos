"""Carga datos de demostración FICTICIOS: 10 empresas, 4 plantas y las 40 rutas entre ellas."""
from django.core.management.base import BaseCommand

from red.demo import AVISO, cargar_datos_demo


class Command(BaseCommand):
    help = "Carga 10 empresas y 4 plantas con rutas (datos FICTICIOS, marcados con ficticio=True). Es idempotente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar", action="store_true", help="Borra antes todos los registros marcados como ficticios."
        )

    def handle(self, *args, **opciones):
        self.stdout.write(self.style.WARNING(AVISO))
        r = cargar_datos_demo(limpiar=opciones["limpiar"])
        self.stdout.write(
            self.style.SUCCESS(f"Listo: {r['empresas']} empresas, {r['plantas']} plantas y {r['rutas']} rutas (todas FICTICIAS).")
        )
