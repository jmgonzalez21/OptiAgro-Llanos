"""Red logística: empresas (oferta) -> rutas -> plantas (capacidad/demanda). Unidades: t/semana, COP."""
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

validar_codigo = RegexValidator(
    r"^[A-Za-z0-9_]+$", "Use solo letras, números y guion bajo (sin espacios ni guiones)."
)
NO_NEGATIVO = [MinValueValidator(0)]


def campo_latitud():
    return models.DecimalField(
        "latitud (grados)", max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )  # fmt: skip


def campo_longitud():
    return models.DecimalField(
        "longitud (grados)", max_digits=9, decimal_places=6, null=True, blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )  # fmt: skip


class TipoDemanda(models.TextChoices):
    CAPACIDAD_MAXIMA = "capacity_max", "Capacidad máxima (<=)"
    EXACTA = "exact", "Demanda exacta (=)"
    MINIMA = "minimum", "Demanda mínima (>=)"


class Empresa(models.Model):
    """Agroempresa generadora de residuos (nodo de oferta)."""

    codigo = models.CharField(max_length=20, unique=True, validators=[validar_codigo])
    nombre = models.CharField(max_length=120)
    municipio = models.CharField(max_length=80, blank=True)
    oferta = models.FloatField("oferta (t/semana)", validators=NO_NEGATIVO)
    precio_tonelada = models.FloatField(
        "precio de la tonelada (COP/t)", default=0, validators=NO_NEGATIVO,
        help_text="Se suma al costo efectivo de toda ruta que sale de esta empresa (0 = se retira sin costo).",
    )  # fmt: skip
    latitud = campo_latitud()
    longitud = campo_longitud()
    activa = models.BooleanField(default=True)
    ficticio = models.BooleanField(
        default=False, help_text="Dato de demostración FICTICIO (no corresponde a una empresa real)."
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["codigo"]
        verbose_name = "empresa"
        verbose_name_plural = "empresas"
        constraints = [
            models.CheckConstraint(condition=models.Q(oferta__gte=0), name="empresa_oferta_no_negativa"),
            models.CheckConstraint(condition=models.Q(precio_tonelada__gte=0), name="empresa_precio_no_negativo"),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} · {self.nombre}"


class Planta(models.Model):
    """Planta de procesamiento (nodo de demanda/capacidad)."""

    codigo = models.CharField(max_length=20, unique=True, validators=[validar_codigo])
    nombre = models.CharField(max_length=120)
    municipio = models.CharField(max_length=80, blank=True)
    capacidad = models.FloatField("capacidad / demanda (t/semana)", validators=NO_NEGATIVO)
    tipo_demanda = models.CharField(max_length=20, choices=TipoDemanda.choices, default=TipoDemanda.CAPACIDAD_MAXIMA)
    costo_operacion_ton = models.FloatField(
        "costo de operación (COP/t)", default=0, validators=NO_NEGATIVO,
        help_text="Se suma al costo efectivo de toda ruta que llega a esta planta (procesamiento/operación).",
    )  # fmt: skip
    latitud = campo_latitud()
    longitud = campo_longitud()
    activa = models.BooleanField(default=True)
    ficticio = models.BooleanField(
        default=False, help_text="Dato de demostración FICTICIO (no corresponde a una planta real)."
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["codigo"]
        verbose_name = "planta"
        verbose_name_plural = "plantas"
        constraints = [
            models.CheckConstraint(condition=models.Q(capacidad__gte=0), name="planta_capacidad_no_negativa"),
            models.CheckConstraint(condition=models.Q(costo_operacion_ton__gte=0), name="planta_operacion_no_negativa"),
        ]

    def __str__(self) -> str:
        return f"{self.codigo} · {self.nombre}"


class FuenteDistancia(models.TextChoices):
    CARRETERA = "carretera", "Por carretera (OSRM/OpenStreetMap)"
    ESTIMADA = "estimada", "Estimada (línea recta x 1,3)"
    MANUAL = "manual", "Ingresada manualmente"


class Ruta(models.Model):
    """Arco dirigido empresa -> planta.

    Costo de TRANSPORTE (COP/t): si hay ``distancia_km`` y ``tarifa_km_ton`` es su producto
    (el campo ``costo_unitario`` se sincroniza al guardar); si no, es ``costo_unitario``.
    El costo que minimiza el optimizador suma además ``costo_operacion_ton`` de la planta y
    ``precio_tonelada`` de la empresa (ver ``dominio.modelos``).
    """

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="rutas")
    planta = models.ForeignKey(Planta, on_delete=models.CASCADE, related_name="rutas")
    distancia_km = models.FloatField(null=True, blank=True, validators=NO_NEGATIVO)
    distancia_fuente = models.CharField(max_length=10, choices=FuenteDistancia.choices, default=FuenteDistancia.MANUAL)
    trayecto = models.JSONField(
        null=True, blank=True, help_text="GeoJSON LineString del trayecto por carretera (caché; [lon, lat])."
    )
    tarifa_km_ton = models.FloatField("tarifa (COP por t·km)", null=True, blank=True, validators=NO_NEGATIVO)
    costo_unitario = models.FloatField("costo unitario (COP/t)", null=True, blank=True, validators=NO_NEGATIVO)
    limite = models.FloatField("límite de flujo (t/semana)", null=True, blank=True, validators=NO_NEGATIVO)
    activa = models.BooleanField(default=True)
    ficticio = models.BooleanField(default=False, help_text="Dato de demostración FICTICIO.")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["empresa__codigo", "planta__codigo"]
        verbose_name = "ruta"
        verbose_name_plural = "rutas"
        constraints = [
            models.UniqueConstraint(fields=["empresa", "planta"], name="ruta_unica_por_par"),
            models.CheckConstraint(
                condition=models.Q(costo_unitario__isnull=False)
                | (models.Q(distancia_km__isnull=False) & models.Q(tarifa_km_ton__isnull=False)),
                name="ruta_con_costo_definido",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.empresa.codigo}->{self.planta.codigo}"

    @property
    def costo_efectivo(self) -> float | None:
        if self.distancia_km is not None and self.tarifa_km_ton is not None:
            return self.distancia_km * self.tarifa_km_ton
        return self.costo_unitario

    def clean(self):
        if self.costo_efectivo is None:
            raise ValidationError("Indique costo_unitario o bien distancia_km y tarifa_km_ton.")

    def save(self, *args, **kwargs):
        if self.distancia_km is not None and self.tarifa_km_ton is not None:
            self.costo_unitario = self.distancia_km * self.tarifa_km_ton
            campos = kwargs.get("update_fields")
            if campos is not None:
                kwargs["update_fields"] = set(campos) | {"costo_unitario"}
        super().save(*args, **kwargs)
