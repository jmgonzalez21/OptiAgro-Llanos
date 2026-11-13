from __future__ import annotations

import math

from django.conf import settings
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from cuentas.models import Rol, Usuario
from escenarios.models import Ejecucion, Escenario
from optimizacion.algoritmo_genetico import CRUCES, INICIALIZACIONES, SELECCIONES, ConfigAG
from red.models import Empresa, Planta, Ruta
from servicios import rutas_viales as svc_viales
from servicios.ejecucion import TIPOS_VARIACION

LIMITES = settings.OPTIAGRO


class ErrorSerializer(serializers.Serializer):
    """Respuesta 400: ``errores`` es una lista de mensajes o un dict campo -> mensajes."""

    detail = serializers.CharField()
    errores = serializers.JSONField()


# ---------------------------------------------------------------------------------------
# Cuentas
# ---------------------------------------------------------------------------------------
class UsuarioSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "username", "nombre_completo", "first_name", "last_name", "email", "rol"]
        read_only_fields = fields


class UsuarioGestionSerializer(serializers.ModelSerializer):
    """Usuario tal como lo ve el administrador. Nunca incluye contraseña ni hash."""

    nombre_completo = serializers.CharField(source="get_full_name", read_only=True)
    activo = serializers.BooleanField(source="is_active", read_only=True)
    ultimo_acceso = serializers.DateTimeField(source="last_login", read_only=True)
    fecha_creacion = serializers.DateTimeField(source="date_joined", read_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id", "username", "first_name", "last_name", "nombre_completo", "email", "rol", "activo",
            "ultimo_acceso", "fecha_creacion",
        ]  # fmt: skip
        read_only_fields = fields


def validar_contrasena(valor: str, usuario: Usuario | None = None) -> str:
    """Validadores de Django (mínimo 10 caracteres, no común, no solo numérica, no parecida a los datos)."""
    try:
        password_validation.validate_password(valor, user=usuario)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc
    return valor


class UsuarioCrearSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"}, trim_whitespace=False)
    rol = serializers.ChoiceField(choices=Rol.choices, default=Rol.ANALISTA)
    activo = serializers.BooleanField(source="is_active", default=True)
    email = serializers.EmailField(required=False, allow_blank=True, default="")

    class Meta:
        model = Usuario
        fields = ["username", "password", "first_name", "last_name", "email", "rol", "activo"]

    def validate(self, attrs):
        usuario = Usuario(
            username=attrs.get("username", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
            email=attrs.get("email", ""),
        )
        try:
            validar_contrasena(attrs["password"], usuario)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({"password": exc.detail}) from exc
        return attrs

    def create(self, validated_data):
        from servicios.usuarios import sincronizar_banderas

        clave = validated_data.pop("password")
        usuario = Usuario(**validated_data)
        sincronizar_banderas(usuario)
        usuario.set_password(clave)
        usuario.save()
        return usuario


class UsuarioActualizarSerializer(serializers.ModelSerializer):
    """PATCH: nombre, apellido, email, rol y activo. El username no se edita."""

    activo = serializers.BooleanField(source="is_active", required=False)
    rol = serializers.ChoiceField(choices=Rol.choices, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "email", "rol", "activo"]


class RestablecerContrasenaSerializer(serializers.Serializer):
    nueva_contrasena = serializers.CharField(
        required=False,
        write_only=True,
        trim_whitespace=False,
        help_text="Si se omite, el servidor genera una contraseña temporal y la devuelve UNA sola vez.",
    )


class RestablecerContrasenaRespuestaSerializer(serializers.Serializer):
    detail = serializers.CharField()
    contrasena_temporal = serializers.CharField(allow_null=True, help_text="Solo si el servidor la generó.")


class PerfilActualizarSerializer(serializers.ModelSerializer):
    """PATCH /auth/me/: el usuario edita sus propios datos (no el rol)."""

    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "email"]


class CambiarContrasenaSerializer(serializers.Serializer):
    contrasena_actual = serializers.CharField(write_only=True, trim_whitespace=False)
    contrasena_nueva = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_contrasena_actual(self, valor):
        if not self.context["request"].user.check_password(valor):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return valor

    def validate(self, attrs):
        usuario = self.context["request"].user
        if attrs["contrasena_nueva"] == attrs["contrasena_actual"]:
            raise serializers.ValidationError({"contrasena_nueva": "Debe ser distinta de la actual."})
        try:
            validar_contrasena(attrs["contrasena_nueva"], usuario)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError({"contrasena_nueva": exc.detail}) from exc
        return attrs


