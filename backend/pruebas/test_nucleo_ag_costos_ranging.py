"""Núcleo sin Django: AG completo, modelo de costos, ranging del LP y generador sintético."""
import pytest

from dominio.modelos import ArcoCosto, EmpresaAgropecuaria, ParametrosModelo, PlantaProcesamiento
from dominio.redes_sinteticas import generar_red_sintetica
from optimizacion import AlgoritmoGenetico, ConfigAG, MetodoExacto
from optimizacion.metodo_exacto import analizar_lp


def cp01(cap_p1=15.0, op_p2=0.0, precio_e1=0.0):
    return ParametrosModelo(
        (EmpresaAgropecuaria("E1", "E1", "X", 12, precio_e1), EmpresaAgropecuaria("E2", "E2", "X", 8)),
        (PlantaProcesamiento("P1", "P1", "X", cap_p1), PlantaProcesamiento("P2", "P2", "X", 10, costo_operacion_ton=op_p2)),
        (ArcoCosto("E1", "P1", 4), ArcoCosto("E1", "P2", 6), ArcoCosto("E2", "P1", 5), ArcoCosto("E2", "P2", 2)),
    )


# --------------------------------------------------------------------------- modelo de costos
def test_cp01_sigue_dando_64_sin_costos_extra():
    r = MetodoExacto().resolver(cp01())
    assert r.objetivo == 64 and r.metricas["desglose_costos"] == {"transporte": 64.0, "operacion": 0.0, "precio": 0.0, "total": 64.0}


def test_costo_operacion_de_planta_calculado_a_mano():
    # P2 cuesta 5 más por t: E1->P1 12 (48), E2->P1 3 (15), E2->P2 5 (7x5=35) = 98
    r = MetodoExacto().resolver(cp01(op_p2=5))
    assert r.objetivo == pytest.approx(98)
    q = {(a["empresa_id"], a["planta_id"]): a["cantidad"] for a in r.asignaciones}
    assert q == {("E1", "P1"): pytest.approx(12), ("E2", "P1"): pytest.approx(3), ("E2", "P2"): pytest.approx(5)}
    d = r.metricas["desglose_costos"]
    assert d["transporte"] == pytest.approx(48 + 15 + 10) and d["operacion"] == pytest.approx(25) and d["total"] == pytest.approx(98)
    e2p2 = next(a for a in r.asignaciones if a["planta_id"] == "P2")
    assert e2p2["costo_unitario"] == 7 and e2p2["costo_transporte"] == 2 and e2p2["costo_operacion"] == 5


def test_precio_por_tonelada_suma_a_las_rutas_de_la_empresa():
    # precio 100 en E1 (12 t): solo suma 1200 (constante en modo base, no cambia la asignación)
    r = MetodoExacto().resolver(cp01(precio_e1=100))
    assert r.objetivo == pytest.approx(64 + 1200) and r.metricas["desglose_costos"]["precio"] == pytest.approx(1200)
    ag = AlgoritmoGenetico().resolver(cp01(op_p2=5, precio_e1=100), {"semilla": 3, "poblacion": 40, "generaciones": 60})
    assert ag.factible and ag.objetivo == pytest.approx(98 + 1200)


def test_validacion_rechaza_costos_negativos():
    p = cp01(op_p2=-1)
    assert MetodoExacto().resolver(p).estado == "INVALID_INPUT"
    assert AlgoritmoGenetico().resolver(p).estado == "INVALID_INPUT"


