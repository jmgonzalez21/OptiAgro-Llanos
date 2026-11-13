import pytest

URLS_PROTEGIDAS = [
    ("get", "/api/v1/auth/me/"),
    ("get", "/api/v1/empresas/"),
    ("get", "/api/v1/plantas/"),
    ("get", "/api/v1/rutas/"),
    ("get", "/api/v1/red/matriz-costos/"),
    ("put", "/api/v1/red/matriz-costos/"),
    ("post", "/api/v1/optimizacion/exacto/"),
    ("post", "/api/v1/optimizacion/genetico/"),
    ("post", "/api/v1/optimizacion/sensibilidad/"),
    ("post", "/api/v1/optimizacion/reporte/"),
    ("get", "/api/v1/ejecuciones/"),
    ("get", "/api/v1/escenarios/"),
    ("get", "/api/v1/schema/"),
]


@pytest.mark.parametrize("metodo,url", URLS_PROTEGIDAS)
def test_sin_token_401(anonimo, metodo, url):
    assert getattr(anonimo, metodo)(url, {}, format="json").status_code == 401


def test_token_invalido_401(anonimo):
    anonimo.credentials(HTTP_AUTHORIZATION="Bearer no-es-un-token")
    assert anonimo.get("/api/v1/empresas/").status_code == 401


def test_login_devuelve_tokens_y_rol(anonimo, admin, clave):
    r = anonimo.post("/api/v1/auth/login/", {"username": "admin_t", "password": clave}, format="json")
    assert r.status_code == 200
    assert r.data["access"] and r.data["refresh"]
    assert r.data["usuario"]["rol"] == "administrador"
    assert "password" not in r.data["usuario"]


def test_login_incorrecto_401(anonimo, admin):
    r = anonimo.post("/api/v1/auth/login/", {"username": "admin_t", "password": "incorrecta"}, format="json")
    assert r.status_code == 401


def test_login_sin_campos_400(anonimo):
    assert anonimo.post("/api/v1/auth/login/", {}, format="json").status_code == 400


def test_refresh_y_me(anonimo, analista, clave):
    login = anonimo.post("/api/v1/auth/login/", {"username": "analista_t", "password": clave}, format="json").data
    r = anonimo.post("/api/v1/auth/refresh/", {"refresh": login["refresh"]}, format="json")
    assert r.status_code == 200 and r.data["access"]
    anonimo.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    me = anonimo.get("/api/v1/auth/me/")
    assert me.status_code == 200
    assert me.data["username"] == "analista_t" and me.data["rol"] == "analista"


def test_me_incluye_id_nombre_completo_email_y_rol(cliente_admin, admin):
    admin.first_name, admin.last_name, admin.email = "Ana", "Pérez", "ana@ejemplo.invalid"
    admin.save()
    me = cliente_admin.get("/api/v1/auth/me/").data
    assert me["id"] == admin.id and me["username"] == "admin_t"
    assert me["nombre_completo"] == "Ana Pérez" and me["email"] == "ana@ejemplo.invalid"
    assert me["rol"] == "administrador"
    assert "password" not in me
    # sin barra final redirige (APPEND_SLASH) a la ruta canónica
    assert cliente_admin.get("/api/v1/auth/me").status_code in (200, 301)


def test_refresh_invalido_401(anonimo):
    assert anonimo.post("/api/v1/auth/refresh/", {"refresh": "xxx"}, format="json").status_code == 401
