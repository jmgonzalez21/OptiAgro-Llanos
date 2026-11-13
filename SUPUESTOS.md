# Supuestos y limitaciones

## Datos

- El documento docente no aporta ofertas, capacidades, distancias ni costos regionales completos. Los datos de demo
  (`cargar_demo`, `POST /demo/cargar/`, `OPTIAGRO_CARGAR_DEMO`) son explícitamente **ficticios** (`ficticio=true`), y las
  ejecuciones que los usan se marcan con `incluye_ficticios`. Las redes de la prueba de escalabilidad son sintéticas y ficticias.

## Modelo

- Modo BASE por defecto: oferta obligatoria (`=`) y capacidad máxima por planta (`<=`). Cada planta puede configurarse
  como demanda exacta o mínima (solo el LP); el AG implementa únicamente el modo base para no reportar factibilidad errónea.
  Este supuesto requiere ratificación académica.
- **Costos del negocio.** El costo efectivo de una ruta (COP/t) es
  `transporte + costo_operacion_ton de la planta + precio_tonelada de la empresa`, con
  `transporte = distancia_km x tarifa_km_ton` (o el `costo_unitario` directo). Ambos adicionales valen 0 por defecto:
  el modelo clásico (CP-01 = 64) no cambia. En el modo base el precio por tonelada es constante en el objetivo (se retira
  toda la oferta) y solo influye con `modo_oferta=maximum`; se incluye porque el enunciado habla de "precio de la tonelada".
  Es un supuesto de modelado pendiente de validar con la empresa.
- **Nodos de paso (transbordo) NO implementados.** El enunciado los menciona "si aplica". Se decidió no implementarlos
  porque (1) la red base son rutas directas empresa -> planta con distancia y tarifa por arco, sin centros de acopio
  intermedios en las fuentes disponibles; (2) transbordo exige pasar de un problema de transporte a flujo de costo mínimo
  (conservación de flujo en nodos intermedios, capacidades de nodo), lo que cambia la verificación, el AG (cromosoma de
  rutas en vez de prioridades) y la interpretación de los precios sombra; y (3) una ruta indirecta puede modelarse hoy
  sumando sus tramos en un único arco directo. El modelo queda extensible: `Ruta` ya es un arco dirigido con costo y
  límite, y bastaría añadir un tipo de nodo "paso" y las restricciones de conservación en `MetodoExacto`.
- Moneda COP, unidad toneladas por semana (validado en `optimizacion/validacion.py`).

## Algoritmo genético

- Cromosoma de prioridades por ruta con decodificador que repara (nunca excede oferta, capacidad ni límites).
  Aptitud = `1 / (1 + costo_total + lambda x toneladas_sin_asignar)`; `lambda = 10 x (costo_max + 1) x (oferta_total + 1)`.
  La ruleta usa escalamiento por ventana. Selección `torneo|ruleta`, cruce `un_punto|dos_puntos`, elitismo y semilla
  reproducible. La inicialización `heuristica` (parte de la población sesgada hacia rutas baratas) es opcional; la
  línea base es `aleatoria`. Con redes grandes y poco presupuesto el AG aleatorio se aleja del óptimo (gap de decenas de %
  en 25x8 o más); es el comportamiento esperado de una metaheurística y se informa en el reporte.
- Los límites de trabajo del AG (`OPTIAGRO_AG_MAX_TRABAJO`) son una estimación de tiempo (~0.4 microsegundos por
  unidad en el contenedor de desarrollo); en otro hardware ajuste el valor.

## Sensibilidad

- Los precios sombra salen del LP (duales). Los **rangos de variación** (oferta, capacidad y costo de ruta, uno a la vez,
  sin cambiar la base óptima) se obtienen con `Highs.getRanging` (`highspy==1.11.0`); para restricciones inactivas se
  calculan analíticamente. En soluciones degeneradas los rangos son válidos pero pueden ser conservadores. Se validan con
  CP-01 (óptimo 64), con un caso calculado a mano (planta P1 con capacidad 11: rango [10, 12]) y reoptimizando dentro y fuera
  del rango (la base de HiGHS cambia solo fuera).
- Los escenarios (combustible = % sobre la tarifa km-ton; oferta global o por empresa; capacidad de una o varias plantas;
  costo de ruta) se resuelven con exacto y AG. "La base cambió" compara la base óptima de HiGHS (estado de variables y
  restricciones) con la del caso base; en degeneración puede haber cambio de base sin cambio de asignaciones.
- Una ruta con costo unitario directo (sin distancia ni tarifa) se trata como costo de transporte y también se escala
  con el escenario de combustible.

## Seguridad y operación

- Una sola aplicación presentada (SPA). El admin de Django está apagado por defecto (`OPTIAGRO_ADMIN_HABILITADO=false`).
- JWT: access 30 min, refresh 24 h con rotación y lista negra; contraseña mínima de 10 caracteres.
- HU-01 a HU-03, HU-53 y despliegue de HU-55 de la versión Streamlit original quedaron superadas por la arquitectura web
  con autenticación y API REST.
