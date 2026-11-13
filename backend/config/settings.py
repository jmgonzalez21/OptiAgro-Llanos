"""Configuración de OptiAgro-Llanos. Todo lo sensible viene de variables de entorno."""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent


def env(nombre: str, defecto: str | None = None) -> str | None:
    valor = os.environ.get(nombre)
    return valor if valor not in (None, "") else defecto


def env_bool(nombre: str, defecto: bool = False) -> bool:
    valor = env(nombre)
    return defecto if valor is None else valor.strip().lower() in ("1", "true", "t", "yes", "si", "sí")


def env_int(nombre: str, defecto: int) -> int:
    valor = env(nombre)
    return defecto if valor is None else int(valor)


def env_lista(nombre: str, defecto: str = "") -> list[str]:
    return [x.strip() for x in (env(nombre, defecto) or "").split(",") if x.strip()]


# --- Seguridad -------------------------------------------------------------------------
# DEBUG es False por defecto (producción). Se activa solo con DJANGO_DEBUG=True.
DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        # Clave efímera: en desarrollo los tokens dejan de valer al reiniciar el proceso.
        SECRET_KEY = get_random_secret_key()
    else:
        raise ImproperlyConfigured("Defina DJANGO_SECRET_KEY (vea .env.example).")

ALLOWED_HOSTS = env_lista("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend")
CSRF_TRUSTED_ORIGINS = env_lista(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000,http://localhost:8080,http://127.0.0.1:8080",
)

# El admin de Django NO forma parte de la aplicación presentada: apagado por defecto. Si es False, /admin/ no se monta (404).
ADMIN_HABILITADO = env_bool("OPTIAGRO_ADMIN_HABILITADO", False)

# --- Aplicaciones ----------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "cuentas",
    "red",
    "escenarios",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Base de datos (PostgreSQL 16) -----------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "optiagro"),
        "USER": env("POSTGRES_USER", "optiagro"),
        "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST", "db"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Usuarios --------------------------------------------------------------------------
AUTH_USER_MODEL = "cuentas.Usuario"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internacionalización --------------------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# --- Estáticos (admin) -----------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# --- CORS (el frontend Vue habla con la API desde otro origen) -------------------------
CORS_ALLOWED_ORIGINS = env_lista("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

# --- DRF / JWT / OpenAPI ---------------------------------------------------------------
REST_FRAMEWORK = {
    # Solo JWT: la API no depende de sesiones de Django (ni del admin).
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "api.paginacion.PaginacionEstandar",
    "PAGE_SIZE": 50,
    "DEFAULT_THROTTLE_RATES": {"login": env("THROTTLE_LOGIN", "30/min")},
    "EXCEPTION_HANDLER": "api.errores.manejador_excepciones",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_ACCESS_MINUTOS", 30)),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=env_int("JWT_REFRESH_MINUTOS", 60 * 24)),
    # El refresh rota en cada renovación y el anterior queda en lista negra (logout y cambios de contraseña
    # también lo revocan). Ventana deslizante: expira JWT_REFRESH_MINUTOS después de la última renovación.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "OptiAgro-Llanos API",
    "DESCRIPTION": (
        "API REST de optimización de la red logística de residuos agropecuarios "
        "(modelo de transporte exacto con HiGHS y algoritmo genético). "
        "Contrato entre backend y frontend. Unidades: toneladas por semana, costos en COP. "
        "Autenticación: JWT en la cabecera 'Authorization: Bearer <access>'. Errores 400: {\"detail\": str, \"errores\": lista|dict}."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # /api/v1/schema/ y /api/v1/docs/: abiertos solo con DJANGO_DEBUG=True; en producción exigen un JWT válido.
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny" if DEBUG else "rest_framework.permissions.IsAuthenticated"],
    "SERVE_AUTHENTICATION": ["rest_framework_simplejwt.authentication.JWTAuthentication"],
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "SORT_OPERATIONS": False,
    "TAGS": [
        {"name": "auth", "description": "Autenticación JWT, perfil propio y cambio de contraseña."},
        {"name": "usuarios", "description": "Gestión de usuarios (solo administrador)."},
        {"name": "red", "description": "Empresas, plantas, rutas y matriz de costos."},
        {"name": "optimizacion", "description": "Ejecución de solvers, sensibilidad y reporte comparativo."},
        {"name": "escenarios", "description": "Escenarios guardados."},
        {"name": "ejecuciones", "description": "Historial de ejecuciones."},
        {"name": "demo", "description": "Datos de demostración FICTICIOS."},
    ],
}

# --- Límites de tamaño de los problemas (evitan bloquear el servidor) ------------------
OPTIAGRO = {
    "MAX_EMPRESAS": env_int("OPTIAGRO_MAX_EMPRESAS", 200),
    "MAX_PLANTAS": env_int("OPTIAGRO_MAX_PLANTAS", 50),
    "MAX_RUTAS": env_int("OPTIAGRO_MAX_RUTAS", 2000),
    "AG_MAX_POBLACION": env_int("OPTIAGRO_AG_MAX_POBLACION", 300),
    "AG_MAX_GENERACIONES": env_int("OPTIAGRO_AG_MAX_GENERACIONES", 1000),
    # poblacion * generaciones * rutas * corridas; acota el tiempo del AG (~0.4 us por unidad: 20M ~ 8 s)
    "AG_MAX_TRABAJO": env_int("OPTIAGRO_AG_MAX_TRABAJO", 20_000_000),
    "SENSIBILIDAD_MAX_ESCENARIOS": env_int("OPTIAGRO_SENSIBILIDAD_MAX_ESCENARIOS", 40),
    # Prueba de escalabilidad: tamaños distintos por solicitud y trabajo total del AG (suma sobre todos los tamaños).
    "ESCALABILIDAD_MAX_TAMANOS": env_int("OPTIAGRO_ESCALABILIDAD_MAX_TAMANOS", 8),
    "ESCALABILIDAD_MAX_TRABAJO": env_int("OPTIAGRO_ESCALABILIDAD_MAX_TRABAJO", 60_000_000),
}

# --- Distancias por carretera (OSRM sobre OpenStreetMap) -------------------------------
# El servidor público es de uso razonable (sin garantías); en producción conviene alojar OSRM propio.
OPTIAGRO_OSRM = {
    "HABILITADO": env_bool("OPTIAGRO_OSRM_HABILITADO", True),
    "URL": env("OPTIAGRO_OSRM_URL", "https://router.project-osrm.org"),
    "TIMEOUT": float(env("OPTIAGRO_OSRM_TIMEOUT", "10")),
    "MAX_COORDENADAS": env_int("OPTIAGRO_OSRM_MAX_COORDENADAS", 100),  # límite de /table del servidor
    "PAUSA_LOTES": float(env("OPTIAGRO_OSRM_PAUSA_LOTES", "1")),  # segundos entre lotes
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
