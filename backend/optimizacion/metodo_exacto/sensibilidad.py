"""Análisis de sensibilidad del LP exacto con HiGHS nativo (``highspy``): base óptima y rangos (ranging).

Python puro, sin Django. Construye el MISMO modelo que ``MetodoExacto`` (mismas filas y columnas) y devuelve:

* ``base``: estado de cada variable y restricción en el óptimo (firma de la base). Dos escenarios tienen la
  misma base óptima si y solo si su firma coincide.
* ``rangos`` (solo si se pide): intervalos en los que un parámetro puede variar, UNO A LA VEZ y con el resto
  fijo, sin que cambie la base óptima (la solución cambia linealmente, el conjunto de variables básicas no):

  - lado derecho de cada restricción (oferta de cada empresa, capacidad/demanda de cada planta),
  - coeficiente de costo de cada ruta.

Cómo se obtienen los límites:

* Restricciones activas (con precio sombra distinto de cero o que fijan la solución): ``Highs.getRanging``.
* Restricciones inactivas (holgura básica): HiGHS no da un rango útil, pero es exacto y trivial. Una
  restricción ``<=`` inactiva puede subir sin límite y bajar hasta su actividad actual (a partir de ahí pasa a
  estar activa); una ``>=`` inactiva, al revés. Ese cálculo se hace aquí.
* Costos de ruta: ``Highs.getRanging`` (cotas de los costos reducidos).

En soluciones degeneradas los rangos son válidos pero pueden ser conservadores (dependen de la base que
entrega el solver). Un límite ``None`` significa "sin límite" (infinito).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from dominio.modelos import ParametrosModelo
from optimizacion.validacion import validar

try:  # highspy es una dependencia opcional del núcleo; sin ella no hay ranging ni firma de base.
    import highspy
    import numpy as np

    DISPONIBLE = True
except ImportError:  # pragma: no cover
    highspy = None  # type: ignore[assignment]
    DISPONIBLE = False

_TOL = 1e-9


@dataclass
class AnalisisLP:
    optimo: bool
    objetivo: float | None = None
    firma_base: tuple[int, ...] | None = None
    precios_sombra: dict[str, float] = field(default_factory=dict)
    rangos: dict[str, Any] | None = None
    mensaje: str = ""


def _finito(valor: float) -> float | None:
    """inf / -inf / NaN -> None; -0.0 -> 0.0."""
    if valor is None or not math.isfinite(valor):
        return None
    return float(valor) + 0.0


def _construir(parametros: ParametrosModelo):
    """Filas (en el orden de MetodoExacto: empresas y luego plantas) y columnas (arcos)."""
    inf = highspy.kHighsInf
    arcos = list(parametros.arcos)
    filas: list[dict[str, Any]] = []
    for e in parametros.empresas:
        if parametros.modo_oferta == "exact":
            inferior, superior = e.oferta, e.oferta
        else:
            inferior, superior = -inf, e.oferta
        filas.append({"tipo": "oferta", "id": e.id, "rhs": e.oferta, "inf": inferior, "sup": superior})
    for p in parametros.plantas:
        if p.tipo_demanda == "exact":
            inferior, superior = p.capacidad, p.capacidad
        elif p.tipo_demanda == "capacity_max":
            inferior, superior = -inf, p.capacidad
        else:
            inferior, superior = p.capacidad, inf
        filas.append({"tipo": "planta", "id": p.id, "rhs": p.capacidad, "inf": inferior, "sup": superior})
    indice_fila = {(f["tipo"], f["id"]): i for i, f in enumerate(filas)}
    inicio, indices, valores = [0], [], []
    for a in arcos:  # matriz por columnas: cada arco toca su fila de empresa y su fila de planta
        indices.extend(sorted((indice_fila[("oferta", a.empresa_id)], indice_fila[("planta", a.planta_id)])))
        valores.extend([1.0, 1.0])
        inicio.append(len(indices))
    lp = highspy.HighsLp()
    lp.num_col_ = len(arcos)
    lp.num_row_ = len(filas)
    lp.col_cost_ = np.array(parametros.costos_efectivos(), dtype=float)
    lp.col_lower_ = np.zeros(len(arcos))
    lp.col_upper_ = np.array([a.limite if a.limite is not None else inf for a in arcos], dtype=float)
    lp.row_lower_ = np.array([f["inf"] for f in filas], dtype=float)
    lp.row_upper_ = np.array([f["sup"] for f in filas], dtype=float)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = np.array(inicio, dtype=np.int32)
    lp.a_matrix_.index_ = np.array(indices, dtype=np.int32)
    lp.a_matrix_.value_ = np.array(valores, dtype=float)
    return lp, filas, arcos


def analizar_lp(parametros: ParametrosModelo, con_rangos: bool = False) -> AnalisisLP:
    """Resuelve el LP con HiGHS y devuelve base, precios sombra y (opcionalmente) rangos de variación."""
    if not DISPONIBLE:
        return AnalisisLP(False, mensaje="highspy no está instalado.")
    errores = validar(parametros)
    if errores:
        return AnalisisLP(False, mensaje="; ".join(errores))
    lp, filas, arcos = _construir(parametros)
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    h.passModel(lp)
    h.run()
    if h.getModelStatus() != highspy.HighsModelStatus.kOptimal:
        return AnalisisLP(False, mensaje=h.modelStatusToString(h.getModelStatus()))
    solucion, base = h.getSolution(), h.getBasis()
    estado_col = [int(s) for s in base.col_status]
    estado_fila = [int(s) for s in base.row_status]
    analisis = AnalisisLP(
        True,
        objetivo=float(h.getInfo().objective_function_value),
        firma_base=tuple(estado_col + estado_fila),
        precios_sombra={f"{f['tipo']}:{f['id']}": float(solucion.row_dual[i]) + 0.0 for i, f in enumerate(filas)},
    )
    if not con_rangos:
        return analisis
    estado, rango = h.getRanging()
    if estado != highspy.HighsStatus.kOk:
        analisis.mensaje = "HiGHS no pudo calcular el ranging."
        return analisis
    basica = int(highspy.HighsBasisStatus.kBasic)
    flujo = list(solucion.col_value)
    actividad = list(solucion.row_value)

    def lado_derecho(i: int, f: dict[str, Any]) -> dict[str, Any]:
        if estado_fila[i] == basica and f["inf"] != f["sup"]:
            # restricción inactiva: sin efecto mientras no cruce su actividad actual
            minimo, maximo = (_finito(actividad[i]), None) if not math.isfinite(f["inf"]) else (None, _finito(actividad[i]))
            return {"minimo": minimo, "maximo": maximo, "objetivo_en_minimo": analisis.objetivo, "objetivo_en_maximo": analisis.objetivo}
        return {
            "minimo": _finito(rango.row_bound_dn.value_[i]),
            "maximo": _finito(rango.row_bound_up.value_[i]),
            "objetivo_en_minimo": _finito(rango.row_bound_dn.objective_[i]),
            "objetivo_en_maximo": _finito(rango.row_bound_up.objective_[i]),
        }

    def fila_rango(i: int, f: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": f["id"],
            "valor_actual": float(f["rhs"]),
            "precio_sombra": analisis.precios_sombra[f"{f['tipo']}:{f['id']}"],
            "activa": estado_fila[i] != basica,
            **lado_derecho(i, f),
        }

    efectivo = parametros.costos_efectivos()
    analisis.rangos = {
        "oferta": [fila_rango(i, f) for i, f in enumerate(filas) if f["tipo"] == "oferta"],
        "capacidad": [fila_rango(i, f) for i, f in enumerate(filas) if f["tipo"] == "planta"],
        "costos": [
            {
                "ruta": f"{a.empresa_id}->{a.planta_id}",
                "costo_actual": float(efectivo[k]),
                "flujo": float(flujo[k]) + 0.0,
                "en_base": estado_col[k] == basica,
                "costo_reducido": float(solucion.col_dual[k]) + 0.0,
                "minimo": _finito(rango.col_cost_dn.value_[k]),
                "maximo": _finito(rango.col_cost_up.value_[k]),
                "objetivo_en_minimo": _finito(rango.col_cost_dn.objective_[k]),
                "objetivo_en_maximo": _finito(rango.col_cost_up.objective_[k]),
            }
            for k, a in enumerate(arcos)
        ],
    }
    return analisis
