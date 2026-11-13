"""Persistencia de ejecuciones y resultados (JSON)."""
from __future__ import annotations

import json
from typing import Any

from django.db import transaction

from escenarios.models import Ejecucion, Escenario, Resultado


def _json_seguro(datos: Any) -> Any:
    """Garantiza JSON válido para PostgreSQL (jsonb rechaza NaN/Infinity)."""
    return json.loads(json.dumps(datos, default=str), parse_constant=lambda _: None)


@transaction.atomic
def registrar_ejecucion(
    *,
    usuario,
    metodo: str,
    estado: str,
    objetivo: float | None,
    duracion_ms: float,
    configuracion: dict,
    parametros: dict,
    datos: dict,
    escenario: Escenario | None = None,
    incluye_ficticios: bool = False,
) -> Ejecucion:
    ejecucion = Ejecucion.objects.create(
        usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
        escenario=escenario,
        metodo=metodo,
        incluye_ficticios=incluye_ficticios,
        estado=estado,
        objetivo=objetivo,
        duracion_ms=duracion_ms,
        configuracion=_json_seguro(configuracion),
        parametros=_json_seguro(parametros),
    )
    Resultado.objects.create(ejecucion=ejecucion, datos=_json_seguro(datos))
    return ejecucion