# --------------------------------------------------------------------------- AG completo
@pytest.mark.parametrize("seleccion", ["torneo", "ruleta"])
@pytest.mark.parametrize("cruce", ["un_punto", "dos_puntos"])
def test_ag_operadores_factibles_reproducibles_y_con_historial(seleccion, cruce):
    cfg = {"semilla": 11, "poblacion": 30, "generaciones": 40, "seleccion": seleccion, "tipo_cruce": cruce, "tamano_torneo": 4}
    a = AlgoritmoGenetico().resolver(cp01(), cfg)
    b = AlgoritmoGenetico().resolver(cp01(), cfg)
    assert a.estado == "FEASIBLE" and a.verificacion["valida"] and a.objetivo >= 64 - 1e-9
    assert a.objetivo == b.objetivo and a.metricas["convergencia"] == b.metricas["convergencia"]
    m = a.metricas
    assert m["seleccion"] == seleccion and m["tipo_cruce"] == cruce and m["tamano_torneo"] == 4
    for clave in ("convergencia", "convergencia_promedio", "aptitud_mejor", "aptitud_promedio", "factibles"):
        assert len(m[clave]) == 40
    assert all(prom >= mejor - 1e-9 for mejor, prom in zip(m["convergencia"], m["convergencia_promedio"]))
    # con elitismo la mejor aptitud nunca empeora y la aptitud es la inversa del costo penalizado
    assert all(y >= x - 1e-12 for x, y in zip(m["aptitud_mejor"], m["aptitud_mejor"][1:]))
    assert m["aptitud_mejor"][0] == pytest.approx(1 / (1 + m["convergencia"][0]))


def test_ag_semillas_distintas_dan_historiales_distintos():
    cfg = {"poblacion": 20, "generaciones": 10}
    a = AlgoritmoGenetico().resolver(cp01(), {**cfg, "semilla": 1})
    b = AlgoritmoGenetico().resolver(cp01(), {**cfg, "semilla": 2})
    assert a.metricas["convergencia_promedio"] != b.metricas["convergencia_promedio"]


def test_ag_penaliza_la_violacion_y_la_reparacion_evita_exceder_capacidad():
    # Oferta 20 pero la ruta E1->P1 limita el flujo a 5: el déficit es inevitable y se penaliza
    p = ParametrosModelo(
        (EmpresaAgropecuaria("E1", "E1", "X", 12),), (PlantaProcesamiento("P1", "P1", "X", 100),),
        (ArcoCosto("E1", "P1", 4, limite=5),),
    )  # fmt: skip
    r = AlgoritmoGenetico().resolver(p, {"poblacion": 10, "generaciones": 5})
    assert r.estado == "INFEASIBLE" and not r.factible and r.objetivo is None
    assert r.metricas["violacion_t"] == pytest.approx(7)
    # costo penalizado = costo (5x4=20) + lambda x 7, con lambda = 10 x (4+1) x (12+1) = 650
    assert r.metricas["convergencia"][0] == pytest.approx(20 + 650 * 7)
    assert sum(a["cantidad"] for a in r.asignaciones) == pytest.approx(5)


def test_ag_prefiere_factible_aunque_tenga_mayor_costo_bruto():
    r = AlgoritmoGenetico().resolver(cp01(cap_p1=12), {"semilla": 5, "poblacion": 30, "generaciones": 30})
    assert r.estado == "FEASIBLE"
    q = sum(a["cantidad"] for a in r.asignaciones)
    assert q == pytest.approx(20)
    for planta, cap in (("P1", 12), ("P2", 10)):
        assert sum(a["cantidad"] for a in r.asignaciones if a["planta_id"] == planta) <= cap + 1e-9


@pytest.mark.parametrize(
    "cfg",
    [
        {"poblacion": 1}, {"poblacion": 2.5}, {"generaciones": 0}, {"cruce": 1.1}, {"cruce": float("nan")}, {"mutacion": -0.1},
        {"semilla": -1}, {"elitismo": 60}, {"tamano_torneo": 1}, {"tamano_torneo": 61}, {"seleccion": "azar"},
        {"tipo_cruce": "tres_puntos"}, {"inicializacion": "x"}, {"poblacion": True},
    ],
)
def test_configuracion_ag_invalida(cfg):
    assert ConfigAG.desde_dict(cfg).errores()
    assert AlgoritmoGenetico().resolver(cp01(), cfg).estado == "INVALID_INPUT"


