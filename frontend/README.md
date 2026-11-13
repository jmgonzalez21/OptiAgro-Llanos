# OptiAgro-Llanos · Frontend

SPA en **Vue 3** (Composition API, `<script setup lang="ts">`) + **Vite** + **TypeScript estricto** + **Pinia** + **Vue Router**, con **Leaflet** para el mapa y **Vitest** + **Vue Test Utils** para las pruebas. Interfaz en español.

El frontend solo habla con el backend por la API REST (`/api/v1/`, contrato en `docs/api/openapi.yaml`).

## Requisitos

- Node 24+ y npm.

## Comandos

```bash
npm install        # instala dependencias (versiones fijadas exactamente)
npm run dev        # servidor de desarrollo en http://localhost:5173
npm run build      # vue-tsc (tipos) + vite build -> dist/
npm run preview    # sirve dist/ localmente
npm test           # Vitest (una pasada)
npm run test:watch # Vitest en modo observador
npm run lint       # ESLint
npm run typecheck  # vue-tsc sin generar archivos
```

## Mock o API real

La variable `VITE_USE_MOCK` decide qué se usa (por defecto **`false`**: API real; el proxy de `npm run dev` reenvía `/api` a `http://127.0.0.1:8000`):

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `VITE_USE_MOCK` | `false` | `true` = capa mock (solo login, /auth/me y estaciones); `false` = API real |
| `VITE_API_BASE` | `/api/v1` | Base de la API |
| `VITE_PROXY_TARGET` | `http://127.0.0.1:8000` | Destino del proxy de `npm run dev` para `/api` |

Copia `.env.example` a `.env` (ignorado por git) para cambiarlas.

### Credenciales del mock

Cualquier usuario no vacío con cualquier contraseña no vacía. El usuario `admin` entra como **administrador**; cualquier otro, como **analista**. No hay contraseñas ni secretos en el repositorio.

### Cambiar a la API real

1. Levanta el backend (Django) y pon en `.env`: `VITE_USE_MOCK=false`. En desarrollo, el proxy de Vite reenvía `/api` a `VITE_PROXY_TARGET`.
2. (Opcional, para retirar el mock del todo) Borra `src/api/mock/` y las 2 líneas marcadas con `// MOCK` (y el import de `USAR_MOCK`) en `src/api/index.ts`. Nada más depende de esa carpeta (solo las pruebas, que usan `src/test/helpers.ts`; ahí se puede sustituir el mock por otro `fetch` falso o por pruebas de contrato).

### Cómo está aislado el mock

El mock **no** reemplaza servicios: es un `fetch` falso (`src/api/mock/index.ts`) que responde con las mismas rutas, códigos HTTP y JSON (incluida la paginación `{count,next,previous,results}`) que la API real. Por eso el cliente HTTP, el interceptor JWT/refresh, el manejo de errores y los servicios (`src/api/servicios.ts`) se ejercitan igual en ambos modos. Los datos de demostración están en `src/api/mock/datos.ts`: 4 plantas (sedes reales, capacidades de relleno) y 10 agroempresas **ficticias** (marcadas con `ficticio: true`).

## Pantallas

Inicio (mapa; el administrador puede cargar los datos de demostración), Red logística (empresas, plantas y rutas; CRUD solo administrador), Matriz de costos (editable, solo administrador escribe), Optimización (exacto y AG con parámetros), Sensibilidad (escenarios, precios sombra, rangos), Reporte comparativo (+ escalabilidad, CSV e imprimir), Historial, Usuarios (solo administrador) y Mi perfil. El aviso «Datos de demostración» aparece cuando la red activa contiene registros con `ficticio: true`. Las pantallas de gestión y análisis necesitan la API real (el mock no las cubre).

## Estructura

```
src/
  api/            cliente HTTP (http.ts), errores tipados, servicios por endpoint, capa mock (mock/)
  stores/         Pinia: auth (sesión) y red (estaciones activas)
  router/         rutas, guards (sesión/rol) y creación del router
  views/          LoginView, HomeView (mapa), SinPermisoView
  layouts/        AppLayout (panel lateral + barra superior)
  components/     MenuPerfil, mapa/ (MapaRed, LeyendaMapa)  — ui/ queda para el agente `ui`
  composables/    useEstaciones (lógica pura de estaciones), useFullscreen
  types/          tipos del contrato y metas de rutas
  styles/         (reservado al agente `ui`)
  test/           utilidades de pruebas
```

## Autenticación

- Usuario, rol y tokens viven **en memoria** (store `auth`). Solo el **refresh token** se guarda en `sessionStorage` (con `try/catch`) para sobrevivir a un refresco de página; el access token nunca se persiste.
- El cliente añade `Authorization: Bearer <access>`; ante un `401` renueva con `POST /auth/refresh/` (una sola renovación compartida; el refresh ROTA y se guarda el nuevo) y reintenta una vez. El cierre de sesión llama a `POST /auth/logout/`. Si la renovación falla, la sesión expira y se redirige a `/login?motivo=expirada`.
- Route guards (`src/router/guards.ts`): `meta.requiereAuth`, `meta.soloInvitado` (login) y `meta.roles` (preparado: `roles: ['administrador']`).
- Errores tipados (`src/api/errores.ts`): `ErrorCredenciales`, `ErrorRed`, `ErrorPermiso` (403), `ErrorSesionExpirada`, `ErrorValidacion`, `ErrorServidor`.

## Mapa (Inicio)

Leaflet con mapa base CARTO Positron (atribución a OpenStreetMap y CARTO). Marcadores distintos por forma y color (círculo = agroempresa, cuadrado con chimenea = planta), popup con nombre/tipo/municipio/oferta o capacidad, zoom, pantalla completa, "Reencuadrar todas", filtros por tipo, contador y leyenda. Solo se muestran estaciones **activas**; las que no tienen coordenadas se listan aparte. Si una estación deja de venir como activa (al recargar), desaparece del mapa.

## Accesibilidad

Etiquetas asociadas a los campos, errores en línea con `aria-describedby`/`aria-invalid`, `role="alert"` y `role="status"`, enlace "Saltar al contenido", foco al contenido principal al cambiar de vista, menú de perfil con teclado (flechas, Inicio/Fin, Esc, Tab) y marcadores del mapa accesibles por teclado.
