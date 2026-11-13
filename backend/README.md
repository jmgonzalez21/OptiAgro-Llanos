# OptiAgro-Llanos · Backend

Django 5.2 LTS + Django REST Framework + SimpleJWT + drf-spectacular, PostgreSQL 16, Python 3.12 (Docker).
Unidades: toneladas por semana; costos en COP. El contrato con el frontend es `docs/api/openapi.yaml`.

```
backend/
  config/        settings (variables de entorno), urls
  cuentas/       Usuario con rol: administrador | analista (+ comandos crear_usuarios_demo, inicializar_demo)
  red/           Empresa, Planta, Ruta, carga de datos demo FICTICIOS (red/demo.py)
  escenarios/    Escenario, Ejecucion, Resultado (JSON)
  servicios/     ORM -> ParametrosModelo y llamadas a los solvers (única puerta de entrada a optimizacion/)
  api/           serializers, vistas, permisos y rutas de /api/v1/
  dominio/       Python puro (sin Django): ParametrosModelo, ResultadoOptimizacion, generador de redes sintéticas
  optimizacion/  Python puro: MetodoExacto (HiGHS), analizar_lp (base + ranging con highspy), AlgoritmoGenetico
  pruebas/       pytest
```

`dominio/` y `optimizacion/` no importan Django; solo `servicios/` los invoca.

## Puesta en marcha (todo en Docker, una sola entrada)

```powershell
Copy-Item .env.example .env        # y cambie los valores de ejemplo (SECRET_KEY, contraseñas)
docker compose up -d --build       # db + backend (gunicorn) + frontend (nginx + SPA) -> http://localhost:8080
```

- El backend aplica las migraciones y recopila estáticos al arrancar (`backend/entrypoint.sh`). Con
  `OPTIAGRO_CARGAR_DEMO=true` crea además los usuarios demo y carga los datos FICTICIOS **solo si no existen**
  (las contraseñas salen de `DEMO_ADMIN_PASSWORD` / `DEMO_ANALISTA_PASSWORD`; nunca están en el repo).
  También se pueden cargar desde la SPA (`POST /api/v1/demo/cargar/`, administrador) o con
  `docker compose exec backend python manage.py inicializar_demo`.
- Puerto publicado: `FRONTEND_PORT` (por defecto 8080). nginx reenvía `/api/` al backend. El backend también queda
  en `127.0.0.1:8000` solo para desarrollo (`npm run dev`); quite ese bloque de `docker-compose.yml` para una entrada única.
- **El admin de Django está apagado** (`OPTIAGRO_ADMIN_HABILITADO=false`): `/admin/` responde 404. Para usarlo en
  desarrollo ponga `OPTIAGRO_ADMIN_HABILITADO=true` y cree un superusuario con
  `docker compose exec backend python manage.py createsuperuser` (rol administrador). La gestión de usuarios,
  empresas, plantas y rutas se hace desde la SPA / API.
- Documentación interactiva `/api/v1/docs/` y esquema `/api/v1/schema/`: abiertos solo con `DJANGO_DEBUG=True`; en
  producción exigen `Authorization: Bearer <access>` (use `curl` con el token o consulte `docs/api/openapi.yaml`).
- Los datos de demo son **FICTICIOS** (`ficticio=True`; nombres "FICTICIA"). `cargar_demo --limpiar` solo borra los ficticios.
- `DEBUG=False` por defecto. Con `DJANGO_DEBUG=False` es obligatorio definir `DJANGO_SECRET_KEY`.

### Probar con curl (a través del proxy)

```powershell
$cuerpo = '{"username":"admin_demo","password":"<DEMO_ADMIN_PASSWORD de .env>"}'
$cuerpo | Set-Content login.json -Encoding ascii
curl.exe -s -X POST http://localhost:8080/api/v1/auth/login/ -H "Content-Type: application/json" --data "@login.json"
# -> {"refresh": "...", "access": "...", "usuario": {..., "rol": "administrador"}}
curl.exe -s -X POST http://localhost:8080/api/v1/optimizacion/exacto/ -H "Authorization: Bearer <access>" -H "Content-Type: application/json" -d "{}"
```

## Pruebas

