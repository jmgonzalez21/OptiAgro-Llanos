# Fase 1 — Login, shell autenticado e Inicio (mapa)

Especificación UX para `ui` (sistema visual) y `frontend` (pantallas). Idioma de la interfaz: español (Colombia). Alcance: solo esta fase; las pantallas de fases futuras aparecen únicamente como ítems deshabilitados.

## 0. Dirección de tono (el color lo define `ui`)

Cliente objetivo: mayorista muy importante. La interfaz debe transmitir **confianza, orden y frescura agroindustrial moderna**.

- Fondo blanco dominante, verde claro como acento y para estados activos; mucho espacio en blanco; sin degradados estridentes, sombras pesadas ni ilustraciones infantiles.
- Tipografía sans moderna, 2 pesos como máximo en cada vista; títulos con buen tamaño, texto de apoyo en gris neutro.
- Esquinas redondeadas suaves (8–12 px), bordes finos, sombras muy sutiles, transiciones de 150–200 ms (respetar `prefers-reduced-motion`).
- Datos de demostración (si los hay) marcados como "Datos de demostración" (CLAUDE.md).
- Textos sobrios y de negocio: "estación", "oferta", "capacidad". Sin jerga técnica en pantalla.

Trazabilidad: la autenticación y los roles vienen de CLAUDE.md (sección Autenticación); el mapa visualiza la red del requisito 1 del PDF (10 agroempresas → 4 plantas).

---

## 1. Login

### 1.1 Layout

- **Escritorio (≥1024 px):** pantalla dividida 50/50 (mínimo 480 px por lado en ≥1280; en 1024–1279 proporción 45/55).
  - **Panel de marca** (izquierda, fondo verde muy claro): logo OptiAgro-Llanos, titular de valor, 3 puntos de valor, patrón/ilustración SVG sobrio (líneas finas de curvas de nivel + nodos y arcos que evocan una red logística; monocromo verde en 2–3 tonos; `aria-hidden="true"`, sin texto incrustado). Pie: "EcoResiduos del Llano S.A.S. · Meta, Colombia".
  - **Panel de formulario** (derecha, blanco): tarjeta centrada de máx. 400 px de ancho.
- **Tableta (600–1023 px):** el panel de marca se reduce a una franja superior (logo + titular, ~160 px); formulario debajo.
- **Móvil (<600 px):** solo logo arriba y formulario; sin ilustración; padding lateral 16–24 px.

### 1.2 Contenido del panel de marca

- Titular: **"Menos residuos, mejores rutas."**
- Subtítulo: "Planifica el transporte de residuos agropecuarios del Meta con costos mínimos y decisiones respaldadas por datos."
- Puntos de valor (icono + línea corta):
  1. "Red logística clara: de la finca a la planta."
  2. "Escenarios que muestran el costo antes de decidir."
  3. "Resultados comparables y listos para reportar."

### 1.3 Formulario

| Elemento | Especificación |
|---|---|
| Título | "Bienvenido" (h1) + subtítulo "Ingresa con tu cuenta para continuar." |
| Campo 1 | Etiqueta visible **"Usuario"** (o correo si el backend usa correo; ver Decisiones). `autocomplete="username"`, `autocapitalize="none"`, `spellcheck="false"`, `autofocus` al cargar. |
| Campo 2 | Etiqueta visible **"Contraseña"**, `type="password"`, `autocomplete="current-password"`. Botón al final del campo "Mostrar"/"Ocultar" (icono ojo + `aria-label` "Mostrar contraseña"/"Ocultar contraseña", `aria-pressed`, `type="button"`). |
| Acción primaria | Botón ancho completo **"Iniciar sesión"** (envía con Enter desde cualquier campo). |
| Enlace secundario | "¿Olvidaste tu contraseña? **Contacta al administrador.**" Es texto informativo; "Contacta al administrador" muestra al activarse una nota inline: "Pide al administrador del sistema que restablezca tu contraseña." (sin `mailto` ni flujo funcional). |
| Ausentes | Sin "Registrarse", sin "Recordarme", sin login social. |
| Pie | "© 2026 OptiAgro-Llanos · Universidad de los Llanos" (texto pequeño, contraste AA). |

Tras iniciar sesión se redirige a Inicio (`/`), o a la ruta que el usuario intentaba abrir (parámetro `redirect`, solo rutas internas).

### 1.4 Validación en línea

- Se valida **al salir del campo (blur)** y al enviar; nunca mientras se escribe por primera vez. Tras el primer error, se revalida mientras se corrige.
- Mensajes bajo cada campo, vinculados con `aria-describedby`, campo con `aria-invalid="true"`:
  - Usuario vacío: "Ingresa tu usuario."
  - Contraseña vacía: "Ingresa tu contraseña."
