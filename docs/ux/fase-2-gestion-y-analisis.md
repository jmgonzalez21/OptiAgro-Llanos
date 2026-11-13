# Fase 2 — Gestión de la red y análisis (una sola aplicación)

Especificación UX para `ui` (componentes y gráficos) y `frontend` (pantallas). Continúa `fase-1-login-home.md` (shell, login, mapa) y usa los tokens de `docs/ui/guia-de-estilo.md`. Idioma: español (Colombia). Contrato de datos: `docs/api/openapi.yaml`; lo que el backend aún está ampliando se marca **(previsto)** y está resumido en la sección 17.

**Decisión del cliente que gobierna esta fase:** no existe panel de administración de Django para el cliente. Todo (red, costos, usuarios, análisis) se gestiona desde la SPA.

## 0. Cambios sobre la Fase 1 (obligatorios)

| Fase 1 | Fase 2 |
|---|---|
| Enlace "Panel de administración" en el menú de perfil (admin) | **Se elimina.** No hay `/admin/` en la experiencia. |
| Estado vacío del mapa (admin): "Gestionar en el panel de administración" | Botón **"Ir a Red logística"** (navega a `/red?tab=empresas`) y botón secundario **"Agregar empresa"** (abre el panel de creación). Analista: solo el texto informativo. |
| Nota de estaciones sin ubicación (admin): "Agrega las coordenadas en el panel de administración" | "Agrega las coordenadas en Red logística." y, en cada fila de la lista, botón **"Agregar ubicación"** que abre el panel de edición de esa estación (`/red?tab=…&editar=<id>`). Analista: sin acción. |
| Ítems "Próximamente": Red logística, Escenarios, Optimización, Sensibilidad, Reportes | Pasan a ser **reales** (sección 2). "Escenarios" se reemplaza por **"Matriz de costos"**; los escenarios guardados se gestionan como "base de cálculo" (ver decisión D1). |
| "Mi perfil" deshabilitado | Habilitado (sección 11). |
| Fase 1 §4 (gestión en Django admin) | Obsoleto. Ver matriz de permisos (sección 3). |
| Decisión Fase 1 n.º 2 (periodo) | Resuelta por el contrato: **toneladas por semana (t/semana)** y costos en **COP**. Confirmar (D2). |
| Decisión Fase 1 n.º 1 (login) | El contrato usa `username`: etiqueta "Usuario". |
| Etiqueta "Datos de demostración" | Se gobierna por el campo `ficticio` de los datos (sección 14.3), no por el modo mock. |

Criterios de Fase 1 reemplazados: n.º 10 (ítems Próximamente), n.º 14 (menú de perfil), n.º 25 y 26 (acciones del administrador en estados vacío/sin ubicación). Los demás siguen vigentes.

## 1. Personas

| | **Administrador** (Camila, coordinadora logística) | **Analista** (Andrés, analista de operaciones) |
|---|---|---|
| Objetivo | Mantener la red al día (empresas, plantas, rutas, costos) y los accesos del equipo. | Responder "¿cuánto cuesta, qué pasa si…?" y llevar resultados defendibles a gerencia. |
| Tareas | Crear/editar/desactivar nodos y rutas; ampliar la red; editar la matriz de costos; gestionar usuarios; también ejecuta análisis. | Ejecutar exacto y AG; construir escenarios de sensibilidad; generar el reporte comparativo; consultar y comparar el historial. Consulta la red sin modificarla. |
| Frustraciones | Perder cambios por no guardar; romper la red al borrar un nodo; no saber qué rutas faltan al agregar una sede. | No entender el resultado ("¿por qué este costo?"); esperar sin saber qué pasa; no poder repetir una ejecución; tablas ilegibles. |
| Necesita ver | Impacto de cada cambio antes de confirmar. | Costo, tiempo y gap lado a lado; qué planta limita el costo; si el AG cumplió las restricciones. |

Trazabilidad: roles de CLAUDE.md (Autenticación); requisito 4 del PDF (editar matrices, ofertas, demandas; ampliar empresas y sedes; sensibilidad); requisito 5 (reporte comparativo).

## 2. Arquitectura de información y navegación

### 2.1 Mapa de pantallas

| Ruta | Pantalla | Admin | Analista | Requisito |
|---|---|---|---|---|
| `/` | Inicio (mapa) | Ver | Ver | Req. 1 |
| `/red?tab=empresas\|plantas\|rutas` | Red logística | Ver y escribir | Solo lectura | Req. 1, 4 |
| `/matriz` | Matriz de costos | Ver y escribir | Solo lectura | Req. 4 |
| `/optimizacion` | Optimización | Ejecutar | Ejecutar | Req. 2, 3 |
| `/sensibilidad` | Sensibilidad | Ejecutar | Ejecutar | Req. 4 |
| `/reportes` | Reporte comparativo | Generar | Generar | Req. 5 |
| `/historial`, `/historial/:id`, `/historial/comparar?a=&b=` | Historial | Todas las ejecuciones | Solo las propias | Req. 5 |
| `/usuarios` | Usuarios | Sí | No (403) | Autenticación |
| `/perfil` | Mi perfil | Sí | Sí | Autenticación |

### 2.2 Sidebar (reemplaza el de Fase 1)

Grupos con rótulo (visibles expandido; colapsado se muestran como separador con `aria-label` del grupo). Cada ítem: icono + texto; activo = fondo menta + barra de 3 px + peso mayor (Fase 1 §2.2). Ya no hay ítems deshabilitados.

```
┌────────────────┐
│ [logo]         │
│ OptiAgro-Llanos│
│▌◉ Inicio       │
│ RED            │   <- rótulo de grupo (h2 visualmente pequeño, no enlace)
│  ◌ Red logística│
│  ◌ Matriz de   │
│    costos      │
│ ANÁLISIS       │
│  ◌ Optimización│
│  ◌ Sensibilidad│
│  ◌ Reportes    │
│  ◌ Historial   │
│ ADMINISTRACIÓN │   <- solo administrador (no se renderiza para analista)
│  ◌ Usuarios    │
│ [‹] Contraer   │
│ v0.2           │   <- sin "Datos de demostración" (ver 14.3)
└────────────────┘
```

- El ítem "Usuarios" y su grupo **no se renderizan** para el analista (no es una función disponible para su rol); la URL directa muestra la pantalla 403 de Fase 1 §4.
- Menú de perfil: cabecera (nombre, usuario, rol) · **Mi perfil** · **Guía de sustentación** · separador · **Cerrar sesión**. Sin "Panel de administración".
- Barra superior: `h1`, contexto, **chip "Datos de demostración"** (solo si aplica, ver 14.3) y avatar. Migas de pan (`Inicio / Red logística / Plantas`) solo en `/historial/:id` y `/historial/comparar`.
- Ayuda consistente (WCAG 3.2.6): cada pantalla tiene en el mismo lugar (arriba a la derecha del título) un enlace "¿Cómo funciona?" que abre un panel breve con la explicación y el glosario de esa pantalla.
- Persistencia entre pantallas: los últimos resultados de la sesión (exacto, AG, sensibilidad, reporte) se conservan en memoria para no perderlos al navegar; se rotulan "Resultado de esta sesión · hh:mm".

## 3. Matriz de roles y permisos

| Pantalla / acción | Administrador | Analista |
|---|---|---|
| Ver mapa (Inicio) | Sí | Sí |
| Ver empresas, plantas, rutas | Sí | Sí (solo lectura) |
| Crear, editar, activar/desactivar, eliminar empresa/planta/ruta; ampliar la red | Sí | No (botones no se renderizan) |
| Ver matriz de costos y cambiar de capa | Sí | Sí |
| Editar y guardar la matriz | Sí | No (cuadrícula `aria-readonly`, aviso "Solo lectura") |
| Guardar red actual como escenario | Sí | Sí |
| Ejecutar exacto, AG, sensibilidad, reporte | Sí | Sí |
| Cargar datos de demostración (previsto) | Sí | No |
| Historial: ver y abrir | Todas | Solo las propias (el filtro "Usuario" no aparece) |
| Historial: comparar dos ejecuciones | Sí | Sí (entre las que ve) |
| Eliminar escenario guardado | Cualquiera | Solo los propios |
| Usuarios (listar, crear, editar, rol, activar, restablecer contraseña) | Sí | No (ítem oculto, URL → 403) |
| Mi perfil, cambiar contraseña propia | Sí | Sí |

Regla de renderizado: lo que el rol no puede hacer **no se muestra** (botones de escritura); lo que sí puede ver pero no editar se muestra en solo lectura con una nota informativa ("Solo lectura: tu rol Analista no puede modificar la red."). El backend sigue siendo la autoridad: un 403 en una acción muestra "No tienes permiso para esta acción." (nunca un error genérico).

## 4. Convenciones comunes

### 4.1 Terminología y unidades (usar siempre así)

| Término en pantalla | Significado | Unidad |
|---|---|---|
| Empresa agropecuaria / empresa | Fuente de residuos | — |
| Planta (sede de procesamiento) | Destino. Al ampliar: "sede" | — |
| Ruta | Camino empresa → planta (arco) | — |
| **Oferta** | Residuo que genera una empresa | t/semana |
| **Capacidad** | Máximo que procesa una planta | t/semana |
| Tipo de demanda | Capacidad máxima (≤) · Demanda exacta (=) · Demanda mínima (≥) | — |
| Distancia | De la ruta | km |
| Tarifa | Costo de transportar 1 t por 1 km | COP por t·km |
| **Costo unitario** (de la ruta) | Costo de mover 1 t por esa ruta = distancia × tarifa, o valor directo | COP por t |
| Costo de operación (previsto) | Costo de procesar 1 t en una planta | COP por t |
| Límite de ruta | Máximo que puede circular por la ruta | t/semana |
| **Costo total** | Valor de la solución | COP/semana |
| **Precio sombra** | Cuánto cambia el costo total por cada tonelada adicional de capacidad (planta) u oferta (empresa) | COP por t (por semana) |
| **Gap %** | (AG − exacto) / exacto × 100: qué tan por encima del óptimo quedó el AG; 0 % = igual de bueno | % |
| Método exacto | Programación lineal (HiGHS); da el óptimo | — |
| Algoritmo genético (AG) | Búsqueda aproximada; ajustable | — |
| Cuello de botella | Planta llena que, de ampliarse, bajaría el costo | — |
| Base óptima | El plan de rutas óptimo; "cambió" = el plan es distinto | — |

Evitar en pantalla: "dual", "LP", "RHS", "HiGHS" (solo en "Detalle técnico" plegado), "cromosoma", "fitness" (usar "costo con penalización").

### 4.2 Formatos (es-CO)

- Miles con punto, decimales con coma: `1.234.567`; moneda `$ 1.234.567 COP` (en tablas la unidad va en el encabezado y la celda lleva solo el número; fuera de tablas `$ 1.234.567`). Toneladas `120 t` (`1.250,5 t`). Porcentaje `4,2 %` (espacio fino). Signo explícito en variaciones: `+4,2 %`, `−3,0 %` (signo menos U+2212).
- Tiempo: `< 1 ms`, `12 ms`, `1,4 s`, `1 min 12 s`.
- Cifras alineadas a la derecha con `font-variant-numeric: tabular-nums`; sin abreviar (no "1,2M") en tablas; en gráficos se admite "1,2 M" con la cifra exacta en el tooltip/tabla.
- Entrada numérica (`UiNumberInput`): acepta `12500`, `12.500`, `12.500,5`; rechaza `1.5` con "Usa coma para decimales, por ejemplo 1,5."; teclado `inputmode="decimal"`; pegar permitido.
- Fechas: `12 nov 2026, 14:35` (hora local; `<time datetime>`).

### 4.3 Validación en línea (patrón único)

Igual a Fase 1 §1.4: se valida al salir del campo y al enviar; tras el primer error, mientras se corrige. Mensaje bajo el campo (`aria-describedby`, `aria-invalid`), icono + texto. Al enviar con errores: resumen `role="alert"` ("Corrige 2 campos para continuar") y foco al primer inválido. Errores 400 del servidor (`{detail, errores}`) se asignan al campo por nombre; los que no tienen campo van a la alerta del formulario. El botón de envío no se deshabilita por campos vacíos.

### 4.4 Estados comunes (todas las pantallas usan `UiEmptyState`/`UiAlert`/`UiSkeleton`)

| Estado | Regla |
|---|---|
| Cargando | Esqueleto con la forma final; `role="status"` "Cargando …"; no mover el layout al llegar los datos. |
| Vacío | Icono, título, una frase, **una** acción primaria (solo si el rol puede). |
| Sin resultados (filtros/búsqueda) | "No hay … con los filtros elegidos." + "Limpiar filtros". |
| Error (red/5xx) | "No pudimos cargar …" + "Reintentar" (`role="alert"`); lo ya cargado se conserva. |
| Sin permisos (403) | "No tienes permiso para ver esta página." + "Volver al inicio". En acción: "No tienes permiso para esta acción." |
| No encontrado (404) | "Este elemento ya no existe." + volver a la lista. |
| Sesión expirada (401) | Redirige al login con el aviso de Fase 1 §1.6; si hay cambios sin guardar en matriz, se guardan en `sessionStorage` y se ofrece restaurarlos tras volver a ingresar. |
| Ejecución en curso | Botón con spinner; texto "Calculando… 3 s"; tras 15 s: "Esto está tardando más de lo normal…". Un solo cálculo a la vez por pantalla. |
| INFEASIBLE | Sección 12. |

### 4.5 Confirmaciones de acciones destructivas o de alto impacto

| Acción | Confirmación | Texto del botón | Detalles |
|---|---|---|---|
| Eliminar empresa / planta | Diálogo con impacto y **escribir el código** para habilitar | "Eliminar empresa" / "Eliminar planta" (rojo) | Foco inicial en "Cancelar". Ver 5.6. |
| Eliminar ruta | Diálogo simple con impacto | "Eliminar ruta" (rojo) | |
| Desactivar empresa / planta / ruta | Diálogo con impacto (reversible) | "Desactivar" | Reactivar no pide confirmación. |
| Desactivar usuario, restablecer contraseña | Diálogo | "Desactivar usuario" / "Restablecer contraseña" | Sección 10. |
| Salir con cambios sin guardar (matriz, panel con edición) | Diálogo de 3 opciones | "Guardar y salir" · "Salir sin guardar" · "Seguir editando" | También `beforeunload`. |
| Descartar todos los cambios de la matriz | Diálogo | "Descartar N cambios" | |
| Eliminar escenario guardado | Diálogo | "Eliminar escenario" | |
| Ejecutar sensibilidad con AG y >30 escenarios | Aviso previo (no bloquea) | "Ejecutar de todos modos" | "Puede tardar varios minutos." |

