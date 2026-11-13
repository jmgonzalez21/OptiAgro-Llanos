/**
 * Punto de entrada de la capa API.
 *
 * Elige entre la API real y la capa mock según `VITE_USE_MOCK` (por defecto true).
 * Para pasar definitivamente a la API real basta con borrar la carpeta `./mock`,
 * las 2 líneas marcadas con "MOCK" y el import de USAR_MOCK de este archivo.
 */
import { API_BASE, USAR_MOCK } from '@/config'
import { crearApi, crearClienteHttp, type ApiService } from './servicios'
import { crearMockFetch } from './mock' // MOCK

export type { ApiService } from './servicios'

function crearApiPorDefecto(): ApiService {
  const fetchImpl = USAR_MOCK ? crearMockFetch().fetch : undefined // MOCK
  return crearApi(crearClienteHttp({ base: API_BASE, fetchImpl }))
}

let instancia: ApiService | null = null

/** API activa (se crea al primer uso). */
export function obtenerApi(): ApiService {
  instancia ??= crearApiPorDefecto()
  return instancia
}

/** Gancho para pruebas: sustituye la API activa (o `null` para restablecer). */
export function reemplazarApi(api: ApiService | null): void {
  instancia = api
}