- Al enviar con errores: foco al primer campo inválido; no se llama a la API.
- No se valida complejidad de contraseña en el login. No se recorta (`trim`) la contraseña; sí el usuario.

### 1.5 Estados

| Estado | Comportamiento |
|---|---|
| Reposo | Botón habilitado (no deshabilitar por campos vacíos: la validación explica el porqué). |
| Cargando | Botón con spinner y texto "Ingresando…", `aria-busy="true"`, campos de solo lectura (no `disabled`, para no perder el foco), segundo envío bloqueado. Si tarda >8 s: texto bajo el botón "Esto está tardando más de lo normal…". |
| Éxito | Transición a Inicio; el foco va al título de la página. |
| Error | Alerta al inicio del formulario (`role="alert"`), tono de error sobrio, con icono + texto (no solo color). El foco se mueve a la alerta o al campo contraseña según el caso. Los datos del usuario se conservan; la contraseña se vacía solo en credenciales inválidas. |

### 1.6 Mensajes de error

| Caso (HTTP) | Título | Detalle | Foco |
|---|---|---|---|
| Credenciales inválidas (401) | "Usuario o contraseña incorrectos." | "Revisa los datos e inténtalo de nuevo." (no revelar cuál es incorrecto) | Contraseña |
| Cuenta sin permisos / inactiva (403) | "Tu cuenta no tiene acceso a OptiAgro." | "Contacta al administrador para que active tu cuenta o te asigne un rol." | Alerta |
| Servidor caído / sin red / 5xx | "No pudimos conectar con el servidor." | "Verifica tu conexión e inténtalo de nuevo en unos minutos." + botón secundario "Reintentar" | Alerta |
| Demasiados intentos (429, si el backend lo implementa) | "Demasiados intentos." | "Espera unos minutos antes de volver a intentarlo." | Alerta |
| Sesión expirada (redirección desde la app) | Aviso informativo (no error): "Tu sesión expiró. Ingresa de nuevo para continuar." | — | Usuario |
| Error inesperado | "Algo salió mal." | "Inténtalo de nuevo. Si persiste, contacta al administrador." | Alerta |

### 1.7 Accesibilidad específica

- Orden de tabulación: Usuario → Contraseña → Mostrar/Ocultar → Iniciar sesión → "Contacta al administrador". Un `skip link` no es necesario (página corta), pero el `<main>` debe estar marcado.
- `<form>` real con `<label for>`; sin placeholders como etiquetas.
- Los gestores de contraseñas y el autocompletado del navegador deben funcionar: `name="username"`, `name="password"`, `autocomplete` correcto, sin `autocomplete="off"`, sin bloquear pegar.
- Anillo de foco visible (≥2 px, contraste ≥3:1 contra el fondo) en todos los controles; objetivos táctiles ≥44×44 px (WCAG 2.2: mínimo 24×24).
- Alertas anunciadas por lector de pantalla (`role="alert"`); el cambio de estado de carga anunciado con `aria-live="polite"`.
- Ilustración decorativa oculta a tecnologías de apoyo. Título de documento: "Iniciar sesión · OptiAgro-Llanos".
- El texto de ayuda no puede depender solo del color. Contraste AA: 4.5:1 texto, 3:1 componentes.
- Cumple WCAG 2.2 3.3.8 (Autenticación accesible): sin pruebas cognitivas, pegar permitido.

---

## 2. Shell autenticado

### 2.1 Estructura

```
┌──────────┬─────────────────────────────────────────────┐
│ Sidebar  │ Topbar (título de página · avatar/menú)     │
│ (nav)    ├─────────────────────────────────────────────┤
│          │ Contenido (área útil)                       │
└──────────┴─────────────────────────────────────────────┘
```

Landmarks: `<nav aria-label="Principal">`, `<header>`, `<main id="contenido">`. Un `skip link` "Saltar al contenido" es el primer elemento enfocable.

### 2.2 Panel lateral

- Ancho expandido 256 px; colapsado 72 px (solo iconos con tooltip y `aria-label`). El botón de colapsar está al pie o junto al logo, con `aria-expanded` y etiqueta "Contraer menú"/"Expandir menú". La preferencia se recuerda (localStorage, con try/catch).
- Parte superior: logo + nombre "OptiAgro-Llanos" (colapsado: solo isotipo).
- Ítems de navegación (icono + texto):

