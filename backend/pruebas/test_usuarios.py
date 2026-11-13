"""Gestión de usuarios, cambio de contraseña, perfil, refresh rotativo y logout."""
import pytest

from cuentas.models import Rol, Usuario

URL = "/api/v1/usuarios/"
CLAVE_FUERTE = "Clave-Segura-2026!"


def _nuevo(cliente, **extra):
    cuerpo = {"username": "nuevo_u", "password": CLAVE_FUERTE, "rol": "analista", **extra}
    return cliente.post(URL, cuerpo, format="json")


# ------------------------------------------------------------------ permisos
@pytest.mark.parametrize("metodo,sufijo", [("get", ""), ("post", ""), ("get", "1/"), ("patch", "1/"), ("delete", "1/"),
                                           ("post", "1/desactivar/"), ("post", "1/restablecer-contrasena/")])
def test_usuarios_sin_token_401(anonimo, metodo, sufijo):
    assert getattr(anonimo, metodo)(URL + sufijo, {}, format="json").status_code == 401


@pytest.mark.parametrize("metodo,sufijo", [("get", ""), ("post", ""), ("get", "{id}/"), ("patch", "{id}/"), ("delete", "{id}/"),
                                           ("post", "{id}/activar/"), ("post", "{id}/desactivar/"),
                                           ("post", "{id}/restablecer-contrasena/")])
def test_usuarios_analista_403(cliente_analista, admin, metodo, sufijo):
    r = getattr(cliente_analista, metodo)(URL + sufijo.format(id=admin.id), {}, format="json")
    assert r.status_code == 403


# ------------------------------------------------------------------ listado y alta
def test_listar_con_busqueda_y_filtros(cliente_admin, admin, analista, otro_analista):
    Usuario.objects.filter(pk=otro_analista.pk).update(is_active=False, first_name="Zoila")
    todos = cliente_admin.get(URL).data
    assert todos["count"] == 3
    fila = next(u for u in todos["results"] if u["username"] == "analista_t")
    assert set(fila) == {"id", "username", "first_name", "last_name", "nombre_completo", "email", "rol", "activo",
                         "ultimo_acceso", "fecha_creacion"}
    assert cliente_admin.get(URL + "?rol=administrador").data["count"] == 1
    assert cliente_admin.get(URL + "?activo=false").data["count"] == 1
    assert cliente_admin.get(URL + "?activo=true&rol=analista").data["count"] == 1
    assert cliente_admin.get(URL + "?search=zoila").data["results"][0]["username"] == "analista_t2"


def test_crear_usuario_no_devuelve_contrasena_ni_hash(cliente_admin):
    r = _nuevo(cliente_admin, first_name="Nu", last_name="Evo", email="nuevo@ejemplo.invalid")
    assert r.status_code == 201, r.data
    assert r.data["rol"] == "analista" and r.data["activo"] is True
    assert "password" not in r.data
    assert CLAVE_FUERTE not in str(r.data) and "pbkdf2" not in str(r.data)
    u = Usuario.objects.get(username="nuevo_u")
    assert u.check_password(CLAVE_FUERTE) and u.password != CLAVE_FUERTE and not u.is_staff
    assert cliente_admin.get(f"{URL}{u.id}/").data["username"] == "nuevo_u"
    assert "password" not in cliente_admin.get(URL).data["results"][0]


def test_crear_administrador_sincroniza_banderas(cliente_admin):
    assert _nuevo(cliente_admin, rol="administrador").status_code == 201
    u = Usuario.objects.get(username="nuevo_u")
    assert u.es_administrador and u.is_staff and u.is_superuser


@pytest.mark.parametrize("clave", ["corta1!A", "9876543210", "qwertyuiop", "nuevo_u12345"])
def test_crear_con_contrasena_debil_400(cliente_admin, clave):
    r = cliente_admin.post(URL, {"username": "nuevo_u", "password": clave}, format="json")
    assert r.status_code == 400 and "password" in r.data["errores"]
    assert not Usuario.objects.filter(username="nuevo_u").exists()


def test_crear_username_duplicado_y_rol_invalido_400(cliente_admin, analista):
    assert cliente_admin.post(URL, {"username": "analista_t", "password": CLAVE_FUERTE}, format="json").status_code == 400
    assert _nuevo(cliente_admin, rol="superheroe").status_code == 400


# ------------------------------------------------------------------ edición
def test_editar_usuario(cliente_admin, analista):
    r = cliente_admin.patch(f"{URL}{analista.id}/", {"first_name": "Ana", "email": "ana@ejemplo.invalid", "rol": "administrador"}, format="json")
    assert r.status_code == 200, r.data
    analista.refresh_from_db()
    assert analista.first_name == "Ana" and analista.es_administrador and analista.is_staff
    r = cliente_admin.patch(f"{URL}{analista.id}/", {"username": "otro_nombre"}, format="json")
    analista.refresh_from_db()
    assert analista.username == "analista_t"  # el username no se edita