Diálogos: `role="alertdialog"` para destructivas (`dialog` para el resto), `aria-modal`, foco atrapado, Esc cancela, título como nombre accesible, descripción vinculada, foco vuelve al disparador. Éxito: toast `role="status"` que se cierra a los 6 s (pausa con hover/foco; botón cerrar); los errores no usan toast desaparecible.

---

## 5. Red logística (`/red`)

**Propósito:** ver y gestionar los nodos y las rutas del grafo (Req. 1) y ampliar la red (Req. 4). **API:** `GET/POST /empresas/`, `/plantas/`, `/rutas/` y `/{id}/` (PATCH, DELETE); filtros `search`, `activa`, `ordering`, `page`, `page_size`; rutas además `empresa`, `planta`.

### 5.1 Layout

```
Red logística                                         ¿Cómo funciona?
Empresas, plantas y rutas de la red   [Datos de demostración]
10 empresas · 4 plantas · 40 rutas      [Ampliar la red ▾]  (solo admin)
┌ ⚠ Faltan 4 rutas por definir: Empresa E11 → 4 plantas. [Completar en la matriz] ┐
├────────────────────────────────────────────────────────────────────────────────┤
│ [Empresas 10] [Plantas 4] [Rutas 40]                      (tablist)             │
├────────────────────────────────────────────────────────────────────────────────┤
│ 🔍 Buscar por código, nombre o municipio  Estado:[Todas|Activas|Inactivas]      │
│                                              [+ Nueva empresa] (solo admin)     │
├──────┬──────────────┬───────────┬──────────────┬───────────┬────────┬─────┬────┤
│Código▲│Nombre        │Municipio  │Oferta (t/sem)│Ubicación  │Rutas   │Estado│ ⋮ │
├──────┼──────────────┼───────────┼──────────────┼───────────┼────────┼─────┼────┤
│E1    │Finca La Esp.  │Acacías    │        120,0 │ ✓         │ 4 de 4 │Activa│ ⋮ │
│E11   │Agro Nuevo [Demo]│Granada  │         80,0 │ ⚠ Sin ubic.│ ⚠ 0 de 4│Activa│ ⋮ │
├──────┴──────────────┴───────────┴──────────────┴───────────┴────────┴─────┴────┤
│ Mostrando 1–10 de 10                         Filas: [10 ▾]   ‹ 1 2 ›            │
└────────────────────────────────────────────────────────────────────────────────┘
```

- Pestañas: patrón WAI-ARIA tabs (flechas ←/→, Home/End; activación automática; el panel conserva búsqueda y filtros por pestaña). La pestaña activa se refleja en la URL `?tab=`. Cada pestaña muestra su conteo.
- Chip "Demo" por fila cuando `ficticio=true` (texto "Demostración", no solo color).
- Fila clicable abre el panel (admin: edición; analista: detalle de solo lectura). Menú de acciones por fila (`⋮`, nombre accesible "Acciones de E1 Finca La Esperanza"): **Editar**, **Activar/Desactivar**, **Eliminar** (rojo, al final). Analista: sin columna de acciones; la fila abre "Ver detalle".
- Columnas ordenables con botón en el encabezado (`aria-sort`, icono + estado anunciado). Por defecto: código ascendente.
- Búsqueda con retardo de 300 ms; el conteo se anuncia (`aria-live="polite"`: "7 resultados").
- Responsive: <768 px la tabla pasa a **tarjetas apiladas** (nombre, 3 datos clave, estado, menú); las columnas secundarias se ocultan, no se pierden (están en el detalle).

### 5.2 Columnas por pestaña

| Pestaña | Columnas (· = solo ≥1024 px) |
|---|---|
| Empresas | Código · Nombre · Municipio · **Oferta (t/semana)** · Ubicación · **Rutas** ("4 de 4"; aviso si faltan) · Estado · Acciones |
| Plantas | Código · Nombre · Municipio · **Capacidad (t/semana)** · Tipo de demanda · **Costo de operación (COP/t)** (previsto) · Ubicación · Rutas · Estado · Acciones |
| Rutas | **Empresa** · **Planta** · Distancia (km) · Tarifa (COP/t·km) · **Costo unitario (COP/t)** (con nota "calculado" o "directo") · Límite (t/semana) · Estado · Acciones. Filtros extra: Empresa, Planta (selects). |

"Rutas: 4 de 4" = rutas activas definidas hacia plantas activas / plantas activas. Se calcula en el cliente con `rutas?empresa=`. Estado: badge "Activa" (verde, punto) / "Inactiva" (neutro, tachado suave + texto).

### 5.3 Panel lateral de crear/editar

Panel derecho de 480 px (`role="dialog"`, `aria-modal="true"`, foco atrapado, título "Nueva empresa" / "Editar planta Granada"); en <768 px ocupa toda la pantalla. Cabecera con título y "×"; pie fijo con **Guardar** (primaria) y **Cancelar**. Esc o "×" con cambios → diálogo de 3 opciones (4.5). El pie fijo no debe tapar el campo enfocado (WCAG 2.4.11: `scroll-padding-bottom`).

**Empresa:** Código\* · Nombre\* · Municipio · Oferta (t/semana)\* · Ubicación (selector 5.4) · Estado (interruptor "Activa", por defecto sí).
**Planta:** Código\* · Nombre\* · Municipio · Capacidad (t/semana)\* · **Tipo de demanda**\* (lista: "Capacidad máxima — recibe hasta esa cantidad", "Demanda exacta — recibe exactamente esa cantidad", "Demanda mínima — recibe al menos esa cantidad") · **Costo de operación (COP por tonelada)** (previsto, opcional, por defecto 0) · Ubicación · Activa.
**Ruta:** Empresa\* y Planta\* (listas; solo pares sin ruta; si existe: "Ya existe una ruta E3 → Granada. Edítala en la matriz de costos." con enlace) · modo de costo (radio "Calcular desde distancia × tarifa" / "Ingresar costo directo") · Distancia (km) · Tarifa (COP por t·km) · Costo unitario (COP/t; calculado y de solo lectura en el primer modo) · Límite (t/semana, opcional: "Déjalo vacío si no hay límite") · Activa.

Datos ficticios: si el registro es `ficticio=true`, se muestra la nota "Este registro es de demostración." (solo lectura). Los nuevos se crean con `ficticio=false`.

### 5.4 Validación (textos)

| Campo | Regla | Mensaje |
|---|---|---|
| Código | Obligatorio; `^[A-Za-z0-9_]+$`; ≤20; único por tipo | "Ingresa un código." · "Usa solo letras, números y guion bajo (sin espacios ni tildes)." · "Máximo 20 caracteres." · "Ya existe una empresa con el código E3." (servidor) |
| Código en edición | Bloqueado (solo lectura) con ayuda "El código identifica a la empresa en rutas e historial y no se puede cambiar." (D5) | |
| Nombre | Obligatorio, ≤120 | "Ingresa el nombre." · "Máximo 120 caracteres." |
| Municipio | ≤80 | "Máximo 80 caracteres." |
| Oferta / Capacidad | Número **> 0** | "La oferta debe ser mayor que 0 t/semana." / "La capacidad debe ser mayor que 0 t/semana." · "Escribe un número, por ejemplo 120 o 1.250,5." |
| Latitud | −90 a 90 | "La latitud debe estar entre −90 y 90." |
| Longitud | −180 a 180 | "La longitud debe estar entre −180 y 180." |
| Lat/Lon | Ambas o ninguna | "Ingresa también la longitud." / "Ingresa también la latitud." |
| Lat/Lon fuera del Meta (aprox. lat 2,0–5,5; lon −75,5 a −71,0) | **Aviso, no error** | "Esta ubicación queda fuera del Meta. Verifica que sea correcta." |
| Costo de operación | ≥ 0 | "El costo de operación no puede ser negativo." |
| Tipo de demanda ≠ capacidad máxima | Aviso informativo | "El algoritmo genético solo funciona con capacidad máxima. Con este tipo solo se podrá ejecutar el método exacto." |
| Distancia / Tarifa / Límite | ≥ 0 | "No puede ser negativo." · distancia 0: aviso "Distancia 0 km: ¿es correcto?" · límite 0: "Un límite de 0 t/semana bloquea esta ruta." |
| Ruta sin costo | Debe haber costo directo o distancia y tarifa | "Ingresa el costo unitario o completa distancia y tarifa." |
| Oferta total > capacidad total tras guardar | Aviso en el toast de éxito | "La oferta total (1.320 t/semana) ahora supera la capacidad total (1.200). El método exacto quedará sin solución si se retira toda la oferta." |

### 5.5 Selector de ubicación (`UiSelectorUbicacion`)

```
Ubicación
┌─ Latitud ──────────┐ ┌─ Longitud ─────────┐
│ 4,15060            │ │ -73,63500          │     [Centrar en el Meta] [Quitar ubicación]
└────────────────────┘ └────────────────────┘
 Escribe las coordenadas en grados decimales o haz clic en el mapa.
┌────────────────────────────────────────────┐
│  (mapa Leaflet claro, 280 px de alto)      │  ● otras estaciones, tenues
│            ✚ marcador movible              │
└────────────────────────────────────────────┘
```

- Los campos numéricos son la vía principal y accesible; el mapa es una ayuda: clic/toque coloca o mueve el marcador y rellena los campos; arrastrar es opcional (alternativa sin arrastre = clic o campos, WCAG 2.5.7). Con el marcador enfocado, flechas lo mueven 0,001° (Mayús = 0,01°) y se anuncia "Latitud 4,151, longitud −73,635".
- Escribir en el campo actualiza el marcador y centra el mapa. Pegar `4.1506, -73.635` en Latitud reparte los dos valores.
- Mapa con `aria-label="Mapa para elegir la ubicación. También puedes escribir latitud y longitud."`; zoom +/−; mismo fondo CARTO Positron y atribución. Sin servicios externos de búsqueda de direcciones (privacidad).
- "Quitar ubicación" deja la estación "Sin ubicación" (no aparece en el mapa de Inicio; advertir en el toast).

### 5.6 Activar/desactivar y eliminar (con impacto)

El diálogo calcula el impacto en el cliente (rutas asociadas con `rutas?empresa=` / `?planta=`; totales con las listas ya cargadas).

**Desactivar empresa "Finca La Esperanza" (E1):**
> Título: "¿Desactivar «Finca La Esperanza»?"
> "Dejará de aparecer en el mapa y no se incluirá en las optimizaciones nuevas. Sus **4 rutas** se conservan, pero no se usarán. La oferta total activa baja de 1.320 a 1.200 t/semana. Puedes reactivarla cuando quieras."
> Botones: **Desactivar** · Cancelar.

**Desactivar planta (con aviso de capacidad):** "La capacidad total activa baja de 1.200 a 800 t/semana. **Las 10 empresas dejan de tener ruta a esta planta.**" Si la oferta total pasa a superar la capacidad total o si queda sin plantas activas: aviso `aviso` "Con este cambio el método exacto no tendrá solución mientras se retire toda la oferta."

**Eliminar empresa/planta (irreversible):**
> Título: "¿Eliminar definitivamente «Granada»?"
> "Se eliminarán también sus **10 rutas**. Desaparecerá del mapa, de la matriz de costos y de las próximas optimizaciones. Las ejecuciones guardadas conservan sus resultados. **Esta acción no se puede deshacer.**"
> "¿Solo quieres dejar de usarla? **Desactívala** en su lugar." (enlace que cambia al diálogo de desactivar)
> Campo: "Para confirmar, escribe el código **P3**" → habilita **Eliminar planta** (rojo). Foco inicial: Cancelar.

**Eliminar ruta:** "Se eliminará la ruta E3 → Granada (102.000 COP/t). Si la empresa queda sin rutas, el método exacto no tendrá solución." Sin escribir código.

Tras desactivar/eliminar: toast "Planta Granada desactivada. Ya no aparece en el mapa." La lista se actualiza sin recargar y el foco pasa a la fila siguiente (o a la tabla si era la última).

### 5.7 Flujo "Ampliar la red"

Disparadores: botón **"Ampliar la red"** (menú: "Agregar empresa", "Agregar planta (sede)", "Agregar ruta") y "Nueva empresa/Nueva planta" de cada pestaña. Solo administrador. Es un asistente de 3 pasos **dentro del mismo panel** (`UiStepper`, "Paso 2 de 3"); los datos no se piden dos veces (WCAG 3.3.7).

```
Paso 1 de 3 · Datos de la nueva empresa      (formulario de 5.3; botón "Guardar y definir rutas")
Paso 2 de 3 · Define las rutas hacia las 4 plantas
 Faltan 4 rutas por definir                                   [Copiar rutas de… ▾]
┌────────────────┬──────────────┬─────────────────┬────────────────┬─────────────┐
│ Planta         │ Distancia km │ Tarifa COP/t·km │ Costo COP/t    │ Límite t/sem│
│ Villavicencio  │ [  85 ]      │ [ 1.200 ]       │ 102.000 (calc.)│ [        ]  │
│ Restrepo       │ [     ]      │ [       ]       │ —              │ [        ]  │
│ Granada  ☐ Sin ruta        ...                                                  │
└────────────────┴──────────────┴─────────────────┴────────────────┴─────────────┘
 [Definir después]                          [Atrás]  [Guardar rutas]
Paso 3 de 3 · Resumen
 ✓ Empresa E11 agregada. Red: 11 empresas · 4 plantas · 44 rutas (40 definidas, 4 por definir)
 [Ejecutar optimización con la red ampliada]   [Agregar otra]   [Cerrar]
```