| Ítem | Estado en Fase 1 | Notas |
|---|---|---|
| **Inicio** | Activo (página actual) | `aria-current="page"` |
| Red logística | Deshabilitado + etiqueta "Próximamente" | |
| Escenarios | Deshabilitado + "Próximamente" | |
| Optimización | Deshabilitado + "Próximamente" | |
| Sensibilidad | Deshabilitado + "Próximamente" | |
| Reportes | Deshabilitado + "Próximamente" | |

- **Estado activo:** fondo verde claro, barra vertical de acento de 3 px a la izquierda, texto e icono en verde oscuro con peso mayor (no solo color: la barra y el peso lo refuerzan).
- **Ítems deshabilitados:** texto atenuado pero con contraste ≥4.5:1 (la etiqueta "Próximamente" es información, no decoración), `aria-disabled="true"`, sin `href`, no activables, **sí** enfocables con teclado para que el lector de pantalla los anuncie ("Red logística, no disponible, próximamente"). Tooltip: "Disponible en una próxima fase". Colapsado: la etiqueta pasa al tooltip.
- Pie del sidebar: versión de la app en texto pequeño ("v0.1 · Datos de demostración" solo si aplica).

### 2.3 Barra superior

- Izquierda: botón de menú (solo tableta/móvil), título de la página en `h1` ("Inicio"), y opcionalmente una línea de contexto en gris ("Red logística del Meta").
- Derecha: **avatar** (círculo con iniciales del nombre, fondo verde claro; foto no se admite en esta fase) como botón de menú: `aria-haspopup="menu"`, `aria-expanded`, etiqueta "Menú de usuario".
- **Menú de perfil** (patrón menu button WAI-ARIA):
  - Cabecera no interactiva: **Nombre completo**, correo/usuario, **rol** como chip ("Administrador" / "Analista").
  - "Mi perfil" — deshabilitado + "Próximamente".
  - Separador.
  - **"Cerrar sesión"** (icono salir). Activarlo: limpia tokens y estado, redirige al login con aviso "Cerraste sesión correctamente." (`role="status"`). Sin diálogo de confirmación (acción reversible).
  - Teclado: Enter/Espacio/↓ abre y enfoca el primer ítem; ↑/↓ navega; Home/End; Esc cierra y devuelve el foco al avatar; Tab cierra.

### 2.4 Responsive

| Ancho | Sidebar | Topbar |
|---|---|---|
| ≥1280 px | Expandido por defecto, colapsable | Título + avatar |
| 1024–1279 px | Colapsado por defecto (iconos), expandible | Título + avatar |
| 600–1023 px | **Drawer** oculto; se abre con botón hamburguesa; overlay con fondo atenuado; ancho 280 px | Hamburguesa + título + avatar |
| <600 px | Drawer a ancho 85 % (máx. 320 px) | Hamburguesa + título corto + avatar |

Drawer: `role="dialog"` modal con `aria-label="Menú principal"`, foco atrapado, Esc y clic en overlay lo cierran, el foco regresa al botón hamburguesa, se cierra al navegar, el scroll del fondo se bloquea.

---

## 3. Inicio = Mapa

### 3.1 Propósito

Dar al usuario, nada más entrar, la imagen de su red: **dónde están las empresas agropecuarias (oferta de residuos) y las plantas de procesamiento (capacidad)** en el Meta. Es solo lectura en esta fase.

### 3.2 Layout

El mapa ocupa **todo el área útil** (bajo la topbar, a la derecha del sidebar), sin márgenes internos ni scroll de página. Los controles flotan sobre el mapa:

- **Arriba-izquierda:** tarjeta de filtros y contador (ver 3.5).
- **Arriba-derecha:** controles de mapa (zoom +/−, reencuadrar, pantalla completa), en columna.
- **Abajo-izquierda:** leyenda (colapsable en móvil).
- **Abajo-derecha:** atribución obligatoria "© OpenStreetMap © CARTO" (Leaflet).
- **Ficha de estación:** popup anclado al marcador en escritorio; en móvil, hoja inferior (bottom sheet).

Mapa base: **Leaflet + CARTO Positron** (claro, tono neutro que deja resaltar el verde). Encuadre inicial: ajustar (`fitBounds`) a todas las estaciones visibles con padding; si no hay ninguna, centro del Meta (aprox. 4.0° N, −73.0° O), zoom 8. Zoom mínimo 6, máximo 17.

### 3.3 Tipos de estación (forma + color + etiqueta)

| Tipo | Etiqueta | Forma del marcador | Icono interior | Color |
|---|---|---|---|---|
| Empresa agropecuaria | "Empresa agropecuaria" (oferta) | **Círculo** | Hoja/brote | Verde medio |
| Planta de procesamiento | "Planta de procesamiento" (capacidad) | **Cuadrado redondeado / pin con base cuadrada** (algo más grande) | Engranaje/fábrica | Verde oscuro o tono de contraste definido por `ui` |

