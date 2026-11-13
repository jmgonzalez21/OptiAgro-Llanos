"""API fase 2: AG completo, sensibilidad con rangos y AG, costos del negocio, escalabilidad, demo, historial, docs/admin."""
import importlib
from datetime import date, timedelta

import pytest
from django.test import Client
from django.urls import clear_url_caches, set_urlconf

from escenarios.models import Ejecucion
from red.models import Empresa, Planta

EXACTO = "/api/v1/optimizacion/exacto/"
GENETICO = "/api/v1/optimizacion/genetico/"
SENSIBILIDAD = "/api/v1/optimizacion/sensibilidad/"
REPORTE = "/api/v1/optimizacion/reporte/"
ESCALABILIDAD = "/api/v1/optimizacion/escalabilidad/"
AG_RAPIDO = {"poblacion": 30, "generaciones": 30, "semilla": 5}


# --------------------------------------------------------------------------- AG por API
@pytest.mark.parametrize("seleccion,cruce", [("torneo", "un_punto"), ("ruleta", "dos_puntos"), ("ruleta", "un_punto"), ("torneo", "dos_puntos")])
def test_genetico_api_selecciones_y_cruces(cliente_analista, red_cp01, seleccion, cruce):
    cuerpo = {**AG_RAPIDO, "seleccion": seleccion, "tipo_cruce": cruce, "tamano_torneo": 5, "guardar": False}
    r = cliente_analista.post(GENETICO, cuerpo, format="json")
    assert r.status_code == 200, r.data
    m = r.data["resultado"]["metricas"]
    assert r.data["resultado"]["factible"] and m["seleccion"] == seleccion and m["tipo_cruce"] == cruce and m["tamano_torneo"] == 5
    assert len(m["convergencia"]) == len(m["convergencia_promedio"]) == AG_RAPIDO["generaciones"]
    assert r.data["resultado"]["asignaciones"][0]["costo_transporte"] >= 0


@pytest.mark.parametrize(
    "cuerpo",
    [{"seleccion": "azar"}, {"tipo_cruce": "tres"}, {"tamano_torneo": 1}, {"poblacion": 10, "tamano_torneo": 11}, {"inicializacion": "x"}],
)
def test_genetico_api_parametros_nuevos_invalidos_400(cliente_analista, red_cp01, cuerpo):
    r = cliente_analista.post(GENETICO, cuerpo, format="json")
    assert r.status_code == 400 and r.data["errores"]


def test_reporte_expone_configuracion_y_convergencia_promedio(cliente_analista, red_cp01):
    r = cliente_analista.post(REPORTE, {"config_ag": {**AG_RAPIDO, "seleccion": "ruleta", "tipo_cruce": "dos_puntos"}}, format="json")
    assert r.status_code == 200, r.data
    rep = r.data["resultado"]
    assert rep["configuracion_ag"]["seleccion"] == "ruleta" and rep["configuracion_ag"]["tipo_cruce"] == "dos_puntos"
    assert len(rep["genetico"]["convergencia_promedio"]) == 30 and rep["comparacion"]["gap_pct"] >= -1e-6