def test_put_no_permitido(cliente_admin, analista):
    assert cliente_admin.put(f"{URL}{analista.id}/", {"first_name": "X"}, format="json").status_code == 405


def test_desactivar_y_activar_revoca_sesiones(cliente_admin, analista, clave, anonimo):
    sesion = anonimo.post("/api/v1/auth/login/", {"username": "analista_t", "password": clave}, format="json").data
    r = cliente_admin.post(f"{URL}{analista.id}/desactivar/")
    assert r.status_code == 200 and r.data["activo"] is False
    assert anonimo.post("/api/v1/auth/refresh/", {"refresh": sesion["refresh"]}, format="json").status_code == 401
    assert anonimo.post("/api/v1/auth/login/", {"username": "analista_t", "password": clave}, format="json").status_code == 401
    r = cliente_admin.patch(f"{URL}{analista.id}/", {"activo": True}, format="json")
    assert r.status_code == 200 and r.data["activo"] is True
    assert anonimo.post("/api/v1/auth/login/", {"username": "analista_t", "password": clave}, format="json").status_code == 200


def test_restablecer_contrasena_indicada_y_generada(cliente_admin, analista, clave, anonimo):
    r = cliente_admin.post(f"{URL}{analista.id}/restablecer-contrasena/", {"nueva_contrasena": "123"}, format="json")
    assert r.status_code == 400 and "nueva_contrasena" in r.data["errores"]
    r = cliente_admin.post(f"{URL}{analista.id}/restablecer-contrasena/", {"nueva_contrasena": CLAVE_FUERTE}, format="json")
    assert r.status_code == 200 and r.data["contrasena_temporal"] is None and CLAVE_FUERTE not in str(r.data)
    analista.refresh_from_db()
    assert analista.check_password(CLAVE_FUERTE)
    r = cliente_admin.post(f"{URL}{analista.id}/restablecer-contrasena/", {}, format="json")
    temporal = r.data["contrasena_temporal"]
    assert r.status_code == 200 and len(temporal) >= 10
    assert anonimo.post("/api/v1/auth/login/", {"username": "analista_t", "password": temporal}, format="json").status_code == 200


def test_eliminar_usuario(cliente_admin, analista):
    assert cliente_admin.delete(f"{URL}{analista.id}/").status_code == 204
    assert not Usuario.objects.filter(pk=analista.pk).exists()
    assert cliente_admin.delete(f"{URL}{analista.id}/").status_code == 404


# ------------------------------------------------------------------ reglas de protección
def test_no_puede_desactivar_eliminar_ni_degradar_a_si_mismo(cliente_admin, admin, analista):
    segundo = Usuario.objects.create_user("admin_t2", password="x" * 12, rol=Rol.ADMINISTRADOR)  # hay otro admin activo
    for r in (
        cliente_admin.post(f"{URL}{admin.id}/desactivar/"),
        cliente_admin.patch(f"{URL}{admin.id}/", {"activo": False}, format="json"),
        cliente_admin.patch(f"{URL}{admin.id}/", {"rol": "analista"}, format="json"),
        cliente_admin.delete(f"{URL}{admin.id}/"),
    ):
        assert r.status_code == 400 and r.data["detail"] and r.data["errores"]
    admin.refresh_from_db()
    assert admin.is_active and admin.es_administrador and segundo.is_active


def test_no_se_puede_dejar_sin_administradores_activos(cliente_admin, admin):
    otro = Usuario.objects.create_user("admin_t2", password="x" * 12, rol=Rol.ADMINISTRADOR)
    # 'admin' (quien actúa) intenta tocar al otro, que es admin activo pero NO el último: permitido.
    # Primero se deja a 'otro' como único admin activo desactivando a un tercero inexistente: ver caso siguiente.
    from servicios import usuarios as svc
    from servicios.errores import ErrorDeNegocio

    Usuario.objects.filter(pk=admin.pk).update(is_active=False)  # ahora 'otro' es el único admin activo
    actor = Usuario.objects.create_user("tercero", password="x" * 12, rol=Rol.ANALISTA)
    for kwargs in ({"activo_nuevo": False}, {"rol_nuevo": "analista"}, {"eliminar": True}):
        with pytest.raises(ErrorDeNegocio) as e:
            svc.validar_cambio(actor, otro, **kwargs)
        assert "administradores activos" in e.value.mensaje


def test_ultimo_admin_via_api(cliente_admin, admin):
    """Un admin que NO es el último puede desactivar al otro; luego el restante queda protegido."""
    otro = Usuario.objects.create_user("admin_t2", password="x" * 12, rol=Rol.ADMINISTRADOR)
    assert cliente_admin.post(f"{URL}{otro.id}/desactivar/").status_code == 200
    # ahora solo 'admin' está activo: se protege (por ser el propio usuario y el último)
    r = cliente_admin.post(f"{URL}{admin.id}/desactivar/")
    assert r.status_code == 400
    assert cliente_admin.patch(f"{URL}{otro.id}/", {"rol": "analista"}, format="json").status_code == 200  # inactivo: no cuenta


