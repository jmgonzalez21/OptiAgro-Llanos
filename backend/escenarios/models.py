from django.conf import settings
from django.db import models


class Escenario(models.Model):
    """Instantánea (JSON) de los parámetros de la red en un momento dado."""

    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    parametros = models.JSONField(help_text="Serialización de ParametrosModelo.")
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="escenarios"
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado_en"]
        verbose_name = "escenario"
        verbose_name_plural = "escenarios"

    def __str__(self) -> str:
        return self.nombre


class Ejecucion(models.Model):
    class Metodo(models.TextChoices):
        EXACTO = "exacto", "Método exacto (HiGHS)"
        GENETICO = "genetico", "Algoritmo genético"
        SENSIBILIDAD = "sensibilidad", "Análisis de sensibilidad"
        REPORTE = "reporte", "Reporte comparativo"
        ESCALABILIDAD = "escalabilidad", "Prueba de escalabilidad"

    escenario = models.ForeignKey(Escenario, null=True, blank=True, on_delete=models.SET_NULL, related_name="ejecuciones")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="ejecuciones"
    )
    metodo = models.CharField(max_length=20, choices=Metodo.choices)
    estado = models.CharField(max_length=30, help_text="OPTIMAL, FEASIBLE, INFEASIBLE, COMPLETADA, ...")
    objetivo = models.FloatField(null=True, blank=True, help_text="Costo total (COP/semana), si aplica.")
    duracion_ms = models.FloatField(default=0)
    configuracion = models.JSONField(default=dict, blank=True)
    parametros = models.JSONField(default=dict, blank=True, help_text="Parámetros del modelo usados (reproducibilidad).")
    incluye_ficticios = models.BooleanField(
        default=False, help_text="La red usada incluía empresas o plantas marcadas como FICTICIAS (datos de demostración)."
    )
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada_en", "-id"]
        verbose_name = "ejecución"
        verbose_name_plural = "ejecuciones"

    def __str__(self) -> str:
        return f"#{self.pk} {self.metodo} {self.estado}"


class Resultado(models.Model):
    ejecucion = models.OneToOneField(Ejecucion, on_delete=models.CASCADE, related_name="resultado")
    datos = models.JSONField(help_text="Resultado completo: asignaciones, duales, verificación, métricas...")

    class Meta:
        verbose_name = "resultado"
        verbose_name_plural = "resultados"

    def __str__(self) -> str:
        return f"Resultado de la ejecución #{self.ejecucion_id}"