# --------------------------------------------------------------------------- sensibilidad completa
def test_sensibilidad_devuelve_rangos_y_exacto_mas_ag_por_defecto(cliente_analista, red_cp01):
    Planta.objects.filter(codigo="P1").update(capacidad=11)  # cuello de botella: P1 activa
    cuerpo = {
        "variaciones": [
            {"tipo": "capacidad", "ids": ["P1"], "porcentajes": [5, 20]},  # 11.55 (dentro de [10, 12]) y 13.2 (fuera)
            {"tipo": "combustible", "porcentajes": [10]},
        ],
        "config_ag": AG_RAPIDO,
        "guardar": False,
    }
    r = cliente_analista.post(SENSIBILIDAD, cuerpo, format="json")
    assert r.status_code == 200, r.data
    res = r.data["resultado"]
    assert res["base"]["exacto"]["objetivo"] == pytest.approx(66) and res["base"]["genetico"]["factible"]
    # rangos (null = infinito)
    rg = res["rangos"]
    assert rg["disponible"] is True and rg["metodo"] == "highs_ranging"
    cap = {f["id"]: f for f in rg["capacidad"]}
    assert (cap["P1"]["minimo"], cap["P1"]["maximo"], cap["P1"]["activa"]) == (10, 12, True)
    assert cap["P1"]["precio_sombra"] == pytest.approx(-2)
    assert (cap["P2"]["minimo"], cap["P2"]["maximo"]) == (9, None)
    ofe = {f["id"]: f for f in rg["oferta"]}
    assert (ofe["E1"]["minimo"], ofe["E1"]["maximo"]) == (11, 13)
    costos = {f["ruta"]: f for f in rg["costos"]}
    assert set(costos) == {"E1->P1", "E1->P2", "E2->P1", "E2->P2"}
    assert costos["E1->P1"]["maximo"] == 6 and costos["E1->P1"]["minimo"] is None
    # escenarios: exacto + AG, gap, tiempos, estados, cambios de asignación y base
    dentro, fuera, comb = res["escenarios"]
    assert dentro["dentro_de_rango"] is True and dentro["base_cambio"] is False
    assert dentro["exacto"]["objetivo"] == pytest.approx(66 - 2 * 0.55)
    assert fuera["dentro_de_rango"] is False and fuera["base_cambio"] is True
    assert fuera["exacto"]["objetivo"] == pytest.approx(64)
    assert fuera["asignaciones_cambiadas"] == 2  # E1->P1 sube a 12 y E1->P2 desaparece
    cambios = {(c["empresa"], c["planta"]): c for c in fuera["cambios_asignacion"]}
    assert cambios[("E1", "P1")]["base"] == pytest.approx(11) and cambios[("E1", "P1")]["escenario"] == pytest.approx(12)
    assert cambios[("E1", "P2")]["delta"] == pytest.approx(-1)
    for fila in (dentro, fuera, comb):
        assert fila["genetico"]["factible"] and fila["costo_ag"] >= fila["costo_exacto"] - 1e-6
        assert fila["gap_pct"] == pytest.approx((fila["costo_ag"] - fila["costo_exacto"]) / fila["costo_exacto"] * 100)
        assert fila["tiempo_exacto_ms"] > 0 and fila["tiempo_ag_ms"] > 0
        assert fila["estado_exacto"] == "OPTIMAL" and fila["estado_ag"] == "FEASIBLE"
    assert comb["tipo"] == "combustible" and comb["dentro_de_rango"] is None
    assert comb["exacto"]["objetivo"] > 66
    # resumen agregado
    assert res["resumen"]["escenarios"] == 3 and res["resumen"]["factibles_exacto"] == res["resumen"]["factibles_ag"] == 3
    assert res["resumen"]["gap_pct_maximo"] >= res["resumen"]["gap_pct_promedio"] >= -1e-6
    assert res["resumen"]["escenarios_con_cambio_de_base"] >= 1


def test_sensibilidad_solo_exacto_si_incluir_ag_false(cliente_analista, red_cp01):
    cuerpo = {"variaciones": [{"tipo": "oferta", "porcentajes": [-10]}], "incluir_ag": False, "guardar": False}
    fila = cliente_analista.post(SENSIBILIDAD, cuerpo, format="json").data["resultado"]["escenarios"][0]
    assert fila["genetico"] is None and fila["gap_pct"] is None and fila["costo_ag"] is None and fila["tiempo_ag_ms"] is None


def test_sensibilidad_escenario_inviable_se_informa_con_ambos_metodos(cliente_analista, red_cp01):
    cuerpo = {"variaciones": [{"tipo": "capacidad", "ids": ["P1", "P2"], "porcentajes": [-60]}], "config_ag": AG_RAPIDO, "guardar": False}
    fila = cliente_analista.post(SENSIBILIDAD, cuerpo, format="json").data["resultado"]["escenarios"][0]
    assert fila["estado_exacto"] == "INVALID_INPUT" and fila["estado_ag"] == "INVALID_INPUT"
    assert fila["base_cambio"] is None and fila["gap_pct"] is None and fila["cambios_asignacion"] == []


def test_sensibilidad_combustible_solo_toca_la_tarifa(cliente_admin, cliente_analista, red_cp01):
    from red.models import Ruta

    Ruta.objects.all().delete()
    for e, p, d, t in [("E1", "P1", 10, 0.4), ("E1", "P2", 20, 0.3), ("E2", "P1", 25, 0.2), ("E2", "P2", 10, 0.2)]:
        r = cliente_admin.post("/api/v1/rutas/", {"empresa": e, "planta": p, "distancia_km": d, "tarifa_km_ton": t}, format="json")
        assert r.status_code == 201, r.data
    Planta.objects.filter(codigo="P2").update(costo_operacion_ton=1)  # la operación no se escala con el combustible
    cuerpo = {"variaciones": [{"tipo": "combustible", "porcentajes": [50]}], "incluir_ag": False, "guardar": False}
    res = cliente_analista.post(SENSIBILIDAD, cuerpo, format="json").data["resultado"]
    base, esc = res["base"]["exacto"]["objetivo"], res["escenarios"][0]["exacto"]["objetivo"]
    # base: E1->P1 12x4 = 48 y E2->P2 8x(2+1) = 24 (E2->P1 cuesta 5)  -> 72; escenario: transporte x1.5, operación igual
    assert base == pytest.approx(72) and esc == pytest.approx(12 * 6 + 8 * (3 + 1))


