"""Formato uniforme de errores: {"detail": "...", "errores": [...] | {...}} en los 400."""
import logging

from django.http import Http404  # noqa: F401  (manejado por DRF)
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from servicios.errores import ErrorDeNegocio

logger = logging.getLogger("optiagro.api")


def manejador_excepciones(exc, contexto):
    if isinstance(exc, ErrorDeNegocio):
        return Response({"detail": exc.mensaje, "errores": exc.errores}, status=status.HTTP_400_BAD_REQUEST)
    respuesta = exception_handler(exc, contexto)
    if respuesta is None:
        logger.exception("Error no controlado en la API", exc_info=exc)
        return Response(
            {"detail": "Error interno del servidor. Consulte los registros."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    if isinstance(exc, ValidationError):
        respuesta.data = {"detail": "Datos de entrada inválidos.", "errores": respuesta.data}
    return respuesta
