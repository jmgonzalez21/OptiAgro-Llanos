"""Distancias por carretera: OSRM simulado (sin red)."""
import pytest

from red.models import Empresa, Planta, Ruta
from servicios import rutas_viales as rv

GEOM = {"type": "LineString", "coordinates": [[-73.6, 4.1], [-73.5, 4.2], [-72.1, 4.3]]}


@pytest.fixture
def osrm(monkeypatch):
    """OSRM simulado: table -> 100 km entre todo par; route -> GEOM. Registra las llamadas."""
    llamadas = []

    def falso(ruta, params=None):
        llamadas.append((ruta, params))
        if "/table/" in ruta:
            n_o = len(params["sources"].split(";"))
            n_d = len(params["destinations"].split(";"))
            return {"code": "Ok", "distances": [[100_040.0] * n_d for _ in range(n_o)]}
        return {"code": "Ok", "routes": [{"distance": 123_456.0, "geometry": GEOM}]}

    monkeypatch.setattr(rv, "_get_json", falso)
    return llamadas


@pytest.fixture
def osrm_caido(monkeypatch):
    def falla(ruta, params=None):
        raise rv.ErrorOSRM("sin conexión")

    monkeypatch.setattr(rv, "_get_json", falla)


@pytest.fixture
def nodos(db):
    e = Empresa.objects.create(codigo="E1", nombre="E1", oferta=5, latitud=3.9, longitud=-73.7)
    p = Planta.objects.create(codigo="P1", nombre="P1", capacidad=9, latitud=4.14, longitud=-73.62)
    return e, p


def test_distancias_lote_divide_y_redondea(osrm, settings):
    settings.OPTIAGRO_OSRM = {**settings.OPTIAGRO_OSRM, "MAX_COORDENADAS": 4, "PAUSA_LOTES": 0}
    pts = [(3.0 + i / 10, -73.0) for i in range(5)]
    m = rv.distancias_lote(pts, pts[:3])
    assert len(m) == 5 and all(len(f) == 3 for f in m) and m[4][2] == 100.0
    assert len(osrm) > 1  # varias peticiones table
    assert all(len(p["sources"].split(";")) + len(p["destinations"].split(";")) <= 4 for _, p in osrm)


def test_crear_ruta_calcula_distancia_por_carretera(cliente_admin, nodos, osrm):
    r = cliente_admin.post("/api/v1/rutas/", {"empresa": "E1", "planta": "P1", "tarifa_km_ton": 500}, format="json")
    assert r.status_code == 201, r.data
    assert r.data["distancia_km"] == 100.0 and r.data["distancia_fuente"] == "carretera" and r.data["aviso"] is None
    assert r.data["costo_unitario"] == 50_000.0


def test_crear_ruta_respaldo_estimada_si_osrm_falla(cliente_admin, nodos, osrm_caido):
    r = cliente_admin.post("/api/v1/rutas/", {"empresa": "E1", "planta": "P1", "tarifa_km_ton": 500}, format="json")
    assert r.status_code == 201, r.data
    assert r.data["distancia_fuente"] == "estimada" and r.data["aviso"]
    assert 20 < r.data["distancia_km"] < 60  # ~27 km en línea recta x 1,3


def test_crear_ruta_con_distancia_es_manual_y_sin_coordenadas_da_400(cliente_admin, nodos, osrm):
    r = cliente_admin.post(
        "/api/v1/rutas/", {"empresa": "E1", "planta": "P1", "distancia_km": 10, "tarifa_km_ton": 100}, format="json"
    )
    assert r.status_code == 201 and r.data["distancia_fuente"] == "manual" and osrm == []
    Empresa.objects.create(codigo="E2", nombre="E2", oferta=1)
    r = cliente_admin.post("/api/v1/rutas/", {"empresa": "E2", "planta": "P1", "tarifa_km_ton": 100}, format="json")
    assert r.status_code == 400