def test_sensibilidad_ids_de_combustible_desconocidos_400(cliente_analista, red_cp01):
    r = cliente_analista.post(SENSIBILIDAD, {"variaciones": [{"tipo": "combustible", "ids": ["E9->P9"], "porcentajes": [10]}]}, format="json")
    assert r.status_code == 400


def test_reporte_con_sensibilidad_incluye_rangos_y_resumen(cliente_analista, red_cp01):
    cuerpo = {"config_ag": AG_RAPIDO, "variaciones": [{"tipo": "costo", "ids": ["E1->P1"], "porcentajes": [10, 80]}]}
    sens = cliente_analista.post(REPORTE, cuerpo, format="json").data["resultado"]["sensibilidad"]
    assert sens["rangos"]["disponible"] and sens["resumen"]["escenarios"] == 2
    a, b = sens["escenarios"]  # c11 = 4.4 (dentro, <= 6) y 7.2 (fuera)
    assert (a["dentro_de_rango"], a["base_cambio"]) == (True, False) and (b["dentro_de_rango"], b["base_cambio"]) == (False, True)


def test_sensibilidad_con_ag_sobre_datos_demo_es_rapida(cliente_admin, cliente_analista, db):
    import time

    assert cliente_admin.post("/api/v1/demo/cargar/").status_code == 201
    cuerpo = {
        "variaciones": [
            {"tipo": "combustible", "porcentajes": [-20, 10, 30]},
            {"tipo": "oferta", "porcentajes": [-20, 20]},
            {"tipo": "capacidad", "ids": ["P1"], "porcentajes": [-30, -10, 10]},
            {"tipo": "capacidad", "ids": ["P1", "P3"], "porcentajes": [-15]},
        ],
        "guardar": False,
    }
    t = time.perf_counter()
    r = cliente_analista.post(SENSIBILIDAD, cuerpo, format="json")
    assert r.status_code == 200, r.data
    assert time.perf_counter() - t < 15
    assert len(r.data["resultado"]["rangos"]["costos"]) == 40


# --------------------------------------------------------------------------- costos del negocio por API
def test_costos_de_negocio_en_api_y_matriz(cliente_admin, cliente_analista, red_cp01):
    e1, p2 = red_cp01["E1"], red_cp01["P2"]
    assert cliente_admin.patch(f"/api/v1/plantas/{p2.id}/", {"costo_operacion_ton": 5}, format="json").data["costo_operacion_ton"] == 5
    assert cliente_admin.patch(f"/api/v1/empresas/{e1.id}/", {"precio_tonelada": 100}, format="json").data["precio_tonelada"] == 100
    assert cliente_admin.patch(f"/api/v1/plantas/{p2.id}/", {"costo_operacion_ton": -1}, format="json").status_code == 400
    m = cliente_analista.get("/api/v1/red/matriz-costos/").data
    assert m["costos"] == [[4, 6], [5, 2]]  # transporte
    assert m["costos_totales"] == [[104, 111], [5, 7]]  # + precio de E1 (100) + operación de P2 (5)
    assert m["plantas"][1]["costo_operacion_ton"] == 5 and m["empresas"][0]["precio_tonelada"] == 100
    r = cliente_analista.post(EXACTO, {"guardar": False}, format="json").data["resultado"]
    assert r["objetivo"] == pytest.approx(98 + 1200)
    assert r["metricas"]["desglose_costos"]["operacion"] == pytest.approx(25)


def test_costos_por_defecto_cero_y_cp01_sigue_en_64(cliente_analista, red_cp01):
    assert Empresa.objects.get(codigo="E1").precio_tonelada == 0 and Planta.objects.get(codigo="P1").costo_operacion_ton == 0
    assert cliente_analista.post(EXACTO, {"guardar": False}, format="json").data["resultado"]["objetivo"] == pytest.approx(64)


