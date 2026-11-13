"""Healthcheck del contenedor: la API responde (un 401 sin token cuenta como sano; no hay endpoints abiertos)."""
import sys
import urllib.error
import urllib.request

try:
    urllib.request.urlopen("http://127.0.0.1:8000/api/v1/auth/me/", timeout=4)
except urllib.error.HTTPError as exc:
    sys.exit(0 if exc.code == 401 else 1)
except Exception:
    sys.exit(1)
sys.exit(0)
