# Plan y trazabilidad

## Modelo implementado

Red dirigida bipartita `I x J`, variable continua `x_ij >= 0`, objetivo `min sum c_ij x_ij` con
`c_ij = transporte + operación de la planta j + precio de la empresa i`. En el modo base, `sum_j x_ij = s_i` y
`sum_i x_ij <= d_j`; se admiten demanda exacta y mínima en el motor exacto. Los arcos son configurables y pueden tener límite.

## Trazabilidad de los requisitos del PDF

| Requisito | Implementación | Pruebas |
|---|---|---|
| 1. Red como grafo dirigido (10 agroempresas, 4 plantas, distancia y costo km-ton; nodos de paso "si aplica") | `backend/red/` (Empresa, Planta, Ruta), matriz de costos; nodos de paso: no implementados, justificado en `SUPUESTOS.md` | `test_api_red.py`, `test_comandos.py` |
| 2. Modelo de transporte LP + validación de restricciones | `optimizacion/metodo_exacto/solver.py`, `optimizacion/validacion.py` | `test_optimizacion.py` (CP-01 = 64), `test_nucleo_ag_costos_ranging.py` |
| 3. AG: cromosoma, fitness penalizado, selección torneo/ruleta, cruce 1-2 puntos, mutación; parámetros ajustables | `optimizacion/algoritmo_genetico/` (`ConfigAG`), `POST optimizacion/genetico/` | `test_nucleo_ag_costos_ranging.py`, `test_api_fase2.py` |
| 4. UI: editar matrices, ofertas, demandas; ampliar empresas y sedes; sensibilidad con precios sombra y rangos | API CRUD + `PUT red/matriz-costos/`; `POST optimizacion/sensibilidad/` (rangos con HiGHS); SPA en `frontend/` | `test_api_red.py`, `test_api_fase2.py` |
| 5. Reporte comparativo exacto vs AG (costo, tiempo, gap %) y escenarios | `POST optimizacion/reporte/`, `resumen` de sensibilidad, `POST optimizacion/escalabilidad/` | `test_api_optimizacion.py`, `test_api_fase2.py` |
| 6. Entregables: Git modularizado con instrucciones, informe IEEE, sustentación | `README.md`, `backend/README.md`, `docker-compose.yml` (una sola entrada); el informe IEEE y la sustentación están fuera del código | verificación desde cero con `docker compose down -v && docker compose up -d --build` |
| Transversal: usuarios y roles | `/api/v1/usuarios/`, `auth/*` (login, refresh rotativo, logout, cambio de contraseña, perfil) | `test_usuarios.py`, `test_api_auth.py` |

## Estado de la Fase 2 del backend

Completado: gestión de usuarios y sesión; admin de Django apagado; AG completo; sensibilidad con rangos y escenarios
exacto + AG; modelo de costos (operación y precio); escalabilidad; Docker de una sola entrada; carga demo desde la API;
historial con `incluye_ficticios` y filtros por fecha. Pendiente: informe IEEE, sustentación, integración final de la SPA
con los nuevos endpoints (`docs/api/openapi.yaml`) y arreglo del error de tipos de `frontend/src/components/ui/formato.ts`
que hace fallar `npm run typecheck`.

Los vacíos y conflictos se registran en `SUPUESTOS.md`.
