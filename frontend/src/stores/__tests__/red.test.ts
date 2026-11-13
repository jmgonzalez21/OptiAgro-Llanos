import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { obtenerApi, reemplazarApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useRedStore } from '@/stores/red'
import { limpiarAlmacenamiento, prepararApiMock } from '@/test/helpers'

describe('store de la red', () => {
  let mock: ReturnType<typeof prepararApiMock>['mock']

  beforeEach(async () => {
    limpiarAlmacenamiento()
    ;({ mock } = prepararApiMock())
    setActivePinia(createPinia())
    await useAuthStore().login({ username: 'ana', password: 'x' })
  })

  it('carga 10 empresas y 4 plantas activas', async () => {
    const red = useRedStore()
    expect(red.estado).toBe('inactivo')
    await red.cargar()
    expect(red.estado).toBe('listo')
    expect(red.empresas).toHaveLength(10)
    expect(red.plantas).toHaveLength(4)
    expect(red.total).toBe(14)
  })

  it('una estación que deja de venir como activa desaparece al recargar', async () => {
    const red = useRedStore()
    await red.cargar()
    mock.estado.empresas[2]!.activa = false
    mock.estado.plantas[1]!.activa = false
    await red.cargar()
    expect(red.empresas).toHaveLength(9)
    expect(red.plantas).toHaveLength(3)
    expect(red.empresas.some((e) => e.id === 3)).toBe(false)
  })

  it('descarta estaciones inactivas aunque lleguen del servidor', async () => {
    const red = useRedStore()
    const real = obtenerApi()
    // Simula un backend que ignora el filtro activa=true.
    reemplazarApi({
      ...real,
      listarEmpresas: async () => {
        const todas = await real.listarEmpresas()
        return todas.map((e, i) => (i === 0 ? { ...e, activa: false } : e))
      },
    })
    await red.cargar()
    expect(red.empresas).toHaveLength(9)
    expect(red.empresas.every((e) => e.activa)).toBe(true)
  })

  it('error de red: estado error con mensaje y se puede reintentar', async () => {
    const red = useRedStore()
    mock.estado.caido = true
    await red.cargar()
    expect(red.estado).toBe('error')
    expect(red.error).toContain('No hay conexión')

    mock.estado.caido = false
    await red.cargar()
    expect(red.estado).toBe('listo')
    expect(red.error).toBeNull()
  })

  it('403 se informa como falta de permiso', async () => {
    const red = useRedStore()
    mock.estado.forzarEstado = 403
    await red.cargar()
    expect(red.estado).toBe('error')
    expect(red.error).toContain('No tienes permiso')
  })
})
