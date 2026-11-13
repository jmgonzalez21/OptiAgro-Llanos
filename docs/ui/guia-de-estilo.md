# Guía de estilo — OptiAgro-Llanos

Sistema visual del frontend. Dirección: **blanco + verde menta/salvia suave** como acento; verdes profundos solo para texto y botones primarios (contraste AA). Sobrio, mucho espacio en blanco, bordes finos, sombras suaves con tinte verde, transiciones de 150–200 ms.

Código: `frontend/src/styles/` (tokens y base), `frontend/src/components/ui/` (componentes). Nada de colores hardcodeados fuera de los tokens (salvo el degradado del isotipo y el favicon).

## 1. Paleta y contraste

Se usan los **tokens semánticos** (`--color-*`); la escala `--verde-50…950` es solo referencia. Tema claro por defecto; oscuro con `prefers-color-scheme: dark` o forzado con `<html data-theme="dark">` (y `data-theme="light"` fuerza el claro).

| Token | Claro | Uso | Contraste |
|---|---|---|---|
| `--color-fondo` | `#f6fbf7` | Fondo de la app (blanco verdoso sutil) | — |
| `--color-superficie` | `#ffffff` | Tarjetas, paneles, campos | — |
| `--color-superficie-2` | `#f1f8f3` | Fondos hundidos, hover | — |
| `--color-borde` / `-fuerte` | `#dfe9e2` / `#c6d6cc` | Divisores decorativos de tarjetas y paneles | — |
| `--color-borde-control` | `#7c9284` | Borde de campos, casillas, chips y botón secundario | 3.3:1 sobre blanco (WCAG 1.4.11); oscuro `#5f7a68` 3.8:1 |
| `--color-texto` | `#14231b` | Texto principal | 16.3:1 sobre blanco |
| `--color-texto-2` | `#44574b` | Texto secundario | 7.8:1 sobre blanco; 7.2:1 sobre superficie-2 |
| `--color-texto-suave` | `#5a6b60` | Ayudas, metadatos, “Próximamente” | 5.7:1 sobre blanco; 5.3:1 sobre superficie-2 |
| `--color-primario` | `#1f6b43` | Botón primario, enlaces, check | 6.5:1 con texto blanco; hover `#185a37` 8.2:1 |
| `--color-acento` / `-suave` | `#cfeadb` / `#e6f4ea` | Menta: fondos activos, chips, avatar | texto `#1b5535` sobre `#e6f4ea` = 7.7:1 |
| `--color-activo-barra` | `#2f8f55` | Barra de acento del ítem activo | no textual |
| `--color-foco` | `#2f8f55` | Anillo de foco (2 px + halo) | 4.1:1 sobre blanco; 3.6:1 sobre menta |
| `--color-error` | `#b42318` sobre `#fef3f2` | Errores | 6.1:1 |
| `--color-aviso` | `#8a4b0c` sobre `#fff7e6` | Avisos, “Datos de demostración” | 6.4:1 |
| `--color-info` | `#1d5c8a` sobre `#eef6fc` | Información | 6.5:1 |
| `--color-marcador-empresa` | `#2f8f55` | Círculo con hoja | 3.5:1 contra el mapa claro; glifo blanco 4.1:1 |
| `--color-marcador-planta` | `#14532d` | Cuadrado redondeado con fábrica | 7.9:1 contra el mapa claro |

Tema oscuro (superficie `#111b15`, fondo `#0b120e`): texto 15.7:1, texto-2 10.1:1, texto-suave 7.4:1, botón primario (`#0b120e` sobre `#5cbf84`) 8.4:1, activo (`#bfe9cf` sobre `#1a3a28`) 9.4:1, error 8.5:1, aviso 10.0:1, info 8.9:1, foco 9.9:1. El **mapa base se mantiene claro** en ambos temas (los marcadores conservan su contraste).

Regla: el significado nunca depende solo del color. Estados activos = fondo + barra + peso; chips = ícono de verificación + `aria-pressed`; alertas = ícono + texto; marcadores = forma + glifo + color.

## 2. Tipografía

**Plus Jakarta Sans Variable**, autoalojada con `@fontsource-variable/plus-jakarta-sans` (versión fija `5.3.0`, sin CDN; se importa en `styles/index.css`). Pesos usados: 450 (texto), 550 (énfasis), 700 (títulos/botones).

| Token | Valor | Token | Valor |
|---|---|---|---|
| `--texto-xs` | 0.75rem | `--texto-xl` | 1.375rem |
| `--texto-sm` | 0.875rem | `--texto-2xl` | 1.75rem |
| `--texto-base` | 1rem (campos: evita zoom en iOS) | `--texto-3xl` | 2.375rem |
| `--texto-lg` | 1.125rem | `--altura-linea` | 1.55 (títulos 1.2) |

## 3. Espaciado, radios, sombras, movimiento

- Espaciado `--espacio-1…8` (0.25 → 4 rem). Táctil mínimo `--alto-tactil: 2.75rem`.
- Radios: `--radio-sm 8px`, `-md 12px`, `-lg 16px`, `-xl 22px`, `-pleno 999px`.
- Sombras: `--sombra-xs/sm/md/lg` (tinte verde, muy suaves) y `--sombra-boton`.
- Movimiento: `--trans-rapida 150ms`, `--trans 200ms`, `--trans-lenta 320ms`, curva `--ease`. Con `prefers-reduced-motion: reduce` las animaciones y transiciones se anulan (`base.css`).
- Vidrio (tarjetas sobre el mapa): `--color-vidrio`, `--color-vidrio-borde`, `--color-vidrio-sombra` + `backdrop-filter: blur`.

