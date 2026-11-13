import { describe, expect, it } from 'vitest'
import { crearMockFetch } from '@/api/mock'
import { crearApi, crearClienteHttp, type ApiService } from '@/api/servicios'
import {
  ErrorCredenciales,
  ErrorPermiso,
  ErrorRed,
  ErrorSesionExpirada,
  ErrorValidacion,
} from '@/api/errores'

function crear(opciones: { ttlAccessMs?: number } = {}) {
  const mock = crearMockFetch({ latenciaMs: 0 })
  if (opciones.ttlAccessMs !== undefined) mock.estado.ttlAccessMs = opciones.ttlAccessMs
  const api: ApiService = crearApi(crearClienteHttp({ base: '/api/v1', fetchImpl: mock.fetch }))
  return { api, mock }
}

/** Conecta una sesión en memoria al cliente, como lo hace el store de auth. */
function conSesion(api: ApiService, tokens: { access: string | null; refresh: string | null }) {
  const eventos = { expirada: 0, renovada: 0 }
  api.configurarSesion({
    obtenerAccess: () => tokens.access,
    obtenerRefresh: () => tokens.refresh,
    alRenovar: (a, r) => {
      tokens.access = a
      if (r) tokens.refresh = r
      eventos.renovada++
    },
    alExpirar: () => {
      tokens.access = null
      tokens.refresh = null
      eventos.expirada++
    },
  })
  return eventos
}

describe('capa mock: autenticación', () => {
  it('acepta cualquier usuario y contraseña no vacíos', async () => {
    const { api } = crear()
    const r = await api.login({ username: 'maria', password: 'x' })
    expect(r.access).toBeTruthy()
    expect(r.refresh).toBeTruthy()
    expect(r.usuario?.rol).toBe('analista')
  })

  it('"admin" es administrador y los demás analistas', async () => {
    const { api } = crear()
    const tokens = { access: null as string | null, refresh: null as string | null }
    conSesion(api, tokens)

    const admin = await api.login({ username: 'admin', password: 'cualquiera' })
    tokens.access = admin.access
    expect((await api.obtenerUsuario()).rol).toBe('administrador')

    const otro = await api.login({ username: 'carlos', password: 'cualquiera' })
    tokens.access = otro.access
    const yo = await api.obtenerUsuario()
    expect(yo.rol).toBe('analista')
    expect(yo.username).toBe('carlos')
    expect(yo.nombre_completo).toBeTruthy()
    expect(yo.email).toContain('@')
  })

  it('rechaza usuario o contraseña vacíos con ErrorValidacion (400)', async () => {
    const { api } = crear()
    await expect(api.login({ username: '  ', password: '' })).rejects.toBeInstanceOf(ErrorValidacion)
  })

  it('devuelve ErrorCredenciales cuando el login es rechazado (401)', async () => {
    const { api, mock } = crear()
    mock.estado.rechazarLogin = true
    await expect(api.login({ username: 'a', password: 'b' })).rejects.toBeInstanceOf(ErrorCredenciales)
  })

  it('/auth/me sin token falla con sesión expirada y la notifica', async () => {
    const { api } = crear()
    const eventos = conSesion(api, { access: null, refresh: null })
    await expect(api.obtenerUsuario()).rejects.toBeInstanceOf(ErrorSesionExpirada)
    expect(eventos.expirada).toBe(1)
  })

  it('refrescar entrega un access nuevo y rechaza refresh inválidos', async () => {
    const { api } = crear()
    const { refresh } = await api.login({ username: 'ana', password: 'x' })
    expect((await api.refrescar(refresh)).access).toBeTruthy()
    await expect(api.refrescar('basura')).rejects.toBeInstanceOf(ErrorSesionExpirada)
  })
})

