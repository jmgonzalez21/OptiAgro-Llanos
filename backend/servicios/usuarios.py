"""Reglas de negocio de la gestión de usuarios y revocación de sesiones."""
from __future__ import annotations

from django.db import transaction
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from cuentas.models import Rol, Usuario

from .errores import ErrorDeNegocio


def revocar_sesiones(usuario: Usuario) -> int:
    """Pone en lista negra todos los refresh tokens vigentes del usuario. Devuelve cuántos revocó."""
    revocados = 0
    for token in OutstandingToken.objects.filter(user=usuario):
        _, creado = BlacklistedToken.objects.get_or_create(token=token)
        revocados += int(creado)
    return revocados


def sincronizar_banderas(usuario: Usuario) -> None:
    """is_staff/is_superuser solo importan si se habilita el admin de Django: siguen al rol."""
    es_admin = usuario.rol == Rol.ADMINISTRADOR
    usuario.is_staff = es_admin
    usuario.is_superuser = es_admin


def administradores_activos_bloqueados():
    """Administradores activos con bloqueo de fila (evita que dos peticiones simultáneas dejen la app sin admin)."""
    return list(Usuario.objects.select_for_update().filter(rol=Rol.ADMINISTRADOR, is_active=True))


def validar_cambio(actor: Usuario, objetivo: Usuario, *, rol_nuevo: str | None = None, activo_nuevo: bool | None = None, eliminar: bool = False) -> None:
    """Aplica las reglas de protección. Debe llamarse dentro de ``transaction.atomic``.

    * Nadie puede desactivarse, eliminarse ni quitarse el rol administrador a sí mismo.
    * No se puede desactivar, eliminar ni degradar al último administrador activo.
    """
    pierde_activo = eliminar or activo_nuevo is False
    pierde_admin = rol_nuevo is not None and rol_nuevo != Rol.ADMINISTRADOR and objetivo.rol == Rol.ADMINISTRADOR
    if objetivo.pk == actor.pk:
        if eliminar:
            raise ErrorDeNegocio("No puede eliminar su propio usuario.", ["Pida a otro administrador que lo haga."])
        if activo_nuevo is False and objetivo.is_active:
            raise ErrorDeNegocio("No puede desactivar su propio usuario.", ["Pida a otro administrador que lo haga."])
        if pierde_admin:
            raise ErrorDeNegocio("No puede quitarse a sí mismo el rol de administrador.", ["Pida a otro administrador que lo haga."])
    if (pierde_activo or pierde_admin) and objetivo.rol == Rol.ADMINISTRADOR and objetivo.is_active:
        if len(administradores_activos_bloqueados()) <= 1:
            raise ErrorDeNegocio(
                "No se puede dejar el sistema sin administradores activos.",
                ["Es el último administrador activo: cree o active otro administrador antes de continuar."],
            )


@transaction.atomic
def aplicar_cambios(actor: Usuario, objetivo: Usuario, datos: dict) -> Usuario:
    """Edita un usuario (nombre, apellido, email, rol, activo) respetando las reglas de protección."""
    rol_nuevo = datos.get("rol")
    activo_nuevo = datos.get("is_active")
    if rol_nuevo == objetivo.rol:
        rol_nuevo = None
    if activo_nuevo == objetivo.is_active:
        activo_nuevo = None
    validar_cambio(actor, objetivo, rol_nuevo=rol_nuevo, activo_nuevo=activo_nuevo)
    for campo, valor in datos.items():
        setattr(objetivo, campo, valor)
    if rol_nuevo is not None:
        sincronizar_banderas(objetivo)
    objetivo.save()
    if activo_nuevo is False or rol_nuevo is not None:
        revocar_sesiones(objetivo)
    return objetivo


@transaction.atomic
def eliminar_usuario(actor: Usuario, objetivo: Usuario) -> None:
    validar_cambio(actor, objetivo, eliminar=True)
    objetivo.delete()