class CambiarContrasenaRespuestaSerializer(serializers.Serializer):
    detail = serializers.CharField()
    access = serializers.CharField()
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class RefreshRespuestaSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField(help_text="El refresh rota en cada renovación: guarde el nuevo y descarte el anterior.")


class LoginSerializer(TokenObtainPairSerializer):
    """Devuelve access, refresh y los datos del usuario (incluido el rol)."""

    def validate(self, attrs):
        datos = super().validate(attrs)
        datos["usuario"] = UsuarioSerializer(self.user).data
        return datos


class LoginRespuestaSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    usuario = UsuarioSerializer()


# ---------------------------------------------------------------------------------------
# Red
# ---------------------------------------------------------------------------------------
class ValidaFinitos:
    """Rechaza NaN e infinitos (MinValueValidator(0) deja pasar NaN)."""

    def validate(self, attrs):
        for campo, valor in attrs.items():
            if isinstance(valor, float) and not math.isfinite(valor):
                raise serializers.ValidationError({campo: "Debe ser un número finito."})
        return super().validate(attrs)


class CoordenadasMixin(serializers.Serializer):
    """latitud/longitud como números JSON (no cadenas) para el mapa del frontend."""

    latitud = serializers.DecimalField(
        max_digits=9, decimal_places=6, min_value=-90, max_value=90, required=False, allow_null=True, coerce_to_string=False
    )
    longitud = serializers.DecimalField(
        max_digits=9, decimal_places=6, min_value=-180, max_value=180, required=False, allow_null=True, coerce_to_string=False
    )


class CodigoInmutable:
    """El ``codigo`` (identificador del modelo de optimización) no se edita tras crearlo."""

    def validate_codigo(self, valor):
        if self.instance is not None and valor != self.instance.codigo:
            raise serializers.ValidationError("El código no se puede modificar una vez creado.")
        return valor