Reglas: la distinción debe ser perceptible **en escala de grises** (forma + icono) y con contraste ≥3:1 entre el marcador y el mapa. Tamaño del marcador ≥32 px (objetivo táctil ≥44 px con área invisible). Las plantas se dibujan por encima de las empresas cuando se solapan. Con zoom bajo y estaciones muy próximas: agrupación (cluster) con contador, si el volumen lo exige; con ~14 estaciones no se agrupa por defecto.

### 3.4 Leyenda

Siempre visible (abajo-izquierda): muestra el marcador real de cada tipo + etiqueta + conteo ("Empresas agropecuarias · 10", "Plantas de procesamiento · 4"). Los conteos reflejan las estaciones activas. Es también un resumen para lectores de pantalla (`role="group"`, `aria-label="Leyenda del mapa"`).

### 3.5 Filtros y contador

- Dos **chips conmutables** (`<button aria-pressed>`): "Empresas agropecuarias", "Plantas de procesamiento". Ambos activos por defecto; el estado se anuncia. Si el usuario intenta apagar ambos, se permite y se muestra el estado "sin resultados por filtros" (3.7) con acción "Mostrar todas".
- **Contador** (`aria-live="polite"`): "Mostrando **14** de 14 estaciones" / "Mostrando 4 de 14 estaciones". El total es el de estaciones activas con coordenadas.
- Aplicar un filtro no cambia el encuadre; el botón "Reencuadrar" ajusta a las visibles.

### 3.6 Controles de mapa

| Control | Comportamiento | Etiqueta accesible |
|---|---|---|
| Zoom + / − | Zoom de un nivel; también `+`/`−` con el mapa enfocado, flechas para mover, rueda y pellizco | "Acercar" / "Alejar" |
| Reencuadrar | Ajusta el mapa a las estaciones visibles (icono de marco con esquinas) | "Ver todas las estaciones" |
| Pantalla completa | Alterna pantalla completa del contenedor del mapa (conserva filtros, leyenda y ficha); Esc la cierra | "Pantalla completa" / "Salir de pantalla completa" |

Todos son botones reales con tooltip, ≥44 px en táctil, operables por teclado. El rueda del ratón hace zoom solo si el mapa tiene el foco (evita atrapar el scroll en móvil: gestos de dos dedos).

### 3.7 Ficha de estación (popup)

Se abre al hacer clic/tocar o Enter/Espacio sobre un marcador enfocado. Contenido:

```
┌──────────────────────────────┐
│ [icono] Finca La Esperanza   │  <- nombre (h2 de la ficha)
│ Empresa agropecuaria  (chip) │
│ Municipio: Acacías           │
│ Oferta: 120 t/mes            │  <- empresa: "Oferta"
│                          [×] │
└──────────────────────────────┘
```

- Empresa: **Oferta** en toneladas (`t`); planta: **Capacidad máxima** en toneladas (`t`). Unidad de periodo según el modelo (confirmar: t/mes o t/semana).
- Campos: nombre, tipo, municipio, oferta/capacidad. Sin edición ni enlaces a fases futuras.
- Cierre: botón "×" (`aria-label="Cerrar ficha"`), Esc, clic fuera. El foco vuelve al marcador.
- Un solo popup abierto a la vez. Al abrirlo, el mapa no se mueve salvo para que la ficha quede entera en pantalla.
- Marcadores: son elementos enfocables (`role="button"`, `aria-label="Finca La Esperanza, empresa agropecuaria, Acacías"`), orden de tabulación de norte a sur, luego oeste a este (determinista). El control del mapa se salta con un enlace "Ir a la lista de estaciones" (ver 3.9).

### 3.8 Regla de negocio: solo estaciones activas

- El mapa, la leyenda y el contador muestran **únicamente estaciones activas** (`activa = true`).
- Una estación **eliminada o desactivada** desaparece del mapa en la siguiente carga; si el usuario tiene la ficha de esa estación abierta y llega una actualización, la ficha se cierra con aviso "Esta estación ya no está activa."
- Refresco: al entrar a Inicio y con un botón/atajo "Actualizar" (icono refrescar) en la tarjeta de filtros; no se requiere tiempo real en esta fase. Al volver a la pestaña tras >5 min se recarga en segundo plano.
- Los datos maestros (nodos) los gestiona el administrador en Django admin (ver sección 4).

### 3.9 Estados

