/** Errores tipados de la capa API. La UI decide el mensaje según la clase o el código. */

export type CodigoError =
  | 'credenciales'
  | 'red'
  | 'prohibido'
  | 'sesion_expirada'
  | 'validacion'
  | 'no_encontrado'
  | 'servidor'
  | 'desconocido'

export class ErrorApi extends Error {
  readonly codigo: CodigoError
  readonly status?: number
  /** Detalle devuelto por el backend (campo `detail`), si lo hubo. */
  readonly detalle?: string
  /** Errores por campo (`errores` del contrato), si los hubo. */
  readonly errores?: unknown

  constructor(
    codigo: CodigoError,
    mensaje: string,
    opciones: { status?: number; detalle?: string; errores?: unknown } = {},
  ) {
    super(mensaje)
    this.name = new.target.name
    this.codigo = codigo
    this.status = opciones.status
    this.detalle = opciones.detalle
    this.errores = opciones.errores
  }
}

/** 401 en el login: usuario o contraseña incorrectos. */
export class ErrorCredenciales extends ErrorApi {
  constructor(detalle?: string) {
    super('credenciales', 'Usuario o contraseña incorrectos.', { status: 401, detalle })
  }
}

/** Sin conexión, servidor inalcanzable o tiempo de espera agotado. */
export class ErrorRed extends ErrorApi {
  constructor(mensaje = 'No se pudo conectar con el servidor.') {
    super('red', mensaje)
  }
}

/** 403: autenticado pero sin permiso. */
export class ErrorPermiso extends ErrorApi {
  constructor(detalle?: string) {
    super('prohibido', 'No tienes permiso para realizar esta acción.', { status: 403, detalle })
  }
}

/** El access token venció y no se pudo renovar con el refresh token. */
export class ErrorSesionExpirada extends ErrorApi {
  constructor() {
    super('sesion_expirada', 'Tu sesión expiró. Inicia sesión de nuevo.', { status: 401 })
  }
}

/** 400: datos inválidos. */
export class ErrorValidacion extends ErrorApi {
  constructor(detalle?: string, errores?: unknown) {
    super('validacion', detalle || 'Los datos enviados no son válidos.', { status: 400, detalle, errores })
  }
}

export class ErrorServidor extends ErrorApi {
  constructor(status: number, detalle?: string) {
    super('servidor', 'El servidor tuvo un problema. Inténtalo de nuevo en unos minutos.', { status, detalle })
  }
}

/** Mensaje en español apto para mostrar al usuario. */
export function mensajeDeError(error: unknown): string {
  if (error instanceof ErrorApi) {
    switch (error.codigo) {
      case 'red':
        return 'No hay conexión con el servidor. Revisa tu red e inténtalo de nuevo.'
      case 'credenciales':
        return 'Usuario o contraseña incorrectos.'
      case 'prohibido':
        return 'No tienes permiso para realizar esta acción.'
      case 'sesion_expirada':
        return 'Tu sesión expiró. Inicia sesión de nuevo.'
      case 'servidor':
        return 'El servidor tuvo un problema. Inténtalo de nuevo en unos minutos.'
      default:
        return error.message
    }
  }
  return 'Ocurrió un error inesperado.'
}
