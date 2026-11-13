# OptiAgro-Llanos

Aplicación web para **minimizar el costo logístico** de recolectar residuos agropecuarios y llevarlos a plantas de
procesamiento en el Meta (caso: EcoResiduos del Llano S.A.S.). Calcula la mejor distribución de envíos empresa → planta
con un **modelo de transporte exacto** (programación lineal) y con un **algoritmo genético**, compara ambos y permite
responder preguntas del tipo *"¿qué pasa si sube el combustible?"*.

Proyecto final de Optimización · Universidad de los Llanos · 2026-II.

## ¿Qué puedes hacer?

- **Mapa de la red:** ver las empresas y plantas ubicadas en el Meta.
- **Red logística:** agregar, editar, desactivar o eliminar empresas, plantas y rutas. Al agregar una empresa eliges su
  municipio, el pin se coloca solo en el mapa y las rutas hacia las plantas se crean con su **distancia por carretera**.
- **Matriz de costos:** costo por tonelada de cada empresa a cada planta, con la oferta de cada empresa y la capacidad de
  cada planta (tabla de transporte).
- **Optimización:** calcula la distribución más barata (método exacto) o con algoritmo genético, y dibuja los envíos
  sobre las carreteras.
- **¿Qué pasa si…?:** análisis de sensibilidad (combustible, oferta, capacidad), precios sombra, cuellos de botella y
  rangos de variación.
- **Reporte comparativo:** costo, tiempo y *gap* % del algoritmo genético frente al óptimo, escalabilidad y exportación
  a CSV.
- **Historial y usuarios:** registro de cálculos y gestión de usuarios con roles (administrador y analista).

## Requisitos

Solo necesitas **Docker** (incluye Docker Compose). No hace falta instalar Python, Node ni PostgreSQL.

