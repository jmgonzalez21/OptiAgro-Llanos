"""Casos de uso de optimización: exacto, AG, sensibilidad y reporte comparativo."""
from __future__ import annotations

from dataclasses import dataclass, replace
from time import perf_counter
from typing import Any

from django.conf import settings

from dominio.modelos import ParametrosModelo, ResultadoOptimizacion
from optimizacion import AlgoritmoGenetico, ConfigAG, MetodoExacto
from optimizacion.metodo_exacto import analizar_lp

from .conversion import resumen_modelo, validar_tamano
from .errores import ErrorDeNegocio


# ---------------------------------------------------------------------------------------
# Solvers individuales
# ---------------------------------------------------------------------------------------
def resolver_exacto(parametros: ParametrosModelo) -> ResultadoOptimizacion:
    validar_tamano(parametros)
    resultado = MetodoExacto().resolver(parametros)
    if resultado.estado == "INVALID_INPUT":
        raise ErrorDeNegocio("El escenario no es válido para optimizar.", resultado.mensajes)
    return resultado


def configuracion_ag(configuracion: dict | None) -> dict[str, Any]:
    """Valida (rangos del núcleo + límites del servidor) y devuelve la configuración completa del AG."""
    cfg = ConfigAG.desde_dict(configuracion)
    errores = cfg.errores()
    limites = settings.OPTIAGRO
    if isinstance(cfg.poblacion, int) and cfg.poblacion > limites["AG_MAX_POBLACION"]:
        errores.append(f"poblacion debe estar entre 2 y {limites['AG_MAX_POBLACION']}.")
    if isinstance(cfg.generaciones, int) and cfg.generaciones > limites["AG_MAX_GENERACIONES"]:
        errores.append(f"generaciones debe estar entre 1 y {limites['AG_MAX_GENERACIONES']}.")
    if errores:
        raise ErrorDeNegocio("Configuración del algoritmo genético inválida.", errores)
    return cfg.como_dict()


def _validar_trabajo_ag(parametros: ParametrosModelo, cfg: dict, corridas: int = 1) -> None:
    trabajo = cfg["poblacion"] * cfg["generaciones"] * max(1, len(parametros.arcos)) * corridas
    if trabajo > settings.OPTIAGRO["AG_MAX_TRABAJO"]:
        raise ErrorDeNegocio(
            "La configuración del AG es demasiado costosa para este problema.",
            [
                f"poblacion x generaciones x rutas x corridas = {trabajo:,} excede el máximo "
                f"{settings.OPTIAGRO['AG_MAX_TRABAJO']:,}. Reduzca población, generaciones o escenarios."
            ],
        )


def resolver_genetico(parametros: ParametrosModelo, configuracion: dict | None = None) -> tuple[ResultadoOptimizacion, dict]:
    validar_tamano(parametros)
    cfg = configuracion_ag(configuracion)
    _validar_trabajo_ag(parametros, cfg)
    resultado = AlgoritmoGenetico().resolver(parametros, cfg)
    if resultado.estado == "INVALID_INPUT":
        raise ErrorDeNegocio("El escenario no es válido para el algoritmo genético.", resultado.mensajes)
    return resultado, cfg


# ---------------------------------------------------------------------------------------
# Utilidades de presentación
# ---------------------------------------------------------------------------------------
def resumen(resultado: ResultadoOptimizacion, *, con_duales: bool = False) -> dict[str, Any]:
    salida = {
        "estado": resultado.estado,
        "factible": resultado.factible,
        "objetivo": resultado.objetivo,
        "duracion_ms": resultado.duracion_ms,
        "mensajes": resultado.mensajes,
    }
    if con_duales:
        salida["duales"] = resultado.duales
    return salida


def gap_porcentual(heuristico: float | None, exacto: float | None) -> float | None:
    if heuristico is None or exacto is None or abs(exacto) < 1e-12:
        return None
    return (heuristico - exacto) / abs(exacto) * 100


def analisis_plantas(parametros: ParametrosModelo, resultado: ResultadoOptimizacion) -> list[dict[str, Any]]:
    """Utilización, precio sombra y detección de cuellos de botella por planta."""
    flujo: dict[str, float] = {}
    for a in resultado.asignaciones:
        flujo[a["planta_id"]] = flujo.get(a["planta_id"], 0.0) + a["cantidad"]
    filas = []
    for p in parametros.plantas:
        usado = flujo.get(p.id, 0.0)
        utilizacion = (usado / p.capacidad * 100) if p.capacidad > 0 else None
        precio = resultado.duales.get(f"planta:{p.id}")
        saturada = p.tipo_demanda == "capacity_max" and p.capacidad > 0 and usado >= p.capacidad - 1e-6
        filas.append(
            {
                "planta": p.id,
                "nombre": p.nombre,
                "tipo_demanda": p.tipo_demanda,
                "capacidad": p.capacidad,
                "flujo": usado,
                "utilizacion_pct": utilizacion,
                "precio_sombra": precio,
                "cuello_de_botella": bool(saturada and precio is not None and abs(precio) > 1e-9),
            }
        )
    return filas