class EmpresaSerializer(CodigoInmutable, ValidaFinitos, CoordenadasMixin, serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = [
            "id", "codigo", "nombre", "municipio", "oferta", "precio_tonelada", "latitud", "longitud",
            "activa", "ficticio", "creado_en", "actualizado_en",
        ]  # fmt: skip
        read_only_fields = ["id", "creado_en", "actualizado_en"]


class PlantaSerializer(CodigoInmutable, ValidaFinitos, CoordenadasMixin, serializers.ModelSerializer):
    class Meta:
        model = Planta
        fields = [
            "id", "codigo", "nombre", "municipio", "capacidad", "tipo_demanda", "costo_operacion_ton", "latitud", "longitud",
            "activa", "ficticio", "creado_en", "actualizado_en",
        ]  # fmt: skip
        read_only_fields = ["id", "creado_en", "actualizado_en"]


CAMPOS_COSTO = ("costo_unitario", "distancia_km", "tarifa_km_ton")


def costo_resultante(actual: dict, cambios: dict) -> float | None:
    """Costo efectivo tras aplicar ``cambios`` sobre ``actual`` (distancia x tarifa si ambas existen)."""
    datos = {**actual, **cambios}
    if datos.get("distancia_km") is not None and datos.get("tarifa_km_ton") is not None:
        return datos["distancia_km"] * datos["tarifa_km_ton"]
    return datos.get("costo_unitario")


def normalizar_cambios_costo(cambios: dict) -> dict:
    """Un ``costo_unitario`` directo, sin distancia ni tarifa, anula la distancia/tarifa previas."""
    cambios = dict(cambios)
    if cambios.get("costo_unitario") is not None and "distancia_km" not in cambios and "tarifa_km_ton" not in cambios:
        cambios["distancia_km"] = None
        cambios["tarifa_km_ton"] = None
    return cambios


class RutaSerializer(ValidaFinitos, serializers.ModelSerializer):
    """``empresa`` y ``planta`` se expresan con su ``codigo``.

    Si se indican ``distancia_km`` y ``tarifa_km_ton``, ``costo_unitario`` = distancia x tarifa
    (el valor enviado se ignora). Un ``costo_unitario`` solo, anula distancia y tarifa.
    """

    empresa = serializers.SlugRelatedField(slug_field="codigo", queryset=Empresa.objects.all())
    planta = serializers.SlugRelatedField(slug_field="codigo", queryset=Planta.objects.all())
    empresa_nombre = serializers.CharField(source="empresa.nombre", read_only=True)
    planta_nombre = serializers.CharField(source="planta.nombre", read_only=True)
    costo_unitario = serializers.FloatField(required=False, allow_null=True, min_value=0)
    tiene_trayecto = serializers.SerializerMethodField(help_text="True si el trayecto por carretera ya está en caché.")
    aviso = serializers.SerializerMethodField(
        help_text="Solo al crear: advertencia si la distancia tuvo que estimarse (OSRM no disponible)."
    )

    class Meta:
        model = Ruta
        fields = [
            "id", "empresa", "empresa_nombre", "planta", "planta_nombre", "distancia_km", "distancia_fuente",
            "tarifa_km_ton", "costo_unitario", "limite", "activa", "ficticio", "tiene_trayecto", "aviso",
            "creado_en", "actualizado_en",
        ]  # fmt: skip
        read_only_fields = ["id", "distancia_fuente", "creado_en", "actualizado_en"]

    def get_tiene_trayecto(self, obj) -> bool:
        return bool(obj.trayecto)

    def get_aviso(self, obj) -> str | None:
        return getattr(obj, "_aviso", None)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        cambios = normalizar_cambios_costo({k: v for k, v in attrs.items() if k in CAMPOS_COSTO})
        attrs.update(cambios)
        actual = {k: getattr(self.instance, k) for k in CAMPOS_COSTO} if self.instance else {}
        # Alta sin distancia ni costo directo: se calcula por carretera (con respaldo estimado).
        if self.instance is None and cambios.get("distancia_km") is None and cambios.get("costo_unitario") is None:
            if cambios.get("tarifa_km_ton") is not None:
                a, b = svc_viales.punto(attrs["empresa"]), svc_viales.punto(attrs["planta"])
                if a is not None and b is not None:
                    km, fuente, aviso = svc_viales.distancia_con_respaldo(a, b)
                    attrs.update(distancia_km=km, distancia_fuente=fuente, _aviso=aviso)
                    cambios["distancia_km"] = km
        elif cambios.get("distancia_km") is not None or "distancia_km" in cambios:
            attrs["distancia_fuente"] = "manual"  # el usuario fijó (o anuló) la distancia
        if costo_resultante(actual, cambios) is None:
            raise serializers.ValidationError(
                {"costo_unitario": "Indique costo_unitario o bien distancia_km y tarifa_km_ton "
                 "(sin distancia_km, ambas empresa y planta deben tener coordenadas para calcularla)."}
            )
        return attrs

    def create(self, validated_data):
        aviso = validated_data.pop("_aviso", None)
        ruta = super().create(validated_data)
        ruta._aviso = aviso
        return ruta


class RecalcularDistanciasSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=False, max_length=LIMITES["MAX_RUTAS"],
        help_text="IDs de rutas a recalcular. Si se omite, todas las rutas con fuente carretera/estimada.",
    )
    solo_estimadas = serializers.BooleanField(
        required=False, default=False, help_text="Solo rutas con distancia_fuente=estimada (reintento tras un fallo de OSRM)."
    )
    incluir_manuales = serializers.BooleanField(
        required=False, default=False,
        help_text="Si es true, también sobrescribe rutas con distancia manual (use con cuidado; requiere ids o aplica a todas).",
    )


class RecalcularDistanciasRespuestaSerializer(serializers.Serializer):
    actualizadas = serializers.IntegerField()
    estimadas = serializers.IntegerField(help_text="De las actualizadas, cuántas quedaron como estimada (sin OSRM).")
    errores = serializers.IntegerField(help_text="Rutas omitidas (p. ej. sin coordenadas).")
    detalle_errores = serializers.ListField(child=serializers.CharField())
    aviso = serializers.CharField(allow_null=True)


class TrayectoRespuestaSerializer(serializers.Serializer):
    ruta_id = serializers.IntegerField()
    distancia_km = serializers.FloatField(allow_null=True)
    distancia_fuente = serializers.CharField()
    fuente = serializers.CharField(help_text="carretera = geometría de OSRM; estimada = línea recta de respaldo (no se cachea).")
    cacheado = serializers.BooleanField()
    trayecto = serializers.JSONField(help_text="GeoJSON LineString; coordinates = [[lon, lat], ...].")
    aviso = serializers.CharField(allow_null=True)


