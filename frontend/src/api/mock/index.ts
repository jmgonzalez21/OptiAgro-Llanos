/**
 * Capa MOCK: un `fetch` falso que responde como lo hará la API real
 * (mismas rutas, códigos HTTP y forma JSON, incluida la paginación).
 * Así el cliente HTTP, el interceptor JWT y los servicios se ejercitan igual
 * con mock y con backend. Para quitar el mock: borrar esta carpeta y las
 * líneas marcadas con "MOCK" en `src/api/index.ts`.
 *
 * Los tokens son cadenas de juguete sin firma ni secreto (no son JWT reales).
 */
import { EMPRESAS_MOCK, PLANTAS_MOCK } from './datos'
import type { Empresa, Planta, Rol, Usuario } from '@/types/api'

export interface EstadoMock {
  empresas: Empresa[]
  plantas: Planta[]
  /** Simula servidor caído: todas las peticiones fallan como error de red. */
  caido: boolean
  /** Si es true, el login responde 401 (credenciales inválidas). */
  rechazarLogin: boolean
  /** Vida del access token en ms (negativo = ya vencido; útil para probar el refresh). */
  ttlAccessMs: number
  /** Vida del refresh token en ms. */
  ttlRefreshMs: number
  /** Si se define, las rutas protegidas responden este código (p. ej. 403). */
  forzarEstado: number | null
  /** Peticiones recibidas "METODO /ruta" (para pruebas). */
  registro: string[]
}

export interface OpcionesMock {
  /** Latencia simulada en ms (por defecto 250; usar 0 en pruebas). */
  latenciaMs?: number
}

export interface MockApi {
  fetch: typeof fetch
  estado: EstadoMock
}

const PREFIJO = '/api/v1'
const TAMANO_PAGINA_POR_DEFECTO = 50

type Json = Record<string, unknown> | unknown[]

function respuesta(estado: number, cuerpo?: Json): Response {
  return new Response(cuerpo === undefined ? null : JSON.stringify(cuerpo), {
    status: estado,
    headers: { 'Content-Type': 'application/json' },
  })
}

