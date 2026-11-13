import pytest

from escenarios.models import Ejecucion
from red.models import Planta

EXACTO = "/api/v1/optimizacion/exacto/"
GENETICO = "/api/v1/optimizacion/genetico/"
SENSIBILIDAD = "/api/v1/optimizacion/sensibilidad/"
REPORTE = "/api/v1/optimizacion/reporte/"
CONFIG_AG = {"poblacion": 30, "generaciones": 40, "semilla": 7}


def test_exacto_cp01_es_64(cliente_analista, red_cp01):
    r = cliente_analista.post(EXACTO, {}, format="json")
    assert r.status_code == 200, r.data
    res = r.data["resultado"]
    assert res["estado"] == "OPTIMAL" and res["factible"] is True
    assert res["objetivo"] == pytest.approx(64)
    assert res["verificacion"]["valida"] is True
    asignado = {(a["empresa_id"], a["planta_id"]): a["cantidad"] for a in res["asignaciones"]}
    assert asignado[("E1", "P1")] == pytest.approx(12) and asignado[("E2", "P2")] == pytest.approx(8)
    assert "planta:P1" in res["duales"] and "oferta:E1" in res["duales"]
    ejecucion = Ejecucion.objects.get(pk=r.data["ejecucion_id"])
    assert ejecucion.metodo == "exacto" and ejecucion.objetivo == pytest.approx(64)
    assert ejecucion.resultado.datos["estado"] == "OPTIMAL"


def test_exacto_sin_guardar(cliente_analista, red_cp01):
    r = cliente_analista.post(EXACTO, {"guardar": False}, format="json")
    assert r.status_code == 200 and r.data["ejecucion_id"] is None
    assert Ejecucion.objects.count() == 0


def test_exacto_ignora_elementos_inactivos(cliente_admin, red_cp01):
    # Sin P1 (inactiva) solo quedan 10 t de capacidad para 20 t de oferta -> 400 claro.
    Planta.objects.filter(codigo="P1").update(activa=False)
    r = cliente_admin.post(EXACTO, {}, format="json")
    assert r.status_code == 400
    assert any("capacidad" in e.lower() for e in r.data["errores"])


def test_exacto_inviable_da_400_claro(cliente_analista, red_cp01):
    Planta.objects.filter(codigo="P1").update(capacidad=5)
    r = cliente_analista.post(EXACTO, {}, format="json")
    assert r.status_code == 400
    assert r.data["detail"] and isinstance(r.data["errores"], list) and r.data["errores"]


def test_exacto_red_vacia_400(cliente_analista, db):
    r = cliente_analista.post(EXACTO, {}, format="json")
    assert r.status_code == 400 and r.data["errores"]


def test_exacto_escenario_inexistente_404(cliente_analista, red_cp01):
    assert cliente_analista.post(EXACTO, {"escenario_id": 99999}, format="json").status_code == 404


def test_exacto_modo_invalido_400(cliente_analista, red_cp01):
    assert cliente_analista.post(EXACTO, {"modo_oferta": "otro"}, format="json").status_code == 400


def test_escenario_guardado_se_reutiliza(cliente_analista, cliente_admin, red_cp01):
    r = cliente_analista.post("/api/v1/escenarios/", {"nombre": "base"}, format="json")
    assert r.status_code == 201 and r.data["resumen"]["rutas"] == 4
    esc = r.data["id"]
    # cambiar la red no afecta al escenario guardado
    cliente_admin.patch(f"/api/v1/empresas/{red_cp01['E1'].id}/", {"oferta": 1}, format="json")
    r = cliente_analista.post(EXACTO, {"escenario_id": esc}, format="json")
    assert r.status_code == 200 and r.data["resultado"]["objetivo"] == pytest.approx(64)
    assert Ejecucion.objects.get(pk=r.data["ejecucion_id"]).escenario_id == esc
    assert cliente_analista.get(f"/api/v1/escenarios/{esc}/").data["parametros"]["empresas"]


def test_borrar_escenario_solo_dueno_o_admin(cliente_analista, cliente_otro, cliente_admin, red_cp01):
    esc = cliente_analista.post("/api/v1/escenarios/", {"nombre": "mio"}, format="json").data["id"]
    assert cliente_otro.delete(f"/api/v1/escenarios/{esc}/").status_code == 403
    assert cliente_admin.delete(f"/api/v1/escenarios/{esc}/").status_code == 204