def test_degradar_al_unico_admin_activo_desde_otro_admin_400(cliente_admin, admin):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import AccessToken

    otro = Usuario.objects.create_user("admin_t2", password="x" * 12, rol=Rol.ADMINISTRADOR)
    cliente_otro = APIClient()
    cliente_otro.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(otro)}")
    assert cliente_otro.post(f"{URL}{admin.id}/desactivar/").status_code == 200  # 'otro' desactiva a 'admin'
    assert cliente_otro.post(f"{URL}{admin.id}/activar/").status_code == 200
    # con ambos activos se puede degradar a uno; el que queda es el último y ya no se puede tocar
    assert cliente_otro.patch(f"{URL}{admin.id}/", {"rol": "analista"}, format="json").status_code == 200
    assert cliente_admin.get(URL).status_code == 403  # 'admin' ya es analista
    r = cliente_otro.patch(f"{URL}{otro.id}/", {"rol": "analista"}, format="json")
    assert r.status_code == 400


# ------------------------------------------------------------------ perfil, contraseña, refresh, logout
def test_patch_me_edita_perfil_pero_no_rol(cliente_analista, analista):
    r = cliente_analista.patch("/api/v1/auth/me/", {"first_name": "Luz", "last_name": "Mar", "email": "luz@ejemplo.invalid", "rol": "administrador"}, format="json")
    assert r.status_code == 200 and r.data["nombre_completo"] == "Luz Mar" and r.data["rol"] == "analista"
    analista.refresh_from_db()
    assert analista.email == "luz@ejemplo.invalid" and analista.rol == "analista"
    assert cliente_analista.patch("/api/v1/auth/me/", {"email": "no-es-correo"}, format="json").status_code == 400


def test_patch_me_requiere_token(anonimo):
    assert anonimo.patch("/api/v1/auth/me/", {"first_name": "X"}, format="json").status_code == 401


def test_cambiar_contrasena(cliente_analista, analista, clave, anonimo):
    url = "/api/v1/auth/cambiar-contrasena/"
    assert cliente_analista.post(url, {"contrasena_actual": "mal", "contrasena_nueva": CLAVE_FUERTE}, format="json").status_code == 400
    r = cliente_analista.post(url, {"contrasena_actual": clave, "contrasena_nueva": "corta"}, format="json")
    assert r.status_code == 400 and "contrasena_nueva" in r.data["errores"]
    assert cliente_analista.post(url, {"contrasena_actual": clave, "contrasena_nueva": clave}, format="json").status_code == 400
    vieja = anonimo.post("/api/v1/auth/login/", {"username": "analista_t", "password": clave}, format="json").data["refresh"]
    r = cliente_analista.post(url, {"contrasena_actual": clave, "contrasena_nueva": CLAVE_FUERTE}, format="json")
    assert r.status_code == 200 and r.data["access"] and r.data["refresh"]
    analista.refresh_from_db()
    assert analista.check_password(CLAVE_FUERTE)
    assert anonimo.post("/api/v1/auth/refresh/", {"refresh": vieja}, format="json").status_code == 401  # sesiones previas revocadas
    assert anonimo.post("/api/v1/auth/refresh/", {"refresh": r.data["refresh"]}, format="json").status_code == 200


def test_cambiar_contrasena_requiere_token(anonimo):
    assert anonimo.post("/api/v1/auth/cambiar-contrasena/", {}, format="json").status_code == 401


def test_refresh_rota_y_el_anterior_queda_invalido(anonimo, analista, clave):
    login = anonimo.post("/api/v1/auth/login/", {"username": "analista_t", "password": clave}, format="json").data
    r = anonimo.post("/api/v1/auth/refresh/", {"refresh": login["refresh"]}, format="json")
    assert r.status_code == 200 and r.data["access"] and r.data["refresh"] != login["refresh"]
    assert anonimo.post("/api/v1/auth/refresh/", {"refresh": login["refresh"]}, format="json").status_code == 401
    assert anonimo.post("/api/v1/auth/refresh/", {"refresh": r.data["refresh"]}, format="json").status_code == 200


def test_logout_revoca_el_refresh(anonimo, analista, clave):
    login = anonimo.post("/api/v1/auth/login/", {"username": "analista_t", "password": clave}, format="json").data
    assert anonimo.post("/api/v1/auth/logout/", {"refresh": login["refresh"]}, format="json").status_code == 204
    assert anonimo.post("/api/v1/auth/refresh/", {"refresh": login["refresh"]}, format="json").status_code == 401
    assert anonimo.post("/api/v1/auth/logout/", {"refresh": login["refresh"]}, format="json").status_code == 400  # ya revocado
    assert anonimo.post("/api/v1/auth/logout/", {"refresh": "basura"}, format="json").status_code == 400
    assert anonimo.post("/api/v1/auth/logout/", {}, format="json").status_code == 400