```powershell
docker compose exec backend pytest -q
# o, sin depender del contenedor en marcha (monta el código local):
docker compose run --rm -v "${PWD}/backend:/app" backend pytest -q
```

pytest-django crea una base `test_<POSTGRES_DB>` en el servicio `db`. `pruebas/test_optimizacion.py` (CP-01 = 64,
capacidad insuficiente, AG reproducible) y `pruebas/test_nucleo_ag_costos_ranging.py` no usan Django.

## Contrato OpenAPI (`docs/api/openapi.yaml`)

Se genera con drf-spectacular; regenérelo tras cualquier cambio en serializers, vistas o rutas (desde la raíz):

```powershell
docker compose run --rm --no-deps -v "${PWD}/docs/api:/docs/api" backend `
  python manage.py spectacular --file /docs/api/openapi.yaml --validate --fail-on-warn
```

## Endpoints (`/api/v1/`)

| Método y ruta | Rol | Descripción |
|---|---|---|
| `POST auth/login/` | público | `{username, password}` -> `{access, refresh, usuario}` |
| `POST auth/refresh/` | público | `{refresh}` -> `{access, refresh}`; **el refresh rota** y el anterior queda en lista negra |
| `POST auth/logout/` | público (con el refresh) | `{refresh}` -> 204; revoca el refresh (inválido o ya revocado: 400) |
| `GET/PATCH auth/me/` | autenticado | usuario y rol; PATCH: `first_name`, `last_name`, `email` propios |
| `POST auth/cambiar-contrasena/` | autenticado | `{contrasena_actual, contrasena_nueva}` -> `{detail, access, refresh}`; revoca las sesiones anteriores |
| `GET/POST usuarios/`, `GET/PATCH/DELETE usuarios/{id}/` | administrador | `?search=`, `?rol=`, `?activo=`; PATCH: nombre, apellido, email, `rol`, `activo` |
| `POST usuarios/{id}/activar/`, `.../desactivar/` | administrador | desactivar revoca sus sesiones |
| `POST usuarios/{id}/restablecer-contrasena/` | administrador | `{nueva_contrasena}` o vacío (genera una temporal, devuelta una vez) |
| `GET demo/estado/`, `POST demo/cargar/` | administrador | datos demo FICTICIOS (carga idempotente: 201 si crea, 200 si ya estaban) |
| `GET/POST empresas/`, `.../{id}/` | lectura: autenticado; escritura: administrador | `precio_tonelada`; `codigo` inmutable tras crear (400); `?search=&activa=` |
| `.../plantas/` | ídem | `tipo_demanda`, `costo_operacion_ton`; `codigo` inmutable |
| `.../rutas/` | ídem | `empresa` y `planta` por `codigo`; `distancia_km`, `tarifa_km_ton`, `costo_unitario`, `limite`, `activa` |
| `POST rutas/recalcular-distancias/` | administrador | `{ids?, solo_estimadas?, incluir_manuales?}` -> `{actualizadas, estimadas, errores, detalle_errores, aviso}` |
| `GET rutas/{id}/trayecto/`, `GET rutas/trayectos/?ids=1,2` (máx. 30) | autenticado | GeoJSON LineString del trayecto por carretera (cacheado) |
| `GET/PUT red/matriz-costos/` | GET: autenticado; PUT: administrador | `costos` (transporte) y `costos_totales` (+ operación + precio) |
| `POST optimizacion/exacto/` | analista/administrador | LP con HiGHS; asignaciones con desglose de costo, duales, verificación |
| `POST optimizacion/genetico/` | analista/administrador | AG completo (ver abajo) |
| `POST optimizacion/sensibilidad/` | analista/administrador | precios sombra, **rangos**, escenarios con exacto + AG |
| `POST optimizacion/reporte/` | analista/administrador | exacto vs AG: costo, tiempos, gap %; opcionalmente con sensibilidad |
| `POST optimizacion/escalabilidad/` | analista/administrador | redes sintéticas crecientes, exacto vs AG |
| `GET/POST/DELETE escenarios/` | analista/administrador | instantáneas de la red (reutilizables con `escenario_id`) |
| `GET ejecuciones/`, `GET ejecuciones/{id}/` | autenticado | historial (analista: propias; administrador: todas). Filtros `?metodo=&estado=&escenario=&usuario=&desde=YYYY-MM-DD&hasta=YYYY-MM-DD&incluye_ficticios=`; campo `incluye_ficticios` |
| `GET schema/`, `GET docs/` | JWT (abiertos con DEBUG) | OpenAPI y Swagger UI |

Reglas relevantes:

- **Contraseñas**: validadores de Django con mínimo **10 caracteres** (no común, no solo numérica, no parecida al usuario).
- **Usuarios**: nadie puede desactivarse, eliminarse ni quitarse el rol administrador a sí mismo, ni dejar el sistema sin
  administradores activos (400 con mensaje claro). Nunca se devuelve la contraseña ni su hash.
- **Sesión**: access 30 min, refresh 24 h con ventana deslizante (`JWT_*_MINUTOS`). Cada renovación emite un refresh
  nuevo y pone el anterior en lista negra (`token_blacklist`); logout, desactivación, restablecer o cambiar contraseña
  también revocan. Los access ya emitidos siguen valiendo hasta que expiran (<= 30 min).
- **Modelo de costos**: costo efectivo de la ruta (COP/t) = `transporte` (distancia x tarifa, o `costo_unitario`)
  + `costo_operacion_ton` de la planta destino + `precio_tonelada` de la empresa origen. Ambos extras valen 0 por
  defecto, así que CP-01 sigue dando 64. Las asignaciones devuelven `costo_unitario` (efectivo) y sus componentes, y
  `metricas.desglose_costos` suma transporte, operación y precio del óptimo. Nota: en el modo base (oferta exacta) el
  precio de una empresa es una constante del objetivo y no cambia la asignación; sí la cambia con `modo_oferta=maximum`.
- **Distancias por carretera** (`servicios/rutas_viales.py`, OSRM sobre OpenStreetMap; `OPTIAGRO_OSRM_URL`,
  `OPTIAGRO_OSRM_TIMEOUT`, `OPTIAGRO_OSRM_HABILITADO`). `Ruta.distancia_fuente` = `carretera` | `estimada` | `manual`.
  Al crear una ruta sin `distancia_km` (con `tarifa_km_ton` y coordenadas en ambos extremos) se calcula por carretera;
  si OSRM falla se usa línea recta x 1,3, se marca `estimada` y la respuesta trae `aviso` (no falla). Al cambiar las
  coordenadas de una empresa/planta se recalculan sus rutas `carretera`/`estimada` (las `manual` no) y se invalida el
  trayecto cacheado. Una distancia enviada por el usuario o por la matriz de costos queda `manual`. El costo efectivo
  sigue siendo distancia x tarifa. **Nota honesta**: la ruta es la que calcula OSRM (en general la más corta/rápida por
  carretera, perfil `driving`); no se restringe explícitamente a vías nacionales. El servidor público
  (`router.project-osrm.org`) es de uso razonable y sin garantías; en producción conviene alojar OSRM propio.
- Solo cuentan para optimizar las empresas, plantas y rutas con `activa=true`.
- **Errores 400**: `{"detail": "...", "errores": [...] | {campo: [...]}}`. Un resultado `INFEASIBLE` del LP se devuelve con 200.
- **Límites de tamaño** (`OPTIAGRO_*`, ver `.env.example`): 200 empresas, 50 plantas, 2000 rutas, población AG <= 300,
  generaciones <= 1000, 40 escenarios de sensibilidad, `poblacion x generaciones x rutas x corridas <= 20.000.000`
  (~8 s) y, en escalabilidad, 8 tamaños y 60.000.000 de trabajo total. Se rechazan con 400.
- El AG solo admite el modo base (oferta exacta, plantas `capacity_max`); el exacto admite además `modo_oferta=maximum`
  y plantas `exact`/`minimum`.

### Algoritmo genético (`POST optimizacion/genetico/`, `config_ag` en reporte/sensibilidad)

| Parámetro | Rango / valores | Defecto |
|---|---|---|
| `poblacion` | 2..300 | 60 |
| `generaciones` | 1..1000 | 150 |
| `cruce` (prob. por pareja) | 0..1 | 0.8 |
| `mutacion` (prob. por gen) | 0..1 | 0.12 |
| `semilla` | 0..2^31-1 (misma semilla = mismo resultado) | 42 |
| `elitismo` | 0..poblacion-1 | 2 |
| `seleccion` | `torneo` \| `ruleta` | torneo |
| `tamano_torneo` | 2..poblacion | 3 |
| `tipo_cruce` | `un_punto` \| `dos_puntos` | un_punto |
| `inicializacion` | `aleatoria` \| `heuristica` | aleatoria |

Cromosoma = vector de prioridades (una por ruta); el decodificador recorre las rutas por prioridad y envía
`min(oferta restante, capacidad restante, límite)` (reparación: nunca excede capacidad ni límites).
**Aptitud** = `1 / (1 + costo_penalizado)` con `costo_penalizado = costo_total + lambda x violacion`, donde `violacion` son
las toneladas sin asignar (más excesos de capacidad/límite, siempre 0 tras la reparación) y
`lambda = 10 x (costo_ruta_max + 1) x (oferta_total + 1)`. La ruleta usa escalamiento por ventana
(`w = f - f_min + 0.05 (f_max - f_min)`) porque aptitudes como 1/65 y 1/67 casi no se distinguirían. `metricas` devuelve
`convergencia` (mejor costo por generación), `convergencia_promedio`, `aptitud_mejor`, `aptitud_promedio`, `factibles`,
`penalizacion`, `evaluaciones` y los parámetros usados. La mejor solución final prefiere factibles sobre infactibles.

### Sensibilidad (`POST optimizacion/sensibilidad/`)

`variaciones: [{tipo, ids, porcentajes}]` con `tipo` = `oferta` (global o por empresa), `capacidad` (una o varias plantas
a la vez; negativa = cuello de botella), `costo` (transporte de rutas `"E1->P2"`) o `combustible` (% sobre la tarifa km-ton).
Cada escenario se resuelve con el exacto y (por defecto, `incluir_ag=true`) con el AG. La respuesta incluye:

- `precios_sombra` (ofertas y capacidades) y `plantas` (utilización y cuello de botella).
- **`rangos`** (HiGHS `getRanging`, `highspy==1.11.0`): para cada oferta y capacidad el intervalo `[minimo, maximo]` del lado
  derecho, y para cada ruta el intervalo del costo efectivo, dentro de los cuales la base óptima no cambia (uno a la vez,
  `null` = sin límite), con el objetivo en cada extremo. Para restricciones inactivas el rango se calcula analíticamente
  (pueden subir sin límite y bajar hasta su actividad). En soluciones degeneradas son válidos pero pueden ser conservadores.
- `escenarios[]`: `costo_exacto`, `costo_ag`, `gap_pct`, `tiempo_exacto_ms`, `tiempo_ag_ms`, `estado_exacto`, `estado_ag`,
  `cambios_asignacion` (ruta, base, escenario, delta), `base_cambio` (la base óptima de HiGHS cambió frente al caso base),
  `dentro_de_rango` (si mueve un solo parámetro: el nuevo valor cae dentro del rango).
- `resumen`: factibles, gap % promedio/máximo, tiempos totales y número de escenarios con cambio de base/asignación.

Con los datos demo (40 rutas) una sensibilidad de 9 escenarios con AG tarda ~2 s. Para redes grandes reduzca
`config_ag` (población/generaciones) o `incluir_ag=false`.

### Escalabilidad (`POST optimizacion/escalabilidad/`)

`{tamanos: [{empresas, plantas}], config_ag, semilla_red, guardar}`. Por defecto 10x4, 20x6, 40x10 y 80x16 con
`poblacion=40`, `generaciones=80` e `inicializacion=heuristica`. Las redes son **sintéticas y FICTICIAS**, deterministas
(misma semilla y tamaño = misma red) y no se guardan. Devuelve por tamaño: rutas, exacto y AG (estado, costo, tiempo),
`gap_pct` y `ratio_tiempo`. Medido en el contenedor: ~2.4 s en total con los tamaños por defecto.

## Migraciones

Versionadas en `*/migrations/` (reversibles). Tras cambiar modelos:

```powershell
docker compose run --rm -v "${PWD}/backend:/app" backend python manage.py makemigrations
```