| Sistema | Qué instalar |
|---|---|
| Windows 10/11 y macOS | [Docker Desktop](https://www.docker.com/products/docker-desktop/) (ábrelo y espera a que diga "running") |
| Linux | Docker Engine + el plugin Compose v2 ([guía oficial](https://docs.docker.com/engine/install/)) |

- Unos **4 GB de RAM** libres y ~2 GB de disco.
- **Internet** al construir la imagen y al usar la app (mapa de OpenStreetMap y cálculo de distancias por carretera).
- El puerto **8080** libre (se puede cambiar, ver más abajo).
- Opcional: [Git](https://git-scm.com/) para clonar el repositorio (o descarga el ZIP desde GitHub).

## Instalación y ejecución

### 1. Descargar el proyecto

```bash
git clone https://github.com/Santique/Proyecto_Optimizacion.git
cd Proyecto_Optimizacion
```

### 2. Crear tu archivo de configuración `.env`

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

Abre `.env` con un editor de texto y **cambia estos valores** (no uses los de ejemplo):

| Variable | Qué poner |
|---|---|
| `DJANGO_SECRET_KEY` | Una clave larga y aleatoria. Puedes generarla con el comando de abajo. |
| `POSTGRES_PASSWORD` | Una contraseña para la base de datos. |
| `OPTIAGRO_CARGAR_DEMO` | `true` la primera vez, para crear usuarios y datos de prueba (ver paso 3). |
| `DEMO_ADMIN_PASSWORD` | Contraseña del administrador de prueba (mínimo 10 caracteres). |
| `DEMO_ANALISTA_PASSWORD` | Contraseña del analista de prueba (mínimo 10 caracteres). |

Para generar una clave aleatoria (sirve en cualquier sistema, usa Docker):

```bash
docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(50))"
```

> El archivo `.env` contiene secretos: **nunca lo subas a GitHub** (ya está en `.gitignore`).

### 3. Levantar la aplicación

```bash
docker compose up -d --build
```

La primera vez tarda unos minutos (descarga imágenes y compila la aplicación). Comprueba que los tres servicios estén
en estado *healthy*:

```bash
docker compose ps
```

### 4. Abrir la aplicación

Entra en **http://localhost:8080**.

Con `OPTIAGRO_CARGAR_DEMO=true` se crearon, solo si no existían:

| Rol | Usuario | Contraseña |
|---|---|---|
| Administrador | `admin_demo` | la de `DEMO_ADMIN_PASSWORD` en tu `.env` |
| Analista | `analista_demo` | la de `DEMO_ANALISTA_PASSWORD` en tu `.env` |

Y los **datos de demostración**: 10 empresas agropecuarias **ficticias** y 4 plantas (Villavicencio, Restrepo, Granada y
Puerto Gaitán). El **administrador** ve y edita todo (incluidos los usuarios); el **analista** ejecuta cálculos y consulta
la red, pero no la modifica.

### Usar la app con tus propios datos (sin demostración)

Si no quieres los datos ficticios, deja `OPTIAGRO_CARGAR_DEMO=false` y crea tu propio administrador:

```bash
docker compose exec backend python manage.py createsuperuser
```

Escribe usuario, correo y contraseña cuando te los pida. Ese usuario entra con rol **administrador**. Desde la app
(sección *Usuarios*) puedes crear los demás.

## Uso diario

```bash
docker compose up -d          # encender (no reconstruye)
docker compose down           # apagar (los datos se conservan)
docker compose logs -f backend   # ver mensajes del servidor
docker compose up -d --build  # aplicar cambios después de actualizar el código (git pull)
```

Tus datos (red, usuarios e historial) viven en un volumen de Docker y **sobreviven** a `docker compose down`.
Para **borrar todo** y empezar de cero (¡se pierden los datos!):

```bash
docker compose down -v
```

## Cambiar el puerto

Si el 8080 está ocupado, agrega o edita en `.env`:

```
FRONTEND_PORT=9090
```

y vuelve a ejecutar `docker compose up -d`. Luego abre `http://localhost:9090`.

## Solución de problemas

| Síntoma | Qué hacer |
|---|---|
| `Defina POSTGRES_PASSWORD en .env` o `Defina DJANGO_SECRET_KEY en .env` | Falta crear o completar el archivo `.env` (paso 2). |
| `Cannot connect to the Docker daemon` | Abre Docker Desktop y espera a que termine de iniciar. |
| `port is already allocated` | Otro programa usa el 8080: cambia `FRONTEND_PORT` (ver arriba). |
| No puedo iniciar sesión | Revisa que sea el usuario y la contraseña correctos. Las contraseñas demo **solo se aplican al crear el usuario**: si luego las cambias en `.env` o desde la app, la base de datos conserva la anterior. Para volver a aplicar las contraseñas de tu `.env` a los usuarios demo: `docker compose exec backend python manage.py crear_usuarios_demo`. |
| Entré pero no hay empresas | Con `OPTIAGRO_CARGAR_DEMO=false` la base empieza vacía: el administrador puede pulsar **"Cargar datos de demostración"** en *Inicio* o agregar sus propias empresas. |
| El mapa se ve sin fondo o las distancias dicen "Estimada" | No hay internet o el servicio de mapas no respondió. Las distancias se estiman en línea recta × 1,3 y se pueden recalcular después con **"Recalcular distancias por carretera"**. |
| Cambié el código y no veo cambios | Reconstruye: `docker compose up -d --build`. |

## Para desarrolladores

Arquitectura: **Vue 3 (SPA) + nginx** → **Django REST Framework (gunicorn)** → **PostgreSQL 16**. El navegador solo usa
`http://localhost:8080`: nginx sirve la SPA y reenvía `/api/` al backend. El admin de Django viene **apagado** por
defecto (`OPTIAGRO_ADMIN_HABILITADO=false`).

```
frontend/   SPA Vue 3 + Vite + TypeScript (Dockerfile en dos etapas + nginx.conf)
backend/    Django 5.2 + DRF + SimpleJWT; dominio/ y optimizacion/ son Python puro (sin Django)
docs/api/   openapi.yaml: contrato entre backend y frontend
docs/ux/    especificaciones de pantallas · docs/ui/ guía de estilo
docker-compose.yml   servicios db, backend y frontend
legacy_streamlit/    versión original en Streamlit (solo referencia histórica)
```

Pruebas:

```bash
docker compose exec backend pytest -q       # backend (Django + núcleo de optimización)
cd frontend && npm install && npm test      # frontend (Vitest)
```

Desarrollo del frontend con recarga en caliente (el backend debe estar corriendo con `docker compose up -d`; publica
`127.0.0.1:8000` y el proxy de Vite lo usa):

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Más detalles: `backend/README.md` (API, variables de entorno, límites), `frontend/README.md`, `SUPUESTOS.md`
(decisiones y limitaciones) y `PLAN.md` (trazabilidad de requisitos).

## Datos y limitaciones

- Los datos de demostración (10 empresas) son **ficticios**; las 4 plantas están en municipios reales, pero sus
  capacidades y costos son de ejemplo.
- Las distancias se calculan con **OSRM sobre OpenStreetMap** (ruta por carretera más corta o rápida). **No** se
  restringe a vías nacionales y puede diferir de la ruta que tome un transportista. El servidor público de OSRM es de
  uso razonable y sin garantías: para producción conviene alojar el propio.
- El algoritmo genético es una heurística: puede quedar por encima del óptimo exacto (el reporte muestra el *gap*).

## Créditos

Mapas © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright). Rutas: [OSRM](https://project-osrm.org/).
Optimización: [HiGHS](https://highs.dev/) vía SciPy. Mapa interactivo: [Leaflet](https://leafletjs.com/).
