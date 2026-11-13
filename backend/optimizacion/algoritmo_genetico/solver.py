"""Algoritmo genético para el modelo de transporte (modo base: oferta exacta, plantas con capacidad máxima).

Cromosoma
    Vector de ``n`` números reales en [0, 1), uno por ruta (llaves aleatorias / *random keys*). El valor de cada
    gen es la PRIORIDAD de su ruta: cuanto menor, antes se usa.

Decodificador con reparación
    Recorre las rutas por prioridad creciente y envía por cada una
    ``min(oferta restante de la empresa, capacidad restante de la planta, límite de la ruta)``.
    Por construcción nunca excede oferta, capacidad ni límites de ruta. La única restricción que puede quedar
    incumplida es la oferta total (toneladas SIN ASIGNAR, ``deficit``) cuando la red no alcanza a absorberla.

Función de aptitud (se maximiza)
    violacion       = deficit + exceso_de_capacidad + exceso_de_limite     (en t; los dos últimos son 0 tras la
                                                                           reparación, se mantienen por robustez)
    costo_penalizado = costo_total + lambda * violacion
    aptitud          = 1 / (1 + costo_penalizado)                          (inversa del costo penalizado)

    con costo_total = suma(cantidad x costo efectivo de la ruta) y
    lambda = FACTOR_PENALIZACION x (costo_efectivo_maximo + 1) x (oferta_total + 1) [COP/t].
    Así una solución factible siempre supera a una que deje toneladas sin asignar, y el AG recibe una señal
    gradual (menos déficit = mejor aptitud) aun cuando la población inicial sea infactible.

Operadores configurables (ver ``ConfigAG``)
    selección: ``torneo`` (gana el mejor de ``tamano_torneo`` individuos al azar) o ``ruleta`` (probabilidad
               proporcional a la aptitud con escalamiento por ventana: w = f - f_min + 0.05 (f_max - f_min); sin
               escalamiento, aptitudes tan parecidas como 1/65 y 1/67 casi no se distinguirían).
    cruce:     ``un_punto`` o ``dos_puntos`` entre dos padres con probabilidad ``cruce``.
    mutación:  cada gen se reemplaza por un valor aleatorio con probabilidad ``mutacion``.
    elitismo:  los ``elitismo`` mejores pasan intactos a la siguiente generación.
    inicialización: ``aleatoria`` (por defecto, línea base del PDF) o ``heuristica`` (parte de la población
               sesgada hacia rutas baratas; mejora el resultado en redes grandes).

Reproducibilidad: todo el azar sale de ``random.Random(semilla)``; misma semilla y datos = mismo resultado.
"""
from __future__ import annotations

import random
from bisect import bisect_left
from itertools import accumulate
from time import perf_counter

from dominio.modelos import ParametrosModelo, ResultadoOptimizacion
from optimizacion.validacion import construir_asignaciones, desglose_objetivo, validar, verificar

from .config import ConfigAG

FACTOR_PENALIZACION = 10.0
TOLERANCIA_DEFICIT = 1e-7


class _Individuo:
    __slots__ = ("genes", "costo", "violacion", "penalizado", "aptitud")

    def __init__(self, genes, costo, violacion, penalizado, aptitud):
        self.genes, self.costo, self.violacion, self.penalizado, self.aptitud = genes, costo, violacion, penalizado, aptitud


