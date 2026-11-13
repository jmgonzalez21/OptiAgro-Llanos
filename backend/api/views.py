from __future__ import annotations

import secrets
from dataclasses import replace

from django.db import transaction
from django.utils.dateparse import parse_date
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from cuentas.models import Usuario

from escenarios.models import Ejecucion, Escenario
from red.models import Empresa, FuenteDistancia, Planta, Ruta
from optimizacion.algoritmo_genetico import ConfigAG
from red.demo import cargar_datos_demo, demo_cargado
from servicios import conversion, escalabilidad as svc_esc, ejecucion as svc, rutas_viales as svc_viales, usuarios as svc_usuarios
from servicios.errores import ErrorDeNegocio
from servicios.historial import registrar_ejecucion

from . import serializers as sz
from .permisos import EsAnalistaOAdministrador, EscrituraSoloAdministrador, SoloAdministrador

ERROR_400 = sz.ErrorSerializer


# ---------------------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------------------
@extend_schema(tags=["auth"], summary="Iniciar sesión (JWT)", responses=sz.LoginRespuestaSerializer)
class LoginView(TokenObtainPairView):
    serializer_class = sz.LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


@extend_schema(
    tags=["auth"],
    summary="Renovar el token de acceso (el refresh rota)",
    description=(
        "Devuelve un access nuevo y un refresh NUEVO; el refresh enviado queda en lista negra. Guarde siempre el "
        "refresh más reciente. Un refresh vencido, revocado o de un usuario desactivado responde 401."
    ),
    responses={200: sz.RefreshRespuestaSerializer, 401: ERROR_400},
)
class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


@extend_schema(
    tags=["auth"],
    summary="Cerrar sesión (revoca el refresh token)",
    description="Pone el refresh en lista negra. Un refresh inválido, vencido o ya revocado responde 400.",
    request=sz.LogoutSerializer,
    responses={204: None, 400: ERROR_400},
)
class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        datos = sz.LogoutSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        try:
            RefreshToken(datos.validated_data["refresh"]).blacklist()
        except TokenError as exc:
            raise ErrorDeNegocio("Token de refresco inválido, vencido o ya revocado.", [str(exc)]) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["auth"])
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Usuario autenticado y su rol", responses=sz.UsuarioSerializer)
    def get(self, request):
        return Response(sz.UsuarioSerializer(request.user).data)

    @extend_schema(
        summary="Editar el propio perfil (nombre, apellido, email)",
        request=sz.PerfilActualizarSerializer,
        responses={200: sz.UsuarioSerializer, 400: ERROR_400},
    )
    def patch(self, request):
        datos = sz.PerfilActualizarSerializer(request.user, data=request.data, partial=True)
        datos.is_valid(raise_exception=True)
        datos.save()
        return Response(sz.UsuarioSerializer(request.user).data)


@extend_schema(
    tags=["auth"],
    summary="Cambiar la propia contraseña",
    description=(
        "Exige la contraseña actual y valida la nueva con los validadores de Django (mínimo 10 caracteres, no común, "
        "no solo numérica, no parecida a los datos del usuario). Revoca todas las sesiones (refresh) anteriores y "
        "devuelve un par de tokens nuevo para continuar la sesión."
    ),
    request=sz.CambiarContrasenaSerializer,
    responses={200: sz.CambiarContrasenaRespuestaSerializer, 400: ERROR_400},
)
class CambiarContrasenaView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):
        datos = sz.CambiarContrasenaSerializer(data=request.data, context={"request": request})
        datos.is_valid(raise_exception=True)
        usuario = request.user
        usuario.set_password(datos.validated_data["contrasena_nueva"])
        usuario.save(update_fields=["password"])
        svc_usuarios.revocar_sesiones(usuario)
        refresh = RefreshToken.for_user(usuario)
        return Response(
            {"detail": "Contraseña actualizada.", "access": str(refresh.access_token), "refresh": str(refresh)}
        )