class TrayectosRespuestaSerializer(serializers.Serializer):
    trayectos = TrayectoRespuestaSerializer(many=True)


class CeldaMatrizSerializer(serializers.Serializer):
    empresa = serializers.CharField(help_text="Código de la empresa.")
    planta = serializers.CharField(help_text="Código de la planta.")
    costo_unitario = serializers.FloatField(required=False, allow_null=True, min_value=0)
    distancia_km = serializers.FloatField(required=False, allow_null=True, min_value=0)
    tarifa_km_ton = serializers.FloatField(required=False, allow_null=True, min_value=0)
    limite = serializers.FloatField(required=False, allow_null=True, min_value=0)
    activa = serializers.BooleanField(required=False)

    def validate(self, attrs):
        for campo, valor in attrs.items():
            if isinstance(valor, float) and not math.isfinite(valor):
                raise serializers.ValidationError({campo: "Debe ser un número finito."})
        return attrs


class MatrizCostosEscrituraSerializer(serializers.Serializer):
    rutas = CeldaMatrizSerializer(many=True, allow_empty=False, max_length=LIMITES["MAX_RUTAS"])


class CeldaMatrizLecturaSerializer(serializers.Serializer):
    empresa = serializers.CharField()
    planta = serializers.CharField()
    costo_unitario = serializers.FloatField(allow_null=True)
    distancia_km = serializers.FloatField(allow_null=True)
    tarifa_km_ton = serializers.FloatField(allow_null=True)
    limite = serializers.FloatField(allow_null=True)
    activa = serializers.BooleanField()


class NodoMatrizSerializer(serializers.Serializer):
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    activa = serializers.BooleanField()
    precio_tonelada = serializers.FloatField(required=False, help_text="Solo empresas (COP/t).")
    costo_operacion_ton = serializers.FloatField(required=False, help_text="Solo plantas (COP/t).")


class MatrizCostosSerializer(serializers.Serializer):
    empresas = NodoMatrizSerializer(many=True)
    plantas = NodoMatrizSerializer(many=True)
    costos = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField(allow_null=True)),
        help_text="costos[i][j] = costo de TRANSPORTE de empresas[i] a plantas[j] (COP/t); null si no hay ruta.",
    )
    costos_totales = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField(allow_null=True)),
        help_text=(
            "costos_totales[i][j] = costo efectivo que minimiza el optimizador: transporte + costo_operacion_ton de la "
            "planta j + precio_tonelada de la empresa i; null si no hay ruta."
        ),
    )
    rutas = CeldaMatrizLecturaSerializer(many=True)


# ---------------------------------------------------------------------------------------
# Solicitudes de optimización
# ---------------------------------------------------------------------------------------
_D = ConfigAG()


class ConfigAGSerializer(serializers.Serializer):
    poblacion = serializers.IntegerField(min_value=2, max_value=LIMITES["AG_MAX_POBLACION"], default=_D.poblacion)
    generaciones = serializers.IntegerField(min_value=1, max_value=LIMITES["AG_MAX_GENERACIONES"], default=_D.generaciones)
    cruce = serializers.FloatField(min_value=0, max_value=1, default=_D.cruce, help_text="Probabilidad de cruce por pareja.")
    mutacion = serializers.FloatField(min_value=0, max_value=1, default=_D.mutacion, help_text="Probabilidad de mutación por gen.")
    semilla = serializers.IntegerField(min_value=0, max_value=2**31 - 1, default=_D.semilla)
    elitismo = serializers.IntegerField(min_value=0, default=_D.elitismo, help_text="Individuos que pasan intactos; < población.")
    seleccion = serializers.ChoiceField(
        choices=list(SELECCIONES),
        default=_D.seleccion,
        help_text="torneo: gana el mejor de tamano_torneo individuos; ruleta: proporcional a la aptitud (con escalamiento).",
    )
    tipo_cruce = serializers.ChoiceField(choices=list(CRUCES), default=_D.tipo_cruce, help_text="Cruce de uno o de dos puntos.")
    tamano_torneo = serializers.IntegerField(min_value=2, default=_D.tamano_torneo, help_text="Solo con seleccion=torneo; <= población.")
    inicializacion = serializers.ChoiceField(
        choices=list(INICIALIZACIONES),
        default=_D.inicializacion,
        help_text="aleatoria (línea base) o heuristica (parte de la población sesgada hacia rutas baratas).",
    )

    def validate(self, attrs):
        errores = ConfigAG.desde_dict(attrs).errores()
        if errores:
            raise serializers.ValidationError(errores)
        return attrs