| Estado | Qué ve el usuario |
|---|---|
| **Cargando** | Mapa base visible de inmediato; velo suave + spinner centrado y texto "Cargando estaciones…" (`role="status"`). Los filtros y el contador muestran esqueleto. Los controles de zoom siguen operando. |
| **Con datos** | Marcadores, leyenda, contador, filtros. |
| **Vacío** (0 estaciones activas) | Mapa del Meta centrado + tarjeta centrada: icono de mapa, **"Aún no hay estaciones activas"**, "Cuando el administrador active empresas o plantas, aparecerán aquí." Para `administrador`: botón secundario **"Gestionar en el panel de administración"** (abre `/admin/` en pestaña nueva). Para `analista`: sin botón. |
| **Sin resultados por filtros** | Mapa sin marcadores + aviso "No hay estaciones con los filtros elegidos." + botón "Mostrar todas". |
| **Error al cargar** (red/5xx) | Mapa base visible + banner/tarjeta (`role="alert"`): **"No pudimos cargar las estaciones."** "Revisa tu conexión e inténtalo de nuevo." + botón **"Reintentar"**. Sin marcadores parciales. |
| **Sin permisos (403)** | "No tienes permiso para ver las estaciones. Contacta al administrador." (sin reintentar) |
| **Sesión expirada (401 irrecuperable)** | Redirige al login con el aviso de la sección 1.6. |
| **Estaciones sin coordenadas** | No se dibujan. Se listan aparte (ver abajo). |

**Estaciones sin coordenadas:** aviso compacto (chip ámbar sobrio con icono) en la tarjeta de filtros: "**2 estaciones sin ubicación**" → abre un panel/lista (disclosure o diálogo no modal) con nombre, tipo, municipio y oferta/capacidad de cada una, y el texto "Estas estaciones están activas pero no tienen coordenadas, por lo que no aparecen en el mapa." Para `administrador`: nota "Agrega las coordenadas en el panel de administración." El contador cuenta solo las visibles en el mapa ("Mostrando 12 de 12 en el mapa"); las sin ubicación se mencionan en su chip. Coordenadas fuera del Meta o inválidas (lat ∉ [−90,90], lng ∉ [−180,180]) se tratan igual que ausentes.

**Alternativa accesible al mapa:** enlace "Ver lista de estaciones" en la tarjeta de filtros que abre un panel con la tabla de estaciones activas (nombre, tipo, municipio, oferta/capacidad), operable por teclado y lector de pantalla; seleccionar una fila centra el mapa y abre la ficha. Cumple que la información del mapa no dependa solo de la vista espacial.

### 3.10 Datos que necesita el frontend (para `backend`/contrato)

Listado de estaciones activas: `id`, `nombre`, `tipo` (`empresa` | `planta`), `municipio`, `latitud`, `longitud` (nullable), `oferta` o `capacidad` (número, toneladas), `activa`. El filtro `activa=true` debe aplicarse **en el servidor** (el cliente no debe recibir inactivas). Cualquier cambio de contrato va primero a `docs/api/openapi.yaml`.

---

## 4. Roles en la Fase 1

| Aspecto | `administrador` | `analista` |
|---|---|---|
| Login, shell, avatar y menú | Sí | Sí |
| Inicio (mapa, filtros, ficha, lista) | Sí | Sí |
| Chip de rol en el menú | "Administrador" | "Analista" |
| Estado vacío / sin coordenadas | Ve la acción "Gestionar en el panel de administración" / nota de coordenadas | Solo ve el mensaje informativo |
| Enlace "Panel de administración" (`/admin/`) | Visible en el menú de perfil, entre "Mi perfil" y "Cerrar sesión" (pestaña nueva, con icono de enlace externo) | No visible |
| Ítems "Próximamente" | Igual para ambos | Igual para ambos |
| Edición de estaciones desde el mapa | No (solo lectura) | No |

Gestión de datos maestros: en esta fase, la **creación, edición, activación/desactivación y eliminación de nodos (estaciones) y rutas se hace en Django admin** (`/admin/`, login por sesión de Django propio, distinto del login JWT de la SPA). Más adelante el administrador tendrá pantallas equivalentes dentro de la SPA (Red logística, ampliar empresas y sedes). El analista nunca gestiona datos maestros. Si un usuario con rol analista abre una ruta restringida, ve la pantalla "No tienes permiso para ver esta página." con botón "Volver al inicio".

---

## 5. Criterios de aceptación (QA)

