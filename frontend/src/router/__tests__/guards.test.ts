import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, type RouteRecordRaw } from 'vue-router'
import { crearRouter } from '@/router'
import { redireccionSegura } from '@/router/guards'
import { rutasApp } from '@/router/routes'
import { useAuthStore } from '@/stores/auth'
import { CLAVE_REFRESH } from '@/config'
import { limpiarAlmacenamiento, prepararApiMock } from '@/test/helpers'

const Vacia = { template: '<div />' }

/** Rutas de prueba con las mismas metas que las reales (más una exclusiva de administradores). */
const rutasPrueba: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: Vacia, meta: { soloInvitado: true } },
  {
    path: '/',
    component: Vacia,
    meta: { requiereAuth: true },
    children: [
      { path: '', name: 'inicio', component: Vacia },
      { path: 'sin-permiso', name: 'sin-permiso', component: Vacia },
      { path: 'admin', name: 'admin', component: Vacia, meta: { roles: ['administrador'] } },
    ],
  },
]

describe('route guards', () => {
  beforeEach(() => {
    limpiarAlmacenamiento()
    prepararApiMock()
    setActivePinia(createPinia())
  })

  it('una ruta privada sin sesión redirige a /login conservando el destino', async () => {
    const router = crearRouter(createMemoryHistory(), rutasPrueba)
    await router.push('/admin')
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/admin')
  })

  it('la raíz sin sesión va a /login sin parámetro redirect', async () => {
    const router = crearRouter(createMemoryHistory(), rutasPrueba)
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBeUndefined()
  })

  it('/login con sesión redirige al inicio', async () => {
    const auth = useAuthStore()
    await auth.login({ username: 'ana', password: 'x' })
    const router = crearRouter(createMemoryHistory(), rutasPrueba)
    await router.push('/login')
    expect(router.currentRoute.value.name).toBe('inicio')
  })

  it('una ruta con roles bloquea a quien no lo tiene (analista)', async () => {
    const auth = useAuthStore()
    await auth.login({ username: 'ana', password: 'x' })
    const router = crearRouter(createMemoryHistory(), rutasPrueba)
    await router.push('/admin')
    expect(router.currentRoute.value.name).toBe('sin-permiso')
  })

  it('una ruta con roles permite al administrador', async () => {
    const auth = useAuthStore()
    await auth.login({ username: 'admin', password: 'x' })
    const router = crearRouter(createMemoryHistory(), rutasPrueba)
    await router.push('/admin')
    expect(router.currentRoute.value.name).toBe('admin')
  })

  it('restaura la sesión desde sessionStorage antes de decidir', async () => {
    const previa = useAuthStore()
    await previa.login({ username: 'ana', password: 'x' })
    expect(sessionStorage.getItem(CLAVE_REFRESH)).toBeTruthy()

    setActivePinia(createPinia()) // "recarga de página"
    const router = crearRouter(createMemoryHistory(), rutasPrueba)
    await router.push('/')
    expect(router.currentRoute.value.name).toBe('inicio')
    expect(useAuthStore().autenticado).toBe(true)
  })

  it('las rutas reales declaran las metas de acceso esperadas', () => {
    const login = rutasApp.find((r) => r.path === '/login')
    const layout = rutasApp.find((r) => r.path === '/')
    expect(login?.meta?.soloInvitado).toBe(true)
    expect(layout?.meta?.requiereAuth).toBe(true)
  })
})

describe('redireccionSegura', () => {
  it('acepta rutas internas y rechaza externas', () => {
    expect(redireccionSegura('/escenarios')).toBe('/escenarios')
    expect(redireccionSegura('//evil.com')).toBe('/')
    expect(redireccionSegura('https://evil.com')).toBe('/')
    expect(redireccionSegura(undefined)).toBe('/')
  })
})
