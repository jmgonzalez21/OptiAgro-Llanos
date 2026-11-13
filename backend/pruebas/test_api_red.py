import pytest

from red.models import Ruta


def test_analista_lee_pero_no_escribe(cliente_analista, red_cp01):
    assert cliente_analista.get("/api/v1/empresas/").status_code == 200
    assert cliente_analista.get("/api/v1/plantas/").status_code == 200
    assert cliente_analista.get("/api/v1/rutas/").status_code == 200
    assert cliente_analista.post("/api/v1/empresas/", {"codigo": "X1", "nombre": "X", "oferta": 1}, format="json").status_code == 403
    assert cliente_analista.patch(f"/api/v1/empresas/{red_cp01['E1'].id}/", {"oferta": 1}, format="json").status_code == 403
    assert cliente_analista.delete(f"/api/v1/plantas/{red_cp01['P1'].id}/").status_code == 403
    assert cliente_analista.put("/api/v1/red/matriz-costos/", {"rutas": []}, format="json").status_code == 403


def test_crud_empresas(cliente_admin):
    r = cliente_admin.post("/api/v1/empresas/", {"codigo": "E9", "nombre": "Nueva", "municipio": "Acacías", "oferta": 5.5}, format="json")
    assert r.status_code == 201, r.data
    pk = r.data["id"]
    assert cliente_admin.get(f"/api/v1/empresas/{pk}/").data["oferta"] == 5.5
    r = cliente_admin.patch(f"/api/v1/empresas/{pk}/", {"oferta": 7}, format="json")
    assert r.status_code == 200 and r.data["oferta"] == 7
    lista = cliente_admin.get("/api/v1/empresas/?search=Nueva")
    assert lista.data["count"] == 1
    assert cliente_admin.delete(f"/api/v1/empresas/{pk}/").status_code == 204
    assert cliente_admin.get(f"/api/v1/empresas/{pk}/").status_code == 404


def test_crud_plantas(cliente_admin):
    r = cliente_admin.post("/api/v1/plantas/", {"codigo": "PX", "nombre": "Planta X", "capacidad": 20}, format="json")
    assert r.status_code == 201, r.data
    assert r.data["tipo_demanda"] == "capacity_max"
    pk = r.data["id"]
    r = cliente_admin.patch(f"/api/v1/plantas/{pk}/", {"capacidad": 25, "activa": False}, format="json")
    assert r.status_code == 200 and r.data["capacidad"] == 25 and r.data["activa"] is False
    assert cliente_admin.get("/api/v1/plantas/?activa=false").data["count"] == 1
    assert cliente_admin.delete(f"/api/v1/plantas/{pk}/").status_code == 204


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"codigo": "E 1", "nombre": "x", "oferta": 1},  # código con espacio
        {"codigo": "E-1", "nombre": "x", "oferta": 1},  # guion no permitido
        {"codigo": "E1", "nombre": "x", "oferta": -3},  # oferta negativa
        {"codigo": "E1", "nombre": "x", "oferta": "nan"},  # no finito
        {"codigo": "E1", "nombre": "x"},  # falta oferta
    ],
)
def test_empresa_invalida_400(cliente_admin, cuerpo):
    r = cliente_admin.post("/api/v1/empresas/", cuerpo, format="json")
    assert r.status_code == 400
    assert r.data["detail"] and r.data["errores"]


def test_codigo_empresa_duplicado_400(cliente_admin, red_cp01):
    r = cliente_admin.post("/api/v1/empresas/", {"codigo": "E1", "nombre": "x", "oferta": 1}, format="json")
    assert r.status_code == 400 and "codigo" in r.data["errores"]


def test_crud_rutas(cliente_admin, red_cp01):
    Ruta.objects.all().delete()
    r = cliente_admin.post("/api/v1/rutas/", {"empresa": "E1", "planta": "P1", "costo_unitario": 4.5}, format="json")
    assert r.status_code == 201, r.data
    assert r.data["costo_unitario"] == 4.5 and r.data["empresa_nombre"] == "E1"
    pk = r.data["id"]
    # distancia x tarifa define el costo
    r = cliente_admin.patch(f"/api/v1/rutas/{pk}/", {"distancia_km": 50, "tarifa_km_ton": 100}, format="json")
    assert r.status_code == 200 and r.data["costo_unitario"] == 5000
    # un costo directo anula distancia y tarifa
    r = cliente_admin.patch(f"/api/v1/rutas/{pk}/", {"costo_unitario": 7}, format="json")
    assert r.status_code == 200
    assert r.data["costo_unitario"] == 7 and r.data["distancia_km"] is None and r.data["tarifa_km_ton"] is None
    assert cliente_admin.get("/api/v1/rutas/?empresa=E1&planta=P1").data["count"] == 1
    assert cliente_admin.delete(f"/api/v1/rutas/{pk}/").status_code == 204


def test_ruta_distancia_tarifa_sin_costo(cliente_admin, red_cp01):
    Ruta.objects.all().delete()
    r = cliente_admin.post("/api/v1/rutas/", {"empresa": "E2", "planta": "P2", "distancia_km": 10, "tarifa_km_ton": 450}, format="json")
    assert r.status_code == 201 and r.data["costo_unitario"] == 4500


