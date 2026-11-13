from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.include_root_view = False
router.register("empresas", views.EmpresaViewSet, basename="empresa")
router.register("plantas", views.PlantaViewSet, basename="planta")
router.register("rutas", views.RutaViewSet, basename="ruta")
router.register("usuarios", views.UsuarioViewSet, basename="usuario")
router.register("escenarios", views.EscenarioViewSet, basename="escenario")
router.register("ejecuciones", views.EjecucionViewSet, basename="ejecucion")

urlpatterns = [
    path("auth/login/", views.LoginView.as_view(), name="auth-login"),
    path("auth/refresh/", views.RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", views.MeView.as_view(), name="auth-me"),
    path("auth/cambiar-contrasena/", views.CambiarContrasenaView.as_view(), name="auth-cambiar-contrasena"),
    path("demo/estado/", views.DemoEstadoView.as_view(), name="demo-estado"),
    path("demo/cargar/", views.DemoCargarView.as_view(), name="demo-cargar"),
    path("red/matriz-costos/", views.MatrizCostosView.as_view(), name="matriz-costos"),
    path("optimizacion/exacto/", views.EjecutarExactoView.as_view(), name="optimizacion-exacto"),
    path("optimizacion/genetico/", views.EjecutarGeneticoView.as_view(), name="optimizacion-genetico"),
    path("optimizacion/sensibilidad/", views.SensibilidadView.as_view(), name="optimizacion-sensibilidad"),
    path("optimizacion/reporte/", views.ReporteComparativoView.as_view(), name="optimizacion-reporte"),
    path("optimizacion/escalabilidad/", views.EscalabilidadView.as_view(), name="optimizacion-escalabilidad"),
    # Esquema y documentación: abiertos solo con DJANGO_DEBUG=True; en producción exigen JWT (ver settings).
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("", include(router.urls)),
]
