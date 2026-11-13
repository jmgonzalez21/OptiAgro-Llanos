from django.contrib import admin

from .models import Empresa, Planta, Ruta


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "municipio", "oferta", "precio_tonelada", "latitud", "longitud", "activa", "ficticio")
    fieldsets = (
        (None, {"fields": ("codigo", "nombre", "municipio", "oferta", "precio_tonelada", "activa", "ficticio")}),
        ("Ubicación (mapa)", {"fields": ("latitud", "longitud")}),
    )
    list_filter = ("activa", "ficticio", "municipio")
    search_fields = ("codigo", "nombre", "municipio")
    list_editable = ("activa",)
    ordering = ("codigo",)


@admin.register(Planta)
class PlantaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "municipio", "capacidad", "tipo_demanda", "costo_operacion_ton", "latitud", "longitud", "activa", "ficticio")
    fieldsets = (
        (None, {"fields": ("codigo", "nombre", "municipio", "capacidad", "tipo_demanda", "costo_operacion_ton", "activa", "ficticio")}),
        ("Ubicación (mapa)", {"fields": ("latitud", "longitud")}),
    )
    list_filter = ("tipo_demanda", "activa", "ficticio", "municipio")
    search_fields = ("codigo", "nombre", "municipio")
    list_editable = ("activa",)
    ordering = ("codigo",)


@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "empresa", "planta", "distancia_km", "tarifa_km_ton", "costo_unitario", "limite", "activa", "ficticio")
    list_filter = ("activa", "ficticio", "planta", "empresa")
    search_fields = ("empresa__codigo", "empresa__nombre", "planta__codigo", "planta__nombre")
    list_select_related = ("empresa", "planta")
    autocomplete_fields = ("empresa", "planta")
    readonly_fields = ()
    ordering = ("empresa__codigo", "planta__codigo")