# ---------------------------------------------------------------------------------------
# Sensibilidad
# ---------------------------------------------------------------------------------------
TIPOS_VARIACION = ("oferta", "capacidad", "costo", "combustible")


@dataclass(frozen=True)
class Variacion:
    """Variación porcentual de un parámetro.

    ``oferta``: ofertas de empresas (ids = códigos de empresa).
    ``capacidad``: capacidades de plantas; varias a la vez = cuello de botella en varias plantas (ids = códigos de planta).
    ``costo``: costo de TRANSPORTE de rutas (ids = "E1->P2"); no altera la operación de la planta ni el precio.
    ``combustible``: % sobre la TARIFA km-ton de las rutas (ids = "E1->P2"); una ruta con costo unitario directo
                     (sin distancia ni tarifa) se trata como costo de transporte y se escala igual.
    ``ids`` vacío = todos los elementos del tipo.
    """

    tipo: str
    ids: tuple[str, ...]
    porcentajes: tuple[float, ...]


def _aplicar(parametros: ParametrosModelo, tipo: str, ids: tuple[str, ...], porcentaje: float) -> ParametrosModelo:
    factor = 1 + porcentaje / 100
    todos = not ids
    if tipo == "oferta":
        return replace(
            parametros,
            empresas=tuple(replace(e, oferta=e.oferta * factor) if todos or e.id in ids else e for e in parametros.empresas),
        )
    if tipo == "capacidad":
        return replace(
            parametros,
            plantas=tuple(
                replace(p, capacidad=p.capacidad * factor) if todos or p.id in ids else p for p in parametros.plantas
            ),
        )

    def escalar(a):
        if tipo == "combustible" and a.distancia_km is not None and a.tarifa_km_ton is not None:
            return replace(a, tarifa_km_ton=a.tarifa_km_ton * factor)
        # costo (o combustible sobre un costo directo): el costo de transporte se fija directamente
        return replace(a, costo_unitario=a.costo_calculado * factor, distancia_km=None, tarifa_km_ton=None)

    return replace(
        parametros,
        arcos=tuple(escalar(a) if todos or f"{a.empresa_id}->{a.planta_id}" in ids else a for a in parametros.arcos),
    )


def _validar_ids(parametros: ParametrosModelo, variacion: Variacion) -> None:
    if variacion.tipo == "oferta":
        validos = {e.id for e in parametros.empresas}
    elif variacion.tipo == "capacidad":
        validos = {p.id for p in parametros.plantas}
    else:
        validos = {f"{a.empresa_id}->{a.planta_id}" for a in parametros.arcos}
    desconocidos = [i for i in variacion.ids if i not in validos]
    if desconocidos:
        raise ErrorDeNegocio(
            f"Identificadores desconocidos o inactivos para '{variacion.tipo}'.",
            [f"No existe '{i}' en la red activa." for i in desconocidos],
        )


def _cambios_asignacion(base: ResultadoOptimizacion, escenario: ResultadoOptimizacion) -> list[dict[str, Any]]:
    """Diferencias de toneladas por ruta (exacto del escenario frente al exacto del caso base)."""
    antes = {(a["empresa_id"], a["planta_id"]): a["cantidad"] for a in base.asignaciones}
    despues = {(a["empresa_id"], a["planta_id"]): a["cantidad"] for a in escenario.asignaciones}
    filas = []
    for clave in sorted(set(antes) | set(despues)):
        delta = despues.get(clave, 0.0) - antes.get(clave, 0.0)
        if abs(delta) > 1e-6:
            filas.append(
                {
                    "empresa": clave[0],
                    "planta": clave[1],
                    "base": antes.get(clave, 0.0),
                    "escenario": despues.get(clave, 0.0),
                    "delta": delta,
                }
            )
    return filas


def _dentro_de_rango(nuevo: ParametrosModelo, variacion: Variacion, rangos: dict | None):
    """Si el escenario mueve UN solo parámetro, ¿su nuevo valor cae dentro del rango que conserva la base óptima?"""
    if not rangos or len(variacion.ids) != 1:
        return None
    ident = variacion.ids[0]
    if variacion.tipo == "oferta":
        fila = next((f for f in rangos["oferta"] if f["id"] == ident), None)
        valor = next(e.oferta for e in nuevo.empresas if e.id == ident)
    elif variacion.tipo == "capacidad":
        fila = next((f for f in rangos["capacidad"] if f["id"] == ident), None)
        valor = next(p.capacidad for p in nuevo.plantas if p.id == ident)
    else:
        fila = next((f for f in rangos["costos"] if f["ruta"] == ident), None)
        k = next(i for i, a in enumerate(nuevo.arcos) if f"{a.empresa_id}->{a.planta_id}" == ident)
        valor = nuevo.costos_efectivos()[k]
    if fila is None:
        return None
    eps = 1e-9
    return bool(
        (fila["minimo"] is None or valor >= fila["minimo"] - eps) and (fila["maximo"] is None or valor <= fila["maximo"] + eps)
    )


def _resumen_escenarios(filas: list[dict[str, Any]]) -> dict[str, Any]:
    gaps = [f["gap_pct"] for f in filas if f["gap_pct"] is not None]
    return {
        "escenarios": len(filas),
        "factibles_exacto": sum(1 for f in filas if f["exacto"]["factible"]),
        "factibles_ag": sum(1 for f in filas if f["genetico"] and f["genetico"]["factible"]),
        "ag_alcanza_optimo": sum(1 for g in gaps if abs(g) < 1e-6),
        "gap_pct_promedio": sum(gaps) / len(gaps) if gaps else None,
        "gap_pct_maximo": max(gaps) if gaps else None,
        "tiempo_exacto_total_ms": sum(f["exacto"]["duracion_ms"] for f in filas),
        "tiempo_ag_total_ms": sum(f["genetico"]["duracion_ms"] for f in filas if f["genetico"]),
        "escenarios_con_cambio_de_base": sum(1 for f in filas if f["base_cambio"]),
        "escenarios_con_cambio_de_asignacion": sum(1 for f in filas if f["asignaciones_cambiadas"] > 0),
    }


def ejecutar_sensibilidad(
    parametros: ParametrosModelo,
    variaciones: list[Variacion],
    incluir_ag: bool = True,
    configuracion: dict | None = None,
) -> dict[str, Any]:
    """Sensibilidad del LP exacto.

    1. Precios sombra de ofertas y capacidades (duales del LP base).
    2. Rangos de variación (ranging de HiGHS): lado derecho de cada oferta/capacidad y costo de cada ruta,
       uno a la vez, dentro de los cuales la base óptima NO cambia.
    3. Escenarios (variaciones porcentuales): cada uno se resuelve con el método exacto y, con ``incluir_ag``,
       también con el AG; se informan costos, gap %, tiempos, estados, cambio de asignaciones y si la base
       óptima cambió (comparando la base de HiGHS del escenario con la del caso base).
    """
    validar_tamano(parametros)
    escenarios = [(v, pct) for v in variaciones for pct in v.porcentajes]
    maximo = settings.OPTIAGRO["SENSIBILIDAD_MAX_ESCENARIOS"]
    if not escenarios:
        raise ErrorDeNegocio("Debe indicar al menos una variación.", ["'variaciones' no puede estar vacío."])
    if len(escenarios) > maximo:
        raise ErrorDeNegocio(
            "Demasiados escenarios de sensibilidad.", [f"Se pidieron {len(escenarios)}; el máximo es {maximo}."]
        )
    for v in variaciones:
        _validar_ids(parametros, v)
    cfg = configuracion_ag(configuracion) if incluir_ag else None
    if incluir_ag:
        _validar_trabajo_ag(parametros, cfg, corridas=len(escenarios) + 1)

    inicio = perf_counter()
    base_exacto = resolver_exacto(parametros)  # el caso base debe ser válido
    base_ag = AlgoritmoGenetico().resolver(parametros, cfg) if incluir_ag else None
    base_obj = base_exacto.objetivo
    base_lp = analizar_lp(parametros, con_rangos=True)
    rangos = base_lp.rangos

    filas = []
    for variacion, pct in escenarios:
        nuevo = _aplicar(parametros, variacion.tipo, variacion.ids, pct)
        exacto = MetodoExacto().resolver(nuevo)
        fila: dict[str, Any] = {
            "nombre": f"{variacion.tipo} {pct:+g}% ({', '.join(variacion.ids) if variacion.ids else 'todas'})",
            "tipo": variacion.tipo,
            "ids": list(variacion.ids),
            "porcentaje": pct,
            "exacto": resumen(exacto, con_duales=True),
            "variacion_objetivo": None,
            "variacion_objetivo_pct": None,
            "genetico": None,
            "gap_pct": None,
            "base_cambio": None,
            "dentro_de_rango": _dentro_de_rango(nuevo, variacion, rangos),
            "asignaciones_cambiadas": 0,
            "cambios_asignacion": [],
        }
        if exacto.objetivo is not None and base_obj is not None:
            fila["variacion_objetivo"] = exacto.objetivo - base_obj
            fila["variacion_objetivo_pct"] = gap_porcentual(exacto.objetivo, base_obj)
            fila["cambios_asignacion"] = _cambios_asignacion(base_exacto, exacto)
            fila["asignaciones_cambiadas"] = len(fila["cambios_asignacion"])
            lp = analizar_lp(nuevo)
            if lp.optimo and base_lp.firma_base is not None:
                fila["base_cambio"] = lp.firma_base != base_lp.firma_base
        if incluir_ag:
            ag = AlgoritmoGenetico().resolver(nuevo, cfg)
            fila["genetico"] = resumen(ag)
            fila["gap_pct"] = gap_porcentual(ag.objetivo, exacto.objetivo)
        # tabla plana (una fila por escenario) para listados y reportes
        fila.update(
            costo_exacto=exacto.objetivo,
            costo_ag=fila["genetico"]["objetivo"] if fila["genetico"] else None,
            tiempo_exacto_ms=exacto.duracion_ms,
            tiempo_ag_ms=fila["genetico"]["duracion_ms"] if fila["genetico"] else None,
            estado_exacto=exacto.estado,
            estado_ag=fila["genetico"]["estado"] if fila["genetico"] else None,
        )
        filas.append(fila)

    return {
        "base": {
            "exacto": resumen(base_exacto, con_duales=True),
            "genetico": resumen(base_ag) if base_ag else None,
            "gap_pct": gap_porcentual(base_ag.objetivo, base_obj) if base_ag else None,
        },
        "precios_sombra": {
            "empresas": {k.split(":", 1)[1]: v for k, v in base_exacto.duales.items() if k.startswith("oferta:")},
            "plantas": {k.split(":", 1)[1]: v for k, v in base_exacto.duales.items() if k.startswith("planta:")},
        },
        "rangos": {
            "disponible": rangos is not None,
            "metodo": "highs_ranging" if rangos else None,
            **(rangos or {"oferta": [], "capacidad": [], "costos": []}),
        },
        "plantas": analisis_plantas(parametros, base_exacto),
        "escenarios": filas,
        "resumen": _resumen_escenarios(filas),
        "configuracion_ag": cfg,
        "duracion_total_ms": (perf_counter() - inicio) * 1000,
        "nota": (
            "Precios sombra = d(costo)/d(rhs) del LP base. 'rangos' = intervalos (null = sin límite) en los que cada "
            "oferta, capacidad o costo de ruta puede variar, uno a la vez, sin cambiar la base óptima (HiGHS ranging). "
            "'base_cambio' compara la base óptima del escenario con la del caso base."
        ),
    }