## 4. Base global (`styles/base.css`)

Reset mínimo, `body` con la fuente y el fondo del tema, `.sr-only`, foco visible (`:focus-visible`: anillo de 2 px + halo suave de 5 px) y `@keyframes` reutilizables (`ui-girar`, `ui-aparecer`, `ui-brillo`).

## 5. Componentes (`frontend/src/components/ui/`)

Todos con `<script setup lang="ts">`. Textos en español; los atributos no declarados (`aria-*`, `class`, `@click`) pasan al elemento raíz.

| Componente | Props / slots principales | Notas |
|---|---|---|
| `UiButton` | `variante` (`primario`·`secundario`·`fantasma`), `tamano` (`sm`·`md`·`lg`), `type`, `loading`, `bloque`, `disabled`; slots default e `icono` | `loading` muestra spinner, deshabilita y pone `aria-busy="true"` |
| `UiIconButton` | `etiqueta` (obligatoria: aria-label + tooltip), `icono`, `variante` (`fantasma`·`secundario`·`vidrio`), `pulsado` (aria-pressed) | 44×44 px |
| `UiField` | `id` (obligatorio), `label`, `type`, `hint`, `error`, `icono`; `v-model`; slot `suffix`; expone `focus()` | Enlaza `label/for`, `aria-invalid`, `aria-describedby` (`${id}-hint`, `${id}-error`). Atributos extra (`name`, `autocomplete`, `disabled`, `@blur`) van al `<input>` |
| `UiPasswordField` | igual que `UiField` sin `type`; `v-model`; expone `focus()` | Botón Mostrar/Ocultar (`.campo__alternar`, `aria-pressed`, `aria-controls`, texto `.sr-only`) |
| `UiAlert` | `tono` (`error`·`aviso`·`info`·`exito`), `titulo`, `rol`; slots default y `acciones`; expone `focus()` | `error` → `role="alert"`; el resto `role="status"`; siempre ícono + texto; `tabindex="-1"` |
| `UiBadge` | `tono` (`neutro`·`verde`·`ambar`·`info`·`error`), `punto` | Chips de rol, estado y “Datos de demostración” |
| `UiCheckbox` | `v-model` booleano, `id`; slot default | `<input type="checkbox">` real |
| `UiChip` | `v-model` booleano; slots default y `simbolo` | Filtro conmutable: `<button aria-pressed>` + check |
| `UiSpinner` | `tamano` | Decorativo; el texto accesible lo pone quien lo usa (`role="status"`) |
| `UiSkeleton` | `ancho`, `alto` | Esqueleto de carga |
| `UiEmptyState` | `icono`, `titulo`, `descripcion`, `tono` (`neutro`·`error`); slot de acciones | Vacío, error, sin resultados |
| `UiCard` | `variante` (`plana`·`elevada`·`vidrio`), `relleno`, `como` | `vidrio` = tarjeta translúcida sobre el mapa |
| `UiAvatar` | `nombre`, `tamano` | Iniciales (máx. 2) sobre menta |
| `UiLogo` | `soloIsotipo`, `tamano` | Isotipo (hoja sobre baldosa verde) + “OptiAgro-Llanos” |
| `UiIcon` | `nombre`, `tamano`, `grosor` | SVG inline propio; catálogo en `icons.ts` (`inicio`, `red`, `hoja`, `fabrica`, `ojo`, `salir`, `mapa`, …) |
| `UiMarcador` | `tipo` (`empresa`·`planta`), `tamano` | Mismo dibujo que el marcador del mapa (leyenda, listas) |
| `UiPatronAgro` | — | Ilustración decorativa del login: curvas de nivel + red de nodos; `aria-hidden` |

Marcadores (`marcadores.ts`): empresa = círculo con hoja (40 px de área táctil); planta = cuadrado redondeado más grande con fábrica/chimenea (46 px). Colores por `--color-marcador-*`.

Estilos del mapa (popup/ficha, atribución, foco de marcadores): `styles/mapa.css`, importado por `MapaRed.vue` tras `leaflet.css`.

## 6. Patrones de pantalla

- **Login:** dividido (≥1024 px: 45/55 y 50/50 desde 1280); franja superior en tableta; solo logo en móvil. Tarjeta de formulario ≤ 25 rem, entrada con animación suave.
- **Shell:** panel lateral de 264 px (colapsable a 76 px con tooltips), estado activo con fondo menta + barra de 3 px; ítems “Próximamente” enfocables con `aria-disabled`; < 1024 px pasa a drawer (`role="dialog"`, foco atrapado, Esc, velo). Barra superior translúcida con desenfoque; menú de perfil con avatar, rol y “Cerrar sesión”.
- **Inicio:** mapa en contenedor de radio 22 px con sombra; filtros/contador, controles y leyenda como tarjetas de vidrio; estados de carga, vacío, sin filtros y error como tarjeta centrada.

## 7. Uso rápido

```vue
<UiButton type="submit" tamano="lg" bloque :loading="cargando">Iniciar sesión</UiButton>
<UiField id="usuario" v-model="u" label="Usuario" icono="usuario" :error="errorUsuario" autocomplete="username" />
<UiAlert tono="error">Usuario o contraseña incorrectos.</UiAlert>
<UiChip v-model="verPlantas"><template #simbolo><UiMarcador tipo="planta" :tamano="22" /></template>Plantas</UiChip>
```

## 8. Pendiente / fuera de esta fase

Tabla de datos editable, pestañas, modal de confirmación y paleta categórica para gráficos (Plotly/Cytoscape) se definirán cuando `ux` especifique esas pantallas. No hay interruptor de tema en la interfaz (los tokens ya soportan `data-theme`).
