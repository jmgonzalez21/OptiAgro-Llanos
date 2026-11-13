"""Generador DETERMINISTA de redes sintéticas (para pruebas de escalabilidad). Python puro, sin Django.

Misma ``(n_empresas, n_plantas, semilla)`` -> exactamente la misma red. La red es siempre completa (todas las
empresas conectadas con todas las plantas) y factible en modo base: la capacidad total es ``holgura`` veces la
oferta total y cada planta puede absorber al menos la oferta media de una empresa.
"""
from __future__ import annotations

import random

from .modelos import ArcoCosto, EmpresaAgropecuaria, ParametrosModelo, PlantaProcesamiento


def generar_red_sintetica(n_empresas: int, n_plantas: int, semilla: int = 2026, holgura: float = 1.3) -> ParametrosModelo:
    if n_empresas < 1 or n_plantas < 1:
        raise ValueError("Se requiere al menos una empresa y una planta.")
    rng = random.Random(f"{semilla}:{n_empresas}x{n_plantas}")
    empresas = tuple(
        EmpresaAgropecuaria(f"E{i}", f"Empresa sintética {i}", "sintético", float(rng.randint(5, 20)))
        for i in range(1, n_empresas + 1)
    )
    oferta_total = sum(e.oferta for e in empresas)
    pesos = [rng.uniform(0.5, 1.5) for _ in range(n_plantas)]
    capacidad_total = max(oferta_total * holgura, oferta_total + 1.0)
    plantas = tuple(
        PlantaProcesamiento(
            f"P{j}", f"Planta sintética {j}", "sintético",
            round(max(w / sum(pesos) * capacidad_total, 1.0) + 1.0, 3),
            costo_operacion_ton=float(rng.randint(0, 3) * 1000),
        )
        for j, w in enumerate(pesos, start=1)
    )  # fmt: skip
    arcos = tuple(
        ArcoCosto(e.id, p.id, 0.0, distancia_km=float(rng.randint(10, 200)), tarifa_km_ton=float(rng.randint(400, 600)))
        for e in empresas
        for p in plantas
    )
    return ParametrosModelo(empresas, plantas, arcos)