class BaseEjecucionSerializer(serializers.Serializer):
    escenario_id = serializers.IntegerField(
        required=False, help_text="Usa la instantánea de un escenario guardado en vez de la red actual."
    )
    guardar = serializers.BooleanField(default=True, help_text="Registrar la ejecución en el historial.")


class EjecutarExactoSerializer(BaseEjecucionSerializer):
    modo_oferta = serializers.ChoiceField(
        choices=["exact", "maximum"], default="exact", help_text="exact: toda la oferta se retira (=); maximum: (<=)."
    )


class EjecutarGeneticoSerializer(BaseEjecucionSerializer, ConfigAGSerializer):
    pass


class VariacionSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(
        choices=list(TIPOS_VARIACION),
        help_text=(
            "oferta | capacidad (cuello de botella si es negativa; varias plantas a la vez) | costo (transporte de "
            "rutas) | combustible (% sobre la tarifa km-ton de las rutas)."
        ),
    )
    ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text=(
            "Códigos afectados: empresas (oferta), plantas (capacidad) o rutas 'E1->P2' (costo, combustible). "
            "Vacío = todos. Para 'varias plantas' liste sus códigos."
        ),
    )
    porcentajes = serializers.ListField(
        child=serializers.FloatField(min_value=-100, max_value=1000),
        min_length=1,
        max_length=LIMITES["SENSIBILIDAD_MAX_ESCENARIOS"],
        help_text="Variaciones porcentuales; cada una genera un escenario reoptimizado.",
    )

    def validate_porcentajes(self, valor):
        if any(not math.isfinite(x) for x in valor):
            raise serializers.ValidationError("Todos los porcentajes deben ser finitos.")
        return valor


class SensibilidadSolicitudSerializer(BaseEjecucionSerializer):
    variaciones = VariacionSerializer(many=True, allow_empty=False)
    incluir_ag = serializers.BooleanField(
        default=True, help_text="Resuelve cada escenario también con el AG (gap % y tiempos). false = solo exacto."
    )
    config_ag = ConfigAGSerializer(required=False)


class ReporteSolicitudSerializer(BaseEjecucionSerializer):
    config_ag = ConfigAGSerializer(required=False)
    variaciones = VariacionSerializer(many=True, required=False, help_text="Si se indica, añade la sección de sensibilidad.")


# ---------------------------------------------------------------------------------------
# Respuestas de optimización (documentación del contrato)
# ---------------------------------------------------------------------------------------
class AsignacionSerializer(serializers.Serializer):
    empresa_id = serializers.CharField()
    planta_id = serializers.CharField()
    cantidad = serializers.FloatField()
    costo_unitario = serializers.FloatField(help_text="Costo efectivo COP/t = transporte + operación + precio.")
    costo_transporte = serializers.FloatField(required=False, help_text="distancia x tarifa, o costo unitario directo.")
    costo_operacion = serializers.FloatField(required=False, help_text="costo_operacion_ton de la planta.")
    precio_tonelada = serializers.FloatField(required=False, help_text="precio_tonelada de la empresa.")


class ResultadoOptimizacionSerializer(serializers.Serializer):
    metodo = serializers.CharField()
    estado = serializers.CharField(help_text="OPTIMAL | FEASIBLE | INFEASIBLE | UNBOUNDED | ...")
    factible = serializers.BooleanField()
    objetivo = serializers.FloatField(allow_null=True, help_text="Costo total COP/semana.")
    asignaciones = AsignacionSerializer(many=True)
    duracion_ms = serializers.FloatField()
    mensajes = serializers.ListField(child=serializers.CharField())
    duales = serializers.DictField(
        child=serializers.FloatField(), help_text="Precios sombra del LP: 'oferta:E1', 'planta:P1' (solo método exacto)."
    )
    verificacion = serializers.DictField(help_text="valida, errores[], violacion_maxima.")
    metricas = serializers.DictField(
        help_text=(
            "Exacto: solver, desglose_costos{transporte, operacion, precio, total}. "
            "AG: parámetros usados, convergencia[] (mejor costo penalizado por generación), convergencia_promedio[], "
            "aptitud_mejor[], aptitud_promedio[], factibles[] (individuos factibles por generación), penalizacion "
            "(lambda), mejor_aptitud, evaluaciones, desglose_costos."
        )
    )


