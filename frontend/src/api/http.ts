/**
 * Cliente HTTP basado en fetch.
 *
 * - Prefija la base (`/api/v1`) y serializa JSON.
 * - Interceptor: añade `Authorization: Bearer <access>` y, ante un 401, renueva el
 *   access token con el refresh token (una sola renovación en vuelo) y reintenta una vez.
 * - Traduce las fallas a errores tipados (`./errores`).
 *
 * No conoce el store: recibe una `SesionHttp` (ver `configurarSesion`).
 */
import {
  ErrorApi,
  ErrorCredenciales,
  ErrorPermiso,
  ErrorRed,
  ErrorServidor,
  ErrorSesionExpirada,
  ErrorValidacion,
} from './errores'
import type { RefrescoRespuesta } from '@/types/api'

export interface SesionHttp {
  obtenerAccess(): string | null
  obtenerRefresh(): string | null
  /** Se invoca tras renovar con éxito (`refresh` solo si el backend lo rotó). */
  alRenovar(access: string, refresh?: string): void
  /** Se invoca cuando la sesión ya no es recuperable. */
  alExpirar(): void
}

export type Consulta = Record<string, string | number | boolean | undefined>

export interface OpcionesSolicitud {
  metodo?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  cuerpo?: unknown
  consulta?: Consulta
  /** Por defecto true. Falso para login/refresh. */
  autenticar?: boolean
  /** Tiempo máximo de espera (ms); por defecto el del cliente. */
  timeoutMs?: number
}

export interface OpcionesCliente {
  base: string
  fetchImpl?: typeof fetch
  timeoutMs?: number
}

const SESION_VACIA: SesionHttp = {
  obtenerAccess: () => null,
  obtenerRefresh: () => null,
  alRenovar: () => undefined,
  alExpirar: () => undefined,
}

export interface ClienteHttp {
  configurarSesion(sesion: SesionHttp): void
  solicitar<T>(ruta: string, opciones?: OpcionesSolicitud): Promise<T>
  /** Canjea un refresh token por un access nuevo SIN tocar la sesión. */
  refrescarConToken(refresh: string): Promise<RefrescoRespuesta>
}

export function crearClienteHttp(opciones: OpcionesCliente): ClienteHttp {
  const base = opciones.base.replace(/\/+$/, '')
  const timeoutMs = opciones.timeoutMs ?? 15000
  let sesion: SesionHttp = SESION_VACIA
  let renovando: Promise<void> | null = null

  function ejecutarFetch(url: string, init: RequestInit): Promise<Response> {
    const f = opciones.fetchImpl ?? globalThis.fetch.bind(globalThis)
    return f(url, init)
  }

  function construirUrl(ruta: string, consulta?: Consulta): string {
    let url = `${base}${ruta.startsWith('/') ? ruta : `/${ruta}`}`
    if (consulta) {
      const params = new URLSearchParams()
      for (const [clave, valor] of Object.entries(consulta)) {
        if (valor !== undefined) params.set(clave, String(valor))
      }
      const texto = params.toString()
      if (texto) url += `?${texto}`
    }
    return url
  }

  async function enviar(ruta: string, op: OpcionesSolicitud, autenticar: boolean): Promise<Response> {
    const headers: Record<string, string> = { Accept: 'application/json' }
    let body: string | undefined
    if (op.cuerpo !== undefined) {
      headers['Content-Type'] = 'application/json'
      body = JSON.stringify(op.cuerpo)
    }
    if (autenticar) {
      const access = sesion.obtenerAccess()
      if (access) headers.Authorization = `Bearer ${access}`
    }
    const controlador = new AbortController()
    const temporizador = setTimeout(() => controlador.abort(), op.timeoutMs ?? timeoutMs)
    try {
      return await ejecutarFetch(construirUrl(ruta, op.consulta), {
        method: op.metodo ?? 'GET',
        headers,
        body,
        signal: controlador.signal,
      })
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') {
        throw new ErrorRed('El servidor tardó demasiado en responder.')
      }
      throw new ErrorRed()
    } finally {
      clearTimeout(temporizador)
    }
  }

  async function leerJson(respuesta: Response): Promise<unknown> {
    if (respuesta.status === 204) return undefined
    const texto = await respuesta.text()
    if (!texto) return undefined
    try {
      return JSON.parse(texto)
    } catch {
      return undefined
    }
  }

  function extraerDetalle(cuerpo: unknown): { detalle?: string; errores?: unknown } {
    if (cuerpo && typeof cuerpo === 'object') {
      const obj = cuerpo as Record<string, unknown>
      return {
        detalle: typeof obj.detail === 'string' ? obj.detail : undefined,
        errores: 'errores' in obj ? obj.errores : obj,
      }
    }
    return {}
  }

  /** Convierte una respuesta no exitosa en el error tipado correspondiente. */
  async function aError(respuesta: Response, autenticado: boolean): Promise<ErrorApi> {
    const { detalle, errores } = extraerDetalle(await leerJson(respuesta))
    const s = respuesta.status
    if (s === 400) return new ErrorValidacion(detalle, errores)
    if (s === 401) return autenticado ? new ErrorSesionExpirada() : new ErrorCredenciales(detalle)
    if (s === 403) return new ErrorPermiso(detalle)
    if (s === 404) return new ErrorApi('no_encontrado', 'No se encontró el recurso solicitado.', { status: s, detalle })
    if (s >= 500) return new ErrorServidor(s, detalle)
    return new ErrorApi('desconocido', detalle || `Error inesperado (${s}).`, { status: s, detalle })
  }

  async function refrescarConToken(refresh: string): Promise<RefrescoRespuesta> {
    const respuesta = await enviar('/auth/refresh/', { metodo: 'POST', cuerpo: { refresh } }, false)
    if (respuesta.ok) {
      const datos = (await leerJson(respuesta)) as RefrescoRespuesta | undefined
      if (!datos?.access) throw new ErrorApi('desconocido', 'Respuesta de renovación inválida.')
      return datos
    }
    if (respuesta.status >= 500) throw new ErrorServidor(respuesta.status)
    throw new ErrorSesionExpirada()
  }

  /** Renueva el access token; las llamadas simultáneas comparten una sola petición. */
  function renovar(): Promise<void> {
    if (!renovando) {
      const refresh = sesion.obtenerRefresh()
      if (!refresh) return Promise.reject(new ErrorSesionExpirada())
      renovando = refrescarConToken(refresh)
        .then((datos) => sesion.alRenovar(datos.access, datos.refresh))
        .finally(() => {
          renovando = null
        })
    }
    return renovando
  }

  async function solicitar<T>(ruta: string, op: OpcionesSolicitud = {}): Promise<T> {
    const autenticar = op.autenticar ?? true
    let respuesta = await enviar(ruta, op, autenticar)

    if (respuesta.status === 401 && autenticar) {
      try {
        await renovar()
      } catch (e) {
        // Una caída de red o del servidor al renovar no invalida la sesión: se informa y se podrá reintentar.
        if (e instanceof ErrorRed || (e instanceof ErrorApi && e.codigo === 'servidor')) throw e
        sesion.alExpirar()
        throw new ErrorSesionExpirada()
      }
      respuesta = await enviar(ruta, op, true)
      if (respuesta.status === 401) {
        sesion.alExpirar()
        throw new ErrorSesionExpirada()
      }
    }

    if (!respuesta.ok) throw await aError(respuesta, autenticar)
    return (await leerJson(respuesta)) as T
  }

  return {
    configurarSesion(nueva) {
      sesion = nueva
    },
    solicitar,
    refrescarConToken,
  }
}