def test_genetico_factible_y_reproducible(cliente_analista, red_cp01):
    a = cliente_analista.post(GENETICO, CONFIG_AG, format="json")
    b = cliente_analista.post(GENETICO, CONFIG_AG, format="json")
    assert a.status_code == 200, a.data
    res = a.data["resultado"]
    assert res["factible"] is True and res["estado"] == "FEASIBLE"
    assert res["objetivo"] >= 64 - 1e-6  # nunca mejor que el óptimo exacto
    assert res["objetivo"] == b.data["resultado"]["objetivo"]
    assert len(res["metricas"]["convergencia"]) == CONFIG_AG["generaciones"]
    ejecucion = Ejecucion.objects.get(pk=a.data["ejecucion_id"])
    assert ejecucion.configuracion["semilla"] == 7 and ejecucion.configuracion["poblacion"] == 30


def test_genetico_acepta_todos_los_parametros(cliente_analista, red_cp01):
    cuerpo = {"poblacion": 20, "generaciones": 10, "cruce": 0.9, "mutacion": 0.2, "semilla": 1, "elitismo": 1}
    r = cliente_analista.post(GENETICO, cuerpo, format="json")
    assert r.status_code == 200
    cfg = Ejecucion.objects.get(pk=r.data["ejecucion_id"]).configuracion
    assert {k: cfg[k] for k in cuerpo} == cuerpo and cfg["seleccion"] == "torneo" and cfg["tipo_cruce"] == "un_punto"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"poblacion": 1},
        {"poblacion": 10**6},
        {"generaciones": 0},
        {"cruce": 1.5},
        {"mutacion": -0.1},
        {"poblacion": 10, "elitismo": 10},
        {"semilla": "abc"},
    ],
)
def test_genetico_parametros_invalidos_400(cliente_analista, red_cp01, cuerpo):
    r = cliente_analista.post(GENETICO, cuerpo, format="json")
    assert r.status_code == 400
    assert r.data["detail"] and r.data["errores"]


def test_genetico_trabajo_excesivo_400(cliente_analista, red_cp01, settings):
    settings.OPTIAGRO = {**settings.OPTIAGRO, "AG_MAX_TRABAJO": 1000}
    r = cliente_analista.post(GENETICO, {"poblacion": 100, "generaciones": 100}, format="json")
    assert r.status_code == 400 and "costosa" in r.data["detail"]


def test_sensibilidad_capacidad_y_duales(cliente_analista, red_cp01):
    Planta.objects.filter(codigo="P1").update(capacidad=10)  # P1 pasa a ser cuello de botella
    cuerpo = {"variaciones": [{"tipo": "capacidad", "ids": ["P1"], "porcentajes": [-10, 10]}], "incluir_ag": False}
    r = cliente_analista.post(SENSIBILIDAD, cuerpo, format="json")
    assert r.status_code == 200, r.data
    res = r.data["resultado"]
    assert res["base"]["exacto"]["estado"] == "OPTIMAL"
    assert res["base"]["exacto"]["objetivo"] == pytest.approx(68)
    # precio sombra: una tonelada más de capacidad en P1 ahorra 2 COP (6 - 4)
    assert res["precios_sombra"]["plantas"]["P1"] == pytest.approx(-2)
    p1 = next(p for p in res["plantas"] if p["planta"] == "P1")
    assert p1["cuello_de_botella"] is True and p1["utilizacion_pct"] == pytest.approx(100)
    filas = {f["porcentaje"]: f for f in res["escenarios"]}
    assert filas[10]["exacto"]["objetivo"] == pytest.approx(66)
    assert filas[10]["variacion_objetivo"] == pytest.approx(-2)
    # P1 = 9 -> capacidad total 19 < oferta 20: el escenario es inviable y así se informa
    assert filas[-10]["exacto"]["estado"] == "INVALID_INPUT" and filas[-10]["exacto"]["objetivo"] is None
    assert filas[10]["genetico"] is None
    assert Ejecucion.objects.get(pk=r.data["ejecucion_id"]).metodo == "sensibilidad"


def test_sensibilidad_oferta_costos_varias_plantas(cliente_analista, red_cp01):
    cuerpo = {
        "variaciones": [
            {"tipo": "oferta", "ids": ["E1"], "porcentajes": [-10]},
            {"tipo": "costo", "porcentajes": [10, 20]},  # todos los costos (p. ej. combustible)
            {"tipo": "capacidad", "ids": ["P1", "P2"], "porcentajes": [-50]},
        ]
    }
    r = cliente_analista.post(SENSIBILIDAD, cuerpo, format="json")
    assert r.status_code == 200, r.data
    filas = r.data["resultado"]["escenarios"]
    assert len(filas) == 4
    assert filas[0]["exacto"]["objetivo"] == pytest.approx(59.2)
    assert filas[1]["exacto"]["objetivo"] == pytest.approx(70.4)
    assert filas[2]["exacto"]["objetivo"] == pytest.approx(76.8)
    # capacidades a la mitad (7.5 + 5 = 12.5 < 20): inviable en modo base -> el escenario lo informa
    assert filas[3]["exacto"]["estado"] == "INVALID_INPUT" and filas[3]["exacto"]["objetivo"] is None