# ---------------------------------------------------------------------------------------
# Usuarios (solo administrador)
# ---------------------------------------------------------------------------------------
@extend_schema_view(
    list=extend_schema(
        summary="Listar usuarios",
        parameters=[
            OpenApiParameter("rol", str, enum=["administrador", "analista"]),
            OpenApiParameter("activo", bool, description="Filtra por usuarios activos/inactivos."),
        ],
    ),
    retrieve=extend_schema(summary="Detalle de usuario"),
)
@extend_schema(tags=["usuarios"])
class UsuarioViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Gestión de usuarios. Reglas: nadie se desactiva, elimina ni degrada a sí mismo, y siempre queda al menos un
    administrador activo. Nunca se devuelve la contraseña ni su hash."""

    queryset = Usuario.objects.all()
    permission_classes = [SoloAdministrador]
    serializer_class = sz.UsuarioGestionSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering_fields = ["username", "rol", "last_login", "date_joined"]
    ordering = ["username"]

    def get_queryset(self):
        qs = super().get_queryset()
        rol = self.request.query_params.get("rol")
        activo = self.request.query_params.get("activo")
        if rol:
            qs = qs.filter(rol=rol)
        if activo is not None:
            qs = qs.filter(is_active=activo.lower() in ("1", "true", "t", "si", "sí"))
        return qs

    @extend_schema(
        summary="Crear usuario",
        request=sz.UsuarioCrearSerializer,
        responses={201: sz.UsuarioGestionSerializer, 400: ERROR_400},
    )
    def create(self, request):
        datos = sz.UsuarioCrearSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        usuario = datos.save()
        return Response(sz.UsuarioGestionSerializer(usuario).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Editar usuario (nombre, apellido, email, rol, activo)",
        description="El username no se edita. Aplica las reglas de protección del propio usuario y del último administrador.",
        request=sz.UsuarioActualizarSerializer,
        responses={200: sz.UsuarioGestionSerializer, 400: ERROR_400},
    )
    def partial_update(self, request, pk=None):
        objetivo = self.get_object()
        datos = sz.UsuarioActualizarSerializer(objetivo, data=request.data, partial=True)
        datos.is_valid(raise_exception=True)
        usuario = svc_usuarios.aplicar_cambios(request.user, objetivo, dict(datos.validated_data))
        return Response(sz.UsuarioGestionSerializer(usuario).data)

    @extend_schema(
        summary="Eliminar usuario",
        description="Se rechaza (400) eliminarse a sí mismo o al último administrador activo. Prefiera desactivar.",
        responses={204: None, 400: ERROR_400},
    )
    def destroy(self, request, pk=None):
        svc_usuarios.eliminar_usuario(request.user, self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _cambiar_activo(self, request, activo: bool):
        usuario = svc_usuarios.aplicar_cambios(request.user, self.get_object(), {"is_active": activo})
        return Response(sz.UsuarioGestionSerializer(usuario).data)

    @extend_schema(summary="Activar usuario", request=None, responses={200: sz.UsuarioGestionSerializer})
    @action(detail=True, methods=["post"])
    def activar(self, request, pk=None):
        return self._cambiar_activo(request, True)

    @extend_schema(
        summary="Desactivar usuario",
        description="Revoca sus sesiones. Rechaza (400) desactivarse a sí mismo o al último administrador activo.",
        request=None,
        responses={200: sz.UsuarioGestionSerializer, 400: ERROR_400},
    )
    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        return self._cambiar_activo(request, False)

    @extend_schema(
        summary="Restablecer la contraseña de un usuario",
        description=(
            "Con nueva_contrasena (validada con los validadores de Django) o, si se omite, genera una contraseña "
            "temporal que se devuelve UNA sola vez. Revoca las sesiones del usuario."
        ),
        request=sz.RestablecerContrasenaSerializer,
        responses={200: sz.RestablecerContrasenaRespuestaSerializer, 400: ERROR_400},
    )
    @action(detail=True, methods=["post"], url_path="restablecer-contrasena")
    def restablecer_contrasena(self, request, pk=None):
        objetivo = self.get_object()
        datos = sz.RestablecerContrasenaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        nueva = datos.validated_data.get("nueva_contrasena")
        generada = None
        if nueva:
            try:
                sz.validar_contrasena(nueva, objetivo)
            except sz.serializers.ValidationError as exc:
                raise sz.serializers.ValidationError({"nueva_contrasena": exc.detail}) from exc
        else:
            nueva = generada = secrets.token_urlsafe(12)
        objetivo.set_password(nueva)
        objetivo.save(update_fields=["password"])
        svc_usuarios.revocar_sesiones(objetivo)
        return Response({"detail": "Contraseña restablecida.", "contrasena_temporal": generada})


# ---------------------------------------------------------------------------------------
# Red
# ---------------------------------------------------------------------------------------
def _filtro_activa(queryset, request):
    activa = request.query_params.get("activa")
    if activa is not None:
        queryset = queryset.filter(activa=activa.lower() in ("1", "true", "t", "si", "sí"))
    return queryset


PARAM_ACTIVA = OpenApiParameter("activa", bool, description="Filtra por estado activo.")
MAX_TRAYECTOS = 30


class RecalculaRutasAlMoverNodo:
    """Si cambian las coordenadas del nodo, recalcula sus rutas carretera/estimada (las manuales se respetan)."""

    def perform_update(self, serializer):
        antes = (serializer.instance.latitud, serializer.instance.longitud)
        instancia = serializer.save()
        if (instancia.latitud, instancia.longitud) != antes:
            svc_viales.recalcular_por_nodo(**{self.nodo: instancia})


@extend_schema_view(
    list=extend_schema(parameters=[PARAM_ACTIVA], summary="Listar empresas"),
    create=extend_schema(summary="Crear empresa (administrador)"),
    retrieve=extend_schema(summary="Detalle de empresa"),
    update=extend_schema(summary="Reemplazar empresa (administrador)"),
    partial_update=extend_schema(summary="Editar empresa (administrador)"),
    destroy=extend_schema(summary="Eliminar empresa y sus rutas (administrador)"),
)
@extend_schema(tags=["red"])
class EmpresaViewSet(RecalculaRutasAlMoverNodo, viewsets.ModelViewSet):
    nodo = "empresa"
    queryset = Empresa.objects.all()
    serializer_class = sz.EmpresaSerializer
    permission_classes = [EscrituraSoloAdministrador]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["codigo", "nombre", "municipio"]
    ordering_fields = ["codigo", "nombre", "oferta", "creado_en"]
    ordering = ["codigo"]

    def get_queryset(self):
        return _filtro_activa(super().get_queryset(), self.request)


@extend_schema_view(
    list=extend_schema(parameters=[PARAM_ACTIVA], summary="Listar plantas"),
    create=extend_schema(summary="Crear planta (administrador)"),
    retrieve=extend_schema(summary="Detalle de planta"),
    update=extend_schema(summary="Reemplazar planta (administrador)"),
    partial_update=extend_schema(summary="Editar planta (administrador)"),
    destroy=extend_schema(summary="Eliminar planta y sus rutas (administrador)"),
)
@extend_schema(tags=["red"])
class PlantaViewSet(RecalculaRutasAlMoverNodo, viewsets.ModelViewSet):
    nodo = "planta"
    queryset = Planta.objects.all()
    serializer_class = sz.PlantaSerializer
    permission_classes = [EscrituraSoloAdministrador]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["codigo", "nombre", "municipio"]
    ordering_fields = ["codigo", "nombre", "capacidad", "creado_en"]
    ordering = ["codigo"]

    def get_queryset(self):
        return _filtro_activa(super().get_queryset(), self.request)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            PARAM_ACTIVA,
            OpenApiParameter("empresa", str, description="Código de empresa."),
            OpenApiParameter("planta", str, description="Código de planta."),
        ],
        summary="Listar rutas",
    ),
    create=extend_schema(summary="Crear ruta (administrador)"),
    retrieve=extend_schema(summary="Detalle de ruta"),
    update=extend_schema(summary="Reemplazar ruta (administrador)"),
    partial_update=extend_schema(summary="Editar ruta (administrador)"),
    destroy=extend_schema(summary="Eliminar ruta (administrador)"),
)
@extend_schema(tags=["red"])
class RutaViewSet(viewsets.ModelViewSet):
    queryset = Ruta.objects.select_related("empresa", "planta")
    serializer_class = sz.RutaSerializer
    permission_classes = [EscrituraSoloAdministrador]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["empresa__codigo", "empresa__nombre", "planta__codigo", "planta__nombre"]
    ordering_fields = ["empresa__codigo", "planta__codigo", "costo_unitario", "distancia_km"]
    ordering = ["empresa__codigo", "planta__codigo"]

    def get_queryset(self):
        qs = _filtro_activa(super().get_queryset(), self.request)
        empresa = self.request.query_params.get("empresa")
        planta = self.request.query_params.get("planta")
        if empresa:
            qs = qs.filter(empresa__codigo=empresa)
        if planta:
            qs = qs.filter(planta__codigo=planta)
        return qs

    @staticmethod
    def _respuesta_trayecto(ruta) -> dict:
        datos = svc_viales.obtener_trayecto(ruta)
        return {
            "ruta_id": ruta.id,
            "distancia_km": ruta.distancia_km,
            "distancia_fuente": ruta.distancia_fuente,
            **datos,
        }

    @extend_schema(
        summary="Recalcular distancias por carretera (administrador)",
        description=(
            "Consulta OSRM (tabla de distancias por lotes) y actualiza distancia_km y el costo efectivo. "
            "Por defecto solo toca rutas con distancia_fuente carretera/estimada; las manuales se respetan "
            "salvo incluir_manuales=true. Si OSRM falla se usa el respaldo (línea recta x 1,3) y se informa en aviso."
        ),
        request=sz.RecalcularDistanciasSerializer,
        responses={200: sz.RecalcularDistanciasRespuestaSerializer, 400: ERROR_400},
    )
    @action(detail=False, methods=["post"], url_path="recalcular-distancias", permission_classes=[SoloAdministrador])
    def recalcular_distancias(self, request):
        entrada = sz.RecalcularDistanciasSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        datos = entrada.validated_data
        qs = Ruta.objects.select_related("empresa", "planta")
        if "ids" in datos:
            qs = qs.filter(id__in=datos["ids"])
        if datos["solo_estimadas"]:
            qs = qs.filter(distancia_fuente=FuenteDistancia.ESTIMADA)
        return Response(svc_viales.recalcular_rutas(qs, incluir_manuales=datos["incluir_manuales"]))

    @extend_schema(
        summary="Trayecto por carretera de una ruta",
        description="GeoJSON LineString. Se consulta a OSRM la primera vez y se cachea; si OSRM falla devuelve una línea recta con aviso (sin cachear).",
        responses={200: sz.TrayectoRespuestaSerializer, 400: ERROR_400},
    )
    @action(detail=True, methods=["get"], url_path="trayecto")
    def trayecto(self, request, pk=None):
        return Response(self._respuesta_trayecto(self.get_object()))

    @extend_schema(
        summary="Trayectos de varias rutas (máx. 30)",
        parameters=[OpenApiParameter("ids", str, required=True, description="IDs separados por coma, p. ej. 1,2,3.")],
        responses={200: sz.TrayectosRespuestaSerializer, 400: ERROR_400},
    )
    @action(detail=False, methods=["get"], url_path="trayectos")
    def trayectos(self, request):
        try:
            ids = [int(x) for x in (request.query_params.get("ids") or "").split(",") if x.strip()]
        except ValueError:
            raise ErrorDeNegocio("ids debe ser una lista de enteros separados por coma.") from None
        if not ids:
            raise ErrorDeNegocio("Indique ids=1,2,3.")
        if len(ids) > MAX_TRAYECTOS:
            raise ErrorDeNegocio(f"Máximo {MAX_TRAYECTOS} rutas por solicitud (recibidas: {len(ids)}).")
        rutas = {r.id: r for r in Ruta.objects.select_related("empresa", "planta").filter(id__in=ids)}
        return Response({"trayectos": [self._respuesta_trayecto(rutas[i]) for i in dict.fromkeys(ids) if i in rutas]})


def _matriz_actual() -> dict:
    empresas = list(Empresa.objects.order_by("codigo"))
    plantas = list(Planta.objects.order_by("codigo"))
    rutas = list(Ruta.objects.select_related("empresa", "planta"))
    por_par = {(r.empresa_id, r.planta_id): r for r in rutas}
    return {
        "empresas": [
            {"codigo": e.codigo, "nombre": e.nombre, "activa": e.activa, "precio_tonelada": e.precio_tonelada}
            for e in empresas
        ],
        "plantas": [
            {"codigo": p.codigo, "nombre": p.nombre, "activa": p.activa, "costo_operacion_ton": p.costo_operacion_ton}
            for p in plantas
        ],
        "costos": [
            [(por_par[(e.id, p.id)].costo_efectivo if (e.id, p.id) in por_par else None) for p in plantas]
            for e in empresas
        ],
        "costos_totales": [
            [
                (
                    por_par[(e.id, p.id)].costo_efectivo + p.costo_operacion_ton + e.precio_tonelada
                    if (e.id, p.id) in por_par
                    else None
                )
                for p in plantas
            ]
            for e in empresas
        ],
        "rutas": [
            {
                "empresa": r.empresa.codigo,
                "planta": r.planta.codigo,
                "costo_unitario": r.costo_efectivo,
                "distancia_km": r.distancia_km,
                "tarifa_km_ton": r.tarifa_km_ton,
                "limite": r.limite,
                "activa": r.activa,
            }
            for r in sorted(rutas, key=lambda r: (r.empresa.codigo, r.planta.codigo))
        ],
    }


@extend_schema(tags=["red"])
class MatrizCostosView(APIView):
    permission_classes = [EscrituraSoloAdministrador]

    @extend_schema(summary="Matriz de costos empresa x planta", responses=sz.MatrizCostosSerializer)
    def get(self, request):
        return Response(_matriz_actual())

    @extend_schema(
        summary="Actualización masiva de la matriz de costos (administrador)",
        description=(
            "Crea o actualiza rutas por par (empresa, planta). Solo se modifican los campos enviados; "
            "un costo_unitario sin distancia/tarifa anula la distancia/tarifa previas. Es atómico: "
            "si una celda es inválida no se aplica ninguna."
        ),
        request=sz.MatrizCostosEscrituraSerializer,
        responses={200: sz.MatrizCostosSerializer, 400: ERROR_400},
    )
    @transaction.atomic
    def put(self, request):
        entrada = sz.MatrizCostosEscrituraSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        celdas = entrada.validated_data["rutas"]
        empresas = {e.codigo: e for e in Empresa.objects.all()}
        plantas = {p.codigo: p for p in Planta.objects.all()}
        existentes = {(r.empresa_id, r.planta_id): r for r in Ruta.objects.all()}
        errores, vistos = [], set()
        for i, celda in enumerate(celdas):
            e, p = empresas.get(celda["empresa"]), plantas.get(celda["planta"])
            if e is None:
                errores.append(f"rutas[{i}]: la empresa '{celda['empresa']}' no existe.")
            if p is None:
                errores.append(f"rutas[{i}]: la planta '{celda['planta']}' no existe.")
            if e is None or p is None:
                continue
            if (e.id, p.id) in vistos:
                errores.append(f"rutas[{i}]: par duplicado {celda['empresa']}->{celda['planta']}.")
                continue
            vistos.add((e.id, p.id))
            ruta = existentes.get((e.id, p.id)) or Ruta(empresa=e, planta=p)
            actual = {k: getattr(ruta, k) for k in sz.CAMPOS_COSTO}
            cambios = sz.normalizar_cambios_costo({k: celda[k] for k in sz.CAMPOS_COSTO if k in celda})
            if sz.costo_resultante(actual, cambios) is None:
                errores.append(f"rutas[{i}]: indique costo_unitario o bien distancia_km y tarifa_km_ton.")
                continue
            for campo in (*sz.CAMPOS_COSTO, "limite", "activa"):
                if campo in celda or campo in cambios:
                    setattr(ruta, campo, cambios.get(campo, celda.get(campo)))
            if "distancia_km" in cambios or "distancia_km" in celda:
                ruta.distancia_fuente = FuenteDistancia.MANUAL  # la matriz editada a mano fija la distancia
            ruta.save()
        if errores:
            transaction.set_rollback(True)
            raise ErrorDeNegocio("La matriz de costos contiene errores.", errores)
        return Response(_matriz_actual())


# ---------------------------------------------------------------------------------------
# Optimización
# ---------------------------------------------------------------------------------------
def _parametros_para(datos: dict, modo_oferta: str | None = None):
    """Parámetros de un escenario guardado o de la red activa actual."""
    escenario = None
    if datos.get("escenario_id") is not None:
        try:
            escenario = Escenario.objects.get(pk=datos["escenario_id"])
        except Escenario.DoesNotExist as exc:
            raise NotFound(f"El escenario {datos['escenario_id']} no existe.") from exc
        parametros = conversion.parametros_desde_dict(escenario.parametros)
        if modo_oferta:
            parametros = replace(parametros, modo_oferta=modo_oferta)
    else:
        parametros = conversion.construir_parametros(modo_oferta or "exact")
    return parametros, escenario


def _config_ag(datos: dict) -> dict:
    return {k: datos[k] for k in ConfigAG().como_dict() if k in datos}


def _variaciones(datos: list[dict]) -> list[svc.Variacion]:
    return [svc.Variacion(v["tipo"], tuple(v["ids"]), tuple(v["porcentajes"])) for v in datos]


class BaseOptimizacionView(APIView):
    permission_classes = [EsAnalistaOAdministrador]


@extend_schema(
    tags=["optimizacion"],
    summary="Ejecutar el método exacto (LP, HiGHS)",
    description="Resuelve el modelo de transporte. Un estado INFEASIBLE se devuelve con 200; entradas inválidas con 400.",
    request=sz.EjecutarExactoSerializer,
    responses={200: sz.EjecucionResultadoSerializer, 400: ERROR_400},
)
class EjecutarExactoView(BaseOptimizacionView):
    def post(self, request):
        datos = sz.EjecutarExactoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        d = datos.validated_data
        parametros, escenario = _parametros_para(d, d["modo_oferta"])
        resultado = svc.resolver_exacto(parametros)
        ejecucion_id = None
        if d["guardar"]:
            ejecucion_id = registrar_ejecucion(
                usuario=request.user,
                metodo=Ejecucion.Metodo.EXACTO,
                estado=resultado.estado,
                objetivo=resultado.objetivo,
                duracion_ms=resultado.duracion_ms,
                configuracion={"modo_oferta": d["modo_oferta"]},
                parametros=conversion.parametros_a_dict(parametros),
                datos=resultado.como_dict(),
                escenario=escenario,
                incluye_ficticios=conversion.incluye_ficticios(parametros),
            ).pk
        return Response({"ejecucion_id": ejecucion_id, "resultado": resultado.como_dict()})


@extend_schema(
    tags=["optimizacion"],
    summary="Ejecutar el algoritmo genético",
    description=(
        "Solo modo base (oferta exacta, plantas con capacidad máxima). Parámetros ajustables: población, "
        "generaciones, cruce, mutación, semilla y elitismo. Con la misma semilla el resultado es reproducible."
    ),
    request=sz.EjecutarGeneticoSerializer,
    responses={200: sz.EjecucionResultadoSerializer, 400: ERROR_400},
)
class EjecutarGeneticoView(BaseOptimizacionView):
    def post(self, request):
        datos = sz.EjecutarGeneticoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        d = datos.validated_data
        parametros, escenario = _parametros_para(d)
        resultado, cfg = svc.resolver_genetico(parametros, _config_ag(d))
        ejecucion_id = None
        if d["guardar"]:
            ejecucion_id = registrar_ejecucion(
                usuario=request.user,
                metodo=Ejecucion.Metodo.GENETICO,
                estado=resultado.estado,
                objetivo=resultado.objetivo,
                duracion_ms=resultado.duracion_ms,
                configuracion=cfg,
                parametros=conversion.parametros_a_dict(parametros),
                datos=resultado.como_dict(),
                escenario=escenario,
                incluye_ficticios=conversion.incluye_ficticios(parametros),
            ).pk
        return Response({"ejecucion_id": ejecucion_id, "resultado": resultado.como_dict()})


@extend_schema(
    tags=["optimizacion"],
    summary="Análisis de sensibilidad: precios sombra, rangos y escenarios (exacto + AG)",
    description=(
        "Varía porcentualmente la oferta de empresas, la capacidad de una o varias plantas, o los costos de rutas, "
        "reoptimiza cada escenario y devuelve los precios sombra (duales) del caso base, el análisis de cuellos de "
        "botella por planta, los RANGOS de variación (ranging de HiGHS) de ofertas, capacidades y costos de ruta, y la "
        "tabla de escenarios. Cada escenario se resuelve con el exacto y, por defecto (incluir_ag=true), también con el "
        "AG; incluye gap %, tiempos, cambio de asignaciones y si la base óptima cambió (base_cambio)."
    ),
    request=sz.SensibilidadSolicitudSerializer,
    responses={200: sz.EjecucionSensibilidadSerializer, 400: ERROR_400},
)
class SensibilidadView(BaseOptimizacionView):
    def post(self, request):
        datos = sz.SensibilidadSolicitudSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        d = datos.validated_data
        parametros, escenario = _parametros_para(d)
        config = _config_ag(d.get("config_ag", {})) if d["incluir_ag"] else None
        resultado = svc.ejecutar_sensibilidad(parametros, _variaciones(d["variaciones"]), d["incluir_ag"], config)
        ejecucion_id = None
        if d["guardar"]:
            ejecucion_id = registrar_ejecucion(
                usuario=request.user,
                metodo=Ejecucion.Metodo.SENSIBILIDAD,
                estado="COMPLETADA",
                objetivo=resultado["base"]["exacto"]["objetivo"],
                duracion_ms=resultado["duracion_total_ms"],
                configuracion={"variaciones": request.data.get("variaciones"), "incluir_ag": d["incluir_ag"], "config_ag": config},
                parametros=conversion.parametros_a_dict(parametros),
                datos=resultado,
                escenario=escenario,
                incluye_ficticios=conversion.incluye_ficticios(parametros),
            ).pk
        return Response({"ejecucion_id": ejecucion_id, "resultado": resultado})


@extend_schema(
    tags=["optimizacion"],
    summary="Reporte comparativo exacto vs AG",
    description=(
        "Resuelve con ambos métodos y compara costo, tiempo y gap % ((AG - exacto)/exacto x 100). "
        "Opcionalmente incluye el comportamiento de ambos bajo escenarios de sensibilidad."
    ),
    request=sz.ReporteSolicitudSerializer,
    responses={200: sz.EjecucionReporteSerializer, 400: ERROR_400},
)
class ReporteComparativoView(BaseOptimizacionView):
    def post(self, request):
        datos = sz.ReporteSolicitudSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        d = datos.validated_data
        parametros, escenario = _parametros_para(d)
        config = _config_ag(d.get("config_ag", {}))
        variaciones = _variaciones(d["variaciones"]) if d.get("variaciones") else None
        resultado = svc.reporte_comparativo(parametros, config, variaciones)
        ejecucion_id = None
        if d["guardar"]:
            ejecucion_id = registrar_ejecucion(
                usuario=request.user,
                metodo=Ejecucion.Metodo.REPORTE,
                estado="COMPLETADA",
                objetivo=resultado["exacto"]["objetivo"],
                duracion_ms=resultado["exacto"]["duracion_ms"] + resultado["genetico"]["duracion_ms"],
                configuracion={"config_ag": resultado["configuracion_ag"], "con_sensibilidad": bool(variaciones)},
                parametros=conversion.parametros_a_dict(parametros),
                datos=resultado,
                escenario=escenario,
                incluye_ficticios=conversion.incluye_ficticios(parametros),
            ).pk
        return Response({"ejecucion_id": ejecucion_id, "resultado": resultado})


@extend_schema(
    tags=["optimizacion"],
    summary="Prueba de escalabilidad (redes sintéticas, exacto vs AG)",
    description=(
        "Genera redes sintéticas FICTICIAS y deterministas de tamaños crecientes (por defecto 10x4, 20x6, 40x10 y "
        "80x16 empresas x plantas), resuelve cada una con el método exacto y con el AG y compara tiempo, costo y "
        "gap %. Los tamaños y el trabajo total del AG están acotados (OPTIAGRO_ESCALABILIDAD_*): si se exceden, 400. "
        "No usa ni modifica la red guardada."
    ),
    request=sz.EscalabilidadSolicitudSerializer,
    responses={200: sz.EjecucionEscalabilidadSerializer, 400: ERROR_400},
)
class EscalabilidadView(BaseOptimizacionView):
    def post(self, request):
        datos = sz.EscalabilidadSolicitudSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        d = datos.validated_data
        # Solo los parámetros del AG que el cliente envió: el resto toma los valores propios de esta prueba.
        enviados = request.data.get("config_ag") if isinstance(request.data.get("config_ag"), dict) else {}
        config = {k: v for k, v in d.get("config_ag", {}).items() if k in enviados}
        tamanos = [(t["empresas"], t["plantas"]) for t in d["tamanos"]] if d.get("tamanos") else None
        resultado = svc_esc.ejecutar_escalabilidad(tamanos, config, d["semilla_red"])
        ejecucion_id = None
        if d["guardar"]:
            ejecucion_id = registrar_ejecucion(
                usuario=request.user,
                metodo=Ejecucion.Metodo.ESCALABILIDAD,
                estado="COMPLETADA",
                objetivo=None,
                duracion_ms=resultado["duracion_total_ms"],
                configuracion={
                    "tamanos": [f"{f['empresas']}x{f['plantas']}" for f in resultado["tamanos"]],
                    "config_ag": resultado["configuracion_ag"],
                    "semilla_red": d["semilla_red"],
                },
                parametros={},
                datos=resultado,
                incluye_ficticios=True,
            ).pk
        return Response({"ejecucion_id": ejecucion_id, "resultado": resultado})


# ---------------------------------------------------------------------------------------
# Datos de demostración (FICTICIOS)
# ---------------------------------------------------------------------------------------
def _estado_demo() -> dict:
    return {
        "cargado": demo_cargado(),
        "empresas": Empresa.objects.filter(ficticio=True).count(),
        "plantas": Planta.objects.filter(ficticio=True).count(),
        "rutas": Ruta.objects.filter(ficticio=True).count(),
        "ficticio": True,
    }


@extend_schema(tags=["demo"])
class DemoEstadoView(APIView):
    permission_classes = [SoloAdministrador]

    @extend_schema(summary="¿Están cargados los datos demo FICTICIOS?", responses=sz.DemoEstadoSerializer)
    def get(self, request):
        return Response({"cargado": demo_cargado()})


@extend_schema(tags=["demo"])
class DemoCargarView(APIView):
    permission_classes = [SoloAdministrador]

    @extend_schema(
        summary="Cargar los datos de demostración FICTICIOS (administrador, idempotente)",
        description=(
            "Crea 10 empresas, 4 plantas y 40 rutas FICTICIAS (marcadas ficticio=true). Si ya estaban cargadas no "
            "modifica nada y responde 200; si las crea, 201."
        ),
        request=None,
        responses={200: sz.DemoCargaSerializer, 201: sz.DemoCargaSerializer},
    )
    def post(self, request):
        if demo_cargado():
            return Response({**_estado_demo(), "detail": "Los datos demo ya estaban cargados; no se modificó nada."})
        cargar_datos_demo()
        return Response({**_estado_demo(), "detail": "Datos demo FICTICIOS cargados."}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------------------
# Escenarios e historial
# ---------------------------------------------------------------------------------------
@extend_schema_view(
    list=extend_schema(summary="Listar escenarios guardados"),
    create=extend_schema(
        summary="Guardar la red actual como escenario",
        description="Toma una instantánea (JSON) de la red activa; solo se envían nombre y descripción.",
    ),
    retrieve=extend_schema(summary="Detalle del escenario con sus parámetros"),
    destroy=extend_schema(summary="Eliminar escenario (propietario o administrador)"),
)
@extend_schema(tags=["escenarios"])
class EscenarioViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Escenario.objects.select_related("creado_por")
    permission_classes = [EsAnalistaOAdministrador]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["creado_en", "nombre"]

    def get_serializer_class(self):
        return sz.EscenarioDetalleSerializer if self.action == "retrieve" else sz.EscenarioSerializer

    def perform_create(self, serializer):
        parametros = conversion.construir_parametros()
        if not parametros.empresas or not parametros.plantas:
            raise ErrorDeNegocio("No hay red activa que guardar.", ["Debe existir al menos una empresa y una planta activas."])
        serializer.save(creado_por=self.request.user, parametros=conversion.parametros_a_dict(parametros))

    def perform_destroy(self, instance):
        if instance.creado_por_id != self.request.user.id and not self.request.user.es_administrador:
            raise PermissionDenied("Solo el propietario o un administrador puede eliminar el escenario.")
        instance.delete()


@extend_schema_view(
    list=extend_schema(
        summary="Historial de ejecuciones",
        description="Los administradores ven todas; los analistas solo las propias.",
        parameters=[
            OpenApiParameter("metodo", str, enum=["exacto", "genetico", "sensibilidad", "reporte", "escalabilidad"]),
            OpenApiParameter("estado", str),
            OpenApiParameter("desde", str, description="Fecha inicial YYYY-MM-DD (inclusive, hora de Bogotá)."),
            OpenApiParameter("hasta", str, description="Fecha final YYYY-MM-DD (inclusive, hora de Bogotá)."),
            OpenApiParameter("incluye_ficticios", bool, description="Solo ejecuciones con (true) o sin (false) datos ficticios."),
            OpenApiParameter("escenario", int),
            OpenApiParameter("usuario", str, description="Username (solo administradores)."),
        ],
    ),
    retrieve=extend_schema(summary="Detalle de una ejecución con su resultado completo"),
)
@extend_schema(tags=["ejecuciones"])
class EjecucionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Ejecucion.objects.select_related("usuario", "resultado")
    filter_backends = [OrderingFilter]
    ordering_fields = ["creada_en", "objetivo", "duracion_ms"]
    ordering = ["-creada_en", "-id"]

    def get_serializer_class(self):
        return sz.EjecucionDetalleSerializer if self.action == "retrieve" else sz.EjecucionListaSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user
        params = self.request.query_params
        if usuario.es_administrador:
            if params.get("usuario"):
                qs = qs.filter(usuario__username=params["usuario"])
        else:
            qs = qs.filter(usuario=usuario)
        for campo in ("metodo", "estado"):
            if params.get(campo):
                qs = qs.filter(**{campo: params[campo]})
        for parametro, filtro in (("desde", "creada_en__date__gte"), ("hasta", "creada_en__date__lte")):
            if params.get(parametro):
                fecha = parse_date(params[parametro]) if len(params[parametro]) == 10 else None
                if fecha is None:
                    raise ErrorDeNegocio(f"'{parametro}' debe ser una fecha válida YYYY-MM-DD.", [f"Valor recibido: {params[parametro]!r}."])
                qs = qs.filter(**{filtro: fecha})
        if params.get("incluye_ficticios") is not None:
            qs = qs.filter(incluye_ficticios=params["incluye_ficticios"].lower() in ("1", "true", "t", "si", "sí"))
        if params.get("escenario", "").isdigit():
            qs = qs.filter(escenario_id=int(params["escenario"]))
        return qs
