"""Fixtures compartidas. Los usuarios de prueba usan contraseñas aleatorias generadas al vuelo."""
import secrets

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from cuentas.models import Rol, Usuario
from red.models import Empresa, Planta, Ruta


@pytest.fixture(autouse=True)
def _limpiar_cache():
    """El límite de intentos de login usa la caché local: se reinicia entre pruebas."""
    cache.clear()


def _cliente(usuario):
    cliente = APIClient()
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(usuario)}")
    return cliente


@pytest.fixture
def clave():
    return secrets.token_urlsafe(16)


@pytest.fixture
def admin(db, clave):
    return Usuario.objects.create_user("admin_t", password=clave, rol=Rol.ADMINISTRADOR)


@pytest.fixture
def analista(db, clave):
    return Usuario.objects.create_user("analista_t", password=clave, rol=Rol.ANALISTA)


@pytest.fixture
def otro_analista(db, clave):
    return Usuario.objects.create_user("analista_t2", password=clave, rol=Rol.ANALISTA)


@pytest.fixture
def cliente_admin(admin):
    return _cliente(admin)


@pytest.fixture
def cliente_analista(analista):
    return _cliente(analista)


@pytest.fixture
def cliente_otro(otro_analista):
    return _cliente(otro_analista)


@pytest.fixture
def anonimo():
    return APIClient()


@pytest.fixture
def red_cp01(db):
    """Caso CP-01: óptimo conocido = 64 (E1->P1 12 t, E2->P2 8 t)."""
    e1 = Empresa.objects.create(codigo="E1", nombre="E1", oferta=12)
    e2 = Empresa.objects.create(codigo="E2", nombre="E2", oferta=8)
    p1 = Planta.objects.create(codigo="P1", nombre="P1", capacidad=15)
    p2 = Planta.objects.create(codigo="P2", nombre="P2", capacidad=10)
    for e, p, costo in [(e1, p1, 4), (e1, p2, 6), (e2, p1, 5), (e2, p2, 2)]:
        Ruta.objects.create(empresa=e, planta=p, costo_unitario=costo)
    return {"E1": e1, "E2": e2, "P1": p1, "P2": p2}