**Login**
1. La pantalla de login muestra panel de marca y formulario en ≥1024 px; en <1024 px el panel de marca se reduce o desaparece sin scroll horizontal hasta 320 px de ancho.
2. No existen enlaces ni botones funcionales de registro ni de recuperación de contraseña; sí el texto "¿Olvidaste tu contraseña? Contacta al administrador."
3. Enviar con campos vacíos muestra "Ingresa tu usuario." / "Ingresa tu contraseña.", mueve el foco al primer campo inválido y no realiza ninguna petición.
4. El botón Mostrar/Ocultar alterna el tipo del campo, actualiza `aria-pressed` y su etiqueta, y no envía el formulario.
5. Credenciales inválidas (401) muestran "Usuario o contraseña incorrectos." sin revelar cuál falló; el usuario se conserva, la contraseña se vacía y el foco va a contraseña.
6. Cuenta sin permisos/inactiva (403) muestra "Tu cuenta no tiene acceso a OptiAgro." Servidor caído o sin red muestra "No pudimos conectar con el servidor." con botón "Reintentar".
7. Durante el envío el botón muestra "Ingresando…", `aria-busy="true"` y no permite un segundo envío.
8. Un gestor de contraseñas (p. ej. el del navegador) detecta y rellena usuario y contraseña (`autocomplete="username"` / `"current-password"`); se puede pegar en ambos campos.
9. Login exitoso lleva a Inicio, o a la ruta interna previa indicada en `redirect`; un `redirect` externo se ignora.

**Shell**
10. El sidebar muestra Inicio (activo, `aria-current="page"`, barra de acento + texto en peso mayor) y Red logística, Escenarios, Optimización, Sensibilidad, Reportes con la etiqueta "Próximamente", `aria-disabled="true"`, sin navegación al activarlos.
11. Los ítems deshabilitados son enfocables con Tab y el lector de pantalla los anuncia como no disponibles.
12. El sidebar se colapsa/expande con el botón (`aria-expanded`), conserva la preferencia al recargar y en modo colapsado cada icono tiene tooltip y nombre accesible.
13. En <1024 px el sidebar es un drawer: se abre con la hamburguesa, atrapa el foco, se cierra con Esc/overlay/navegación y devuelve el foco al botón que lo abrió.
14. El avatar abre un menú con nombre, rol, "Mi perfil" (deshabilitado, "Próximamente") y "Cerrar sesión"; solo el administrador ve "Panel de administración".
15. El menú de perfil cumple el patrón de teclado (Enter/Espacio/↓ abre, ↑/↓/Home/End navegan, Esc cierra y devuelve el foco al avatar).
16. "Cerrar sesión" elimina tokens y estado, redirige al login con "Cerraste sesión correctamente." y el botón Atrás del navegador no restablece una vista protegida con datos.
17. Una ruta protegida sin sesión redirige al login; con rol insuficiente muestra "No tienes permiso para ver esta página."

**Mapa**
18. Inicio muestra el mapa Leaflet con CARTO Positron ocupando el área útil completa, sin scroll de página, con la atribución visible.
19. Solo aparecen estaciones con `activa = true`: al desactivar o eliminar una estación en Django admin y recargar Inicio, desaparece del mapa, de la leyenda, del contador y de la lista.
20. Empresas y plantas se distinguen por forma e icono además del color; el contraste de cada marcador frente al mapa es ≥3:1; en escala de grises siguen siendo distinguibles.
21. La leyenda muestra ambos tipos con su conteo, y coincide con los marcadores existentes.
22. Los chips de filtro (`aria-pressed`) muestran/ocultan cada tipo y el contador ("Mostrando X de Y estaciones") se actualiza y se anuncia con `aria-live`.
23. Seleccionar un marcador (clic, toque, Enter o Espacio) abre una ficha con nombre, tipo, municipio y oferta (empresa) o capacidad (planta) en toneladas; Esc/× la cierra y devuelve el foco al marcador.
24. Los controles de zoom, "Ver todas las estaciones" y pantalla completa existen, tienen nombre accesible y funcionan con teclado y táctil; "Ver todas" ajusta el encuadre a las estaciones visibles; Esc sale de pantalla completa.
25. Estado de carga visible (con `role="status"`) mientras llega la respuesta; estado vacío con "Aún no hay estaciones activas" (acción de administración solo para administrador); estado de error con "No pudimos cargar las estaciones." y "Reintentar" que recarga sin refrescar la página.
26. Una estación activa sin coordenadas válidas no se dibuja; aparece en la lista "estaciones sin ubicación" con sus datos y no cuenta en el contador del mapa.
27. La lista alternativa de estaciones es accesible por teclado y seleccionar una fila centra el mapa y abre su ficha.
28. Todos los marcadores son alcanzables con Tab, con nombre accesible "nombre, tipo, municipio"; el mapa no genera trampa de foco.

