from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class Rol(models.TextChoices):
    ADMINISTRADOR = "administrador", "Administrador"
    ANALISTA = "analista", "Analista"


class UsuarioManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("rol", Rol.ADMINISTRADOR)
        return super().create_superuser(username, email, password, **extra_fields)


class Usuario(AbstractUser):
    """Usuario con rol: administrador (CRUD de la red) o analista (ejecuta escenarios)."""

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.ANALISTA)

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    @property
    def es_administrador(self) -> bool:
        # Solo el rol decide los permisos de la API (is_superuser/is_staff solo afectan al admin de Django, apagado
        # por defecto; la API los mantiene sincronizados con el rol).
        return self.rol == Rol.ADMINISTRADOR

    def __str__(self) -> str:
        return f"{self.username} ({self.rol})"