def test_codigo_de_empresa_y_planta_no_se_edita(cliente_admin, red_cp01):
    e, p = red_cp01["E1"], red_cp01["P1"]
    r = cliente_admin.patch(f"/api/v1/empresas/{e.id}/", {"codigo": "NUEVO"}, format="json")
    assert r.status_code == 400 and "codigo" in r.data["errores"]
    assert cliente_admin.patch(f"/api/v1/plantas/{p.id}/", {"codigo": "NUEVO"}, format="json").status_code == 400
    assert cliente_admin.patch(f"/api/v1/empresas/{e.id}/", {"codigo": "E1", "nombre": "Otro nombre"}, format="json").status_code == 200
    assert Empresa.objects.get(pk=e.pk).codigo == "E1"


# --------------------------------------------------------------------------- escalabilidad
def test_escalabilidad_requiere_rol(anonimo, cliente_analista):
    assert anonimo.post(ESCALABILIDAD, {}, format="json").status_code == 401


def test_escalabilidad_tamanos_personalizados(cliente_analista, db):
    cuerpo = {"tamanos": [{"empresas": 5, "plantas": 2}, {"empresas": 10, "plantas": 4}], "config_ag": {"poblacion": 20, "generaciones": 20}}
    r = cliente_analista.post(ESCALABILIDAD, cuerpo, format="json")
    assert r.status_code == 200, r.data
    res = r.data["resultado"]
    assert res["ficticio"] is True and [(f["empresas"], f["plantas"], f["rutas"]) for f in res["tamanos"]] == [(5, 2, 10), (10, 4, 40)]
    for f in res["tamanos"]:
        assert f["exacto"]["estado"] == "OPTIMAL" and f["genetico"]["factible"]
        assert f["gap_pct"] >= -1e-6 and f["exacto"]["duracion_ms"] > 0 and f["genetico"]["duracion_ms"] > 0
    assert res["configuracion_ag"]["poblacion"] == 20 and res["configuracion_ag"]["inicializacion"] == "heuristica"
    ej = Ejecucion.objects.get(pk=r.data["ejecucion_id"])
    assert ej.metodo == "escalabilidad" and ej.incluye_ficticios is True
    # determinista: misma solicitud -> mismos costos
    otra = cliente_analista.post(ESCALABILIDAD, {**cuerpo, "guardar": False}, format="json").data["resultado"]
    assert [f["exacto"]["objetivo"] for f in otra["tamanos"]] == [f["exacto"]["objetivo"] for f in res["tamanos"]]
    assert [f["genetico"]["objetivo"] for f in otra["tamanos"]] == [f["genetico"]["objetivo"] for f in res["tamanos"]]


def test_escalabilidad_por_defecto_usa_los_cuatro_tamanos(cliente_analista, db):
    r = cliente_analista.post(ESCALABILIDAD, {"guardar": False}, format="json")
    assert r.status_code == 200, r.data
    assert [(f["empresas"], f["plantas"]) for f in r.data["resultado"]["tamanos"]] == [(10, 4), (20, 6), (40, 10), (80, 16)]
    assert r.data["resultado"]["duracion_total_ms"] < 30_000


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"tamanos": [{"empresas": 500, "plantas": 4}]},  # empresas fuera de rango
        {"tamanos": [{"empresas": 0, "plantas": 4}]},
        {"tamanos": [{"empresas": 100, "plantas": 30}]},  # 3000 rutas > 2000
        {"tamanos": [{"empresas": 10, "plantas": 4}] * 9},  # demasiados tamaños
        {"tamanos": []},
        {"config_ag": {"poblacion": 300, "generaciones": 1000}},  # trabajo total > límite
        {"config_ag": {"seleccion": "x"}},
    ],
)
def test_escalabilidad_limites_400(cliente_analista, db, cuerpo):
    r = cliente_analista.post(ESCALABILIDAD, cuerpo, format="json")
    assert r.status_code == 400 and r.data["detail"] and r.data["errores"]


