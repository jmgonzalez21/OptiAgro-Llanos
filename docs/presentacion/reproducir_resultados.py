"""Reproduce las cifras de la presentación (red de demostración, CP-01, AG, sensibilidad, escalabilidad).
Uso (con los contenedores en marcha, desde la raíz del proyecto):
  docker compose cp docs/presentacion/reproducir_resultados.py backend:/tmp/exp.py
  docker compose exec -T backend python manage.py shell -c "exec(open('/tmp/exp.py').read())"
  docker compose cp backend:/tmp/exp_out.json docs/presentacion/resultados.json
Los datos de la red de prueba se construyen con las mismas fórmulas FICTICIAS de backend/red/demo.py."""
import json, statistics as st
from time import perf_counter
from dominio.modelos import EmpresaAgropecuaria as E, PlantaProcesamiento as P, ArcoCosto as A, ParametrosModelo as M
from optimizacion import MetodoExacto, AlgoritmoGenetico
from servicios.ejecucion import ejecutar_sensibilidad, Variacion, gap_porcentual
from servicios.escalabilidad import ejecutar_escalabilidad

out = {}

# ---- CP-01 (caso de prueba con óptimo conocido = 64) ----
cp01 = M((E("E1", "E1", "X", 12), E("E2", "E2", "X", 8)), (P("P1", "P1", "X", 15), P("P2", "P2", "X", 10)),
         (A("E1", "P1", 4), A("E1", "P2", 6), A("E2", "P1", 5), A("E2", "P2", 2)))
r = MetodoExacto().resolver(cp01)
ag = AlgoritmoGenetico().resolver(cp01, {"semilla": 7, "poblacion": 40, "generaciones": 50})
out["cp01"] = {"exacto": r.objetivo, "estado": r.estado, "asign": [(a["empresa_id"], a["planta_id"], a["cantidad"]) for a in r.asignaciones],
               "ag": ag.objetivo, "ag_estado": ag.estado}

# ---- Red de demostración (mismas fórmulas que backend/red/demo.py) ----
MUN = ["Acacías", "Cumaral", "Guamal", "San Martín", "Puerto López", "Castilla La Nueva", "Cabuyaro", "El Dorado", "Lejanías", "Mapiripán"]
PL = [("P1", "Villavicencio", 40), ("P2", "Restrepo", 32), ("P3", "Granada", 30), ("P4", "Puerto Gaitán", 34)]
empresas = tuple(E(f"E{i}", f"Agroempresa {i}", MUN[i - 1], float(10 + i % 4), 0.0) for i in range(1, 11))
plantas = tuple(P(c, f"Planta {m}", m, float(cap), "capacity_max", float(1000 + 500 * k)) for k, (c, m, cap) in enumerate(PL))
arcos = []
for i in range(1, 11):
    for j in range(1, 5):
        d = float(15 + (i * 17 + j * 29 + i * j * 5) % 85)
        t = float(420 + 15 * j)
        arcos.append(A(f"E{i}", f"P{j}", d * t, d, t, None))
demo = M(empresas, plantas, tuple(arcos), "exact")
out["demo_modelo"] = {"empresas": 10, "plantas": 4, "rutas": 40, "oferta": sum(e.oferta for e in empresas), "capacidad": sum(p.capacidad for p in plantas),
                      "ofertas": [e.oferta for e in empresas], "capacidades": [p.capacidad for p in plantas], "operacion": [p.costo_operacion_ton for p in plantas]}

tiempos = []
for _ in range(30):
    t0 = perf_counter(); ex = MetodoExacto().resolver(demo); tiempos.append((perf_counter() - t0) * 1000)
out["exacto"] = {"estado": ex.estado, "objetivo": ex.objetivo, "ms_mediana": st.median(tiempos), "ms_min": min(tiempos), "ms_max": max(tiempos),
                 "mensaje": ex.mensajes, "desglose": ex.metricas.get("desglose_costos"), "duales": ex.duales,
                 "verificacion": ex.verificacion,
                 "asignaciones": [(a["empresa_id"], a["planta_id"], round(a["cantidad"], 3)) for a in ex.asignaciones]}