class EjecucionResultadoSerializer(serializers.Serializer):
    ejecucion_id = serializers.IntegerField(allow_null=True, help_text="null si guardar=false.")
    resultado = ResultadoOptimizacionSerializer()


class ResumenSolucionSerializer(serializers.Serializer):
    estado = serializers.CharField()
    factible = serializers.BooleanField()
    objetivo = serializers.FloatField(allow_null=True)
    duracion_ms = serializers.FloatField()
    mensajes = serializers.ListField(child=serializers.CharField())
    duales = serializers.DictField(child=serializers.FloatField(), required=False)


class AnalisisPlantaSerializer(serializers.Serializer):
    planta = serializers.CharField()
    nombre = serializers.CharField()
    tipo_demanda = serializers.CharField()
    capacidad = serializers.FloatField()
    flujo = serializers.FloatField()
    utilizacion_pct = serializers.FloatField(allow_null=True)
    precio_sombra = serializers.FloatField(allow_null=True)
    cuello_de_botella = serializers.BooleanField()


class CambioAsignacionSerializer(serializers.Serializer):
    empresa = serializers.CharField()
    planta = serializers.CharField()
    base = serializers.FloatField(help_text="Toneladas en el caso base (exacto).")
    escenario = serializers.FloatField(help_text="Toneladas en el escenario (exacto).")
    delta = serializers.FloatField()


class EscenarioSensibilidadSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    tipo = serializers.CharField()
    ids = serializers.ListField(child=serializers.CharField())
    porcentaje = serializers.FloatField()
    exacto = ResumenSolucionSerializer()
    variacion_objetivo = serializers.FloatField(allow_null=True, help_text="Costo escenario - costo base (COP).")
    variacion_objetivo_pct = serializers.FloatField(allow_null=True)
    genetico = ResumenSolucionSerializer(allow_null=True)
    gap_pct = serializers.FloatField(allow_null=True, help_text="(AG - exacto) / exacto x 100 en este escenario.")
    base_cambio = serializers.BooleanField(
        allow_null=True,
        help_text="La base óptima del LP cambió frente al caso base. null si el escenario es inviable.",
    )
    dentro_de_rango = serializers.BooleanField(
        allow_null=True,
        help_text="Solo con un único id: el nuevo valor cae dentro del rango (ranging) que conserva la base óptima.",
    )
    asignaciones_cambiadas = serializers.IntegerField(help_text="Rutas cuyo flujo exacto cambia frente al caso base.")
    cambios_asignacion = CambioAsignacionSerializer(many=True)
    costo_exacto = serializers.FloatField(allow_null=True)
    costo_ag = serializers.FloatField(allow_null=True)
    tiempo_exacto_ms = serializers.FloatField()
    tiempo_ag_ms = serializers.FloatField(allow_null=True)
    estado_exacto = serializers.CharField()
    estado_ag = serializers.CharField(allow_null=True)


class BaseSensibilidadSerializer(serializers.Serializer):
    exacto = ResumenSolucionSerializer()
    genetico = ResumenSolucionSerializer(allow_null=True)
    gap_pct = serializers.FloatField(allow_null=True)


class PreciosSombraSerializer(serializers.Serializer):
    empresas = serializers.DictField(child=serializers.FloatField())
    plantas = serializers.DictField(child=serializers.FloatField())


class RangoRhsSerializer(serializers.Serializer):
    id = serializers.CharField(help_text="Código de la empresa (oferta) o de la planta (capacidad).")
    valor_actual = serializers.FloatField()
    precio_sombra = serializers.FloatField()
    activa = serializers.BooleanField(help_text="La restricción está activa (saturada) en el óptimo.")
    minimo = serializers.FloatField(allow_null=True, help_text="Límite inferior que conserva la base óptima; null = sin límite.")
    maximo = serializers.FloatField(allow_null=True, help_text="Límite superior que conserva la base óptima; null = sin límite.")
    objetivo_en_minimo = serializers.FloatField(allow_null=True)
    objetivo_en_maximo = serializers.FloatField(allow_null=True)