def test_ruta_invalidas_400(cliente_admin, red_cp01):
    # duplicada
    assert cliente_admin.post("/api/v1/rutas/", {"empresa": "E1", "planta": "P1", "costo_unitario": 1}, format="json").status_code == 400
    Ruta.objects.all().delete()
    # sin costo definido
    r = cliente_admin.post("/api/v1/rutas/", {"empresa": "E1", "planta": "P1"}, format="json")
    assert r.status_code == 400 and "costo_unitario" in r.data["errores"]
    # empresa inexistente
    r = cliente_admin.post("/api/v1/rutas/", {"empresa": "NOPE", "planta": "P1", "costo_unitario": 1}, format="json")
    assert r.status_code == 400 and "empresa" in r.data["errores"]
    # costo negativo
    assert cliente_admin.post("/api/v1/rutas/", {"empresa": "E1", "planta": "P1", "costo_unitario": -1}, format="json").status_code == 400


def test_matriz_get(cliente_analista, red_cp01):
    r = cliente_analista.get("/api/v1/red/matriz-costos/")
    assert r.status_code == 200
    assert [e["codigo"] for e in r.data["empresas"]] == ["E1", "E2"]
    assert [p["codigo"] for p in r.data["plantas"]] == ["P1", "P2"]
    assert r.data["costos"] == [[4, 6], [5, 2]]
    assert len(r.data["rutas"]) == 4


def test_matriz_put_masivo(cliente_admin, red_cp01):
    cuerpo = {
        "rutas": [
            {"empresa": "E1", "planta": "P1", "costo_unitario": 40},
            {"empresa": "E2", "planta": "P2", "distancia_km": 10, "tarifa_km_ton": 3, "limite": 9},
        ]
    }
    r = cliente_admin.put("/api/v1/red/matriz-costos/", cuerpo, format="json")
    assert r.status_code == 200, r.data
    assert r.data["costos"] == [[40, 6], [5, 30]]
    ruta = Ruta.objects.get(empresa__codigo="E2", planta__codigo="P2")
    assert ruta.limite == 9 and ruta.costo_unitario == 30


def test_matriz_put_crea_ruta_faltante(cliente_admin, red_cp01):
    Ruta.objects.filter(empresa__codigo="E1", planta__codigo="P2").delete()
    r = cliente_admin.put("/api/v1/red/matriz-costos/", {"rutas": [{"empresa": "E1", "planta": "P2", "costo_unitario": 9}]}, format="json")
    assert r.status_code == 200 and r.data["costos"][0][1] == 9


def test_matriz_put_es_atomica_y_clara(cliente_admin, red_cp01):
    cuerpo = {
        "rutas": [
            {"empresa": "E1", "planta": "P1", "costo_unitario": 999},
            {"empresa": "ZZ", "planta": "P1", "costo_unitario": 1},
            {"empresa": "E1", "planta": "P1", "costo_unitario": 2},
        ]
    }
    r = cliente_admin.put("/api/v1/red/matriz-costos/", cuerpo, format="json")
    assert r.status_code == 400
    assert any("ZZ" in e for e in r.data["errores"]) and any("duplicado" in e for e in r.data["errores"])
    assert Ruta.objects.get(empresa__codigo="E1", planta__codigo="P1").costo_unitario == 4  # no se aplicó nada


def test_matriz_put_vacia_400(cliente_admin, red_cp01):
    assert cliente_admin.put("/api/v1/red/matriz-costos/", {"rutas": []}, format="json").status_code == 400


def test_coordenadas_empresa_y_planta(cliente_admin):
    r = cliente_admin.post(
        "/api/v1/empresas/",
        {"codigo": "EG", "nombre": "Geo", "oferta": 3, "latitud": 4.142, "longitud": -73.6266},
        format="json",
    )
    assert r.status_code == 201, r.data
    cuerpo = r.json()  # JSON renderizado: números, no cadenas
    assert cuerpo["latitud"] == 4.142 and cuerpo["longitud"] == -73.6266
    r = cliente_admin.post("/api/v1/plantas/", {"codigo": "PG", "nombre": "Geo", "capacidad": 3, "latitud": 4.3, "longitud": -72.1}, format="json")
    assert r.status_code == 201 and isinstance(r.json()["latitud"], float)
    # sin coordenadas siguen siendo válidas (null)
    r = cliente_admin.post("/api/v1/plantas/", {"codigo": "PN", "nombre": "Sin geo", "capacidad": 3}, format="json")
    assert r.status_code == 201 and r.data["latitud"] is None and r.data["longitud"] is None


@pytest.mark.parametrize("campo,valor", [("latitud", 91), ("latitud", -90.5), ("longitud", 181), ("longitud", -200), ("latitud", "abc")])
def test_coordenadas_fuera_de_rango_400(cliente_admin, campo, valor):
    r = cliente_admin.post("/api/v1/empresas/", {"codigo": "EX", "nombre": "x", "oferta": 1, campo: valor}, format="json")
    assert r.status_code == 400 and campo in r.data["errores"]
    r = cliente_admin.post("/api/v1/plantas/", {"codigo": "PX", "nombre": "x", "capacidad": 1, campo: valor}, format="json")
    assert r.status_code == 400 and campo in r.data["errores"]


def test_filtro_activa_true_oculta_estaciones_desactivadas(cliente_analista, red_cp01):
    red_cp01["P2"].activa = False
    red_cp01["P2"].save()
    red_cp01["E2"].activa = False
    red_cp01["E2"].save()
    plantas = cliente_analista.get("/api/v1/plantas/?activa=true").data["results"]
    empresas = cliente_analista.get("/api/v1/empresas/?activa=true").data["results"]
    assert [p["codigo"] for p in plantas] == ["P1"]
    assert [e["codigo"] for e in empresas] == ["E1"]
    assert cliente_analista.get("/api/v1/plantas/").data["count"] == 2  # sin filtro aparecen todas
