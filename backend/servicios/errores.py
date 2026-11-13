class ErrorDeNegocio(Exception):
    """Entrada válida sintácticamente pero inaceptable para optimizar (la API responde 400)."""

    def __init__(self, mensaje: str, errores: list[str] | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.errores = errores or []