def test_sensibilidad_con_ag_devuelve_gap(cliente_analista, red_cp01):
    cuerpo = {
        "variaciones": [{"tipo": "costo", "porcentajes": [10]}],
        "incluir_ag": True,
        "config_ag": CONFIG_AG,
        "guardar": False,
    }
    r = cliente_analista.post(SENSIBILIDAD, cuerpo, format="json")
    assert r.status_code == 200, r.data
    fila = r.data["resultado"]["escenarios"][0]
    assert fila["genetico"]["factible"] is True
    assert fila["gap_pct"] >= -1e-6
    assert r.data["resultado"]["base"]["gap_pct"] is not None


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"variaciones": []},
        {"variaciones": [{"tipo": "otro", "porcentajes": [10]}]},
        {"variaciones": [{"tipo": "oferta", "porcentajes": []}]},
        {"variaciones": [{"tipo": "oferta", "porcentajes": [-150]}]},
        {"variaciones": [{"tipo": "capacidad", "ids": ["NOPE"], "porcentajes": [10]}]},
        {"variaciones": [{"tipo": "costo", "ids": ["E1->P9"], "porcentajes": [10]}]},
    ],
)
def test_sensibilidad_invalida_400(cliente_analista, red_cp01, cuerpo):
    r = cliente_analista.post(SENSIBILIDAD, cuerpo, format="json")
    assert r.status_code == 400
    assert r.data["detail"] and r.data["errores"]


def test_sensibilidad_demasiados_escenarios_400(cliente_analista, red_cp01, settings):
    settings.OPTIAGRO = {**settings.OPTIAGRO, "SENSIBILIDAD_MAX_ESCENARIOS": 3}
    cuerpo = {"variaciones": [{"tipo": "costo", "porcentajes": [1, 2, 3]}, {"tipo": "oferta", "porcentajes": [1]}]}
    assert cliente_analista.post(SENSIBILIDAD, cuerpo, format="json").status_code == 400


def test_reporte_comparativo(cliente_analista, red_cp01):
    cuerpo = {"config_ag": CONFIG_AG, "variaciones": [{"tipo": "oferta", "ids": ["E1"], "porcentajes": [-10]}]}
    r = cliente_analista.post(REPORTE, cuerpo, format="json")
    assert r.status_code == 200, r.data
    rep = r.data["resultado"]
    assert rep["exacto"]["objetivo"] == pytest.approx(64) and rep["exacto"]["estado"] == "OPTIMAL"
    assert rep["genetico"]["factible"] is True
    comp = rep["comparacion"]
    assert comp["gap_pct"] == pytest.approx((rep["genetico"]["objetivo"] - 64) / 64 * 100)
    assert comp["gap_pct"] >= -1e-6 and comp["ratio_tiempo"] is not None
    assert rep["exacto"]["duracion_ms"] > 0 and rep["genetico"]["duracion_ms"] > 0
    assert rep["modelo"]["empresas"] == 2 and rep["modelo"]["rutas"] == 4
    assert len(rep["sensibilidad"]["escenarios"]) == 1
    assert Ejecucion.objects.get(pk=r.data["ejecucion_id"]).metodo == "reporte"


def test_reporte_sin_sensibilidad(cliente_analista, red_cp01):
    r = cliente_analista.post(REPORTE, {"config_ag": CONFIG_AG}, format="json")
    assert r.status_code == 200 and r.data["resultado"]["sensibilidad"] is None


def test_historial_por_rol(cliente_analista, cliente_otro, cliente_admin, red_cp01):
    a = cliente_analista.post(EXACTO, {}, format="json").data["ejecucion_id"]
    cliente_analista.post(GENETICO, CONFIG_AG, format="json")
    b = cliente_otro.post(EXACTO, {}, format="json").data["ejecucion_id"]

    propias = cliente_analista.get("/api/v1/ejecuciones/")
    assert propias.status_code == 200 and propias.data["count"] == 2
    assert all(e["usuario"] == "analista_t" for e in propias.data["results"])
    assert cliente_analista.get("/api/v1/ejecuciones/?metodo=genetico").data["count"] == 1
    assert cliente_analista.get(f"/api/v1/ejecuciones/{b}/").status_code == 404  # ajena
    detalle = cliente_analista.get(f"/api/v1/ejecuciones/{a}/")
    assert detalle.status_code == 200 and detalle.data["resultado"]["estado"] == "OPTIMAL"
    assert detalle.data["parametros"]["empresas"]

    todas = cliente_admin.get("/api/v1/ejecuciones/")
    assert todas.data["count"] == 3
    assert cliente_admin.get("/api/v1/ejecuciones/?usuario=analista_t2").data["count"] == 1
    assert cliente_admin.get("/api/v1/ejecuciones/?estado=OPTIMAL").data["count"] == 2