- Paso 1 crea el nodo (POST). Paso 2 guarda las rutas con **una sola** actualización atómica de la matriz (`PUT /red/matriz-costos/`). Si falla, no se guarda ninguna y el nodo creado se conserva (se avisa).
- Contador vivo "Faltan N rutas por definir" (`aria-live="polite"`); una ruta cuenta como definida si tiene costo (directo o distancia × tarifa) o está marcada "Sin ruta" a propósito (casilla).
- "Copiar rutas de…" (lista de empresas/plantas del mismo tipo) rellena distancia y tarifa como punto de partida editable.
- **"Definir después"**: el nodo queda con insignia ámbar "Faltan N rutas" en su fila, el banner de la cabecera de Red logística y un chip en la matriz; el análisis advierte que una empresa sin rutas hace infactible la oferta exacta.
- Agregar una **planta** es simétrico: el paso 2 lista las empresas (10 filas); con 10 empresas se ofrece "Aplicar la misma tarifa a todas" para acelerar.
- Agregar una **ruta suelta** va por la pestaña Rutas (5.3) o directamente en la matriz.
- Resumen (paso 3) con los nuevos conteos de empresas, plantas y rutas, y accesos a "Ver en la matriz" y "Ver en el mapa".

### 5.8 Estados específicos

| Estado | Contenido |
|---|---|
| Vacío (sin empresas) | "Aún no hay empresas en la red." Admin: **"Agregar empresa"**; (previsto) **"Cargar datos de demostración"**. Analista: "El administrador debe agregar empresas." |
| Sin resultados | "No hay empresas con los filtros elegidos." + "Limpiar filtros". |
| Error | "No pudimos cargar las empresas." + "Reintentar". |
| Guardar falló (400) | Errores en línea; panel abierto; foco al primer error. |
| Conflicto de código | "Ya existe una empresa con el código E3." en el campo. |
| 403 al guardar | Alerta en el panel: "No tienes permiso para modificar la red." |

---

## 6. Matriz de costos (`/matriz`)

**Propósito:** editar los costos de transporte empresa × planta, con límites por ruta, y que la matriz pueda crecer (Req. 4). **API:** `GET /red/matriz-costos/` (`empresas`, `plantas`, `costos`, `rutas[{distancia_km, tarifa_km_ton, costo_unitario, limite, activa}]`); `PUT /red/matriz-costos/` (masivo y **atómico**: si una celda es inválida no se aplica ninguna).

### 6.1 Layout

```
Matriz de costos                                                 ¿Cómo funciona?
Costo de transportar 1 tonelada de cada empresa a cada planta (COP por tonelada)
┌ Ver: (Costo COP/t) ( Distancia km ) ( Tarifa COP/t·km ) ( Límite t/semana ) ┐
│ ☐ Mapa de calor  ☐ Marcar la ruta más barata de cada empresa  ☐ Mostrar inactivas│
│ 🔍 Buscar empresa o planta     Rutas definidas 40 de 40      [Guardar como escenario…]│
├──────────────────────┬────────────┬────────────┬────────────┬────────────┤
│ Empresa ╲ Planta     │ P1 Villav. │ P2 Restr.  │ P3 Granada │ P4 P.Gait. │
│                      │ cap 400 t  │ cap 300 t  │ cap 350 t  │ cap 150 t  │
│                      │ +op 8.000/t│ +op 6.500/t│ +op 7.000/t│ +op 9.000/t│
├──────────────────────┼────────────┼────────────┼────────────┼────────────┤
│ E1 Finca La Esp.     │   102.000  │    85.000  │  ◢ 98.500  │ ● 64.000   │
│ oferta 120 t         │            │            │ (modificada)│ (más barata)│
│ E2 …                 │     …      │  Sin ruta  │     …      │     …      │
│ E11 Agro Nuevo  ⚠    │  Sin ruta  │  Sin ruta  │  Sin ruta  │  Sin ruta  │
└──────────────────────┴────────────┴────────────┴────────────┴────────────┘
┌ barra fija inferior ───────────────────────────────────────────────────────┐
│ ● 3 cambios sin guardar   [↶ Deshacer] [↷ Rehacer] [Descartar] [Guardar cambios (3)] │
└────────────────────────────────────────────────────────────────────────────┘
```

- **Capas** (control segmentado, un valor numérico por celda en cada capa; un solo `input` por celda mantiene la cuadrícula accesible y escalable):
  - **Costo (COP/t)**: costo unitario efectivo (`costo_unitario`). Si la ruta tiene distancia y tarifa, la celda muestra el valor calculado y un indicador `ƒ` ("calculado: distancia × tarifa"). Editarlo directamente la vuelve "directa" (se borran distancia y tarifa); se avisa una vez con una nota en línea "Editar el costo directamente borra la distancia y la tarifa de esta ruta."
  - **Distancia (km)** y **Tarifa (COP/t·km)**: editables; el costo se recalcula al instante (vista previa) y se ve en la capa Costo.
  - **Límite (t/semana)**: máximo por arco; vacío = "Sin límite".
  Vista "distancia × tarifa" = capas Distancia y Tarifa; vista "costo total" = capa Costo. Un panel lateral de celda seleccionada (opcional, ≥1280 px) muestra los 4 valores de la ruta seleccionada.
- **Encabezados** (fijos al desplazar): fila = código + nombre + oferta (t/semana); columna = código + nombre + capacidad (t/semana) + costo de operación de la planta (solo lectura, "se edita en Red logística", previsto). Casilla "Mostrar costo total por tonelada (transporte + operación)" cambia la capa Costo a vista de solo lectura sumando la operación de la planta (D6).
- **Estados de celda** (nunca solo color): *Con ruta* (número); *Calculada* (número + `ƒ`); *Modificada* (triángulo en la esquina + negrita + etiqueta accesible "modificada, antes 98.000"); *Inválida* (borde de error + icono + mensaje); *Sin ruta* (texto tenue "Sin ruta", borde punteado; escribir un número la crea); *Inactiva* (rayado + "Inactiva", valor atenuado visible); *Más barata de su fila* (opcional, ● + negrita); *Mapa de calor* (opcional: tono menta más intenso = más barato; los números siempre visibles; leyenda con 3 muestras).
- **Crecimiento:** filas/columnas nuevas aparecen al agregar empresas/plantas (5.7) con celdas "Sin ruta" y el chip "Faltan N rutas por definir" + botón "Ir a la primera". Con >30 filas o >12 columnas: encabezados fijos, desplazamiento en ambos ejes, virtualización de filas, y el buscador resalta y mueve el foco a la fila/columna. Filas/columnas inactivas ocultas por defecto ("Mostrar inactivas").
- **Responsive:** <768 px la cuadrícula se reemplaza por **vista por empresa**: lista de acordeones (una empresa por acordeón) con un campo por planta; mismo guardado masivo. También disponible en escritorio como "Vista de lista" (alternativa accesible).
- **Analista:** misma pantalla en solo lectura (`aria-readonly`), sin barra de guardado, con aviso "Solo lectura: tu rol Analista no puede modificar los costos.".
- **Tras guardar:** banner de éxito con acción: "Cambiaste 1 costo. Ejecuta de nuevo para ver el efecto." → **[Ir a Optimización]**.

### 6.2 Edición, validación y guardado

- Escribir en una celda la edita; Enter confirma y baja; Esc restaura. Formato es-CO (4.2). Valores ≥ 0. Mensajes: "Escribe un número, por ejemplo 102.000." · "No puede ser negativo." · "Esta ruta quedaría sin costo. Ingresa el costo directamente o completa distancia y tarifa." · límite 0: aviso "Un límite de 0 t/semana bloquea la ruta." · costo 0: aviso "Costo 0: ¿es correcto?".
- **Guardado masivo atómico:** un solo `PUT` con las celdas modificadas. Éxito: toast "Se guardaron 3 cambios." y la barra desaparece. Error 400: **no se guardó nada**; alerta "No se guardó ningún cambio. Corrige 2 celdas." con enlaces "Ir a E3 → Granada"; las celdas con error quedan marcadas y el foco va a la primera.
- **Deshacer/rehacer:** pila de ediciones (un pegado de bloque = un paso); botones con el nombre del paso ("Deshacer: cambio en E3 → Granada"); la pila se vacía al guardar.
- **Cambios sin guardar:** chip "● N cambios sin guardar" (`role="status"`), marca de celda modificada, `beforeunload` y diálogo al navegar (4.5). Si llega una sesión expirada, se conservan (4.4).
- Pegar desde Excel (texto tabulado) rellena desde la celda activa; resumen "Se pegaron 12 celdas; 1 no es válida" con la celda marcada.
- "Guardar como escenario…": diálogo con Nombre\* y Descripción (`POST /escenarios/`); toast "Escenario «Ampliación Q3» guardado."

### 6.3 Atajos y accesibilidad de la cuadrícula editable

Patrón WAI-ARIA `grid`: `role="grid"`, `aria-rowcount`/`aria-colcount` (virtualización: `aria-rowindex`/`aria-colindex`), `columnheader`/`rowheader`, tabulación con **roving tabindex** (una sola parada de Tab para entrar, otra para salir), `aria-readonly` según rol. Cada celda tiene nombre accesible completo: "E1 Finca La Esperanza a P3 Granada: 98.500 pesos por tonelada, modificada, antes 102.000". Instrucciones breves enlazadas con `aria-describedby` y botón **"Atajos de teclado"** (también con `?`).

| Atajo | Acción |
|---|---|
| ← ↑ → ↓ | Mover entre celdas |
| Inicio / Fin · Ctrl+Inicio / Ctrl+Fin | Primera/última celda de la fila · de la tabla |
| Re Pág / Av Pág | Subir/bajar una pantalla |
| Enter o F2 o empezar a escribir | Editar la celda |
| Enter (editando) / Tab / Shift+Tab | Confirmar y bajar / mover a la derecha / a la izquierda |
| Esc | Cancelar la edición |
| Supr o Retroceso | Vaciar: Costo → marcar "Sin ruta"; Límite → "Sin límite"; Distancia/Tarifa → vacío |
| Shift+flechas | Seleccionar rango |
| Ctrl+C / Ctrl+V | Copiar / pegar (admite bloque de Excel) |
| Ctrl+Z / Ctrl+Y (Ctrl+Shift+Z) | Deshacer / rehacer |
| Ctrl+S | Guardar cambios (solo en esta pantalla) |
| ? | Mostrar atajos |

Los errores de celda se anuncian al salir de la celda ("Valor no válido: no puede ser negativo"); la barra fija no puede tapar la celda enfocada (2.4.11); objetivos de celda ≥ 44×32 px (mín. WCAG 24×24); zoom 200 % mantiene la tabla desplazable (única excepción de reflujo) y la vista de lista ofrece el contenido en una columna.

---

## 7. Optimización (`/optimizacion`)

**Propósito:** ejecutar el método exacto y el AG y entender el resultado (Req. 2, 3). **API:** `POST /optimizacion/exacto/` (`modo_oferta`: `exact` | `maximum`), `POST /optimizacion/genetico/` (`poblacion`, `generaciones`, `cruce`, `mutacion`, `semilla`, `elitismo`, **`seleccion`, `tipo_cruce` (previsto)**), ambos con `escenario_id` y `guardar`.

### 7.1 Layout

```
Optimización                                                     ¿Cómo funciona?
Base de cálculo: (● Red actual) ( ) Escenario guardado ▾
┌ Red: 10 empresas · 4 plantas · 40 rutas │ Oferta 1.320 t/sem │ Capacidad 1.200 t/sem │
│ ⚠ La oferta supera la capacidad por 120 t/semana: el método exacto no tendrá solución. [Ver cómo resolverlo] ┘
┌─ Método exacto ──────────────────────┐ ┌─ Algoritmo genético ─────────────────────┐
│ Encuentra el costo mínimo posible.   │ │ Busca una buena solución por evolución.  │
│ Oferta: (●) Retirar toda la oferta   │ │ Parámetros: Población 60 · 150 generac.… │
│         ( ) Retirar hasta la oferta  │ │ [Editar parámetros ▾]  Preset:[Rápido][Equilibrado][Preciso]│
│ [        Ejecutar método exacto    ] │ │ [      Ejecutar algoritmo genético     ] │
└──────────────────────────────────────┘ └──────────────────────────────────────────┘
Resultado:  [Método exacto ✓ 14:35] [Algoritmo genético ✓ 14:36]      [Comparar en un reporte →]
┌ Estado ──────┐┌ Costo total ───────┐┌ Tiempo ─────┐┌ Toneladas ──────┐┌ Gap vs exacto ┐
│ ✓ Óptimo     ││ $ 118.450.000      ││ 12 ms       ││ 1.200 t/semana  ││ 0,8 % (solo AG)│
│              ││ COP por semana     ││             ││ 3 plantas usadas││                │
└──────────────┘└────────────────────┘└─────────────┘└─────────────────┘└────────────────┘
[ Resumen ] [ Asignaciones ] [ Mapa de flujos ] [ Verificación ✓ ] [ Convergencia (AG) ]
```

- **Base de cálculo:** "Red actual" (por defecto) o "Escenario guardado" (lista de `GET /escenarios/` con resumen: "Ampliación Q3 · 11 empresas · 4 plantas"). Aviso de comprobación previa (oferta vs capacidad total, empresas sin rutas, plantas sin rutas) **antes** de ejecutar, con enlace a la solución (Red logística / matriz). No bloquea.
- **Método exacto:** selector "Retirar toda la oferta" (`exact`, por defecto) / "Retirar hasta la oferta disponible" (`maximum`), con ayuda: "La primera exige que se recoja todo el residuo; la segunda permite dejar parte sin recoger si no hay capacidad."
- **AG:** botón deshabilitado con motivo visible ("El algoritmo genético solo funciona con plantas de capacidad máxima. Revisa el tipo de demanda de: Restrepo.") si alguna planta activa no es `capacity_max` (o si se eligió `maximum`: "solo con retiro de toda la oferta" — confirmar con backend, D7).
- Las dos tarjetas de ejecución son independientes; la última ejecución de cada método de la sesión permanece accesible en las pestañas "Método exacto / Algoritmo genético" del resultado (`role="tablist"`). Si existen ambas, aparece el **gap vs exacto** en la tarjeta del AG y el enlace "Comparar en un reporte".
- Opción "Guardar en el historial" (marcada por defecto) = `guardar`; si se desmarca, la ejecución no queda en el historial (`ejecucion_id` nulo) y se rotula "No guardada".

### 7.2 Panel de parámetros del AG

