#!/bin/sh
# Arranque del backend: migraciones, estáticos, limpieza de tokens vencidos, datos demo opcionales y gunicorn.
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py flushexpiredtokens || true

# OPTIAGRO_CARGAR_DEMO=true crea los usuarios demo y los datos FICTICIOS solo si no existen (idempotente).
# Las contraseñas demo vienen de DEMO_ADMIN_PASSWORD / DEMO_ANALISTA_PASSWORD (entorno), nunca del repositorio.
if [ "${OPTIAGRO_CARGAR_DEMO:-false}" = "true" ]; then
    python manage.py inicializar_demo || echo "AVISO: inicializar_demo no terminó bien (¿faltan las contraseñas demo?)."
fi

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile -
