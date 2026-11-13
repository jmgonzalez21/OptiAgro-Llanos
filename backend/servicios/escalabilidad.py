"""Prueba de escalabilidad: redes sintéticas deterministas de tamaño creciente, exacto vs AG."""
from __future__ import annotations

from time import perf_counter
from typing import Any

from django.conf import settings

from dominio.redes_sinteticas import generar_red_sintetica
from optimizacion import AlgoritmoGenetico, MetodoExacto

from .conversion import validar_tamano
from .ejecucion import configuracion_ag, gap_porcentual, resumen
from .errores import ErrorDeNegocio

TAMANOS_DEFECTO = [(10, 4), (20, 6), (40, 10), (80, 16)]
# El AG de la prueba parte de una población sesgada hacia rutas baratas (si no, con redes grandes y poco presupuesto
# el gap es enorme); se puede pedir inicializacion="aleatoria" para ver la línea base del PDF.
CONFIG_AG_DEFECTO = {"poblacion": 40, "generaciones": 80, "inicializacion": "heuristica"}


def ejecutar_escalabilidad(
    tamanos: list[tuple[int, int]] | None = None,
    configuracion: dict | None = None,
    semilla_red: int = 2026,
) -> dict[str, Any]:
    tamanos = tamanos or list(TAMANOS_DEFECTO)
    limites = settings.OPTIAGRO
    cfg = configuracion_ag({**CONFIG_AG_DEFECTO, **(configuracion or {})})
    errores: list[str] = []
    if len(tamanos) > limites["ESCALABILIDAD_MAX_TAMANOS"]:
        errores.append(f"Se pidieron {len(tamanos)} tamaños; el máximo es {limites['ESCALABILIDAD_MAX_TAMANOS']}.")
    trabajo = 0
    for n_e, n_p in tamanos:
        if n_e > limites["MAX_EMPRESAS"]:
            errores.append(f"{n_e}x{n_p}: demasiadas empresas (máximo {limites['MAX_EMPRESAS']}).")
        if n_p > limites["MAX_PLANTAS"]:
            errores.append(f"{n_e}x{n_p}: demasiadas plantas (máximo {limites['MAX_PLANTAS']}).")
        if n_e * n_p > limites["MAX_RUTAS"]:
            errores.append(f"{n_e}x{n_p}: {n_e * n_p} rutas exceden el máximo {limites['MAX_RUTAS']}.")
        trabajo += cfg["poblacion"] * cfg["generaciones"] * n_e * n_p
    if not errores and trabajo > limites["ESCALABILIDAD_MAX_TRABAJO"]:
        errores.append(
            f"poblacion x generaciones x rutas (sumado) = {trabajo:,} excede el máximo "
            f"{limites['ESCALABILIDAD_MAX_TRABAJO']:,}. Reduzca los tamaños, la población o las generaciones."
        )
    if errores:
        raise ErrorDeNegocio("La prueba de escalabilidad excede los límites del servidor.", errores)

    inicio = perf_counter()
    filas = []
    for n_e, n_p in tamanos:
        red = generar_red_sintetica(n_e, n_p, semilla_red)
        validar_tamano(red)
        exacto = MetodoExacto().resolver(red)
        ag = AlgoritmoGenetico().resolver(red, cfg)
        filas.append(
            {
                "empresas": n_e,
                "plantas": n_p,
                "rutas": len(red.arcos),
                "oferta_total": sum(e.oferta for e in red.empresas),
                "capacidad_total": sum(p.capacidad for p in red.plantas),
                "exacto": resumen(exacto),
                "genetico": resumen(ag),
                "gap_pct": gap_porcentual(ag.objetivo, exacto.objetivo),
                "ratio_tiempo": (ag.duracion_ms / exacto.duracion_ms) if exacto.duracion_ms > 0 else None,
            }
        )
    return {
        "ficticio": True,
        "semilla_red": semilla_red,
        "configuracion_ag": cfg,
        "tamanos": filas,
        "duracion_total_ms": (perf_counter() - inicio) * 1000,
        "nota": (
            "Redes SINTÉTICAS (FICTICIAS) y deterministas: misma semilla y tamaño = misma red. "
            "No se guardan en la base de datos."
        ),
    }