Colapsable ("Editar parámetros", `aria-expanded`); colapsado muestra el resumen de una línea con los valores efectivos. Valores por defecto (del contrato) y **ayuda en lenguaje simple** siempre visible bajo cada campo (no solo en tooltip):

| Parámetro | Control | Rango · defecto | Ayuda |
|---|---|---|---|
| Población | Número + deslizador | 2–300 · **60** | "Cuántas soluciones candidatas se comparan a la vez. Más candidatas buscan mejor, pero tardan más." |
| Generaciones | Número + deslizador | 1–1.000 · **150** | "Cuántas veces se renueva la población. Más generaciones suelen acercarse al óptimo." |
| Tasa de cruce | Porcentaje | 0–100 % · **80 %** | "Con qué frecuencia dos soluciones se combinan para crear una nueva." |
| Tasa de mutación | Porcentaje | 0–100 % · **12 %** | "Con qué frecuencia se altera al azar una parte de la solución, para explorar alternativas." |
| Semilla | Número + botón "Aleatoria" | 0–2.147.483.647 · **42** | "Con la misma semilla el resultado se repite exactamente. Cámbiala para probar otro recorrido." |
| Elitismo | Número | 0 a población−1 · **2** | "Cuántas de las mejores soluciones pasan sin cambios a la siguiente generación." |
| Selección (previsto) | Radio | Torneo · Ruleta · defecto Torneo | "Cómo se eligen las soluciones que se combinan. Torneo: compiten pequeños grupos y gana la mejor. Ruleta: más probabilidad cuanto mejor es la solución." |
| Cruce (previsto) | Radio | 1 punto · 2 puntos · defecto 1 punto | "Cuántos cortes se hacen al combinar dos soluciones. Con 2 puntos se intercambia un tramo central." |

Las tasas se muestran en % y se envían como fracción (0,8 / 0,12). Validación: fuera de rango → "Debe estar entre 2 y 300."; elitismo ≥ población → "El elitismo debe ser menor que la población (60)."; no enteros → "Usa un número entero." Botones: **Restablecer valores por defecto**; presets "Rápido" (30 · 50), "Equilibrado" (valores por defecto), "Preciso" (200 · 500) con aviso de tiempo estimado. Los parámetros usados quedan en el resultado y en el historial. Este mismo panel (`PanelParametrosAG`) se reutiliza en Sensibilidad y Reporte.

### 7.3 Resultado

- **Tarjetas de métrica** (`UiMetricCard`): Estado (con icono: "Óptimo", "Solución factible", "Sin solución"), **Costo total (COP por semana)**, **Tiempo**, **Toneladas movidas** (y número de plantas usadas), y en AG **Gap vs exacto** (si hay exacto de la misma base) + generaciones y semilla en la pestaña Resumen.
- **Asignaciones (tabla):** Empresa · Planta · **Cantidad (t/semana)** · Costo unitario (COP/t) · Costo de la ruta (COP/semana) · % de la oferta de la empresa. Ordenable, filtro por empresa/planta, totales al pie, "Exportar CSV". Fila seleccionada resalta su línea en el mapa.
- **Mapa de flujos:** el mapa de Inicio con las asignaciones dibujadas.
  - Línea empresa → planta con **grosor proporcional a la cantidad** (2 px = mínimo; 14 px = la mayor), curva suave y punta de flecha; la leyenda muestra 3 grosores de referencia con toneladas ("Grosor = toneladas por semana") y el color por planta (del paleta, con inicial de la planta en su marcador).
  - Etiqueta de toneladas junto a la línea (conmutador "Mostrar toneladas", activo por defecto si hay ≤20 flujos). Conmutador "Mostrar rutas sin flujo" (tenues).
  - Ficha: planta → "Recibe 320 de 400 t/semana (80 %)" y orígenes; empresa → "Envía 120 t/semana: Granada 80 t, Restrepo 40 t".
  - Alternativa no visual: la tabla de Asignaciones; "Ver como tabla" salta a ella. Las líneas son enfocables (`role="button"`, nombre "E3 a Granada, 85 toneladas por semana"); las animaciones de flujo se desactivan con `prefers-reduced-motion`.
- **Verificación de restricciones:** encabezado "✓ La solución cumple todas las restricciones" o "✕ La solución viola N restricciones (máx. 3,2 t)" (de `verificacion.valida`, `errores`, `violacion_maxima`); tabla expandible:

| Restricción | Resultado | Estado |
|---|---|---|
| Toda la oferta se retira (por empresa) | 10 de 10 empresas con oferta completa | ✓ Cumple |
| Ninguna planta supera su capacidad | 4 de 4 plantas dentro de su capacidad (máx. 97 %) | ✓ Cumple |
| Ninguna ruta supera su límite | 2 rutas con límite; ninguna excedida | ✓ Cumple |
| Cantidades no negativas y solo por rutas existentes | — | ✓ Cumple |

  Cada fila se expande con el detalle por empresa/planta/ruta (requerido · asignado · holgura). Un AG puede devolver "Solución factible" con violación leve: se muestra el estado exacto y qué restricción falló.
- **Convergencia (solo AG):** gráfico de línea "Mejor costo encontrado por generación" (eje x generaciones, eje y COP por semana, sin forzar cero y rotulado), línea punteada gris "Óptimo exacto" si existe, punto final rotulado ("$ 119.400.000 en la generación 150"), tooltip y navegación por teclado entre puntos; "Ver datos" abre la tabla (generación, costo). Texto resumen: "El AG dejó de mejorar en la generación 96."
- **Detalle técnico** (plegado, solo lectura): `mensajes[]` del solver, `metricas` (semilla, generaciones, solver). Para el exacto, **precios sombra** de la corrida con enlace "Entender los precios sombra" → Sensibilidad.

### 7.4 Estados

| Estado | Contenido |
|---|---|
| Sin ejecuciones | Zona de resultado: "Aún no has ejecutado ningún método." "Elige un método arriba para ver el costo y el plan de rutas." |
| Cargando | Botón con spinner; "Calculando… 2 s"; el AG muestra tiempo transcurrido (la API es síncrona; sin barra de avance real). Al terminar: `role="status"` "Método exacto terminado: costo $ 118.450.000." |
| Error 400 | "Revisa los parámetros." + errores por campo. |
| Error de servidor | "No pudimos ejecutar el cálculo." + "Reintentar"; los resultados previos se conservan. |
| INFEASIBLE | Sección 12. |
| UNBOUNDED / otro | "El cálculo no terminó correctamente (estado: UNBOUNDED)." + "Revisa que las rutas tengan costos y la oferta sea mayor que 0." + Detalle técnico. |

---

## 8. Sensibilidad (`/sensibilidad`)

**Propósito:** responder "¿qué pasa si…?" y revelar cuellos de botella, precios sombra y rangos (Req. 4). **API:** `POST /optimizacion/sensibilidad/` con `variaciones[{tipo: oferta|capacidad|costo, ids[], porcentajes[] (−100…1000, hasta 40)}]`, `incluir_ag`, `config_ag`. Respuesta: `base` (exacto, AG, gap), `precios_sombra`, `plantas[]` (`capacidad`, `flujo`, `utilizacion_pct`, `precio_sombra`, `cuello_de_botella`), `escenarios[]` (exacto, variación en COP y %, AG, gap %, tiempos), **`rangos` y `base_cambio` por escenario (previsto)**.

### 8.1 Constructor de escenarios

```
Sensibilidad                                                      ¿Cómo funciona?
Base de cálculo: (● Red actual) ( ) Escenario guardado ▾
1 · ¿Qué quieres variar?                          [Usar escenarios de ejemplo de la sustentación]
┌ Combustible y transporte ────────────────────────────── [Quitar] ┐
│ Cambia el costo de: (● Todas las rutas) ( ) Rutas elegidas…       │
│ Variaciones: [+10 %×] [+20 %×] [+30 %×] [+ Agregar %]             │
│ Generará 3 escenarios                                             │
└───────────────────────────────────────────────────────────────────┘
┌ Capacidad de plantas (cuello de botella) ───────────────── [Quitar] ┐
│ Plantas: [Granada ×] [Villavicencio ×] [+ Agregar planta]           │
│ Variaciones: [−30 %×] [−50 %×] [+ Agregar %]       Generará 2       │
└────────────────────────────────────────────────────────────────────┘
[+ Agregar variación ▾]  Oferta de residuos · Capacidad de plantas · Combustible y transporte · Costo de una ruta
2 · Opciones
 ☐ Incluir también el algoritmo genético en cada escenario (más lento) [Editar parámetros ▾]
Total: 7 escenarios (+ el caso base)     ⏱ estimado < 5 s      [ Ejecutar análisis ]
```

| Tipo de bloque | `tipo` y `ids` enviados | Alcance | Ejemplo de textos |
|---|---|---|---|
| Combustible y transporte | `costo`, `ids` vacío = todas las rutas | "Todas las rutas" o "Rutas elegidas" | "Sube el costo de transporte de todas las rutas." |
| Oferta de residuos | `oferta`, `ids` = empresas (vacío = todas) | Todas / elegidas | "Cambia la cantidad de residuo que genera cada empresa." |
| Capacidad de plantas | `capacidad`, `ids` = una o varias plantas | **Obligatorio elegir ≥1** (es el análisis de cuello de botella) | "Cambia lo que cada planta puede recibir." |
| Costo de una ruta | `costo`, `ids` = `E1->P2` | Selector empresa → planta | "Cambia el costo de una ruta puntual." |

- Porcentajes: campo "Agregar %" (−100 a 1.000, entero o decimal), se ofrecen atajos ±10 / ±20 / ±30; máximo 40 por bloque; duplicados se ignoran; chips con "×" quitables por teclado. Mensajes: "Ingresa un porcentaje entre −100 y 1.000." · "Ya agregaste +10 %." · "Máximo 40 variaciones por bloque." · "Elige al menos una planta." · "Agrega al menos una variación."
- Un contador global "Total: N escenarios" y, con AG incluido, aviso proporcional al tamaño: >30 escenarios con AG → confirmación previa (4.5). El botón principal queda siempre habilitado; la validación explica qué falta.
- **"Usar escenarios de ejemplo"** (sustentación): carga la plantilla (combustible +10/+20/+30 %; oferta −20/+20 %; capacidad −30/−50 % en la planta con mayor flujo del caso base o en la primera). No ejecuta por sí solo.

### 8.2 Resultados

Orden de lectura, de lo más importante a lo más detallado (secciones con ancla y `h2`; barra de salto "Resumen · Precios sombra · Rangos · Escenarios · Gráficos"):

1. **Caso base** (tarjetas): costo exacto, costo AG (si se incluyó), gap %, tiempos. Nota del backend (`nota`) en "Cómo leer esto".
2. **Precios sombra y cuellos de botella** (8.3).
3. **Rangos de variación** (8.4).
4. **Tabla de escenarios** (8.5).
5. **Gráficos** (8.6).

### 8.3 Precios sombra en lenguaje de negocio

Tarjeta destacada **"Dónde conviene ampliar primero"**: ranking de plantas con cuello de botella por ahorro por tonelada (de `precio_sombra` y `cuello_de_botella`). Debajo, tabla de plantas:

| Planta | Capacidad (t/sem) | Recibe (t/sem) | Uso | Qué significa |
|---|---|---|---|---|
| Granada | 350 | 350 | ████████ 100 % [Cuello de botella] | "Cada tonelada adicional que Granada pudiera recibir bajaría el costo en **$ 4.200 por semana** (hasta 450 t/semana)." |
| Restrepo | 300 | 186 | █████░░░ 62 % | "Le sobra capacidad: ampliarla **no** reduce el costo." |

Plantilla por signo y estado (el frontend la aplica; el backend documenta el signo, D8):
- Planta llena con precio sombra ≠ 0: "Cada tonelada adicional de capacidad **bajaría** el costo en $ X por semana." (hasta el límite del rango de 8.4).
- Planta con holgura (precio 0): "Le sobra capacidad: ampliarla no reduce el costo."
- Empresa (en sección plegable "Precio sombra por empresa"): "Recoger **una tonelada más** de {empresa} **aumentaría** el costo total en $ X por semana." (o "reduciría", si el signo es negativo).
- Definición siempre disponible ("¿Qué es un precio sombra?"): "Es el valor de una tonelada adicional. Para una planta llena, cuánto ahorrarías si pudiera recibir una tonelada más. No es un costo que se paga: es una guía para decidir dónde invertir."
- Barra de uso con texto (%) y el rótulo "Cuello de botella" (icono + texto); no solo color.

### 8.4 Rangos de variación (sin cambiar la base óptima) — previsto

Tabla con barra de rango por fila (`UiBarraRango`), pestañas "Capacidades de plantas" · "Ofertas de empresas" · "Costos de rutas":

```
Planta     Actual   Rango en que el plan óptimo se mantiene
Granada    350 t    280 ├──────────●────────────┤ 450 t        −70 / +100 t   [Se mantiene hasta aquí]
                          ▲ −30 % (escenario)  fuera del rango → el plan cambia
Restrepo   300 t    186 ├──────●──────────────────→ sin límite
Ruta E3→P2 98.500   71.000 ├─────●────┤ 120.000 COP/t
```

- Pista = eje con el rango plausible; segmento verde = **rango en el que el plan de rutas óptimo no cambia** (con ese plan, los precios sombra se mantienen); rombo = valor actual (rotulado); extremos con número; extremo no acotado = flecha y "sin límite".
- Marcas de los escenarios ejecutados sobre la barra (cuadrado con "−30 %"): si caen **fuera** del segmento, se explica por qué el escenario cambió el plan ("fuera del rango → el plan cambia"). Conecta este análisis con la columna "¿Cambió la base?" (8.5).
- Texto equivalente por fila (columna siempre presente, no depende de la barra): "Granada: capacidad actual 350 t/semana. El plan óptimo se mantiene si su capacidad queda entre 280 y 450 t/semana." La barra es `aria-hidden`; la tabla es el contenido accesible.
- Texto de ayuda: "Mientras el valor se mueva dentro de este rango, el plan de rutas óptimo es el mismo (solo cambia el costo total). Fuera del rango, el plan cambia."
- Estado: si el backend aún no entrega rangos, la sección muestra "Los rangos se calcularán al ejecutar el análisis con la versión nueva." (D9).