uso = {p.id: 0.0 for p in plantas}
for a in ex.asignaciones: uso[a["planta_id"]] += a["cantidad"]
out["exacto"]["uso_plantas"] = uso

def corre(cfg):
    t0 = perf_counter(); r = AlgoritmoGenetico().resolver(demo, cfg); ms = (perf_counter() - t0) * 1000
    return r, ms

# AG con parámetros por defecto, semilla 42 (con convergencia)
r42, ms42 = corre({})
conv = r42.metricas["convergencia"]
out["ag_defecto"] = {"objetivo": r42.objetivo, "estado": r42.estado, "ms": ms42, "gap": gap_porcentual(r42.objetivo, ex.objetivo),
                     "evaluaciones": r42.metricas["evaluaciones"], "config": {k: r42.metricas[k] for k in ("poblacion", "generaciones", "cruce", "mutacion", "semilla", "elitismo", "seleccion", "tipo_cruce", "tamano_torneo", "inicializacion")},
                     "conv_muestra": [(g, conv[g]) for g in sorted(set(list(range(0, len(conv), 10)) + [len(conv) - 1]))],
                     "conv_prom_muestra": [(g, r42.metricas["convergencia_promedio"][g]) for g in sorted(set(list(range(0, len(conv), 10)) + [len(conv) - 1]))],
                     "factibles_gen0": r42.metricas["factibles"][0], "factibles_final": r42.metricas["factibles"][-1],
                     "penalizacion": r42.metricas["penalizacion"]}

def serie(base_cfg, semillas=range(1, 11)):
    gaps, ms, objs = [], [], []
    for s in semillas:
        r, t = corre({**base_cfg, "semilla": s})
        gaps.append(gap_porcentual(r.objetivo, ex.objetivo)); ms.append(t); objs.append(r.objetivo)
    return {"gap_media": st.mean(gaps), "gap_min": min(gaps), "gap_max": max(gaps), "gaps": gaps, "ms_media": st.mean(ms), "obj_min": min(objs), "obj_max": max(objs)}

out["ag_series"] = {
    "torneo_1punto": serie({}),
    "ruleta_1punto": serie({"seleccion": "ruleta"}),
    "torneo_2puntos": serie({"tipo_cruce": "dos_puntos"}),
    "ruleta_2puntos": serie({"seleccion": "ruleta", "tipo_cruce": "dos_puntos"}),
    "heuristica": serie({"inicializacion": "heuristica"}),
}

# ---- Sensibilidad (exacto + AG) ----
vars_ = [Variacion("combustible", (), (10.0, 20.0)), Variacion("oferta", (), (-10.0, 15.0)), Variacion("capacidad", ("P3",), (-30.0,))]
s = ejecutar_sensibilidad(demo, vars_, incluir_ag=True)
out["sens"] = {"precios_sombra": s.get("precios_sombra"), "resumen": s.get("resumen"),
               "escenarios": [{k: e.get(k) for k in ("nombre", "estado_exacto", "estado_ag", "costo_exacto", "costo_ag", "gap_pct", "tiempo_exacto_ms", "tiempo_ag_ms", "base_cambio", "asignaciones_cambiadas", "variacion_objetivo_pct")} for e in s["escenarios"]],
               "rangos_capacidad": s["rangos"].get("capacidad"), "rangos_oferta": s["rangos"].get("oferta")[:3] if s["rangos"].get("oferta") else None,
               "rangos_metodo": s["rangos"].get("metodo"), "plantas": s.get("plantas")}

# ---- Escalabilidad ----
esc = ejecutar_escalabilidad()
out["escal"] = [{"n": f"{f['empresas']}x{f['plantas']}", "rutas": f["rutas"], "obj_ex": f["exacto"].get("objetivo"), "ms_ex": f["exacto"].get("duracion_ms"),
                 "obj_ag": f["genetico"].get("objetivo"), "ms_ag": f["genetico"].get("duracion_ms"), "gap": f["gap_pct"], "ratio": f["ratio_tiempo"]} for f in esc["tamanos"]]
out["escal_cfg"] = esc["configuracion_ag"]

json.dump(out, open("/tmp/exp_out.json", "w"), ensure_ascii=False, default=str, indent=1)
print("LISTO")