function capitalizar(texto: string): string {
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

function idEstable(username: string): number {
  let h = 0
  for (const c of username) h = (h * 31 + c.charCodeAt(0)) % 100000
  return 1000 + h
}

function construirUsuario(username: string): Usuario {
  const rol: Rol = username === 'admin' ? 'administrador' : 'analista'
  const first_name = capitalizar(username)
  const last_name = 'Demo'
  return {
    id: idEstable(username),
    username,
    // Se devuelven ambas formas (la pedida y la del OpenAPI actual).
    nombre_completo: `${first_name} ${last_name}`,
    first_name,
    last_name,
    email: `${encodeURIComponent(username).toLowerCase()}@demo.invalid`,
    rol,
  }
}

const crearToken = (tipo: 'access' | 'refresh', username: string, ttl: number) =>
  `mock.${tipo}.${encodeURIComponent(username)}.${Date.now() + ttl}`

/** Devuelve el usuario del token o null si es inválido o venció. */
function leerToken(token: string | undefined, tipo: 'access' | 'refresh'): string | null {
  const partes = token?.split('.')
  if (!partes || partes.length !== 4 || partes[0] !== 'mock' || partes[1] !== tipo) return null
  const expira = Number(partes[3])
  if (!Number.isFinite(expira) || expira <= Date.now()) return null
  return decodeURIComponent(partes[2] ?? '') || null
}

function paginar<T>(items: T[], url: URL, ruta: string): Json {
  const tamano = Math.max(1, Number(url.searchParams.get('page_size')) || TAMANO_PAGINA_POR_DEFECTO)
  const pagina = Math.max(1, Number(url.searchParams.get('page')) || 1)
  const inicio = (pagina - 1) * tamano
  const enlace = (p: number) => {
    const u = new URL(`${PREFIJO}${ruta}`, 'http://mock.local')
    url.searchParams.forEach((v, k) => u.searchParams.set(k, v))
    u.searchParams.set('page', String(p))
    return `http://mock.local${u.pathname}${u.search}`
  }
  return {
    count: items.length,
    next: inicio + tamano < items.length ? enlace(pagina + 1) : null,
    previous: pagina > 1 ? enlace(pagina - 1) : null,
    results: items.slice(inicio, inicio + tamano),
  }
}

function filtrarActiva<T extends { activa: boolean }>(items: T[], url: URL): T[] {
  const activa = url.searchParams.get('activa')
  if (activa === null) return items
  return items.filter((i) => i.activa === (activa === 'true'))
}

export function crearMockFetch(opciones: OpcionesMock = {}): MockApi {
  const latencia = opciones.latenciaMs ?? 250
  const estado: EstadoMock = {
    empresas: structuredClone(EMPRESAS_MOCK),
    plantas: structuredClone(PLANTAS_MOCK),
    caido: false,
    rechazarLogin: false,
    ttlAccessMs: 5 * 60 * 1000,
    ttlRefreshMs: 8 * 60 * 60 * 1000,
    forzarEstado: null,
    registro: [],
  }

  async function manejar(metodo: string, url: URL, headers: Headers, cuerpo: Record<string, unknown>): Promise<Response> {
    const ruta = url.pathname.startsWith(PREFIJO) ? url.pathname.slice(PREFIJO.length) : url.pathname

    // --- Rutas públicas ---
    if (ruta === '/auth/login/' && metodo === 'POST') {
      const username = String(cuerpo.username ?? '').trim()
      const password = String(cuerpo.password ?? '')
      const errores: Record<string, string[]> = {}
      if (!username) errores.username = ['Este campo no puede estar en blanco.']
      if (!password) errores.password = ['Este campo no puede estar en blanco.']
      if (Object.keys(errores).length) {
        return respuesta(400, { detail: 'Datos inválidos.', errores })
      }
      if (estado.rechazarLogin) {
        return respuesta(401, { detail: 'No hay una cuenta activa con las credenciales dadas.' })
      }
      return respuesta(200, {
        access: crearToken('access', username, estado.ttlAccessMs),
        refresh: crearToken('refresh', username, estado.ttlRefreshMs),
        usuario: construirUsuario(username),
      })
    }

    if (ruta === '/auth/refresh/' && metodo === 'POST') {
      const username = leerToken(String(cuerpo.refresh ?? ''), 'refresh')
      if (!username) return respuesta(401, { detail: 'El token es inválido o ha expirado.' })
      return respuesta(200, { access: crearToken('access', username, estado.ttlAccessMs) })
    }

    // --- Rutas protegidas ---
    const portador = headers.get('Authorization')?.replace(/^Bearer\s+/i, '')
    const username = leerToken(portador, 'access')
    if (!username) {
      return respuesta(401, { detail: 'Las credenciales de autenticación no se proporcionaron o han expirado.' })
    }
    if (estado.forzarEstado) {
      return respuesta(estado.forzarEstado, { detail: 'Respuesta forzada por el mock.' })
    }

    if (ruta === '/auth/me/' && metodo === 'GET') return respuesta(200, { ...construirUsuario(username) })
    if (ruta === '/empresas/' && metodo === 'GET') {
      return respuesta(200, paginar(filtrarActiva(estado.empresas, url), url, ruta))
    }
    if (ruta === '/plantas/' && metodo === 'GET') {
      return respuesta(200, paginar(filtrarActiva(estado.plantas, url), url, ruta))
    }
    return respuesta(404, { detail: 'No encontrado.' })
  }

  const mockFetch = async (entrada: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const url = new URL(typeof entrada === 'string' ? entrada : entrada instanceof URL ? entrada.href : entrada.url, 'http://mock.local')
    const metodo = (init?.method ?? 'GET').toUpperCase()
    estado.registro.push(`${metodo} ${url.pathname}`)
    if (latencia > 0) await new Promise((r) => setTimeout(r, latencia))
    if (estado.caido) throw new TypeError('Failed to fetch (mock: servidor caído)')
    let cuerpo: Record<string, unknown> = {}
    if (typeof init?.body === 'string' && init.body) {
      try {
        cuerpo = JSON.parse(init.body) as Record<string, unknown>
      } catch {
        return respuesta(400, { detail: 'JSON inválido.' })
      }
    }
    return manejar(metodo, url, new Headers(init?.headers), cuerpo)
  }

  return { fetch: mockFetch as typeof fetch, estado }
}

export { EMPRESAS_MOCK, PLANTAS_MOCK }
