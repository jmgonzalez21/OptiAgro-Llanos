import { reemplazarApi } from '@/api'
import { crearMockFetch } from '@/api/mock'
import { crearApi, crearClienteHttp } from '@/api/servicios'
import { CLAVE_REFRESH } from '@/config'

/** Crea una API real (cliente HTTP) conectada a un mock sin latencia y la deja activa. */
export function prepararApiMock() {
  const mock = crearMockFetch({ latenciaMs: 0 })
  const api = crearApi(crearClienteHttp({ base: '/api/v1', fetchImpl: mock.fetch }))
  reemplazarApi(api)
  return { api, mock }
}

export function limpiarAlmacenamiento(): void {
  sessionStorage.removeItem(CLAVE_REFRESH)
}