**Accesibilidad transversal (WCAG 2.2 AA)**
29. Contraste: texto normal ≥4.5:1, texto grande y componentes de interfaz ≥3:1, incluidos estados deshabilitados con etiqueta "Próximamente" y chips.
30. Todo es operable solo con teclado, sin trampas; el orden de foco sigue el orden visual; el anillo de foco es visible (≥2 px, ≥3:1) y no queda oculto tras barras fijas (2.4.11).
31. Objetivos táctiles y de puntero ≥24×24 px (meta del proyecto: 44×44 px en controles principales).
32. Hay `skip link` "Saltar al contenido", landmarks (`header`, `nav`, `main`), un único `h1` por vista, `lang="es"` y títulos de documento únicos por pantalla.
33. Con zoom al 200 % y reflujo a 320 px de ancho no hay pérdida de contenido ni funciones (1.4.10), salvo el propio mapa, que puede desplazarse en 2 dimensiones.
34. Con `prefers-reduced-motion` no hay animaciones de zoom/transición no esenciales; ninguna información se transmite solo por color.
35. Los cambios dinámicos (errores, contador, carga, cierre de sesión) se anuncian por lectores de pantalla (`role="alert"`/`status`/`aria-live`).
36. Lighthouse Accesibilidad ≥95 y 0 violaciones críticas/serias de axe en login, shell+Inicio y estados vacío/error.

---

## 6. Wireframes

### 6.1 Login (escritorio)

```
┌─────────────────────────────────┬──────────────────────────────────┐
│  PANEL DE MARCA (verde claro)   │  PANEL DE FORMULARIO (blanco)    │
│                                 │                                  │
│  [logo] OptiAgro-Llanos         │                                  │
│                                 │        Bienvenido                │
│  Menos residuos,                │   Ingresa con tu cuenta para     │
│  mejores rutas.                 │   continuar.                     │
│                                 │                                  │
│  Planifica el transporte de     │   ┌ ! Usuario o contraseña ───┐  │
│  residuos agropecuarios del     │   │   incorrectos.  (si error) │  │
│  Meta con costos mínimos...     │   └────────────────────────────┘  │
│                                 │   Usuario                        │
│  ✓ Red logística clara          │   ┌────────────────────────────┐ │
│  ✓ Escenarios que muestran      │   │                            │ │
│    el costo                     │   └────────────────────────────┘ │
│  ✓ Resultados comparables       │   Contraseña                     │
│                                 │   ┌──────────────────── [ojo] ┐  │
│   ·  ○──○        ╭─╮            │   │                            │  │
│    ╲╱   ╲  ○────○  │ patrón     │   └────────────────────────────┘ │
│   ○──○──□  ╰──╯    │ SVG        │                                  │
│   (curvas de nivel + red)       │   [      Iniciar sesión       ]  │
│                                 │                                  │
│  EcoResiduos del Llano S.A.S.   │   ¿Olvidaste tu contraseña?      │
│  Meta, Colombia                 │   Contacta al administrador.     │
│                                 │   © 2026 OptiAgro-Llanos         │
└─────────────────────────────────┴──────────────────────────────────┘
```

### 6.2 Shell + Inicio (escritorio, sidebar expandido)

```
┌────────────────┬─────────────────────────────────────────────────────────┐
│ [logo]         │ Inicio                                      (JP) ▾      │
│ OptiAgro-Llanos│ Red logística del Meta                                  │
│                ├─────────────────────────────────────────────────────────┤
│▌◉ Inicio       │┌────────────────────────┐              ┌───┐           │
│  ◌ Red logís-  ││ [● Empresas][■ Plantas]│              │ + │ zoom      │
│    tica        ││ Mostrando 14 de 14     │              │ − │           │
│    Próximamente││ ⚠ 2 sin ubicación      │              ├───┤           │
│  ◌ Escenarios  ││ Ver lista · Actualizar │              │ ⤢ │ reencuadrar│
│    Próximamente│└────────────────────────┘              │ ⛶ │ pantalla  │
│  ◌ Optimización│                                         └───┘ completa  │
│    Próximamente│        ●  ●                                             │
│  ◌ Sensibilidad│     ● ┌─────────────────────┐   ■ Villavicencio        │
│    Próximamente│       │ Finca La Esperanza  │                          │
│  ◌ Reportes    │    ●  │ Empresa agropecuaria│   ■ Restrepo             │
│    Próximamente│       │ Municipio: Acacías  │ ●                        │
│                │       │ Oferta: 120 t/mes   │      ■ Granada           │
│                │       └──────────▼──────────┘                          │
│ [‹] Contraer   │        ●   ●                    ■ Puerto Gaitán         │
│ v0.1           │┌──────────────────────┐              © OSM © CARTO     │
│                ││ ● Empresas agrop. 10 │                                │
│                ││ ■ Plantas proces.  4 │                                │
│                │└──────────────────────┘                                │
└────────────────┴─────────────────────────────────────────────────────────┘
  ▌◉ = ítem activo (barra de acento + fondo verde claro)   ◌ = deshabilitado
```

