"""ORM <-> dominio. Los códigos (``codigo``) son los identificadores del modelo de optimización."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from django.conf import settings

from dominio.modelos import ArcoCosto, EmpresaAgropecuaria, ParametrosModelo, PlantaProcesamiento
from red.models import Empresa, Planta, Ruta

from .errores import ErrorDeNegocio


def construir_parametros(modo_oferta: str = "exact") -> ParametrosModelo:
    """Red actual (solo elementos activos) -> ParametrosModelo."""
    empresas = Empresa.objects.filter(activa=True).order_by("codigo")
    plantas = Planta.objects.filter(activa=True).order_by("codigo")
    rutas = (
        Ruta.objects.filter(activa=True, empresa__activa=True, planta__activa=True)
        .select_related("empresa", "planta")
        .order_by("empresa__codigo", "planta__codigo")
    )
    return ParametrosModelo(
        empresas=tuple(EmpresaAgropecuaria(e.codigo, e.nombre, e.municipio, e.oferta, e.precio_tonelada) for e in empresas),
        plantas=tuple(
            PlantaProcesamiento(p.codigo, p.nombre, p.municipio, p.capacidad, p.tipo_demanda, p.costo_operacion_ton)
            for p in plantas
        ),
        arcos=tuple(
            ArcoCosto(
                r.empresa.codigo,
                r.planta.codigo,
                r.costo_efectivo,
                r.distancia_km,
                r.tarifa_km_ton,
                r.limite,
            )
            for r in rutas
        ),
        modo_oferta=modo_oferta,
    )


def parametros_a_dict(parametros: ParametrosModelo) -> dict[str, Any]:
    return asdict(parametros)


def parametros_desde_dict(datos: dict[str, Any]) -> ParametrosModelo:
    return ParametrosModelo(
        empresas=tuple(EmpresaAgropecuaria(**e) for e in datos["empresas"]),
        plantas=tuple(PlantaProcesamiento(**p) for p in datos["plantas"]),
        arcos=tuple(ArcoCosto(**a) for a in datos["arcos"]),
        modo_oferta=datos.get("modo_oferta", "exact"),
        unidad=datos.get("unidad", "toneladas"),
        periodo=datos.get("periodo", "semana"),
        moneda=datos.get("moneda", "COP"),
    )


def resumen_modelo(parametros: ParametrosModelo) -> dict[str, Any]:
    return {
        "empresas": len(parametros.empresas),
        "plantas": len(parametros.plantas),
        "rutas": len(parametros.arcos),
        "oferta_total": sum(e.oferta for e in parametros.empresas),
        "capacidad_total": sum(p.capacidad for p in parametros.plantas),
        "modo_oferta": parametros.modo_oferta,
    }


def validar_tamano(parametros: ParametrosModelo) -> None:
    """Rechaza problemas que bloquearían el servidor (límites en settings.OPTIAGRO)."""
    limites = settings.OPTIAGRO
    errores = []
    if len(parametros.empresas) > limites["MAX_EMPRESAS"]:
        errores.append(f"Demasiadas empresas ({len(parametros.empresas)}); máximo {limites['MAX_EMPRESAS']}.")
    if len(parametros.plantas) > limites["MAX_PLANTAS"]:
        errores.append(f"Demasiadas plantas ({len(parametros.plantas)}); máximo {limites['MAX_PLANTAS']}.")
    if len(parametros.arcos) > limites["MAX_RUTAS"]:
        errores.append(f"Demasiadas rutas ({len(parametros.arcos)}); máximo {limites['MAX_RUTAS']}.")
    if errores:
        raise ErrorDeNegocio("El problema excede el tamaño máximo permitido.", errores)


def incluye_ficticios(parametros: ParametrosModelo) -> bool:
    """True si alguna empresa o planta del modelo corresponde a un registro marcado como FICTICIO en la base."""
    return (
        Empresa.objects.filter(codigo__in=[e.id for e in parametros.empresas], ficticio=True).exists()
        or Planta.objects.filter(codigo__in=[p.id for p in parametros.plantas], ficticio=True).exists()
    )
