from django.contrib import admin

from .models import Ejecucion, Escenario, Resultado


class ResultadoInline(admin.StackedInline):
    model = Resultado
    extra = 0
    can_delete = False
    readonly_fields = ("datos",)


@admin.register(Ejecucion)
class EjecucionAdmin(admin.ModelAdmin):
    list_display = ("id", "metodo", "estado", "objetivo", "duracion_ms", "usuario", "escenario", "creada_en")
    list_filter = ("metodo", "estado", "creada_en", "usuario")
    search_fields = ("id", "usuario__username", "escenario__nombre", "estado")
    date_hierarchy = "creada_en"
    list_select_related = ("usuario", "escenario")
    readonly_fields = ("escenario", "usuario", "metodo", "estado", "objetivo", "duracion_ms", "configuracion", "parametros", "creada_en")
    inlines = [ResultadoInline]

    def has_add_permission(self, request):
        return False


@admin.register(Escenario)
class EscenarioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "creado_por", "creado_en")
    list_filter = ("creado_en", "creado_por")
    search_fields = ("nombre", "descripcion", "creado_por__username")
    readonly_fields = ("parametros", "creado_en")