### 8.5 Tabla de escenarios

| Columna | Contenido |
|---|---|
| Escenario | Nombre (`nombre`), p. ej. "Combustible +20 %" |
| Qué cambia | Tipo y alcance ("Costo · todas las rutas") |
| Cambio | `porcentaje` con signo |
| Costo exacto (COP/semana) | `exacto.objetivo` |
| Variación vs base | `variacion_objetivo` y `%`, con ▲/▼ y signo |
| Costo AG (COP/semana) | Solo si se incluyó el AG |
| Gap % | `gap_pct`; insignia de lectura (≤1 % "Excelente", 1–5 % "Aceptable", >5 % "Mejorable"; umbrales D10) |
| Tiempo exacto / AG | `duracion_ms` |
| ¿Cambió la base óptima? | "Sí" / "No" (previsto `base_cambio`), ayuda: "Sí = el plan de rutas óptimo es distinto al del caso base." |
| Estado | "Óptimo" o "Sin solución" |

- La fila del caso base va primero y fija (rotulada "Caso base"). Ordenable por cualquier columna; filtro "Tipo de variación" y conmutador "Solo los que cambian el plan". Encabezados fijos. Escenario INFEASIBLE: costos "—", estado "Sin solución" (icono) y el diálogo "¿Por qué?" con el mensaje de la sección 12.
- Acciones: "Exportar CSV", "Ver reporte comparativo con estos escenarios" (precarga las mismas variaciones en el reporte).
- Responsive: <768 px, tarjetas por escenario con costo, variación y estado; el resto en "Más detalles".

### 8.6 Gráficos (sin abrumar: uno visible a la vez, conmutador y siempre con "Ver datos")

1. **"Impacto en el costo"** (por defecto): barras horizontales ordenadas por variación de costo (como un tornado): cada escenario una barra desde 0, hacia la derecha = cuesta más (▲, +), izquierda = ahorra (▼, −); valores rotulados al final de la barra; líneas de referencia en 0.
2. **"Costo total según la variación"**: líneas, eje x = % de cambio, eje y = costo exacto (COP/semana), una serie por tipo de variación; AG como puntos con rombo si se incluyó; el caso base marcado en 0 %.
3. **"Gap del AG por escenario"** (solo si hay AG): barras de gap % con banda de referencia.

Series distinguibles por color + forma de marcador + trazo (continuo/discontinuo) + rótulo directo; tooltip enfocable con teclado (flechas entre puntos); "Ver datos" muestra la tabla equivalente; leyenda como botones que ocultan series (`aria-pressed`).

### 8.7 Estados

| Estado | Contenido |
|---|---|
| Antes de ejecutar | Resultados vacíos: "Construye tus escenarios y pulsa Ejecutar análisis." |
| Ejecutando | "Calculando 7 escenarios…" con tiempo transcurrido; los controles del constructor se bloquean (solo lectura, no `disabled`). |
| Caso base sin solución | Se muestra la sección 12 y **no** la tabla ("No se puede analizar la sensibilidad porque el caso base no tiene solución."). |
| Parcial | Algún escenario sin solución: se muestra en la tabla con "Sin solución"; banner informativo con el conteo. |
| Error 400 | Por bloque: marca el bloque con el error (`aria-invalid`) y resumen arriba. |
| Error de servidor | "No pudimos completar el análisis." + "Reintentar" (conserva el constructor). |

---

## 9. Reporte comparativo (`/reportes`)

**Propósito:** entregable de sustentación: exacto vs AG (costo, tiempo, gap %), comportamiento bajo escenarios y escalabilidad (Req. 5). **API:** `POST /optimizacion/reporte/` (`config_ag`, `variaciones`, `escenario_id`); respuesta: `modelo`, `exacto`, `genetico` (con `convergencia`, `asignaciones`), `comparacion` (`diferencia_costo`, `gap_pct`, `ratio_tiempo`, `ag_alcanza_optimo`), `plantas[]`, `sensibilidad?`; **escalabilidad (previsto)**.

### 9.1 Configuración

```
Reporte comparativo                                              ¿Cómo funciona?
Base: (● Red actual) ( ) Escenario guardado ▾   Parámetros del AG: 60 · 150 · 80 % · 12 % [Editar ▾]
☑ Incluir comportamiento bajo escenarios     [Elegir escenarios…] (usa el constructor de Sensibilidad)
☐ Incluir escalabilidad (redes de tamaño creciente)   Tamaños: ☑10×4 (base) ☑20×6 ☑40×10 ☑80×16
                                           [ Generar reporte ]
```

- "Generar reporte" hace una sola petición de reporte (y la de escalabilidad si se marcó). Si la sesión ya tiene un exacto y un AG de la misma base y parámetros, se ofrece "Usar los resultados de esta sesión" para no recalcular (opcional, D11).
- Escalabilidad: aviso "Se crean redes de prueba (ficticias) con la misma estructura. Puede tardar unos minutos con tamaños grandes."

### 9.2 Contenido del reporte (secciones numeradas, con índice lateral "En esta página" y anclas)

1. **Resumen** — Titular: "El algoritmo genético llegó a **0,8 %** del costo óptimo, en 0,4 s; el método exacto tardó 12 ms." (si `ag_alcanza_optimo`: "El AG alcanzó el óptimo."). Cuatro tarjetas: Costo exacto · Costo AG · **Gap %** (con insignia Excelente/Aceptable/Mejorable) · Tiempo (exacto vs AG, "el AG tardó 33 veces más", de `ratio_tiempo`). Etiqueta de datos de demostración si aplica.
2. **Comparación exacto vs AG** — Tabla métrica × método (Estado · Factible · Costo total · Diferencia en COP · Gap % · Tiempo · Plantas usadas · Cumple restricciones) + gráfico de barras agrupadas en **dos paneles pequeños** (Costo y Tiempo; cada uno con su escala, sin doble eje).
3. **Plan de rutas lado a lado** — Tabla Empresa → Planta · Exacto (t) · AG (t) · Diferencia (t) con filas distintas resaltadas ("Difiere") y filtro "Solo diferencias"; "Ver en mapa" alterna Exacto/AG.
4. **Convergencia del AG** — gráfico de 7.3.
5. **Plantas** — uso (%), cuello de botella y precio sombra (8.3 resumido).
6. **Comportamiento bajo escenarios** (si se incluyó) — tabla de 8.5 en versión compacta (Escenario · Costo exacto · Costo AG · Gap % · ¿Cambió la base?) y gráfico de líneas exacto vs AG por escenario + barras de gap; resumen "El gap máximo fue 2,1 % en «Capacidad Granada −50 %»".
7. **Escalabilidad** (si se incluyó) — tabla Tamaño (empresas × plantas) · Rutas · Tiempo exacto · Tiempo AG · Costo exacto · Costo AG · Gap %; gráfico de líneas "Tiempo según el tamaño de la red" (eje y con opción de escala logarítmica rotulada) y de gap %; rótulo permanente "Redes de prueba ficticias, no son datos reales".
8. **Cómo leer este reporte** — glosario corto (gap, precio sombra, base óptima) y fecha, usuario, base y parámetros (reproducibilidad: semilla).

### 9.3 Exportar, imprimir y presentar

- **Exportar** (menú): "CSV de la comparación", "CSV de asignaciones", "CSV de escenarios", "CSV de escalabilidad" (los presentes). CSV en UTF-8 con BOM, separador `;`, decimales con coma (abre bien en Excel es-CO; D12), encabezados con unidades, primera fila de metadatos opcional desactivada. Nombre: `optiagro-reporte-2026-11-12-1435.csv`. Toast "Exportado optiagro-reporte-….csv". Se genera en el cliente a partir de los datos ya cargados.
- **Imprimir / Guardar como PDF**: botón que invoca la impresión del navegador con hoja de estilos de impresión: sin sidebar/topbar/botones, fondo blanco, tipografía 11 pt, una sección por bloque sin cortarlo entre páginas, gráficos en vector con patrón/rótulos (legibles en blanco y negro), encabezado "OptiAgro-Llanos — Reporte comparativo · fecha · usuario · base" y pie con número de página; texto "Datos de demostración" si aplica; URLs visibles.
- **Vista de presentación** (para la sustentación en vivo): botón "Presentar" a pantalla completa; oculta el shell; tipografía base ≥ 20 px; una diapositiva por sección (Resumen · Comparación · Escenarios · Escalabilidad); ←/→ o PgUp/PgDn avanzan; Esc sale; indicador "2 de 4"; contraste y foco iguales al resto. Sin animaciones obligatorias.

### 9.4 Estados

| Estado | Contenido |
|---|---|
| Sin reporte | "Aún no has generado un reporte." "Configura la comparación y pulsa Generar reporte." |
| Generando | "Generando reporte… (exacto, AG, escenarios)" con tiempo transcurrido. |
| INFEASIBLE exacto | Reporte parcial: sección 1 muestra la sección 12 y se ocultan costo/gap ("—"); las demás secciones que dependen del exacto no se muestran. |
| AG sin solución factible | Resumen: "El AG no encontró una solución que cumpla las restricciones; el método exacto sí." + sugerencia "Aumenta población y generaciones." Gap "—". |
| Error | "No pudimos generar el reporte." + "Reintentar" (conserva la configuración). |
| Parcial (sin escalabilidad por error) | El reporte se muestra sin esa sección y un aviso: "No se pudo calcular la escalabilidad." + "Reintentar solo esta sección". |

---

## 10. Usuarios (`/usuarios`, solo administrador)

**API (previsto):** `GET/POST /usuarios/`, `PATCH /usuarios/{id}/`, `POST /usuarios/{id}/restablecer-clave/`; campos `username`, `first_name`, `last_name`, `email`, `rol`, `activo`, `ultimo_acceso`.

```
Usuarios                                                         [+ Nuevo usuario]
🔍 Buscar por nombre, usuario o correo   Rol:[Todos ▾]   Estado:[Todos|Activos|Inactivos]
┌───────────────┬─────────┬────────────────┬─────────────┬────────┬──────────────┬────┐
│Nombre ▲       │Usuario  │Correo          │Rol          │Estado  │Último acceso │ ⋮ │
│Camila Rojas   │crojas   │c@empresa.co    │Administrador│Activo  │hoy 09:12     │ ⋮ │
│Andrés Pérez   │aperez   │a@empresa.co    │Analista     │Inactivo│12 oct 2026   │ ⋮ │
└───────────────┴─────────┴────────────────┴─────────────┴────────┴──────────────┴────┘
```

- Tabla con búsqueda, filtros por rol y estado, ordenamiento y paginación (mismo patrón que 5.1). Fila "(Tú)" etiquetada. Acciones por fila: **Editar**, **Activar/Desactivar**, **Restablecer contraseña**. No hay "Eliminar" (se desactiva para conservar el historial; D13).
- **Crear/editar (panel lateral):** Nombre\* · Apellidos\* · Usuario\* (letras, números y @ . + - _; ≤150; único; no editable al editar) · Correo\* · **Rol\*** (dos tarjetas de selección tipo radio: "Administrador — gestiona la red, los costos y los usuarios; también ejecuta análisis." / "Analista — ejecuta optimizaciones y escenarios; consulta la red sin modificarla.") · Contraseña inicial\* (solo al crear) con **medidor** · "Pedir cambio de contraseña al primer ingreso" (previsto, marcado por defecto) · Activo.
- **Contraseña y medidor (`UiMedidorClave`):** campo con Mostrar/Ocultar, pegar permitido, botón "Generar contraseña segura" (la muestra una vez con botón "Copiar"). Medidor de 4 segmentos con **texto** (Muy débil · Débil · Aceptable · Segura) y lista de requisitos con ✓/✕ en texto: "Al menos 10 caracteres", "No es una contraseña común", "No es solo numérica", "No se parece al usuario o correo" (alinear con los validadores de Django; D14). El medidor guía, el servidor decide: un 400 muestra su mensaje en el campo. Se anuncia el nivel con `aria-live="polite"` (con retardo de 600 ms).
- **Restablecer contraseña:** diálogo "¿Restablecer la contraseña de Andrés Pérez?" → genera una contraseña temporal (o campo para definirla) mostrada **una sola vez** con "Copiar" y la nota "Compártela por un canal seguro. Se le pedirá cambiarla al ingresar." El usuario debe cambiarla en el siguiente ingreso.
- **Desactivar:** "¿Desactivar a Andrés Pérez? No podrá iniciar sesión. Sus ejecuciones se conservan en el historial. Puedes reactivarlo cuando quieras."
- **Protecciones** (acción deshabilitada con motivo visible vinculado por `aria-describedby`, y el servidor también las aplica):
  - "No puedes desactivarte a ti mismo."
  - "No puedes cambiar tu propio rol." (para cambiar de rol, otro administrador debe hacerlo)
  - "Este es el último administrador activo: no se puede desactivar ni cambiar su rol. Crea otro administrador primero."
  - "Para cambiar tu contraseña, usa Mi perfil." (restablecer se oculta en la propia fila).
- Errores: usuario duplicado "Ya existe un usuario con ese nombre." · correo inválido "Escribe un correo válido, por ejemplo nombre@empresa.co." · rol obligatorio "Elige un rol."
- Estados: vacío (solo el propio admin) "Aún no has creado otros usuarios." + "Nuevo usuario"; error "No pudimos cargar los usuarios." + Reintentar; 403 para analista.
- Usuarios creados por el despliegue (primer administrador) quedan fuera de la UI: ver D15.

## 11. Mi perfil (`/perfil`)

```
Mi perfil
┌ Datos personales ────────────────────────┐ ┌ Cambiar contraseña ─────────────────┐
│ Nombre [Julián ]  Apellidos [Pérez   ]   │ │ Contraseña actual  [            ]   │
│ Correo [jperez@empresa.co            ]   │ │ Nueva contraseña   [            ]   │
│ Usuario  jperez   Rol  [Administrador]   │ │  ▮▮▮▯ Aceptable · requisitos…       │
│ (usuario y rol: solo lectura)  [Guardar] │ │ Repite la nueva    [            ]   │
└──────────────────────────────────────────┘ │            [Cambiar contraseña]     │
 Mis ejecuciones recientes → Ver historial   └─────────────────────────────────────┘
```