class AlgoritmoGenetico:
    def resolver(self, parametros: ParametrosModelo, configuracion: dict | ConfigAG | None = None) -> ResultadoOptimizacion:
        errores = validar(parametros)
        if errores:
            return ResultadoOptimizacion("genetico", "INVALID_INPUT", False, None, [], 0, errores)
        # La reparación admite únicamente el modo principal para que el AG no presente factibilidad falsa.
        if parametros.modo_oferta != "exact" or any(p.tipo_demanda != "capacity_max" for p in parametros.plantas):
            return ResultadoOptimizacion(
                "genetico", "INVALID_INPUT", False, None, [], 0,
                ["El AG actual admite el modo base: oferta exacta y capacidades máximas."],
            )  # fmt: skip
        cfg = configuracion if isinstance(configuracion, ConfigAG) else ConfigAG.desde_dict(configuracion)
        errores_cfg = cfg.errores()
        if errores_cfg:
            return ResultadoOptimizacion("genetico", "INVALID_INPUT", False, None, [], 0, errores_cfg)

        rng = random.Random(cfg.semilla)
        arcos = list(parametros.arcos)
        n = len(arcos)
        e_idx = {e.id: i for i, e in enumerate(parametros.empresas)}
        p_idx = {p.id: j for j, p in enumerate(parametros.plantas)}
        arco_e = [e_idx[a.empresa_id] for a in arcos]
        arco_p = [p_idx[a.planta_id] for a in arcos]
        arco_limite = [a.limite if a.limite is not None else float("inf") for a in arcos]
        costos = parametros.costos_efectivos()
        oferta = [e.oferta for e in parametros.empresas]
        capacidad = [p.capacidad for p in parametros.plantas]
        oferta_total = sum(oferta)
        penalizacion = FACTOR_PENALIZACION * (max(costos, default=0.0) + 1.0) * (oferta_total + 1.0)
        rango_n = range(n)

        def decodificar(genes):
            """Prioridades -> flujos [(índice de arco, t)], costo y violación (t sin asignar)."""
            restante_o, restante_c = oferta[:], capacidad[:]
            pendiente = oferta_total
            flujos, costo = [], 0.0
            for k in sorted(rango_n, key=genes.__getitem__):
                if pendiente <= 1e-10:
                    break
                e, p = arco_e[k], arco_p[k]
                disponible = min(restante_o[e], restante_c[p], arco_limite[k])
                if disponible > 1e-10:
                    flujos.append((k, disponible))
                    restante_o[e] -= disponible
                    restante_c[p] -= disponible
                    pendiente -= disponible
                    costo += disponible * costos[k]
            return flujos, costo, max(0.0, pendiente)

        def evaluar(genes) -> _Individuo:
            _, costo, violacion = decodificar(genes)
            penalizado = costo + penalizacion * violacion
            return _Individuo(genes, costo, violacion, penalizado, 1.0 / (1.0 + penalizado))

        def crear_selector(poblacion):
            if cfg.seleccion == "torneo":
                return lambda: max(rng.sample(poblacion, cfg.tamano_torneo), key=lambda i: i.aptitud)
            aptitudes = [i.aptitud for i in poblacion]
            minimo, tramo = min(aptitudes), max(aptitudes) - min(aptitudes)
            pesos = [1.0] * len(aptitudes) if tramo <= 0 else [a - minimo + 0.05 * tramo for a in aptitudes]
            acumulado = list(accumulate(pesos))
            total, ultimo = acumulado[-1], len(poblacion) - 1
            return lambda: poblacion[min(bisect_left(acumulado, rng.random() * total), ultimo)]

        def cruzar(a, b):
            if n < 2:
                return a[:], b[:]
            if cfg.tipo_cruce == "un_punto" or n < 3:
                c = rng.randrange(1, n)
                return a[:c] + b[c:], b[:c] + a[c:]
            c1, c2 = sorted(rng.sample(range(1, n), 2))
            return a[:c1] + b[c1:c2] + a[c2:], b[:c1] + a[c1:c2] + b[c2:]

        def mutar(genes):
            if cfg.mutacion > 0:
                for i in rango_n:
                    if rng.random() < cfg.mutacion:
                        genes[i] = rng.random()
            return genes

        costo_max = max(costos, default=0.0) or 1.0

        def genes_iniciales(i: int):
            """Aleatorio; con inicializacion="heuristica", el individuo 0 ordena las rutas por costo (voraz) y la
            primera mitad de la población lo imita con ruido creciente. El resto sigue siendo aleatorio."""
            if cfg.inicializacion == "heuristica" and i < max(1, cfg.poblacion // 2):
                ruido = 0.0 if i == 0 else rng.uniform(0.05, 0.5)
                return [costos[k] / costo_max * (1 - ruido) + rng.random() * ruido for k in rango_n]
            return [rng.random() for _ in rango_n]

        inicio = perf_counter()
        poblacion = [evaluar(genes_iniciales(i)) for i in range(cfg.poblacion)]
        evaluaciones = cfg.poblacion
        mejor: _Individuo | None = None  # mejor de toda la corrida: primero factible, luego menor costo penalizado
        hist = {"convergencia": [], "convergencia_promedio": [], "aptitud_mejor": [], "aptitud_promedio": [], "factibles": []}
        for generacion in range(cfg.generaciones):
            poblacion.sort(key=lambda i: i.penalizado)
            lider = poblacion[0]
            hist["convergencia"].append(lider.penalizado)
            hist["convergencia_promedio"].append(sum(i.penalizado for i in poblacion) / len(poblacion))
            hist["aptitud_mejor"].append(max(i.aptitud for i in poblacion))
            hist["aptitud_promedio"].append(sum(i.aptitud for i in poblacion) / len(poblacion))
            hist["factibles"].append(sum(1 for i in poblacion if i.violacion <= TOLERANCIA_DEFICIT))
            candidato = min(poblacion, key=lambda i: (i.violacion > TOLERANCIA_DEFICIT, i.penalizado))
            if mejor is None or (candidato.violacion > TOLERANCIA_DEFICIT, candidato.penalizado) < (
                mejor.violacion > TOLERANCIA_DEFICIT, mejor.penalizado
            ):
                mejor = candidato
            if generacion == cfg.generaciones - 1:
                break
            seleccionar = crear_selector(poblacion)
            nueva = poblacion[: cfg.elitismo]
            while len(nueva) < cfg.poblacion:
                a, b = seleccionar().genes, seleccionar().genes
                h1, h2 = cruzar(a, b) if rng.random() < cfg.cruce else (a[:], b[:])
                for hijo in (h1, h2):
                    if len(nueva) < cfg.poblacion:
                        nueva.append(evaluar(mutar(hijo)))
                        evaluaciones += 1
            poblacion = nueva

        assert mejor is not None
        flujos, costo, violacion = decodificar(mejor.genes)
        asignaciones = construir_asignaciones(parametros, flujos)
        comprobacion = verificar(parametros, asignaciones)
        tiempo = (perf_counter() - inicio) * 1000
        metricas = {
            **hist,
            **cfg.como_dict(),
            "penalizacion": penalizacion,
            "mejor_aptitud": mejor.aptitud,
            "evaluaciones": evaluaciones,
            "violacion_t": violacion,
        }
        if violacion > TOLERANCIA_DEFICIT or not comprobacion["valida"]:
            return ResultadoOptimizacion(
                "genetico", "INFEASIBLE", False, None, asignaciones, tiempo,
                ["No se halló una asignación factible."], verificacion=comprobacion, metricas=metricas,
            )  # fmt: skip
        metricas["desglose_costos"] = desglose_objetivo(parametros, asignaciones)
        return ResultadoOptimizacion("genetico", "FEASIBLE", True, costo, asignaciones, tiempo, verificacion=comprobacion, metricas=metricas)
