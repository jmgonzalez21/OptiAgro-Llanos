"""Parámetros del algoritmo genético y su validación (Python puro)."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, fields
from typing import Any

SELECCIONES = ("torneo", "ruleta")
CRUCES = ("un_punto", "dos_puntos")
INICIALIZACIONES = ("aleatoria", "heuristica")
MAX_SEMILLA = 2**31 - 1


@dataclass(frozen=True)
class ConfigAG:
    poblacion: int = 60
    generaciones: int = 150
    cruce: float = 0.8  # probabilidad de cruzar cada pareja de padres
    mutacion: float = 0.12  # probabilidad de mutar cada gen
    semilla: int = 42
    elitismo: int = 2  # individuos que pasan intactos a la siguiente generación
    seleccion: str = "torneo"  # "torneo" | "ruleta"
    tipo_cruce: str = "un_punto"  # "un_punto" | "dos_puntos"
    tamano_torneo: int = 3  # participantes por torneo (solo con seleccion="torneo")
    inicializacion: str = "aleatoria"  # "aleatoria" | "heuristica" (parte de la población sesgada hacia rutas baratas)

    @classmethod
    def desde_dict(cls, datos: dict[str, Any] | None) -> "ConfigAG":
        """Mezcla ``datos`` sobre los valores por defecto; ignora claves desconocidas."""
        nombres = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in (datos or {}).items() if k in nombres})

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)

    def errores(self) -> list[str]:
        """Lista de mensajes de validación (vacía si la configuración es correcta)."""
        e: list[str] = []

        def entero(nombre: str, minimo: int, maximo: int | None = None) -> bool:
            v = getattr(self, nombre)
            if isinstance(v, bool) or not isinstance(v, int):
                e.append(f"{nombre} debe ser un entero.")
                return False
            if v < minimo or (maximo is not None and v > maximo):
                e.append(f"{nombre} debe estar entre {minimo} y {maximo if maximo is not None else 'infinito'}.")
                return False
            return True

        def probabilidad(nombre: str) -> None:
            v = getattr(self, nombre)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1:
                e.append(f"{nombre} debe ser un número entre 0 y 1.")

        pob_ok = entero("poblacion", 2)
        entero("generaciones", 1)
        entero("semilla", 0, MAX_SEMILLA)
        probabilidad("cruce")
        probabilidad("mutacion")
        if entero("elitismo", 0) and pob_ok and self.elitismo >= self.poblacion:
            e.append("elitismo debe ser menor que la población.")
        if entero("tamano_torneo", 2) and pob_ok and self.tamano_torneo > self.poblacion:
            e.append("tamano_torneo no puede superar la población.")
        if self.seleccion not in SELECCIONES:
            e.append(f"seleccion debe ser una de: {', '.join(SELECCIONES)}.")
        if self.tipo_cruce not in CRUCES:
            e.append(f"tipo_cruce debe ser uno de: {', '.join(CRUCES)}.")
        if self.inicializacion not in INICIALIZACIONES:
            e.append(f"inicializacion debe ser una de: {', '.join(INICIALIZACIONES)}.")
        return e