- Editable: nombre, apellidos, correo (`PATCH /auth/me/`, previsto). Usuario y rol en solo lectura con nota "Solo un administrador puede cambiar tu rol."
- Cambio de contraseña (previsto `POST /auth/cambiar-clave/`): actual, nueva (medidor 10), repetir. Mensajes: "Ingresa tu contraseña actual." · "La contraseña actual no es correcta." · "Las contraseñas no coinciden." · "La nueva contraseña debe ser distinta de la actual." Éxito: toast "Contraseña actualizada." y se vacían los campos; la sesión continúa. Sin bloquear pegar (WCAG 3.3.8). `autocomplete="current-password"` / `"new-password"` (x2).
- Estados: guardar → "Cambios guardados."; error 400 por campo; error de red con "Reintentar".

## 12. INFEASIBLE (sin solución) — manejo único

Aplica a Optimización, Sensibilidad (base y escenarios) y Reporte. `UiAlert` tono `aviso` con título **"No existe un plan que cumpla todas las restricciones."** (no es un fallo del sistema). Se diagnostica en el cliente con la red cargada y se lista **la causa más probable primero**:

| Causa detectada | Texto | Acción |
|---|---|---|
| Oferta total > capacidad total (modo "toda la oferta") | "La oferta total (1.320 t/semana) supera la capacidad total de las plantas activas (1.200). Faltan **120 t/semana**." | [Ampliar la capacidad de una planta] → Red logística (Plantas) · [Retirar hasta la oferta disponible] (si el modo lo permite) |
| Empresa(s) sin ruta activa | "Estas empresas no tienen ninguna ruta a una planta activa: E11, E12." | [Definir rutas en la matriz] |
| Límites de ruta muy bajos | "Los límites de ruta impiden mover toda la oferta de: E3." | [Revisar límites] → matriz, capa Límite |
| Planta con demanda exacta o mínima no alcanzable | "La planta Granada exige recibir exactamente 350 t/semana y la oferta disponible no alcanza." | [Editar planta] |
| Causa no determinada | "Revisa la oferta, la capacidad y los límites de las rutas." | Enlaces a Red logística y matriz |
| AG sin factibilidad pero exacto sí | "El algoritmo genético no encontró un plan válido; el método exacto sí." | "Aumentar población y generaciones" / "Ejecutar el método exacto" |

- Los botones de acción están **solo para el administrador**; el analista ve el mismo diagnóstico con "Pide al administrador que ajuste la red."
- "Detalle técnico" (plegado) muestra `mensajes[]` del solver. El resultado INFEASIBLE se guarda en el historial con estado "Sin solución".
- Las tarjetas de métrica muestran "—" (no 0) y el mapa de flujos no se dibuja ("No hay flujos que mostrar").

## 13. Historial (`/historial`, `/historial/:id`, `/historial/comparar`)

**API:** `GET /ejecuciones/` (`metodo`, `estado`, `escenario`, `usuario` solo admin, `ordering`, paginación), `GET /ejecuciones/{id}/`.

```
Historial de ejecuciones
🔍 …  Método:[Todos ▾] Estado:[Todos ▾] Base:[Todas ▾] Usuario:[Todos ▾](admin)   [Comparar (2)]
┌──┬─────┬──────────────┬─────────────────────┬───────────┬──────────────┬───────┬─────────┬──────┐
│☐ │ N.º │Fecha ▼       │Método               │Estado     │Costo (COP/s) │Tiempo │Usuario  │      │
│☑ │ 128 │12 nov 14:36  │Algoritmo genético   │Factible   │119.400.000   │0,4 s  │aperez   │Abrir │
│☑ │ 127 │12 nov 14:35  │Método exacto        │Óptimo     │118.450.000   │12 ms  │aperez   │Abrir │
│☐ │ 126 │12 nov 14:30  │Sensibilidad         │Completada │—             │2,1 s  │crojas   │Abrir │
```

- Columnas: N.º · Fecha · Método (Exacto, Algoritmo genético, Sensibilidad, Reporte) · Estado (insignia con icono) · Costo total · Tiempo · Base (escenario o "Red actual") · Usuario (solo admin ve todas; analista solo las suyas y sin columna ni filtro de usuario). Ordenable por fecha (desc. por defecto), costo y tiempo. Fecha: filtro rápido "Hoy / 7 días / Todas" aplicado en cliente sobre lo cargado (el contrato aún no filtra por fecha; D16).
- **Detalle `/historial/:id`:** migas `Historial / Ejecución 127`. Cabecera con metadatos (fecha, usuario, base, parámetros/configuración) y acciones **"Repetir con estos parámetros"** (abre la pantalla de origen con los campos precargados; no ejecuta sola) y "Comparar con otra ejecución…". El cuerpo reutiliza en **solo lectura** el componente de resultado de la pantalla de origen (Optimización / Sensibilidad / Reporte). Rotulado "Resultado guardado el …" para distinguirlo de uno recién calculado.
- **Comparar dos ejecuciones:** casillas por fila (máx. 2; la tercera se deshabilita con "Solo puedes comparar dos ejecuciones a la vez"); el botón "Comparar (2)" se habilita con exactamente 2. Se comparan **exacto/AG** entre sí (sensibilidad y reporte no tienen asignaciones comparables: casilla deshabilitada con motivo; D17). Vista: dos columnas A/B con: método, estado, base, parámetros (las diferencias resaltadas con "Cambió"), costo total, **diferencia en COP y %** (B respecto de A, con ▲/▼ y signo), tiempo, y tabla de asignaciones por ruta (A · B · diferencia). Acción "Intercambiar A y B".
- Estados: vacío "Aún no hay ejecuciones. Ejecuta un método en Optimización." + [Ir a Optimización]; sin resultados por filtro; error con Reintentar; ejecución 404 "Esta ejecución ya no existe."; ejecución sin `resultado` completo "El detalle de esta ejecución no está disponible."

---

## 14. Estados, demostración y sustentación

### 14.1 Resumen de estados por pantalla

| Pantalla | Vacío | Cargando | Error | Sin permisos |
|---|---|---|---|---|
| Red logística | "Aún no hay empresas/plantas/rutas en la red." | Esqueleto de tabla | "No pudimos cargar …" + Reintentar | Botones de escritura ausentes; 403 al guardar: "No tienes permiso para modificar la red." |
| Matriz | "Aún no hay empresas ni plantas para armar la matriz." + "Ir a Red logística" (admin) | Esqueleto de cuadrícula | "No pudimos cargar la matriz." | Solo lectura |
| Optimización / Sensibilidad / Reporte | "Aún no has ejecutado…" | "Calculando…" | "No pudimos ejecutar…" | No aplica (ambos roles) |
| Historial | "Aún no hay ejecuciones." | Esqueleto | "No pudimos cargar el historial." | Analista solo ve las suyas |
| Usuarios | "Aún no has creado otros usuarios." | Esqueleto | "No pudimos cargar los usuarios." | 403 para analista |
| Perfil | — | Esqueleto | "No pudimos cargar tu perfil." | — |

### 14.2 Tour de la sustentación (recorrido de 5 minutos)

Acceso: avatar → **"Guía de sustentación"**. Panel no modal anclado abajo a la derecha (colapsable a una píldora "Paso 3 de 6 · 1:45"), persiste entre pantallas, no bloquea la interfaz ni usa `aria-modal`. Cada paso tiene: título, qué hacer, qué decir (una frase), tiempo objetivo, botón **"Ir"** (navega a la pantalla) y casilla "Hecho". Cronómetro opcional (inicia/pausa) con alerta suave (`role="status"`) a los 4:30. Se puede cerrar y retomar; no altera datos.

| # | Minuto | Paso | Pantalla | Qué hacer | Qué se debe ver |
|---|---|---|---|---|---|
| 0 | previo | Preparación (lista verificable) | — | Sesión como **administrador**; zoom 100–125 %; demo cargado; semilla del AG = 42; "Rápido" para el AG. | "Datos de demostración" visible. |
| 1 | 0:00–0:40 | **Cargar demo** y mostrar la red | Inicio / Red logística | Si la red está vacía: "Cargar datos de demostración" (previsto). Mostrar el mapa y los conteos 10 empresas, 4 plantas, 40 rutas. | Mapa con 14 estaciones; chip "Datos de demostración". |
| 2 | 0:40–1:30 | **Cambiar un costo** | Matriz de costos | Capa Costo: editar una celda (p. ej. E3 → Granada), ver la marca "modificada", **Guardar cambios (1)**. | Toast "Se guardaron 1 cambios."; banner "Ejecuta de nuevo para ver el efecto". |
| 3 | 1:30–2:15 | **Método exacto** | Optimización | "Ejecutar método exacto"; pestaña Mapa de flujos; Verificación ✓. | Costo total, tiempo en ms, líneas con grosor. |
| 4 | 2:15–3:00 | **Algoritmo genético** | Optimización | Preset "Rápido"; "Ejecutar algoritmo genético"; pestaña Convergencia. | Gap vs exacto (< 2 %), curva que se acerca a la línea del óptimo. |
| 5 | 3:00–4:15 | **Sensibilidad** | Sensibilidad | "Usar escenarios de ejemplo" → Ejecutar; mostrar cuello de botella, rangos y la tabla de escenarios. | Granada como cuello de botella; "¿Cambió la base?"; gráfico "Impacto en el costo". |
| 6 | 4:15–5:00 | **Reporte** | Reportes | "Generar reporte" → **Presentar** → exportar CSV. | Resumen con gap, comparación, escenarios y escalabilidad. |

Notas: el cambio de costo del paso 2 requiere rol administrador; un analista, en su lugar, puede mostrar el mismo efecto con un bloque "Costo de una ruta" en Sensibilidad. Para que el paso 5 sea fluido, la plantilla de ejemplo debe resolverse en < 15 s incluyendo AG (D18). Los últimos resultados persisten en memoria entre pasos (2.2), así el reporte puede reutilizarlos (D11).

### 14.3 Aviso "Datos de demostración" (gobernado por `ficticio`)

- Los modelos `Empresa`, `Planta` y `Ruta` traen `ficticio: boolean`. La interfaz muestra el aviso **si y solo si** la información visible incluye al menos un registro con `ficticio=true`. No depende de `VITE_MOCK` ni de ningún modo de ejecución: el modo mock debe entregar sus datos con `ficticio=true`; una base real sin registros ficticios no muestra el aviso aunque corra en desarrollo.
- Dónde: (a) **chip global** `UiBadge` ámbar "Datos de demostración" en la barra superior, con tooltip/`aria-label`: "Estás viendo datos ficticios: 10 empresas, 4 plantas, 40 rutas. No corresponden a empresas reales." Si hay mezcla: "Incluye datos de demostración (N de M registros)."; (b) insignia "Demostración" en cada fila/ficha de un registro ficticio; (c) en reportes impresos/presentación: etiqueta fija en el encabezado; (d) en resultados: "Calculado con datos de demostración" si la red base los incluye (previsto `incluye_ficticios` en el resumen del modelo, D19; mientras tanto se infiere de la red actual y no en el historial antiguo).
- Reemplaza el texto condicionado de Fase 1 en sidebar ("v0.1 · Datos de demostración"): el pie del sidebar muestra solo la versión.

## 15. Accesibilidad transversal (WCAG 2.2 AA)

- Todo lo de Fase 1 §1.7 y criterios 29–36 sigue vigente. Adicionalmente en esta fase:
- **Tablas de datos:** `<table>` semántica con `<caption>` (visible u oculta), `<th scope>`, `aria-sort`, números alineados a la derecha; encabezados fijos sin tapar el foco (2.4.11); en móvil, tarjetas con los mismos datos.
- **Formularios en panel/diálogo:** foco al abrir en el primer campo (o en el título si hay que leer antes), foco atrapado, Esc, foco devuelto al disparador; resumen de errores; pie fijo que no oculta el foco.
- **Pestañas, menús y acordeones** con los patrones WAI-ARIA correspondientes (flechas, Home/End, `aria-selected`, `aria-expanded`, `aria-controls`).
- **Gráficos:** nunca única fuente de la información: tabla equivalente ("Ver datos") y texto resumen; color + forma + trazo + rótulo directo; contraste de series ≥3:1 contra el fondo y entre elementos adyacentes; tooltips que se pueden descartar, mantener y alcanzar con teclado (1.4.13); sin animación obligatoria.
- **Mapas:** alternativa en lista/tabla para cada uso (flujos, selector, inicio); arrastre con alternativa de clic/teclado (2.5.7).
- **Estados dinámicos** (guardado, resultados, errores, conteos) con `role="status"`/`alert`/`aria-live="polite"`; no mover el foco salvo errores y apertura de diálogos.
- **Objetivos** ≥24×24 (meta 44×44); celdas de matriz ≥44×32; botones de fila con nombre único ("Editar E3").
- **Entrada:** `inputmode`/`autocomplete` correctos; formatos es-CO explicados con ejemplo; sin límites de tiempo salvo toasts (pausables) y sesión (aviso previo de expiración).
- **Reflujo a 320 px / zoom 200 %**: tablas → tarjetas, matriz → vista de lista, mapa y gráficos con desplazamiento propio y datos alternativos.
- **Texto:** 1.4.12 (espaciado) sin pérdida; idioma `es`; títulos de documento únicos ("Matriz de costos · OptiAgro-Llanos").

## 16. Criterios de aceptación (QA)

Numeración continúa la de Fase 1 (1–36).

**Navegación, permisos y demostración**
37. El sidebar muestra Inicio, Red logística, Matriz de costos, Optimización, Sensibilidad, Reportes, Historial y (solo administrador) Usuarios, sin etiquetas "Próximamente" ni ítems deshabilitados; el activo lleva `aria-current="page"`.
38. El menú de perfil contiene Mi perfil (habilitado), Guía de sustentación y Cerrar sesión; no existe ningún enlace, botón o texto que lleve a `/admin/` o diga "panel de administración" en ningún rol ni estado (incluidos mapa vacío y estaciones sin ubicación).
39. El estado vacío del mapa muestra, solo al administrador, "Ir a Red logística" y "Agregar empresa"; el analista solo ve el texto informativo.
40. En la lista "estaciones sin ubicación" el administrador ve "Agregar ubicación" por fila, que abre el panel de edición de esa estación en Red logística; el analista no.
41. Un analista que abre `/usuarios` por URL ve "No tienes permiso para ver esta página." y "Volver al inicio"; el ítem Usuarios no se renderiza para él.
42. Según la matriz de la sección 3, ningún botón de escritura (crear, editar, activar/desactivar, eliminar, guardar matriz, ampliar) existe en el DOM para el analista, y un 403 del servidor muestra "No tienes permiso para esta acción.".
43. El chip "Datos de demostración" aparece si y solo si hay al menos un registro visible con `ficticio=true` (probar: datos con `ficticio=true` y mock desactivado → aparece; datos con `ficticio=false` y mock activado → no aparece); no depende de variables de entorno.
44. Los registros ficticios muestran la insignia "Demostración" en tablas y fichas; los reportes impresos y la vista de presentación incluyen la etiqueta cuando aplica.