def test_configuracion_ag_por_defecto_es_valida():
    cfg = ConfigAG()
    assert not cfg.errores() and cfg.seleccion == "torneo" and cfg.tipo_cruce == "un_punto" and cfg.tamano_torneo == 3


def test_ag_heuristico_mejora_en_red_grande():
    red = generar_red_sintetica(25, 8)
    exacto = MetodoExacto().resolver(red).objetivo
    base = {"poblacion": 30, "generaciones": 40, "semilla": 1}
    aleatorio = AlgoritmoGenetico().resolver(red, {**base, "inicializacion": "aleatoria"})
    heuristico = AlgoritmoGenetico().resolver(red, {**base, "inicializacion": "heuristica"})
    assert aleatorio.factible and heuristico.factible
    assert exacto - 1e-6 <= heuristico.objetivo < aleatorio.objetivo
    assert (heuristico.objetivo / exacto - 1) * 100 < 15


# --------------------------------------------------------------------------- ranging
def _filas(rangos, clave, campo):
    return {f[campo]: f for f in rangos[clave]}


def test_ranging_cp01_calculado_a_mano():
    """CP-01 (óptimo 64): E1->P1 = 12, E2->P2 = 8; ambas plantas con holgura."""
    a = analizar_lp(cp01(), con_rangos=True)
    assert a.optimo and a.objetivo == pytest.approx(64)
    assert a.precios_sombra == {"oferta:E1": pytest.approx(4), "oferta:E2": pytest.approx(2), "planta:P1": 0, "planta:P2": 0}
    oferta, cap, costos = _filas(a.rangos, "oferta", "id"), _filas(a.rangos, "capacidad", "id"), _filas(a.rangos, "costos", "ruta")
    # oferta E1: x11 = E1 <= 15 (capacidad de P1); E2: x22 = E2 <= 10
    assert (oferta["E1"]["minimo"], oferta["E1"]["maximo"]) == (0, 15)
    assert (oferta["E2"]["minimo"], oferta["E2"]["maximo"]) == (0, 10)
    # capacidades con holgura: pueden subir sin límite y bajar hasta lo que se usa (12 y 8)
    assert (cap["P1"]["minimo"], cap["P1"]["maximo"], cap["P1"]["activa"]) == (12, None, False)
    assert (cap["P2"]["minimo"], cap["P2"]["maximo"]) == (8, None)
    # costos: básicas E1->P1 hasta 6 (empata con E1->P2) y E2->P2 hasta 5 (empata con E2->P1); no básicas desde 4 y 2
    assert (costos["E1->P1"]["minimo"], costos["E1->P1"]["maximo"], costos["E1->P1"]["en_base"]) == (None, 6, True)
    assert (costos["E2->P2"]["minimo"], costos["E2->P2"]["maximo"]) == (None, 5)
    assert (costos["E1->P2"]["minimo"], costos["E1->P2"]["maximo"], costos["E1->P2"]["en_base"]) == (4, None, False)
    assert (costos["E2->P1"]["minimo"], costos["E2->P1"]["maximo"]) == (2, None)
    assert costos["E1->P2"]["costo_reducido"] == pytest.approx(2) and costos["E2->P1"]["costo_reducido"] == pytest.approx(3)