# ---------------------------------------------------------------------------------------
# Reporte comparativo exacto vs AG
# ---------------------------------------------------------------------------------------
def reporte_comparativo(
    parametros: ParametrosModelo,
    configuracion: dict | None = None,
    variaciones: list[Variacion] | None = None,
) -> dict[str, Any]:
    validar_tamano(parametros)
    cfg = configuracion_ag(configuracion)
    _validar_trabajo_ag(parametros, cfg, corridas=1 + (sum(len(v.porcentajes) for v in variaciones) + 1 if variaciones else 0))
    exacto = resolver_exacto(parametros)
    ag, cfg = resolver_genetico(parametros, cfg)
    gap = gap_porcentual(ag.objetivo, exacto.objetivo)
    diferencia = (ag.objetivo - exacto.objetivo) if ag.objetivo is not None and exacto.objetivo is not None else None
    reporte = {
        "modelo": resumen_modelo(parametros),
        "exacto": {**resumen(exacto, con_duales=True), "asignaciones": exacto.asignaciones},
        "genetico": {
            **resumen(ag),
            "asignaciones": ag.asignaciones,
            "convergencia": ag.metricas.get("convergencia", []),
            "convergencia_promedio": ag.metricas.get("convergencia_promedio", []),
        },
        "configuracion_ag": cfg,
        "comparacion": {
            "diferencia_costo": diferencia,
            "gap_pct": gap,
            "ratio_tiempo": (ag.duracion_ms / exacto.duracion_ms) if exacto.duracion_ms > 0 else None,
            "ag_alcanza_optimo": bool(gap is not None and abs(gap) < 1e-6),
        },
        "plantas": analisis_plantas(parametros, exacto),
        "sensibilidad": None,
    }
    if variaciones:
        reporte["sensibilidad"] = ejecutar_sensibilidad(parametros, variaciones, incluir_ag=True, configuracion=cfg)
    return reporte