class RangoCostoSerializer(serializers.Serializer):
    ruta = serializers.CharField(help_text="'E1->P2'.")
    costo_actual = serializers.FloatField(help_text="Costo efectivo COP/t (transporte + operación + precio).")
    flujo = serializers.FloatField()
    en_base = serializers.BooleanField(help_text="La variable de la ruta es básica en el óptimo.")
    costo_reducido = serializers.FloatField()
    minimo = serializers.FloatField(allow_null=True, help_text="Costo mínimo que conserva la base óptima; null = sin límite.")
    maximo = serializers.FloatField(allow_null=True, help_text="Costo máximo que conserva la base óptima; null = sin límite.")
    objetivo_en_minimo = serializers.FloatField(allow_null=True)
    objetivo_en_maximo = serializers.FloatField(allow_null=True)


class RangosSerializer(serializers.Serializer):
    disponible = serializers.BooleanField()
    metodo = serializers.CharField(allow_null=True, help_text="highs_ranging")
    oferta = RangoRhsSerializer(many=True)
    capacidad = RangoRhsSerializer(many=True)
    costos = RangoCostoSerializer(many=True)


class ResumenEscenariosSerializer(serializers.Serializer):
    escenarios = serializers.IntegerField()
    factibles_exacto = serializers.IntegerField()
    factibles_ag = serializers.IntegerField()
    ag_alcanza_optimo = serializers.IntegerField()
    gap_pct_promedio = serializers.FloatField(allow_null=True)
    gap_pct_maximo = serializers.FloatField(allow_null=True)
    tiempo_exacto_total_ms = serializers.FloatField()
    tiempo_ag_total_ms = serializers.FloatField()
    escenarios_con_cambio_de_base = serializers.IntegerField()
    escenarios_con_cambio_de_asignacion = serializers.IntegerField()


class SensibilidadResultadoSerializer(serializers.Serializer):
    base = BaseSensibilidadSerializer()
    precios_sombra = PreciosSombraSerializer()
    rangos = RangosSerializer()
    plantas = AnalisisPlantaSerializer(many=True)
    escenarios = EscenarioSensibilidadSerializer(many=True)
    resumen = ResumenEscenariosSerializer()
    configuracion_ag = ConfigAGSerializer(allow_null=True)
    duracion_total_ms = serializers.FloatField()
    nota = serializers.CharField()


class EjecucionSensibilidadSerializer(serializers.Serializer):
    ejecucion_id = serializers.IntegerField(allow_null=True)
    resultado = SensibilidadResultadoSerializer()


class ResumenModeloSerializer(serializers.Serializer):
    empresas = serializers.IntegerField()
    plantas = serializers.IntegerField()
    rutas = serializers.IntegerField()
    oferta_total = serializers.FloatField()
    capacidad_total = serializers.FloatField()
    modo_oferta = serializers.CharField()


class ComparacionSerializer(serializers.Serializer):
    diferencia_costo = serializers.FloatField(allow_null=True)
    gap_pct = serializers.FloatField(allow_null=True, help_text="(AG - exacto) / exacto x 100.")
    ratio_tiempo = serializers.FloatField(allow_null=True, help_text="tiempo AG / tiempo exacto.")
    ag_alcanza_optimo = serializers.BooleanField()


class SolucionReporteSerializer(ResumenSolucionSerializer):
    asignaciones = AsignacionSerializer(many=True)
    convergencia = serializers.ListField(child=serializers.FloatField(), required=False, help_text="Mejor costo por generación.")
    convergencia_promedio = serializers.ListField(
        child=serializers.FloatField(), required=False, help_text="Costo penalizado promedio por generación."
    )


class ReporteResultadoSerializer(serializers.Serializer):
    modelo = ResumenModeloSerializer()
    exacto = SolucionReporteSerializer()
    genetico = SolucionReporteSerializer()
    configuracion_ag = ConfigAGSerializer()
    comparacion = ComparacionSerializer()
    plantas = AnalisisPlantaSerializer(many=True)
    sensibilidad = SensibilidadResultadoSerializer(allow_null=True)


class EjecucionReporteSerializer(serializers.Serializer):
    ejecucion_id = serializers.IntegerField(allow_null=True)
    resultado = ReporteResultadoSerializer()


# ---------------------------------------------------------------------------------------
# Escalabilidad
# ---------------------------------------------------------------------------------------
class TamanoRedSerializer(serializers.Serializer):
    empresas = serializers.IntegerField(min_value=1, max_value=LIMITES["MAX_EMPRESAS"])
    plantas = serializers.IntegerField(min_value=1, max_value=LIMITES["MAX_PLANTAS"])