def test_ranging_caso_con_cuello_de_botella_calculado_a_mano():
    """P1 con capacidad 11: E1->P1 = 11, E1->P2 = 1, E2->P2 = 8 (objetivo 66, precio sombra de P1 = -2)."""
    a = analizar_lp(cp01(cap_p1=11), con_rangos=True)
    assert a.objetivo == pytest.approx(66) and a.precios_sombra["planta:P1"] == pytest.approx(-2)
    oferta, cap, costos = _filas(a.rangos, "oferta", "id"), _filas(a.rangos, "capacidad", "id"), _filas(a.rangos, "costos", "ruta")
    # P1 saturada: con 12 t en P1 se anula E1->P2 (objetivo 64); con 10 t, P2 se llena (objetivo 68)
    assert cap["P1"]["activa"] is True
    assert (cap["P1"]["minimo"], cap["P1"]["maximo"]) == (10, 12)
    assert (cap["P1"]["objetivo_en_minimo"], cap["P1"]["objetivo_en_maximo"]) == (pytest.approx(68), pytest.approx(64))
    # E1: x11 = 11 fija y x12 = E1 - 11 <= 10 - 8 = 2 -> [11, 13]; E2: x22 = E2 <= 10 - 1 = 9
    assert (oferta["E1"]["minimo"], oferta["E1"]["maximo"]) == (11, 13)
    assert (oferta["E2"]["minimo"], oferta["E2"]["maximo"]) == (0, 9)
    assert (cap["P2"]["minimo"], cap["P2"]["maximo"]) == (9, None)
    assert costos["E1->P1"]["maximo"] == 6 and costos["E1->P2"]["minimo"] == 4 and costos["E2->P2"]["maximo"] == 7


def _firma(p):
    a = analizar_lp(p)
    return a.firma_base if a.optimo else None


def test_ranging_validado_por_reoptimizacion():
    """Dentro del rango la base óptima no cambia; fuera de él, sí."""
    base = cp01(cap_p1=11)
    firma0 = _firma(base)
    rangos = analizar_lp(base, con_rangos=True).rangos
    cap_p1 = _filas(rangos, "capacidad", "id")["P1"]
    assert _firma(cp01(cap_p1=cap_p1["minimo"] + 0.01)) == firma0 and _firma(cp01(cap_p1=cap_p1["maximo"] - 0.01)) == firma0
    assert _firma(cp01(cap_p1=cap_p1["maximo"] + 0.01)) != firma0
    # costo de E1->P1: hasta 6 conserva la base, por encima cambia
    c11 = _filas(rangos, "costos", "ruta")["E1->P1"]["maximo"]

    def con_costo(c):
        p = cp01(cap_p1=11)
        return ParametrosModelo(p.empresas, p.plantas, (ArcoCosto("E1", "P1", c),) + p.arcos[1:])

    assert _firma(con_costo(c11 - 0.01)) == firma0 and _firma(con_costo(c11 + 0.01)) != firma0
    # el objetivo en los límites coincide con reoptimizar justo en el límite
    assert MetodoExacto().resolver(cp01(cap_p1=10)).objetivo == pytest.approx(cap_p1["objetivo_en_minimo"])
    assert MetodoExacto().resolver(cp01(cap_p1=12)).objetivo == pytest.approx(cap_p1["objetivo_en_maximo"])


def test_ranging_mantiene_consistencia_con_duales_del_exacto():
    red = generar_red_sintetica(10, 4)
    exacto, lp = MetodoExacto().resolver(red), analizar_lp(red, con_rangos=True)
    assert lp.objetivo == pytest.approx(exacto.objetivo)
    for clave, valor in exacto.duales.items():
        assert lp.precios_sombra[clave] == pytest.approx(valor, abs=1e-6)
    for f in lp.rangos["costos"]:
        assert f["minimo"] is None or f["maximo"] is None or f["minimo"] <= f["costo_actual"] + 1e-9 <= f["maximo"] + 2e-9


def test_analizar_lp_inviable():
    p = cp01()
    p = ParametrosModelo(p.empresas, (PlantaProcesamiento("P1", "P1", "X", 5), p.plantas[1]), p.arcos)
    assert analizar_lp(p).optimo is False


# --------------------------------------------------------------------------- generador sintético
def test_red_sintetica_determinista_y_factible():
    a, b = generar_red_sintetica(20, 6), generar_red_sintetica(20, 6)
    assert a == b and len(a.arcos) == 120 and generar_red_sintetica(20, 6, semilla=1) != a
    assert sum(p.capacidad for p in a.plantas) >= sum(e.oferta for e in a.empresas)
    assert MetodoExacto().resolver(a).estado == "OPTIMAL"
