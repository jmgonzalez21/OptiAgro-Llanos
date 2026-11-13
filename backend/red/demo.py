"""Carga de datos de demostración FICTICIOS: 10 empresas, 4 plantas y las 40 rutas entre ellas.

Lógica compartida por ``manage.py cargar_demo``, ``manage.py inicializar_demo`` y ``POST /api/v1/demo/cargar/``.
"""
from django.db import transaction

from .models import Empresa, Planta, Ruta, TipoDemanda

# Empresas FICTICIAS: coordenadas plausibles (cerca del casco urbano del municipio, con un desplazamiento
# arbitrario). No corresponden a ninguna empresa real.
EMPRESAS = [
    ("Acacías", 3.9870, -73.7580), ("Cumaral", 4.2700, -73.4860), ("Guamal", 3.8800, -73.7700),
    ("San Martín", 3.6960, -73.6940), ("Puerto López", 4.0870, -72.9610), ("Castilla La Nueva", 3.8280, -73.6880),
    ("Cabuyaro", 4.2870, -72.7970), ("El Dorado", 3.7450, -73.8340), ("Lejanías", 3.5280, -74.0210),
    ("Mapiripán", 2.8940, -72.1340),
]  # fmt: skip
# (codigo, municipio, capacidad t/semana, latitud, longitud): coordenadas reales aproximadas; capacidades FICTICIAS.
PLANTAS = [
    ("P1", "Villavicencio", 40, 4.1420, -73.6266),
    ("P2", "Restrepo", 32, 4.2590, -73.5680),
    ("P3", "Granada", 30, 3.5450, -73.7080),
    ("P4", "Puerto Gaitán", 34, 4.3140, -72.0820),
]
AVISO = (
    "DATOS FICTICIOS DE DEMOSTRACIÓN: no corresponden a empresas, plantas, distancias ni tarifas reales. "
    "Las fuentes disponibles no ofrecen una matriz regional validada."
)




def demo_cargado() -> bool:
    """True si ya existe alguna empresa o planta FICTICIA de demostración."""
    return Empresa.objects.filter(ficticio=True).exists() or Planta.objects.filter(ficticio=True).exists()


@transaction.atomic
def cargar_datos_demo(limpiar: bool = False) -> dict:
    """Idempotente: crea o actualiza (por código E1..E10, P1..P4) los registros ficticios. Devuelve conteos."""
    if limpiar:
        # Las rutas se eliminan en cascada junto con sus empresas/plantas.
        Empresa.objects.filter(ficticio=True).delete()
        Planta.objects.filter(ficticio=True).delete()
        Ruta.objects.filter(ficticio=True).delete()
    empresas = []
    for i, (municipio, lat, lon) in enumerate(EMPRESAS, start=1):
        empresa, _ = Empresa.objects.update_or_create(
            codigo=f"E{i}",
            defaults={
                "nombre": f"Agroempresa FICTICIA {i}",
                "municipio": municipio,
                "oferta": 10 + i % 4,  # t/semana
                "latitud": round(lat + ((i * 7) % 5 - 2) * 0.01, 6),  # ficticia
                "longitud": round(lon + ((i * 3) % 5 - 2) * 0.01, 6),  # ficticia
                "activa": True,
                "ficticio": True,
            },
        )
        empresas.append(empresa)
    plantas = []
    for idx, (codigo, municipio, capacidad, lat, lon) in enumerate(PLANTAS):
        planta, _ = Planta.objects.update_or_create(
            codigo=codigo,
            defaults={
                "nombre": f"Planta FICTICIA {municipio}",
                "municipio": municipio,
                "capacidad": capacidad,
                "costo_operacion_ton": float(1000 + 500 * idx),  # COP/t, ficticio
                "latitud": lat,
                "longitud": lon,
                "tipo_demanda": TipoDemanda.CAPACIDAD_MAXIMA,
                "activa": True,
                "ficticio": True,
            },
        )
        plantas.append(planta)
    rutas = 0
    for i, empresa in enumerate(empresas, start=1):
        for j, planta in enumerate(plantas, start=1):
            ruta = Ruta.objects.filter(empresa=empresa, planta=planta).first() or Ruta(empresa=empresa, planta=planta)
            ruta.distancia_km = float(15 + (i * 17 + j * 29 + i * j * 5) % 85)  # km, ficticio
            ruta.tarifa_km_ton = float(420 + 15 * j)  # COP por t·km, ficticio
            ruta.limite = None
            ruta.activa = True
            ruta.ficticio = True
            ruta.save()  # costo_unitario = distancia x tarifa
            rutas += 1
    return {"empresas": len(empresas), "plantas": len(plantas), "rutas": rutas}