**Red logística**
45. `/red` muestra pestañas Empresas, Plantas y Rutas con su conteo; flechas ←/→/Home/End cambian de pestaña; la pestaña activa se refleja en `?tab=` y se restaura al recargar.
46. Cada tabla tiene búsqueda (se anuncia el número de resultados), filtro de estado Todas/Activas/Inactivas, columnas ordenables con `aria-sort` y paginación; ordenar, filtrar y buscar no recargan la página.
47. Crear empresa abre un panel lateral con foco atrapado, título accesible, Esc/"×" para cerrar y foco devuelto al disparador; con cambios sin guardar, Esc pide confirmación.
48. El campo Código rechaza espacios, tildes y símbolos con "Usa solo letras, números y guion bajo (sin espacios ni tildes).", acepta como máximo 20 caracteres y, al repetirse, muestra "Ya existe una empresa con el código …" en el campo.
49. Oferta y Capacidad rechazan 0, negativos y no numéricos con "…debe ser mayor que 0 t/semana."; Latitud y Longitud rechazan valores fuera de −90/90 y −180/180 y exigen ambas o ninguna; fuera del Meta solo se muestra un aviso, sin bloquear.
50. La planta incluye Tipo de demanda (tres opciones con descripción) y Costo de operación (COP por tonelada, ≥ 0); elegir un tipo distinto de capacidad máxima muestra el aviso sobre el AG.
51. El selector de ubicación permite escribir lat/lon (con el mapa actualizándose) o hacer clic en el mapa (con los campos actualizándose); el marcador se puede mover con el teclado; existe "Quitar ubicación"; no se requiere arrastrar.
52. Desactivar muestra un diálogo con el número de rutas asociadas, el efecto en el mapa y el cambio en oferta/capacidad total; tras confirmar, la estación desaparece de Inicio (mapa, leyenda, contador) y puede reactivarse sin confirmación.
53. Eliminar empresa/planta muestra el impacto (nº de rutas que también se eliminan, desaparece del mapa, irreversible), ofrece la alternativa "Desactívala", exige escribir el código para habilitar el botón rojo y pone el foco inicial en "Cancelar".
54. Si tras desactivar o eliminar la oferta total supera la capacidad total (o no quedan plantas activas), se muestra un aviso explícito de que el método exacto no tendrá solución.
55. "Ampliar la red" guía en pasos (datos → rutas → resumen) sin pedir datos dos veces, muestra un contador vivo "Faltan N rutas por definir", guarda las rutas con una sola actualización atómica y muestra al final los nuevos conteos de empresas, plantas y rutas.
56. "Definir después" deja el nodo con insignia "Faltan N rutas", el banner de la cabecera de Red logística y el chip en la matriz; completar las rutas los elimina.
57. En la pestaña Rutas, crear una ruta ya existente muestra "Ya existe una ruta … Edítala en la matriz de costos."; con distancia y tarifa el costo unitario se calcula y es de solo lectura; con costo directo se borran distancia y tarifa.
58. El analista ve las mismas tablas sin acciones de escritura; la fila abre un detalle de solo lectura.
59. Estados vacío, sin resultados, cargando, error y 403 de cada pestaña cumplen la sección 5.8; en <768 px las tablas pasan a tarjetas sin pérdida de datos.

**Matriz de costos**
60. La matriz muestra empresas × plantas con encabezados fijos (código, nombre, oferta/capacidad) y cuatro capas: Costo (COP/t), Distancia (km), Tarifa (COP/t·km) y Límite (t/semana); cambiar de capa conserva la celda activa.
61. Cada celda se distingue sin depender del color: con ruta, calculada (`ƒ`), modificada (marca + texto accesible con el valor anterior), inválida (icono + mensaje), sin ruta, inactiva; el mapa de calor y "ruta más barata" son opcionales y siempre dejan los números visibles.
62. Se edita con Enter/F2/escribir; Enter confirma y baja, Tab mueve a la derecha, Esc cancela; los formatos es-CO se aceptan (`12.500,5`) y `1.5` se rechaza con "Usa coma para decimales, por ejemplo 1,5."
63. Los valores negativos o no numéricos se marcan en la celda con mensaje; una ruta sin costo derivable muestra "Esta ruta quedaría sin costo…".
64. Escribir en una celda "Sin ruta" crea la ruta; Supr en la capa Costo la marca "Sin ruta"; en Límite la deja "Sin límite".
65. Con cambios pendientes aparece la barra fija "N cambios sin guardar" con Deshacer, Rehacer, Descartar y Guardar; el contador y las celdas modificadas coinciden.
66. Ctrl+Z/Ctrl+Y deshacen y rehacen por pasos (un pegado = un paso); Ctrl+S guarda; los botones tienen nombre con el paso ("Deshacer: cambio en E3 → Granada").
67. Guardar envía **una sola** petición con las celdas modificadas; si el servidor responde 400 no se guarda ninguna, se muestra "No se guardó ningún cambio. Corrige N celdas." con enlaces a las celdas y el foco va a la primera.
68. Tras guardar con éxito aparece "Se guardaron N cambios." y la acción "Ir a Optimización".
69. Salir con cambios sin guardar (navegación o recarga) muestra el diálogo de 3 opciones o `beforeunload`; con sesión expirada los cambios se restauran tras volver a ingresar.
70. Pegar un bloque desde Excel rellena desde la celda activa y reporta "Se pegaron N celdas; M no son válidas".
71. Al agregar una empresa o planta, la matriz muestra la fila/columna nueva con celdas "Sin ruta" y el chip "Faltan N rutas por definir"; el buscador y "Mostrar inactivas" funcionan con matrices de 100×20 sin bloquear la interfaz (desplazamiento fluido, encabezados fijos).
72. La cuadrícula usa `role="grid"` con una sola parada de Tab, navegación con flechas/Inicio/Fin/Re Pág/Av Pág, `aria-readonly` según rol y nombre accesible completo por celda; existe el panel "Atajos de teclado" (también con `?`).
73. La barra fija o los encabezados no tapan la celda enfocada (2.4.11); las celdas miden ≥44×32 px; a 200 % de zoom la matriz se puede recorrer y existe "Vista de lista" que reproduce todo en una columna; en <768 px la vista de lista es la predeterminada.
74. El analista ve la matriz en solo lectura con el aviso "Solo lectura…", sin barra de guardado y sin edición de celdas.
75. "Guardar como escenario…" crea el escenario con nombre obligatorio y lo hace disponible como base en Optimización, Sensibilidad y Reporte.

**Optimización**
76. La pantalla ofrece Red actual o Escenario guardado como base y una comprobación previa (oferta vs capacidad, empresas sin rutas) con enlaces de solución antes de ejecutar.
77. "Ejecutar método exacto" y "Ejecutar algoritmo genético" son independientes; durante el cálculo muestran spinner, tiempo transcurrido y bloquean un segundo envío; al terminar se anuncia el resultado por `role="status"`.
78. El panel de parámetros del AG incluye población, generaciones, tasa de cruce, tasa de mutación, semilla, elitismo, selección (ruleta/torneo) y cruce (1/2 puntos), con los valores por defecto 60, 150, 80 %, 12 %, 42, 2, torneo y 1 punto, ayuda visible en lenguaje simple por campo y "Restablecer valores por defecto".
79. Los valores fuera de rango muestran mensajes en línea (p. ej. "Debe estar entre 2 y 300.", "El elitismo debe ser menor que la población (60).") y no se envía la petición hasta corregirlos; las tasas se muestran en % y se envían como fracción.
80. Si alguna planta activa no es de capacidad máxima, el botón del AG muestra el motivo y no se puede ejecutar.
81. El resultado muestra estado (con icono y texto), costo total (COP por semana), tiempo y toneladas movidas; con exacto y AG de la misma base, el AG muestra el gap vs exacto.
82. La tabla de asignaciones es ordenable y filtrable, muestra totales y exporta CSV; seleccionar una fila resalta su línea en el mapa.
83. El mapa de flujos dibuja una línea por asignación con grosor proporcional a la cantidad (el mayor flujo tiene el mayor grosor; flujo 0 no se dibuja), leyenda de grosores en toneladas, color por planta con inicial, ficha con toneladas por planta/empresa y alternativa en tabla; las líneas son enfocables con nombre accesible.
84. La verificación de restricciones muestra "Cumple todas las restricciones" o el número de violaciones con la violación máxima, y filas expandibles para oferta por empresa, capacidad por planta y límites por ruta.
85. La curva de convergencia aparece solo para el AG, con eje rotulado, línea de referencia del óptimo exacto (si existe), valor final rotulado, tooltip por teclado y "Ver datos".
86. Un resultado INFEASIBLE muestra "No existe un plan que cumpla todas las restricciones.", la causa más probable con cifras (p. ej. "Faltan 120 t/semana"), acciones de solución (solo administrador) y "Detalle técnico" plegado; las métricas muestran "—".
87. El resultado queda en el historial salvo que se desmarque "Guardar en el historial"; en ese caso se rotula "No guardada".

**Sensibilidad**
88. El constructor ofrece los cuatro tipos de variación (combustible/transporte, oferta, capacidad por planta, costo de ruta), cada uno con su alcance y chips de porcentajes (−100 a 1.000, máx. 40, sin duplicados) y un contador "Total: N escenarios".
89. El bloque de capacidad exige elegir al menos una planta y permite varias; "Usar escenarios de ejemplo" carga la plantilla sin ejecutarla.
90. Con AG incluido y >30 escenarios se pide confirmación antes de ejecutar.
91. Los resultados muestran caso base (costo exacto, AG, gap), precios sombra por planta con uso en % y la insignia "Cuello de botella", y el texto de negocio por planta ("Cada tonelada adicional… bajaría el costo en $ X por semana"); la tarjeta "Dónde conviene ampliar primero" ordena por ahorro por tonelada.
92. La sección de rangos muestra por fila valor actual, mínimo y máximo (o "sin límite") con barra y con texto equivalente accesible; las marcas de escenarios fuera del rango se indican.
93. La tabla de escenarios incluye costo exacto, variación vs base, costo AG, gap %, tiempo exacto y AG, y "¿Cambió la base óptima?", con caso base fijo primero, ordenamiento, filtro por tipo y exportación CSV.
94. Un escenario sin solución aparece como "Sin solución" con costos "—" sin romper la tabla; con caso base sin solución se muestra la sección 12 en lugar de la tabla.
95. Hay tres gráficos (impacto en el costo, costo según variación, gap del AG) con uno visible a la vez, leyenda conmutable por teclado, tooltips accesibles, series distinguibles sin color (forma/trazo/rótulo) y "Ver datos".
96. "Ver reporte comparativo con estos escenarios" abre Reportes con las mismas variaciones precargadas.

**Reporte comparativo**
97. El reporte permite elegir base, parámetros del AG, incluir escenarios e incluir escalabilidad (tamaños seleccionables) y "Generar reporte" produce todas las secciones solicitadas.
98. La sección Resumen muestra costo exacto, costo AG, gap % con insignia (texto), tiempo y relación de tiempos, y una frase de conclusión; "AG alcanza el óptimo" se indica cuando `ag_alcanza_optimo` es verdadero.
99. La comparación incluye tabla y gráficos de costo y tiempo en escalas separadas (sin doble eje) y la tabla de asignaciones lado a lado con "Solo diferencias".
100. La sección de escenarios muestra costo exacto, costo AG, gap % y base cambiada por escenario, con gráfico exacto vs AG.
101. La sección de escalabilidad muestra, por tamaño de red, rutas, tiempos, costos y gap %, con gráfico de tiempo (escala logarítmica rotulada, opcional) y el rótulo "Redes de prueba ficticias".
102. "Exportar" genera CSV UTF-8 con BOM, separador `;`, decimales con coma, encabezados con unidades y nombre `optiagro-reporte-AAAA-MM-DD-HHMM.csv`; los números exportados coinciden con los mostrados.
103. "Imprimir" produce una vista sin sidebar ni botones, fondo blanco, secciones sin cortes internos, gráficos legibles en blanco y negro, encabezado con fecha/usuario/base y paginación.
104. "Presentar" abre pantalla completa con tipografía ≥20 px, una sección por diapositiva, navegación ←/→ y Esc para salir, manteniendo contraste y foco visibles.
105. Con exacto INFEASIBLE el reporte muestra la sección 12 y oculta costo/gap; si falla solo la escalabilidad, el resto se muestra con aviso y "Reintentar solo esta sección".

**Historial**
106. La lista muestra N.º, fecha, método, estado, costo, tiempo, base y (solo administrador) usuario; filtros por método, estado, base y usuario (admin); ordena por fecha, costo y tiempo; un analista solo ve sus ejecuciones.
107. "Abrir" muestra el detalle de solo lectura con metadatos, parámetros y el mismo componente de resultado que la pantalla de origen; "Repetir con estos parámetros" precarga la pantalla de origen sin ejecutar.
108. Se pueden marcar exactamente dos ejecuciones exacto/AG para comparar; la tercera casilla se deshabilita con motivo; la comparación muestra parámetros distintos resaltados, diferencia de costo en COP y %, tiempos y asignaciones A/B.
109. Estados vacío, sin resultados, error y 404 cumplen la sección 13.