# --------------------------------------------------------------------------- demo
def test_demo_permisos_e_idempotencia(anonimo, cliente_analista, cliente_admin, db):
    for cliente, codigo in ((anonimo, 401), (cliente_analista, 403)):
        assert cliente.get("/api/v1/demo/estado/").status_code == codigo
        assert cliente.post("/api/v1/demo/cargar/").status_code == codigo
    assert cliente_admin.get("/api/v1/demo/estado/").data == {"cargado": False}
    r = cliente_admin.post("/api/v1/demo/cargar/")
    assert r.status_code == 201 and (r.data["empresas"], r.data["plantas"], r.data["rutas"]) == (10, 4, 40) and r.data["cargado"]
    assert cliente_admin.get("/api/v1/demo/estado/").data == {"cargado": True}
    Empresa.objects.filter(codigo="E1").update(oferta=99)
    r = cliente_admin.post("/api/v1/demo/cargar/")
    assert r.status_code == 200 and Empresa.objects.get(codigo="E1").oferta == 99  # no pisa lo ya cargado
    assert not Empresa.objects.filter(ficticio=False).exists()


def test_inicializar_demo_crea_solo_lo_que_falta(db, monkeypatch):
    from django.core.management import call_command

    from cuentas.models import Usuario

    monkeypatch.setenv("DEMO_ADMIN_PASSWORD", "Prueba-Admin-9183!")
    monkeypatch.setenv("DEMO_ANALISTA_PASSWORD", "Prueba-Analista-7712!")
    call_command("inicializar_demo")
    assert Usuario.objects.count() == 2 and Empresa.objects.count() == 10
    u = Usuario.objects.get(username="admin_demo")
    u.set_password("Cambiada-Por-Admin-1!")
    u.save()
    Empresa.objects.filter(codigo="E2").update(oferta=77)
    call_command("inicializar_demo")  # segunda vez: no toca nada
    assert Usuario.objects.get(username="admin_demo").check_password("Cambiada-Por-Admin-1!")
    assert Empresa.objects.get(codigo="E2").oferta == 77


# --------------------------------------------------------------------------- historial
def test_historial_incluye_ficticios_y_filtros_de_fecha(cliente_analista, cliente_admin, red_cp01):
    Empresa.objects.filter(codigo="E1").update(ficticio=True)
    a = cliente_analista.post(EXACTO, {}, format="json").data["ejecucion_id"]
    Empresa.objects.filter(codigo="E1").update(ficticio=False)
    b = cliente_analista.post(GENETICO, {**AG_RAPIDO}, format="json").data["ejecucion_id"]
    lista = {e["id"]: e for e in cliente_analista.get("/api/v1/ejecuciones/").data["results"]}
    assert lista[a]["incluye_ficticios"] is True and lista[b]["incluye_ficticios"] is False
    assert cliente_analista.get("/api/v1/ejecuciones/?incluye_ficticios=true").data["count"] == 1
    hoy = date.today()
    ayer, manana = hoy - timedelta(days=1), hoy + timedelta(days=1)
    assert cliente_analista.get(f"/api/v1/ejecuciones/?desde={manana}").data["count"] == 0
    assert cliente_analista.get(f"/api/v1/ejecuciones/?hasta={ayer}").data["count"] == 0
    assert cliente_analista.get(f"/api/v1/ejecuciones/?desde={ayer}&hasta={manana}&metodo=exacto&estado=OPTIMAL").data["count"] == 1
    r = cliente_analista.get("/api/v1/ejecuciones/?desde=ayer")
    assert r.status_code == 400 and r.data["errores"]
    assert cliente_analista.get(f"/api/v1/ejecuciones/{a}/").data["incluye_ficticios"] is True


# --------------------------------------------------------------------------- admin apagado y documentación
def test_admin_de_django_apagado_por_defecto(db):
    assert Client().get("/admin/").status_code == 404
    assert Client().get("/admin/login/").status_code == 404


def test_admin_de_django_se_monta_si_se_habilita(db, settings):
    import config.urls

    settings.ADMIN_HABILITADO = True
    try:
        importlib.reload(config.urls)
        clear_url_caches()
        set_urlconf(None)
        assert Client().get("/admin/login/").status_code == 200
    finally:
        settings.ADMIN_HABILITADO = False
        importlib.reload(config.urls)
        clear_url_caches()
        set_urlconf(None)
    assert Client().get("/admin/login/").status_code == 404


def test_documentacion_exige_jwt_fuera_de_debug(anonimo, cliente_analista):
    for url in ("/api/v1/schema/", "/api/v1/docs/"):
        assert anonimo.get(url).status_code == 401
        assert cliente_analista.get(url).status_code == 200
    assert b"/api/v1/usuarios/" in cliente_analista.get("/api/v1/schema/").content
    # una sesión de Django (cookie) ya no sirve: solo JWT
    assert Client().get("/api/v1/schema/").status_code == 401
