from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [path("api/v1/", include("api.urls"))]

# El admin de Django está apagado por defecto (OPTIAGRO_ADMIN_HABILITADO=false): sin ruta, /admin/ responde 404.
if settings.ADMIN_HABILITADO:
    admin.site.site_header = "OptiAgro-Llanos · Administración"
    admin.site.site_title = "OptiAgro-Llanos"
    admin.site.index_title = "Red logística de residuos agropecuarios"
    urlpatterns.insert(0, path("admin/", admin.site.urls))