Menú de perfil abierto (desde el avatar):

```
                                  ┌─────────────────────────┐
                                  │ Julián Pérez            │
                                  │ jperez · [Administrador]│
                                  ├─────────────────────────┤
                                  │ Mi perfil  Próximamente │ (deshab.)
                                  │ Panel de administración↗│ (solo admin)
                                  ├─────────────────────────┤
                                  │ ⎋ Cerrar sesión         │
                                  └─────────────────────────┘
```

### 6.3 Shell en móvil (<600 px)

```
Cerrado                    Drawer abierto            Ficha seleccionada
┌──────────────────────┐   ┌───────────┬──────────┐  ┌──────────────────────┐
│ ☰  Inicio       (JP) │   │[logo]  [×]│▒▒▒▒▒▒▒▒▒▒│  │ ☰  Inicio       (JP) │
├──────────────────────┤   │           │▒▒▒▒▒▒▒▒▒▒│  ├──────────────────────┤
│[● Empr.][■ Plantas]  │   │▌◉ Inicio  │▒ overlay▒│  │[● Empr.][■ Plantas]  │
│ 14 de 14 · ⚠ 2 sin   │   │ ◌ Red log.│▒▒▒▒▒▒▒▒▒▒│  │                  ┌─+─┐│
│ ubicación            │   │   Próxim. │▒▒▒▒▒▒▒▒▒▒│  │      ●           │ − ││
│                  ┌─+─┐│   │ ◌ Escena- │▒▒▒▒▒▒▒▒▒▒│  │   ●     ●        │ ⤢ ││
│                  │ − ││   │   rios    │▒▒▒▒▒▒▒▒▒▒│  │       ■          │ ⛶ ││
│        ●   ●     │ ⤢ ││   │   Próxim. │▒▒▒▒▒▒▒▒▒▒│  │                  └───┘│
│     ●      ■     │ ⛶ ││   │ ◌ Optimiz.│▒▒▒▒▒▒▒▒▒▒│  ├──────────────────────┤
│        ●         └───┘│   │ ◌ Sensib. │▒▒▒▒▒▒▒▒▒▒│  │ ═══ (bottom sheet)   │
│  ●        ■          │   │ ◌ Reportes│▒▒▒▒▒▒▒▒▒▒│  │ [●] Finca La Esperanza│
│                      │   │           │▒▒▒▒▒▒▒▒▒▒│  │ Empresa agropecuaria │
│ ● Empr. 10 ■ Pl. 4 ⌄ │   │ v0.1      │▒▒▒▒▒▒▒▒▒▒│  │ Acacías · Oferta 120 t│
└──────────────────────┘   └───────────┴──────────┘  └──────────────────────┘
```

---

## 7. Decisiones que requieren confirmación del usuario

1. **Identificador de login:** ¿usuario (`username`) o correo electrónico? Define la etiqueta y el `autocomplete` (`username`/`email`).
2. **Periodo de oferta/capacidad:** ¿se expresan como t/mes, t/semana o t/día? Debe coincidir con el modelo de optimización y con el dato que guarda el backend.
3. **Enlace "Panel de administración" en el menú del administrador:** ¿se incluye en la Fase 1 (recomendado, porque la gestión de nodos y rutas vive allí) o se omite?
4. **Etiqueta de ruta/pantalla "Inicio":** ¿"Inicio" o "Mapa de la red"? Se propone "Inicio" en el menú y "Red logística del Meta" como contexto.
5. **Alcance del filtro de municipios:** ¿basta el filtro por tipo (propuesto) o se añade buscador por nombre/municipio en esta fase?
6. **Nombre comercial que muestra la marca:** "OptiAgro-Llanos" y pie "EcoResiduos del Llano S.A.S." (tomados de CLAUDE.md); confirmar si el cliente mayorista debe ver también otro nombre o logotipo propio.
7. **Estaciones sin coordenadas:** se propone listarlas aparte (como se pidió) y que el administrador las corrija en Django admin; confirmar si basta con eso o si el backend debe impedir activar una estación sin coordenadas.
8. **Mensaje de bloqueo por intentos (429):** ¿el backend aplicará límite de intentos? Si no, se elimina ese estado.
9. **Datos de demostración:** confirmar si en la presentación al cliente se mostrarán estaciones ficticias; en tal caso se añade una etiqueta visible "Datos de demostración" en la tarjeta de filtros.