class EscalabilidadSolicitudSerializer(BaseEjecucionSerializer):
    tamanos = TamanoRedSerializer(
        many=True,
        required=False,
        allow_empty=False,
        max_length=LIMITES["ESCALABILIDAD_MAX_TAMANOS"],
        help_text="Por defecto 10x4, 20x6, 40x10 y 80x16 (empresas x plantas). Redes sintéticas FICTICIAS.",
    )
    config_ag = ConfigAGSerializer(required=False, help_text="Por defecto poblacion=40, generaciones=80, inicializacion=heuristica.")
    semilla_red = serializers.IntegerField(min_value=0, max_value=2**31 - 1, default=2026, help_text="Semilla del generador de redes.")


class FilaEscalabilidadSerializer(serializers.Serializer):
    empresas = serializers.IntegerField()
    plantas = serializers.IntegerField()
    rutas = serializers.IntegerField()
    oferta_total = serializers.FloatField()
    capacidad_total = serializers.FloatField()
    exacto = ResumenSolucionSerializer()
    genetico = ResumenSolucionSerializer()
    gap_pct = serializers.FloatField(allow_null=True)
    ratio_tiempo = serializers.FloatField(allow_null=True, help_text="tiempo AG / tiempo exacto.")


class EscalabilidadResultadoSerializer(serializers.Serializer):
    ficticio = serializers.BooleanField(help_text="Siempre true: las redes son sintéticas.")
    semilla_red = serializers.IntegerField()
    configuracion_ag = ConfigAGSerializer()
    tamanos = FilaEscalabilidadSerializer(many=True)
    duracion_total_ms = serializers.FloatField()
    nota = serializers.CharField()


class EjecucionEscalabilidadSerializer(serializers.Serializer):
    ejecucion_id = serializers.IntegerField(allow_null=True)
    resultado = EscalabilidadResultadoSerializer()


class DemoEstadoSerializer(serializers.Serializer):
    cargado = serializers.BooleanField(help_text="Existen empresas o plantas FICTICIAS de demostración.")


class DemoCargaSerializer(DemoEstadoSerializer):
    empresas = serializers.IntegerField()
    plantas = serializers.IntegerField()
    rutas = serializers.IntegerField()
    ficticio = serializers.BooleanField()
    detail = serializers.CharField()


# ---------------------------------------------------------------------------------------
# Escenarios y ejecuciones
# ---------------------------------------------------------------------------------------
class EscenarioSerializer(serializers.ModelSerializer):
    creado_por = serializers.CharField(source="creado_por.username", read_only=True, default=None)
    resumen = serializers.SerializerMethodField()

    class Meta:
        model = Escenario
        fields = ["id", "nombre", "descripcion", "creado_por", "creado_en", "resumen"]
        read_only_fields = ["id", "creado_por", "creado_en", "resumen"]

    @extend_schema_field(ResumenModeloSerializer)
    def get_resumen(self, obj):
        p = obj.parametros
        return {
            "empresas": len(p["empresas"]),
            "plantas": len(p["plantas"]),
            "rutas": len(p["arcos"]),
            "oferta_total": sum(e["oferta"] for e in p["empresas"]),
            "capacidad_total": sum(x["capacidad"] for x in p["plantas"]),
            "modo_oferta": p.get("modo_oferta", "exact"),
        }


class EscenarioDetalleSerializer(EscenarioSerializer):
    parametros = serializers.JSONField(read_only=True)

    class Meta(EscenarioSerializer.Meta):
        fields = EscenarioSerializer.Meta.fields + ["parametros"]


class EjecucionListaSerializer(serializers.ModelSerializer):
    usuario = serializers.CharField(source="usuario.username", read_only=True, default=None)

    class Meta:
        model = Ejecucion
        fields = [
            "id", "metodo", "estado", "objetivo", "duracion_ms", "usuario", "escenario", "configuracion",
            "incluye_ficticios", "creada_en",
        ]  # fmt: skip
        read_only_fields = fields


class EjecucionDetalleSerializer(EjecucionListaSerializer):
    resultado = serializers.SerializerMethodField()
    parametros = serializers.JSONField(read_only=True)

    class Meta(EjecucionListaSerializer.Meta):
        fields = EjecucionListaSerializer.Meta.fields + ["parametros", "resultado"]
        read_only_fields = fields

    @extend_schema_field(serializers.JSONField)
    def get_resultado(self, obj):
        return obj.resultado.datos if hasattr(obj, "resultado") else None
