# OptiAgro-Llanos — Guía para agentes

Sistema de optimización de la red logística de residuos agropecuarios (EcoResiduos del Llano S.A.S., Meta).
Proyecto final de Optimización, Universidad de los Llanos 2026-II. Idioma del código de dominio y de la UI: **español**.

## Arquitectura objetivo

```
backend/    Django 5.2 LTS + Django REST Framework + SimpleJWT   (Python 3.12 en Docker)
frontend/   Vue 3 + Vite + TypeScript + Pinia + Vue Router
db          PostgreSQL 16 (contenedor propio, volumen persistente)
docs/api/   openapi.yaml = CONTRATO entre backend y frontend
docker-compose.yml  -> servicios: db, backend, frontend
```

Regla de separación: el frontend **solo** habla con el backend por la API REST (`/api/v1/`). Nunca importa código Python ni toca la BD.

## Núcleo de optimización (se conserva, es Python puro)

- `dominio/` y `optimizacion/` (método exacto con HiGHS vía `scipy.optimize.linprog`, y algoritmo genético) se mueven a `backend/` casi sin cambios. **No dependen de Django.** Mantenerlos así: Django solo los invoca desde la capa de servicios.
- Modo base: oferta exacta (`=`) y plantas con capacidad máxima (`<=`). El LP admite además demanda exacta/mínima; el AG solo el modo base.
- Los precios sombra (duales) salen del LP. Los rangos de sensibilidad se calculan **re-optimizando escenarios** (linprog no entrega ranging de base).

## Requisitos del PDF del proyecto (no perder de vista)

1. Red como grafo dirigido: 10 agroempresas → 4 plantas (Villavicencio, Restrepo, Granada, Puerto Gaitán), arcos con distancia y costo por km-tonelada. Nodos de paso "si aplica".
2. Modelo de transporte LP exacto + validación de que la solución cumple todas las restricciones.
3. AG: cromosoma, fitness penalizado por violar capacidad, selección (torneo/ruleta), cruce 1–2 puntos, mutación; población, generaciones, tasas de cruce y mutación **ajustables desde la interfaz**.
4. UI: editar dinámicamente matrices de costos, ofertas, demandas; **ampliar** empresas y sedes; análisis de sensibilidad (cambios en combustible/transporte, % de oferta, cuellos de botella en plantas); precios sombra y rangos.
5. Reporte comparativo exacto vs AG: costo, tiempo, **gap %**, y comportamiento bajo los escenarios de sensibilidad.
6. Entregables: código en Git modularizado con instrucciones de ejecución; informe IEEE; sustentación en vivo.

## Autenticación

- **Decisión del cliente: una sola aplicación.** Todo (nodos, rutas, matriz de costos, usuarios, optimización, sensibilidad, reportes) se gestiona desde la SPA Vue. El admin de Django queda **apagado por defecto** (`OPTIAGRO_ADMIN_HABILITADO=false`) y solo sirve como respaldo de emergencia; no forma parte de lo que se presenta.
- API: JWT (access + refresh) con SimpleJWT. Roles: `administrador` (CRUD de nodos/rutas/usuarios, matriz de costos) y `analista` (ejecuta escenarios, lectura de la red). Todo endpoint salvo `/api/v1/auth/login/` y `/api/v1/auth/refresh/` exige autenticación.
- El primer administrador se crea por línea de comandos (`crear_usuarios_demo` u otro comando); después todo se hace desde la SPA.
- Frontend: login, token en Pinia, *route guards* por rol. Nunca guardar contraseñas ni secretos en el repo; usar `.env` (ignorado por git).

## Agentes (en `.claude/agents/`)

- `backend`: trabaja solo en `backend/`, `docker-compose.yml`, `docs/api/`.
- `frontend`: trabaja solo en `frontend/` (vistas, router, stores, cliente HTTP). Consume `docs/api/openapi.yaml`.
- `ux`: solo documentos en `docs/ux/` (usuarios, flujos, wireframes, textos, accesibilidad). No escribe código.
- `ui`: sistema de diseño en `frontend/src/styles/`, `frontend/src/components/ui/` y `docs/ui/`. No toca vistas ni lógica.
- `qa`: escribe y ejecuta pruebas; reporta fallos; **no modifica código de producción**.

Flujo de diseño: `ux` especifica → `ui` construye el sistema visual y los componentes base → `frontend` arma las pantallas con ellos.

Si un cambio de API es necesario, se actualiza primero `docs/api/openapi.yaml` y luego se implementa a ambos lados.

## Convenciones

- Commits solo cuando el usuario lo pida. Sin `--no-verify`.
- Datos de demostración son ficticios y deben estar marcados como tales; los datos reales viven solo en la BD.
- Sin secretos en el repositorio. `DEBUG=False` por defecto en producción.
