# Backend OptiAgro-Llanos: Django 5.2 LTS + DRF, Python 3.12.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# INSTALL_DEV=1 añade pytest y pytest-django (útil en desarrollo y CI).
ARG INSTALL_DEV=1
COPY requirements.txt requirements-dev.txt ./
RUN if [ "$INSTALL_DEV" = "1" ]; then pip install -r requirements-dev.txt; else pip install -r requirements.txt; fi

COPY . .

# entrypoint.sh puede llegar con finales de línea CRLF desde Windows: se normaliza.
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh \
    && useradd --create-home --uid 1000 optiagro && chown -R optiagro:optiagro /app
USER optiagro

EXPOSE 8000

# Migraciones, estáticos, limpieza de tokens, datos demo opcionales (OPTIAGRO_CARGAR_DEMO) y gunicorn.
CMD ["./entrypoint.sh"]
