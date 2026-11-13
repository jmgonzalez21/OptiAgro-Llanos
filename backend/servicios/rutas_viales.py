"""Distancias y trayectos por carretera con OSRM (OpenStreetMap).

La ruta es la que calcula OSRM sobre OpenStreetMap (en general la más corta/rápida por carretera, perfil
``driving``); no se restringe explícitamente a vías nacionales. Si OSRM no responde se usa un respaldo
(Haversine x 1,3) y la distancia se marca ``estimada``. Coordenadas siempre en orden lon,lat hacia OSRM.
"""
from __future__ import annotations

import json
import logging
import math
import time
import urllib.error
import urllib.request

from django.conf import settings
from django.db import transaction

logger = logging.getLogger("optiagro.osrm")

FACTOR_RESPALDO = 1.3
USER_AGENT = "OptiAgro-Llanos"
Punto = tuple[float, float]  # (latitud, longitud)


class ErrorOSRM(Exception):
    """OSRM no disponible, respondió con error o no encontró ruta."""


def _cfg() -> dict:
    return settings.OPTIAGRO_OSRM


def habilitado() -> bool:
    return bool(_cfg()["HABILITADO"])


def _get_json(ruta: str, params: dict | None = None) -> dict:
    if not habilitado():
        raise ErrorOSRM("El servicio OSRM está deshabilitado (OPTIAGRO_OSRM_HABILITADO=false).")
    cfg = _cfg()
    url = cfg["URL"].rstrip("/") + ruta
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    peticion = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(peticion, timeout=cfg["TIMEOUT"]) as resp:  # noqa: S310 (URL de configuración)
            datos = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        cuerpo = ""
        try:
            cuerpo = json.loads(exc.read().decode("utf-8")).get("message", "")
        except Exception:  # noqa: BLE001
            pass
        if exc.code == 429:
            raise ErrorOSRM("OSRM limitó las peticiones (429). Intente de nuevo más tarde.") from exc
        raise ErrorOSRM(f"OSRM respondió HTTP {exc.code}. {cuerpo}".strip()) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ErrorOSRM(f"No se pudo contactar con OSRM: {getattr(exc, 'reason', exc)}") from exc
    except ValueError as exc:
        raise ErrorOSRM("OSRM devolvió una respuesta que no es JSON.") from exc
    if datos.get("code") != "Ok":
        raise ErrorOSRM(f"OSRM no encontró ruta ({datos.get('code')}: {datos.get('message', '')}).".strip())
    return datos


def _coords(puntos: list[Punto]) -> str:
    return ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in puntos)


def haversine_km(a: Punto, b: Punto) -> float:
    (lat1, lon1), (lat2, lon2) = a, b
    p1, p2 = math.radians(lat1), math.radians(lat2)
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(h))


def distancia_respaldo_km(a: Punto, b: Punto) -> float:
    return round(haversine_km(a, b) * FACTOR_RESPALDO, 1)


def distancias_lote(origenes: list[Punto], destinos: list[Punto]) -> list[list[float | None]]:
    """Matriz de distancias por carretera en km (redondeada a 0,1); ``None`` si no hay ruta entre un par.

    Divide en lotes para respetar el máximo de coordenadas por petición ``table``. Lanza ``ErrorOSRM`` si falla.
    """
    if not origenes or not destinos:
        return [[] for _ in origenes]
    maximo = max(2, _cfg()["MAX_COORDENADAS"])
    tam_dest = max(1, min(len(destinos), maximo // 2))
    tam_orig = max(1, min(len(origenes), maximo - tam_dest))
    matriz: list[list[float | None]] = [[None] * len(destinos) for _ in origenes]
    primera = True
    for i in range(0, len(origenes), tam_orig):
        for j in range(0, len(destinos), tam_dest):
            if not primera:
                time.sleep(_cfg()["PAUSA_LOTES"])  # cortesía con el servidor público
            primera = False
            o, d = origenes[i : i + tam_orig], destinos[j : j + tam_dest]
            datos = _get_json(
                f"/table/v1/driving/{_coords(o + d)}",
                {
                    "sources": ";".join(str(k) for k in range(len(o))),
                    "destinations": ";".join(str(len(o) + k) for k in range(len(d))),
                    "annotations": "distance",
                },
            )
            filas = datos.get("distances")
            if not filas or len(filas) != len(o):
                raise ErrorOSRM("OSRM no devolvió la matriz de distancias.")
            for a, fila in enumerate(filas):
                for b, metros in enumerate(fila):
                    matriz[i + a][j + b] = None if metros is None else round(metros / 1000, 1)
    return matriz


def distancia_ruta_km(origen: Punto, destino: Punto) -> float:
    """Distancia por carretera entre dos puntos (lanza ``ErrorOSRM`` si no hay ruta)."""
    fila = distancias_lote([origen], [destino])[0]
    if fila[0] is None:
        raise ErrorOSRM("OSRM no encontró ruta entre los dos puntos.")
    return fila[0]


def trayecto_geojson(origen: Punto, destino: Punto) -> tuple[dict, float]:
    """GeoJSON LineString del trayecto por carretera y su distancia en km (lanza ``ErrorOSRM``)."""
    datos = _get_json(
        f"/route/v1/driving/{_coords([origen, destino])}", {"overview": "simplified", "geometries": "geojson"}
    )
    rutas = datos.get("routes") or []
    if not rutas or rutas[0].get("geometry", {}).get("type") != "LineString":
        raise ErrorOSRM("OSRM no devolvió trayecto para la ruta.")
    return rutas[0]["geometry"], round(rutas[0]["distance"] / 1000, 1)


def linea_recta(origen: Punto, destino: Punto) -> dict:
    """Trayecto de respaldo (línea recta) como LineString [lon, lat]."""
    return {"type": "LineString", "coordinates": [[origen[1], origen[0]], [destino[1], destino[0]]]}


# --- Integración con el modelo de red ---------------------------------------------------------
def punto(nodo) -> Punto | None:
    if nodo.latitud is None or nodo.longitud is None:
        return None
    return (float(nodo.latitud), float(nodo.longitud))


def distancia_con_respaldo(origen: Punto, destino: Punto) -> tuple[float, str, str | None]:
    """(km, fuente, aviso): por carretera si OSRM responde; si no, Haversine x 1,3 marcada ``estimada``."""
    try:
        return distancia_ruta_km(origen, destino), "carretera", None
    except ErrorOSRM as exc:
        logger.warning("OSRM no disponible, se usa respaldo: %s", exc)
        return (
            distancia_respaldo_km(origen, destino),
            "estimada",
            f"No se pudo calcular la distancia por carretera ({exc}). Se usó una estimación "
            f"(línea recta x {FACTOR_RESPALDO}); puede recalcularla más tarde.",
        )


def obtener_trayecto(ruta) -> dict:
    """Trayecto de una ruta (cacheado en ``ruta.trayecto``). Si OSRM falla devuelve una línea recta sin cachear."""
    if ruta.trayecto:
        return {"trayecto": ruta.trayecto, "fuente": "carretera", "cacheado": True, "aviso": None}
    a, b = punto(ruta.empresa), punto(ruta.planta)
    if a is None or b is None:
        from .errores import ErrorDeNegocio

        raise ErrorDeNegocio("La empresa o la planta de la ruta no tienen coordenadas.")
    try:
        geometria, _km = trayecto_geojson(a, b)
    except ErrorOSRM as exc:
        return {
            "trayecto": linea_recta(a, b),
            "fuente": "estimada",
            "cacheado": False,
            "aviso": f"No se pudo obtener el trayecto por carretera ({exc}). Se muestra una línea recta.",
        }
    ruta.trayecto = geometria
    ruta.save(update_fields=["trayecto", "actualizado_en"])
    return {"trayecto": geometria, "fuente": "carretera", "cacheado": False, "aviso": None}


def recalcular_rutas(rutas, incluir_manuales: bool = False) -> dict:
    """Recalcula ``distancia_km`` de las rutas dadas. Devuelve {actualizadas, estimadas, errores, detalle_errores, aviso}.

    Por defecto solo toca rutas con fuente ``carretera``/``estimada`` (las ``manual`` se respetan).
    """
    from red.models import FuenteDistancia

    rutas = list(rutas)
    if not incluir_manuales:
        rutas = [r for r in rutas if r.distancia_fuente != FuenteDistancia.MANUAL]
    errores: list[str] = []
    validas = []
    for r in rutas:
        a, b = punto(r.empresa), punto(r.planta)
        if a is None or b is None:
            errores.append(f"Ruta {r}: falta latitud/longitud en la empresa o en la planta.")
        else:
            validas.append((r, a, b))
    aviso = None
    matriz = None
    if validas:
        origenes = sorted({a for _, a, _ in validas})
        destinos = sorted({b for _, _, b in validas})
        try:
            matriz = distancias_lote(origenes, destinos)
        except ErrorOSRM as exc:
            logger.warning("OSRM no disponible al recalcular: %s", exc)
            aviso = (
                f"No se pudo consultar OSRM ({exc}). Las distancias se estimaron como línea recta x "
                f"{FACTOR_RESPALDO}; vuelva a recalcular más tarde."
            )
    io = {p: i for i, p in enumerate(sorted({a for _, a, _ in validas}))}
    idd = {p: i for i, p in enumerate(sorted({b for _, _, b in validas}))}
    actualizadas = estimadas = 0
    with transaction.atomic():
        for r, a, b in validas:
            km = matriz[io[a]][idd[b]] if matriz is not None else None
            if km is None:
                km, fuente = distancia_respaldo_km(a, b), "estimada"
                estimadas += 1
            else:
                fuente = "carretera"
            r.distancia_km, r.distancia_fuente, r.trayecto = km, fuente, None
            r.save()
            actualizadas += 1
    if estimadas and aviso is None:
        aviso = f"{estimadas} ruta(s) sin camino en OSRM se estimaron como línea recta x {FACTOR_RESPALDO}."
    return {
        "actualizadas": actualizadas,
        "estimadas": estimadas,
        "errores": len(errores),
        "detalle_errores": errores,
        "aviso": aviso,
    }


def recalcular_por_nodo(empresa=None, planta=None) -> dict:
    """Tras cambiar coordenadas de un nodo: invalida trayectos y recalcula sus rutas carretera/estimada."""
    from red.models import Ruta

    rutas = Ruta.objects.select_related("empresa", "planta").filter(
        **({"empresa": empresa} if empresa is not None else {"planta": planta})
    )
    rutas.update(trayecto=None)
    return recalcular_rutas(rutas.all())
