import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from cuentas.models import Usuario
from red.models import Empresa, Planta, Ruta
from servicios.conversion import construir_parametros
from servicios.ejecucion import resolver_exacto


def test_cargar_demo_es_ficticio_e_idempotente(db, capsys):
    call_command("cargar_demo")
    call_command("cargar_demo")
    assert Empresa.objects.count() == 10 and Planta.objects.count() == 4 and Ruta.objects.count() == 40
    assert not Empresa.objects.filter(ficticio=False).exists()
    assert not Planta.objects.filter(ficticio=False).exists()
    assert not Ruta.objects.filter(ficticio=False).exists()
    assert set(Planta.objects.values_list("municipio", flat=True)) == {"Villavicencio", "Restrepo", "Granada", "Puerto Gaitán"}
    assert "FICTICIOS" in capsys.readouterr().out
    villavicencio = Planta.objects.get(codigo="P1")
    assert (float(villavicencio.latitud), float(villavicencio.longitud)) == (4.142, -73.6266)
    assert (float(Planta.objects.get(codigo="P2").latitud), float(Planta.objects.get(codigo="P4").longitud)) == (4.259, -72.082)
    assert not Empresa.objects.filter(latitud__isnull=True).exists()
    assert all(2 < float(e.latitud) < 5 and -75 < float(e.longitud) < -71 for e in Empresa.objects.all())  # dentro del Meta
    r = resolver_exacto(construir_parametros())
    assert r.estado == "OPTIMAL" and r.verificacion["valida"]


def test_cargar_demo_limpiar_conserva_datos_reales(db):
    Empresa.objects.create(codigo="REAL1", nombre="Real", oferta=1)
    call_command("cargar_demo")
    call_command("cargar_demo", "--limpiar")
    assert Empresa.objects.filter(ficticio=False).count() == 1 and Empresa.objects.count() == 11


def test_crear_usuarios_demo_exige_contrasenas_del_entorno(db, monkeypatch):
    for var in ("DEMO_ADMIN_PASSWORD", "DEMO_ANALISTA_PASSWORD"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(CommandError):
        call_command("crear_usuarios_demo")
    assert Usuario.objects.count() == 0


def test_crear_usuarios_demo(db, monkeypatch):
    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "Prueba-Admin-9183!")
    monkeypatch.setenv("DEMO_ANALISTA_PASSWORD", "Prueba-Analista-7712!")
    call_command("crear_usuarios_demo")
    admin = Usuario.objects.get(username="admin_demo")
    analista = Usuario.objects.get(username="analista_demo")
    assert admin.rol == "administrador" and admin.is_staff and admin.check_password("Prueba-Admin-9183!")
    assert analista.rol == "analista" and not analista.is_staff and analista.check_password("Prueba-Analista-7712!")