def test_recalcular_respeta_manuales_y_permisos(cliente_admin, cliente_analista, anonimo, nodos, osrm):
    e, p = nodos
    e2 = Empresa.objects.create(codigo="E2", nombre="E2", oferta=1, latitud=3.8, longitud=-73.8)
    auto = Ruta.objects.create(empresa=e, planta=p, distancia_km=1, tarifa_km_ton=10, distancia_fuente="estimada")
    manual = Ruta.objects.create(empresa=e2, planta=p, distancia_km=7, tarifa_km_ton=10)
    url = "/api/v1/rutas/recalcular-distancias/"
    assert anonimo.post(url, {}, format="json").status_code == 401
    assert cliente_analista.post(url, {}, format="json").status_code == 403
    r = cliente_admin.post(url, {}, format="json")
    assert r.status_code == 200 and r.data["actualizadas"] == 1 and r.data["estimadas"] == 0
    auto.refresh_from_db(), manual.refresh_from_db()
    assert (auto.distancia_km, auto.distancia_fuente, auto.costo_unitario) == (100.0, "carretera", 1000.0)
    assert (manual.distancia_km, manual.distancia_fuente) == (7, "manual")
    r = cliente_admin.post(url, {"ids": [manual.id], "incluir_manuales": True}, format="json")
    manual.refresh_from_db()
    assert r.data["actualizadas"] == 1 and manual.distancia_fuente == "carretera"


def test_recalcular_sin_osrm_estima_con_aviso(cliente_admin, nodos, osrm_caido):
    e, p = nodos
    Ruta.objects.create(empresa=e, planta=p, distancia_km=1, tarifa_km_ton=10, distancia_fuente="carretera")
    r = cliente_admin.post("/api/v1/rutas/recalcular-distancias/", {}, format="json")
    assert r.status_code == 200 and r.data["estimadas"] == 1 and r.data["aviso"]
    assert Ruta.objects.get().distancia_fuente == "estimada"


def test_mover_nodo_recalcula_rutas_no_manuales(cliente_admin, nodos, osrm):
    e, p = nodos
    ruta = Ruta.objects.create(empresa=e, planta=p, distancia_km=1, tarifa_km_ton=10, distancia_fuente="carretera")
    r = cliente_admin.patch(f"/api/v1/empresas/{e.id}/", {"latitud": 3.95}, format="json")
    assert r.status_code == 200
    ruta.refresh_from_db()
    assert ruta.distancia_km == 100.0
    # sin cambio de coordenadas no se consulta OSRM
    n = len(osrm)
    cliente_admin.patch(f"/api/v1/empresas/{e.id}/", {"oferta": 6}, format="json")
    assert len(osrm) == n


def test_trayecto_se_cachea_y_permisos(cliente_analista, anonimo, nodos, osrm):
    e, p = nodos
    ruta = Ruta.objects.create(empresa=e, planta=p, distancia_km=5, tarifa_km_ton=10)
    url = f"/api/v1/rutas/{ruta.id}/trayecto/"
    assert anonimo.get(url).status_code == 401
    r1 = cliente_analista.get(url)
    assert r1.status_code == 200 and r1.data["trayecto"] == GEOM and r1.data["cacheado"] is False
    r2 = cliente_analista.get(url)
    assert r2.data["cacheado"] is True and sum("/route/" in c[0] for c in osrm) == 1
    assert cliente_analista.get(f"/api/v1/rutas/{ruta.id}/").data["tiene_trayecto"] is True
    multi = cliente_analista.get(f"/api/v1/rutas/trayectos/?ids={ruta.id}")
    assert multi.status_code == 200 and len(multi.data["trayectos"]) == 1
    assert cliente_analista.get("/api/v1/rutas/trayectos/?ids=" + ",".join(map(str, range(31)))).status_code == 400


def test_trayecto_sin_osrm_devuelve_linea_recta_sin_cachear(cliente_analista, nodos, osrm_caido):
    e, p = nodos
    ruta = Ruta.objects.create(empresa=e, planta=p, distancia_km=5, tarifa_km_ton=10)
    r = cliente_analista.get(f"/api/v1/rutas/{ruta.id}/trayecto/")
    assert r.status_code == 200 and r.data["fuente"] == "estimada" and r.data["aviso"]
    ruta.refresh_from_db()
    assert ruta.trayecto is None
