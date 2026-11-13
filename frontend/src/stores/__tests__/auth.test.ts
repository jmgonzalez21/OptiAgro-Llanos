import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { ErrorCredenciales, ErrorRed } from '@/api/errores'
import { CLAVE_REFRESH } from '@/config'
import { useAuthStore } from '@/stores/auth'
import { limpiarAlmacenamiento, prepararApiMock } from '@/test/helpers'

describe('store de autenticación', () => {
  let mock: ReturnType<typeof prepararApiMock>['mock']

  beforeEach(() => {
    limpiarAlmacenamiento()
    ;({ mock } = prepararApiMock())
    setActivePinia(createPinia())
  })

  it('inicia sin sesión', () => {
    const auth = useAuthStore()
    expect(auth.autenticado).toBe(false)
    expect(auth.rol).toBeNull()
  })

  it('login correcto guarda usuario, rol y tokens; solo el refresh va a sessionStorage', async () => {
    const auth = useAuthStore()
    await auth.login({ username: 'admin', password: 'x' })

    expect(auth.autenticado).toBe(true)
    expect(auth.rol).toBe('administrador')
    expect(auth.esAdministrador).toBe(true)
    expect(auth.nombre).toBe('Admin Demo')
    expect(auth.access).toBeTruthy()
    expect(sessionStorage.getItem(CLAVE_REFRESH)).toBe(auth.refresh)
    // El access token nunca se persiste.
    expect(JSON.stringify({ ...sessionStorage })).not.toContain(auth.access as string)
  })

  it('usuarios distintos de admin son analistas', async () => {
    const auth = useAuthStore()
    await auth.login({ username: 'lucia', password: 'x' })
    expect(auth.rol).toBe('analista')
    expect(auth.etiquetaRol).toBe('Analista')
  })

  it('login con credenciales inválidas lanza ErrorCredenciales y no deja sesión', async () => {
    mock.estado.rechazarLogin = true
    const auth = useAuthStore()
    await expect(auth.login({ username: 'a', password: 'b' })).rejects.toBeInstanceOf(ErrorCredenciales)
    expect(auth.autenticado).toBe(false)
    expect(auth.cargando).toBe(false)
    expect(sessionStorage.getItem(CLAVE_REFRESH)).toBeNull()
  })

  it('login con la red caída lanza ErrorRed', async () => {
    mock.estado.caido = true
    const auth = useAuthStore()
    await expect(auth.login({ username: 'a', password: 'b' })).rejects.toBeInstanceOf(ErrorRed)
    expect(auth.autenticado).toBe(false)
  })

  it('logout limpia memoria y sessionStorage', async () => {
    const auth = useAuthStore()
    await auth.login({ username: 'a', password: 'b' })
    auth.logout()
    expect(auth.autenticado).toBe(false)
    expect(auth.access).toBeNull()
    expect(auth.refresh).toBeNull()
    expect(sessionStorage.getItem(CLAVE_REFRESH)).toBeNull()
  })

  it('restaura la sesión tras un "refresco de página" con el refresh guardado', async () => {
    const primera = useAuthStore()
    await primera.login({ username: 'admin', password: 'x' })
    const guardado = sessionStorage.getItem(CLAVE_REFRESH)
    expect(guardado).toBeTruthy()

    // Simula recargar la página: Pinia nuevo (memoria vacía), sessionStorage intacto.
    setActivePinia(createPinia())
    const nueva = useAuthStore()
    expect(nueva.autenticado).toBe(false)
    const ok = await nueva.restaurarSesion()

    expect(ok).toBe(true)
    expect(nueva.autenticado).toBe(true)
    expect(nueva.rol).toBe('administrador')
  })

  it('restaurar sin refresh guardado devuelve false', async () => {
    const auth = useAuthStore()
    expect(await auth.restaurarSesion()).toBe(false)
  })

  it('restaurar con un refresh inválido lo borra', async () => {
    sessionStorage.setItem(CLAVE_REFRESH, 'token-invalido')
    const auth = useAuthStore()
    expect(await auth.restaurarSesion()).toBe(false)
    expect(sessionStorage.getItem(CLAVE_REFRESH)).toBeNull()
  })

  it('restaurar con la red caída conserva el refresh para reintentar', async () => {
    const primera = useAuthStore()
    await primera.login({ username: 'a', password: 'b' })
    const guardado = sessionStorage.getItem(CLAVE_REFRESH)

    setActivePinia(createPinia())
    mock.estado.caido = true
    const nueva = useAuthStore()
    expect(await nueva.restaurarSesion()).toBe(false)
    expect(sessionStorage.getItem(CLAVE_REFRESH)).toBe(guardado)
  })

  it('si el refresh vence durante el uso, la sesión expira y se marca sesionExpirada', async () => {
    const auth = useAuthStore()
    mock.estado.ttlAccessMs = -1000
    mock.estado.ttlRefreshMs = -1000
    await auth.login({ username: 'a', password: 'b' })

    const { obtenerApi } = await import('@/api')
    await expect(obtenerApi().listarEmpresas()).rejects.toMatchObject({ codigo: 'sesion_expirada' })
    expect(auth.autenticado).toBe(false)
    expect(auth.sesionExpirada).toBe(true)
    expect(sessionStorage.getItem(CLAVE_REFRESH)).toBeNull()
  })

  it('sobrevive a sessionStorage no disponible (try/catch)', async () => {
    const original = Storage.prototype.setItem
    Storage.prototype.setItem = () => {
      throw new Error('bloqueado')
    }
    try {
      const auth = useAuthStore()
      await expect(auth.login({ username: 'a', password: 'b' })).resolves.toBeUndefined()
      expect(auth.autenticado).toBe(true)
    } finally {
      Storage.prototype.setItem = original
    }
  })
})