**Usuarios y perfil**
110. `/usuarios` lista nombre, usuario, correo, rol, estado y último acceso con búsqueda, filtros por rol y estado, ordenamiento y paginación; la propia fila se etiqueta "(Tú)".
111. Crear/editar usuario valida nombre, apellidos, usuario único, correo y rol obligatorio con mensajes en línea; el rol se elige entre "Administrador" y "Analista" con su descripción.
112. La contraseña inicial tiene Mostrar/Ocultar, permite pegar, "Generar contraseña segura" con "Copiar" y un medidor con nivel en texto y lista de requisitos ✓/✕; el nivel se anuncia por `aria-live` sin saturar.
113. Restablecer contraseña muestra una contraseña temporal una sola vez con "Copiar" y la indicación de cambiarla; desactivar pide confirmación y el usuario desactivado no puede iniciar sesión (Fase 1, criterio 6).
114. Protecciones: el administrador no puede desactivarse, cambiarse el rol ni restablecerse la contraseña desde esta pantalla; el último administrador activo no puede desactivarse ni cambiar de rol; las acciones aparecen deshabilitadas con el motivo visible y el servidor las rechaza con el mismo mensaje.
115. `/perfil` permite editar nombre, apellidos y correo, muestra usuario y rol en solo lectura y cambia la contraseña con actual, nueva (con medidor) y repetición; mensajes "La contraseña actual no es correcta." y "Las contraseñas no coinciden."; el éxito muestra "Contraseña actualizada.".

**Sustentación y transversal**
116. "Guía de sustentación" abre un panel no modal con los 6 pasos, tiempos objetivo, "Ir" y "Hecho", cronómetro opcional y persistencia entre pantallas; no bloquea ni modifica datos.
117. El recorrido completo (cargar demo → cambiar un costo → exacto → AG → sensibilidad → reporte) se puede ejecutar en ≤5 minutos con teclado y ratón sin abrir ninguna otra aplicación; los resultados previos se conservan al navegar.
118. Todas las acciones destructivas de la sección 4.5 piden la confirmación indicada, con foco inicial en la opción segura, `alertdialog` en las irreversibles y Esc para cancelar.
119. Los números siguen el formato es-CO (miles con punto, decimales con coma), con unidades en encabezados o junto al valor (t/semana, COP, COP/t, km, ms/s, %); no hay "NaN", "undefined" ni números sin formatear.
120. Los diálogos y paneles cumplen: foco atrapado, Esc, foco devuelto, nombre accesible y `aria-modal`; los toasts de éxito son `role="status"`, se pausan con hover/foco y no son el único aviso de errores.
121. Los gráficos de todas las pantallas tienen tabla equivalente ("Ver datos"), resumen en texto, series distinguibles sin color, contraste ≥3:1 y no se animan con `prefers-reduced-motion`.
122. Con zoom 200 % y a 320 px de ancho no hay pérdida de contenido ni de funciones en ninguna pantalla nueva (las tablas pasan a tarjetas/lista; mapa y matriz pueden desplazarse).
123. Lighthouse Accesibilidad ≥95 y 0 violaciones críticas/serias de axe en Red logística (lista y panel), Matriz, Optimización (con resultado), Sensibilidad (con resultado), Reporte, Historial, Usuarios y Perfil.

## 17. Datos previstos del backend (para que `backend` los confirme en `docs/api/openapi.yaml`)

| Necesidad UX | Campo/endpoint previsto |
|---|---|
| Usuarios | `GET/POST /usuarios/`, `PATCH /usuarios/{id}/`, `POST /usuarios/{id}/restablecer-clave/`; `activo`, `ultimo_acceso`, `debe_cambiar_clave`; protecciones con 400 y mensaje (último admin, uno mismo) |
| Perfil | `PATCH /auth/me/` (nombre, apellidos, correo); `POST /auth/cambiar-clave/` |
| Costo de operación | `Planta.costo_operacion` (COP/t, ≥0, defecto 0); regla de cómo se suma al costo efectivo |
| AG | `ConfigAG.seleccion` (`torneo`\|`ruleta`) y `tipo_cruce` (`un_punto`\|`dos_puntos`); opcional `torneo_k` |
| Rangos | En `SensibilidadResultado`: `rangos.plantas[]`, `rangos.empresas[]`, `rangos.rutas[]` con `id`, `actual`, `minimo`, `maximo` (null = sin límite); documentar el signo del precio sombra |
| Base cambió | `EscenarioSensibilidad.base_cambio: boolean` |
| Escalabilidad | En `ReporteResultado` o `POST /optimizacion/escalabilidad/`: `tamanos[{empresas, plantas}]` → `puntos[{empresas, plantas, rutas, exacto{objetivo,duracion_ms}, genetico{...}, gap_pct}]` |
| Demo | `POST /demo/cargar/` (admin); `incluye_ficticios` en `ResumenModelo` |
| Historial | Filtro por fecha (`creada_en__gte/lte`); `ficticio`/`incluye_ficticios` por ejecución |
| Validación | La UI exige oferta/capacidad **> 0**; el contrato hoy acepta ≥ 0 (alinear) |

## 18. Componentes nuevos para el agente `ui`

Todos con `<script setup lang="ts">`, tokens `--color-*`, español y accesibilidad según la sección 15. Los que ya existen en `components/ui/` se reutilizan (`UiButton`, `UiField`, `UiAlert`, `UiBadge`, `UiChip`, `UiEmptyState`, `UiSkeleton`, `UiCard`).

| Componente | Descripción y requisitos |
|---|---|
| `UiDataTable` | Tabla semántica con `caption`, columnas ordenables (`aria-sort`), encabezado fijo, selección por casilla, menú de acciones por fila, paginación, densidad, estados cargando/vacío/sin resultados/error, colapso a tarjetas <768 px; números tabulares a la derecha. |
| `UiGridEditable` | Cuadrícula `role="grid"` para la matriz: roving tabindex, edición en celda, selección de rango, copiar/pegar TSV, pila deshacer/rehacer, estados de celda (con ruta, calculada, modificada, inválida, sin ruta, inactiva), virtualización de filas/columnas, encabezados fijos, solo lectura, vista de lista alternativa, panel de atajos. |
| `UiTabs` | Patrón WAI-ARIA tabs (flechas, Home/End), con conteo y sincronización con la URL. |
| `UiDialog` / `UiDrawer` | Diálogo de confirmación (`dialog`/`alertdialog`) y panel lateral (480 px, pantalla completa en móvil) con foco atrapado, Esc, pie fijo con `scroll-padding`, variante de 3 opciones, campo "escribe el código". |
| `UiStepper` | Pasos "Paso 2 de 3" para ampliar la red, con estado y contador de pendientes. |
| `UiSelectorUbicacion` | Campos lat/lon + mapa Leaflet pequeño con marcador movible por clic/teclado, "Centrar en el Meta", "Quitar", pegado de "lat, lon". |
| `UiMetricCard` | Etiqueta, valor grande con unidad, estado/insignia, nota de apoyo, variante delta (▲/▼ con signo y texto). |
| `UiNumberInput` | Entrada es-CO (miles/decimales), `inputmode`, unidad como sufijo, rango y paso, mensajes de error. |
| `UiSegmented`, `UiSwitch`, `UiSelect`, `UiSlider` (+ número) | Controles de formulario accesibles (radio/`aria-checked`); deslizador con campo numérico sincronizado. |
| `UiMenu` | Menú de acciones por fila (menu button WAI-ARIA). |
| `UiToast` | Región `role="status"`, cierre automático pausable, cierre manual; no para errores. |
| `UiMedidorClave` | Medidor de 4 segmentos con texto de nivel y lista de requisitos ✓/✕; `aria-live` con retardo. |
| `UiBarraRango` | Barra horizontal: eje, segmento de rango, rombo del valor actual, extremos rotulados, extremo abierto ("sin límite →"), marcas de escenarios, `aria-hidden` + texto equivalente. |
| `GraficoConvergencia` | Línea de mejor costo por generación, referencia "Óptimo exacto", valor final rotulado, tooltip por teclado, "Ver datos". |
| `GraficoComparacion` | Barras agrupadas exacto vs AG en paneles de escala separada (costo, tiempo), con rótulos directos y tabla equivalente. |
| `GraficoImpacto` | Barras horizontales divergentes (tornado) del cambio de costo por escenario, con signo y flecha. |
| `GraficoLineas` | Series múltiples (costo vs variación; tiempo y gap vs tamaño), marcadores por serie, trazo continuo/discontinuo, escala lineal/log, leyenda conmutable (`aria-pressed`). |
| `MapaFlujos` (estilos y leyenda) | Capa de líneas con grosor proporcional (2–14 px), curva y flecha, color por planta con inicial, etiqueta de toneladas, leyenda de grosores, estado "sin flujos"; líneas enfocables. |
| `UiProgresoUso` | Barra de uso (%) con texto, para capacidad de plantas. |
| `UiDiff` | Tabla/valores A vs B con "Cambió" resaltado, delta con signo. |
| `UiPanelGuia` | Panel no modal de la sustentación (píldora colapsable, pasos, cronómetro). |
| `UiAyuda` | Disclosure "¿Cómo funciona?" y "¿Qué es…?" con glosario; contenido siempre en texto, no solo tooltip. |

**Paleta de gráficos (propuesta; `ui` verifica contrastes ≥3:1 contra el fondo y ≥4.5:1 en textos, y define la variante oscura):**

| Token | Valor | Uso |
|---|---|---|
| `--grafico-exacto` | `#1f6b43` | Método exacto (trazo continuo, marcador círculo) |
| `--grafico-ag` | `#1d5c8a` | Algoritmo genético (trazo discontinuo, marcador rombo) |
| `--grafico-referencia` | `#5a6b60` | Óptimo exacto de referencia, caso base, ejes |
| `--grafico-mas-cuesta` / `--grafico-ahorra` | `#b42318` / `#1f6b43` | Variación de costo; siempre con ▲/▼, signo y texto |
| `--grafico-cat-1…6` | `#1f6b43` `#1d5c8a` `#b45309` `#7e3fa8` `#be123c` `#0e7490` | Plantas/series categóricas (flujos por planta); cada serie con forma de marcador y rótulo propios; ciclar con rótulo si hay más de 6 |
| `--grafico-banda` | `#e6f4ea` | Rangos y bandas de referencia |

Reglas: máx. 6 series por gráfico; rejilla `--color-borde`; texto de ejes `--color-texto-suave` ≥12 px; el significado jamás solo en color.

---

## 19. Decisiones que requieren confirmación del usuario

1. **D1 — Dónde viven los escenarios guardados.** Se propone reemplazar "Escenarios" del menú por **"Matriz de costos"** y tratar los escenarios guardados como "base de cálculo" (se guardan desde la matriz y se eligen en Optimización, Sensibilidad y Reporte). ¿Basta o se quiere una pantalla propia de "Escenarios guardados" (listar, renombrar, eliminar)?
2. **D2 — Periodo:** el contrato dice t/semana; se usa "t/semana" y COP/semana en toda la interfaz. Confirmar.
3. **D3 — Sin Django admin:** confirmar que `/admin/` queda fuera de la experiencia y de la documentación del cliente. Hay que actualizar `CLAUDE.md` (sección Autenticación) y Fase 1 §4/criterios 14, 25, 26 (yo solo escribo en `docs/ux/`).
4. **D4 — "Cargar datos de demostración":** ¿habrá endpoint/botón para el administrador (paso 1 de la sustentación) o el demo se carga por línea de comandos antes de presentar? Si no, el paso 1 se reduce a "verificar" y se quita el botón.
5. **D5 — Código de nodo no editable** tras crearlo (propuesto, para no romper rutas e historial). Confirmar o permitir cambiarlo.
6. **D6 — Costo de operación por planta:** ¿se suma al costo efectivo de cada ruta (transporte + operación)? Se propone mostrarlo en la matriz como fila de solo lectura y un conmutador "costo total por tonelada". Confirmar la fórmula con el backend.
7. **D7 — AG y modo de oferta:** ¿el AG solo admite "retirar toda la oferta" y plantas de capacidad máxima? Se deshabilita con motivo en caso contrario.
8. **D8 — Signo del precio sombra:** el backend debe documentar el signo; la interfaz redacta "bajaría/aumentaría el costo" según el signo recibido.
9. **D9 — Forma de los rangos de variación** (sección 17) y si cubren capacidades, ofertas y costos de ruta, o solo capacidades para empezar.
10. **D10 — Umbrales de lectura del gap:** ≤1 % Excelente, 1–5 % Aceptable, >5 % Mejorable. Confirmar o ajustar.
11. **D11 — Reutilizar resultados de la sesión** en el reporte (en lugar de recalcular) cuando base y parámetros coinciden. ¿Se desea?
12. **D12 — Formato del CSV:** UTF-8 con BOM, separador `;`, decimales con coma (Excel es-CO). Alternativa: coma y punto decimal (estándar). Confirmar.
13. **D13 — Usuarios:** no se elimina, solo se desactiva (conserva el historial). ¿Se requiere eliminar de verdad?
14. **D14 — Política de contraseñas:** longitud mínima 10 y reglas de Django (no común, no numérica, no similar). Confirmar con backend (hoy Django exige 8).
15. **D15 — Primer administrador:** se crea por línea de comandos en el despliegue (sin pantalla de registro). Confirmar.
16. **D16 — Historial:** filtro por fecha en servidor (hoy no existe) y retención de ejecuciones.
17. **D17 — Comparación de ejecuciones:** limitada a exacto/AG; ¿se quiere comparar también reportes o sensibilidades por su resumen?
18. **D18 — Rendimiento en vivo:** la plantilla de sensibilidad con AG debe terminar en <15 s; si no, se corre con "Rápido" o sin AG por defecto. ¿Qué tolerancia de espera tiene la sustentación?
19. **D19 — Aviso de demostración en resultados históricos:** el contrato no marca si una ejecución usó datos ficticios; se pide `incluye_ficticios` por ejecución o se muestra solo para la red actual.
20. **D20 — Oferta/capacidad > 0:** la UI exige mayor que 0 (el contrato acepta 0). ¿Se alinea el backend o se permite 0 como "sin oferta/capacidad"?
21. **D21 — Rol del analista en la matriz:** hoy solo lectura. Si el analista debe poder simular cambios de costo sin guardarlos, se añade un "modo simulación" local; confirmar si se necesita (el efecto ya se logra con Sensibilidad).
22. **D22 — Redes de prueba de escalabilidad:** tamaños 10×4, 20×6, 40×10, 80×16 y datos sintéticos generados en el servidor. Confirmar tamaños y que se rotulen siempre como ficticios.
