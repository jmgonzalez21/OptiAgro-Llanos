from rest_framework.permissions import SAFE_METHODS, BasePermission

from cuentas.models import Rol


class EscrituraSoloAdministrador(BasePermission):
    """Lectura para cualquier usuario autenticado; escritura solo rol administrador."""

    message = "Solo el rol administrador puede modificar la red."

    def has_permission(self, request, view):
        usuario = request.user
        if not (usuario and usuario.is_authenticated):
            return False
        return request.method in SAFE_METHODS or usuario.es_administrador


class EsAnalistaOAdministrador(BasePermission):
    """Ejecutar optimizaciones: roles analista y administrador."""

    message = "Se requiere rol analista o administrador."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario and usuario.is_authenticated and (usuario.es_administrador or usuario.rol == Rol.ANALISTA)
        )


class SoloAdministrador(BasePermission):
    """Lectura y escritura solo para el rol administrador."""

    message = "Solo el rol administrador puede realizar esta acción."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(usuario and usuario.is_authenticated and usuario.es_administrador)