describe('capa mock: interceptor JWT', () => {
  it('renueva el access vencido con el refresh y reintenta la petición', async () => {
    const { api, mock } = crear({ ttlAccessMs: -1000 }) // los access nacen vencidos
    const tokens = { access: null as string | null, refresh: null as string | null }
    const eventos = conSesion(api, tokens)
    const login = await api.login({ username: 'ana', password: 'x' })
    tokens.access = login.access
    tokens.refresh = login.refresh

    mock.estado.ttlAccessMs = 5 * 60 * 1000 // el access renovado sí será válido
    const usuario = await api.obtenerUsuario()

    expect(usuario.username).toBe('ana')
    expect(eventos.renovada).toBe(1)
    expect(mock.estado.registro.filter((r) => r.includes('/auth/refresh/'))).toHaveLength(1)
  })

  it('peticiones simultáneas comparten una sola renovación', async () => {
    const { api, mock } = crear({ ttlAccessMs: -1000 })
    const tokens = { access: null as string | null, refresh: null as string | null }
    conSesion(api, tokens)
    const login = await api.login({ username: 'ana', password: 'x' })
    tokens.access = login.access
    tokens.refresh = login.refresh
    mock.estado.ttlAccessMs = 5 * 60 * 1000

    await Promise.all([api.listarEmpresas(), api.listarPlantas(), api.obtenerUsuario()])
    expect(mock.estado.registro.filter((r) => r.includes('/auth/refresh/'))).toHaveLength(1)
  })

  it('si el refresh también venció, expira la sesión', async () => {
    const { api, mock } = crear({ ttlAccessMs: -1000 })
    mock.estado.ttlRefreshMs = -1000
    const tokens = { access: null as string | null, refresh: null as string | null }
    const eventos = conSesion(api, tokens)
    const login = await api.login({ username: 'ana', password: 'x' })
    tokens.access = login.access
    tokens.refresh = login.refresh

    await expect(api.listarEmpresas()).rejects.toBeInstanceOf(ErrorSesionExpirada)
    expect(eventos.expirada).toBe(1)
    expect(tokens.access).toBeNull()
  })
})

describe('capa mock: datos y errores', () => {
  async function autenticada() {
    const ctx = crear()
    const tokens = { access: null as string | null, refresh: null as string | null }
    conSesion(ctx.api, tokens)
    const login = await ctx.api.login({ username: 'ana', password: 'x' })
    tokens.access = login.access
    tokens.refresh = login.refresh
    return ctx
  }

  it('devuelve 10 empresas ficticias y 4 plantas reales, activas y con coordenadas', async () => {
    const { api } = await autenticada()
    const empresas = await api.listarEmpresas({ activa: true })
    const plantas = await api.listarPlantas({ activa: true })

    expect(empresas).toHaveLength(10)
    expect(empresas.every((e) => e.ficticio === true && e.activa)).toBe(true)
    expect(plantas.map((p) => p.municipio).sort()).toEqual(['Granada', 'Puerto Gaitán', 'Restrepo', 'Villavicencio'])
    const villavicencio = plantas.find((p) => p.municipio === 'Villavicencio')
    expect(villavicencio).toMatchObject({ latitud: 4.142, longitud: -73.6266 })
    for (const e of [...empresas, ...plantas]) {
      expect(e.latitud).toBeGreaterThan(3)
      expect(e.latitud).toBeLessThan(5)
      expect(e.longitud).toBeLessThan(-71)
    }
    expect(empresas[0]).toHaveProperty('oferta')
    expect(plantas[0]).toHaveProperty('capacidad')
  })

  it('filtra por activa=true', async () => {
    const { api, mock } = await autenticada()
    mock.estado.empresas[0]!.activa = false
    expect(await api.listarEmpresas({ activa: true })).toHaveLength(9)
    expect(await api.listarEmpresas({ activa: false })).toHaveLength(1)
  })

  it('recorre todas las páginas (page_size pequeño en el servidor)', async () => {
    const { api, mock } = await autenticada()
    // El mock pagina de a 50 por defecto; con 120 empresas el cliente debe unir las páginas.
    const base = mock.estado.empresas[0]!
    mock.estado.empresas = Array.from({ length: 120 }, (_, i) => ({ ...base, id: 100 + i }))
    // El cliente pide 200 por página: se comprueba además el caso explícito con el mock en 50.
    const resp = await mock.fetch('/api/v1/empresas/?page_size=50', {
      headers: { Authorization: `Bearer ${(await api.login({ username: 'ana', password: 'x' })).access}` },
    })
    const pagina = (await resp.json()) as { count: number; next: string | null; results: unknown[] }
    expect(pagina.count).toBe(120)
    expect(pagina.results).toHaveLength(50)
    expect(pagina.next).toContain('page=2')
    expect(await api.listarEmpresas()).toHaveLength(120)
  })

  it('servidor caído -> ErrorRed', async () => {
    const { api, mock } = crear()
    mock.estado.caido = true
    await expect(api.login({ username: 'a', password: 'b' })).rejects.toBeInstanceOf(ErrorRed)
  })

  it('403 -> ErrorPermiso', async () => {
    const { api, mock } = await autenticada()
    mock.estado.forzarEstado = 403
    await expect(api.listarEmpresas()).rejects.toBeInstanceOf(ErrorPermiso)
  })
})
