"""Entidades y contratos independientes de interfaz y persistencia (Python puro, sin Django).

Modelo de costos (COP por tonelada que viaja de la empresa ``i`` a la planta ``j``):

    costo_efectivo(i, j) = costo_transporte(i, j)            # distancia x tarifa km-ton, o costo unitario directo
                         + costo_operacion_ton de la planta j # costo de operar/procesar en la planta
                         + precio_tonelada de la empresa i    # precio que se paga por la tonelada de residuo

Con ``costo_operacion_ton = 0`` y ``precio_tonelada = 0`` (valores por defecto) el costo efectivo coincide con el
costo de transporte y el modelo se comporta exactamente igual que antes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any, Literal

TipoDemanda = Literal["capacity_max", "exact", "minimum"]


@dataclass(frozen=True)
class EmpresaAgropecuaria:
    id: str
    nombre: str
    ubicacion: str
    oferta: float
    precio_tonelada: float = 0.0  # COP/t pagados por el residuo (0 = se retira sin costo)

    def actualizar_oferta(self, oferta: float) -> "EmpresaAgropecuaria":
        return replace(self, oferta=oferta)


@dataclass(frozen=True)
class PlantaProcesamiento:
    id: str
    nombre: str
    municipio: str
    capacidad: float
    tipo_demanda: TipoDemanda = "capacity_max"
    costo_operacion_ton: float = 0.0  # COP/t de operación/procesamiento en la planta

    def actualizar_capacidad(self, capacidad: float) -> "PlantaProcesamiento":
        return replace(self, capacidad=capacidad)


@dataclass(frozen=True)
class ArcoCosto:
    empresa_id: str
    planta_id: str
    costo_unitario: float
    distancia_km: float | None = None
    tarifa_km_ton: float | None = None
    limite: float | None = None

    @property
    def costo_calculado(self) -> float:
        """Costo de TRANSPORTE de la ruta (distancia x tarifa si ambas existen; si no, el costo unitario)."""
        if self.distancia_km is None or self.tarifa_km_ton is None:
            return self.costo_unitario
        return self.distancia_km * self.tarifa_km_ton


@dataclass(frozen=True)
class ParametrosModelo:
    empresas: tuple[EmpresaAgropecuaria, ...]
    plantas: tuple[PlantaProcesamiento, ...]
    arcos: tuple[ArcoCosto, ...]
    modo_oferta: Literal["exact", "maximum"] = "exact"
    unidad: str = "toneladas"
    periodo: str = "semana"
    moneda: str = "COP"

    def desglose_arcos(self) -> list[tuple[float, float, float]]:
        """(transporte, operación de la planta, precio de la empresa) de cada arco, en el orden de ``arcos``."""
        operacion = {p.id: p.costo_operacion_ton for p in self.plantas}
        precio = {e.id: e.precio_tonelada for e in self.empresas}
        return [(a.costo_calculado, operacion.get(a.planta_id, 0.0), precio.get(a.empresa_id, 0.0)) for a in self.arcos]

    def costos_efectivos(self) -> list[float]:
        """Costo efectivo (COP/t) de cada arco: lo que minimizan los solvers."""
        return [t + o + p for t, o, p in self.desglose_arcos()]


@dataclass
class ResultadoOptimizacion:
    metodo: str
    estado: str
    factible: bool
    objetivo: float | None
    asignaciones: list[dict[str, Any]]
    duracion_ms: float
    mensajes: list[str] = field(default_factory=list)
    duales: dict[str, float] = field(default_factory=dict)
    verificacion: dict[str, Any] = field(default_factory=dict)
    metricas: dict[str, Any] = field(default_factory=dict)

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MatrizCostos:
    costos: dict[tuple[str, str], float]

    def actualizar_costo(self, empresa_id: str, planta_id: str, costo: float) -> None:
        self.costos[(empresa_id, planta_id)] = costo

    def obtener_costo(self, empresa_id: str, planta_id: str) -> float | None:
        return self.costos.get((empresa_id, planta_id))


@dataclass
class RedLogistica:
    empresas: list[EmpresaAgropecuaria]
    plantas: list[PlantaProcesamiento]
    matriz_costos: MatrizCostos

    def construir_red(self) -> list[tuple[str, str, float]]:
        return [(i, j, c) for (i, j), c in self.matriz_costos.costos.items()]
