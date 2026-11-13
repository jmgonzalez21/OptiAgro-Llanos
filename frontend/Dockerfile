# Frontend OptiAgro-Llanos en dos etapas: node compila la SPA (API real, sin mock) y nginx la sirve.
# --- Etapa 1: compilación ---
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# La imagen de producción habla con el backend real a través del proxy /api/ de nginx (mismo origen).
ENV VITE_USE_MOCK=false \
    VITE_API_BASE=/api/v1
# El build incluye la verificación de tipos (vue-tsc).
RUN npm run build

# --- Etapa 2: servidor estático + proxy ---
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD wget -q --spider http://127.0.0.1/ || exit 1
