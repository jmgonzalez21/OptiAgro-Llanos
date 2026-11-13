import type { Empresa, Planta } from '@/types/api'

export type TipoEstacion = 'empresa' | 'planta'

/** Estación normalizada para el mapa y los listados. */
export interface Estacion {
  clave: string
  id: number
  tipo: TipoEstacion
  nombre: string
  municipio: string
  /** Oferta (empresa) o capacidad (planta), en t/semana. */
  cantidad: number
  latitud: number | null
  longitud: number | null
  ficticio: boolean
}

export interface EstacionUbicada extends Estacion {
  latitud: number
  longitud: number
}

export const ETIQUETA_TIPO: Record<TipoEstacion, string> = {
  empresa: 'Agroempresa',
  planta: 'Planta',
}

export const ETIQUETA_CANTIDAD: Record<TipoEstacion, string> = {
  empresa: 'Oferta',
  planta: 'Capacidad',
}

export function coordenadasValidas(lat: number | null | undefined, lng: number | null | undefined): boolean {
  return (
    typeof lat === 'number' &&
    typeof lng === 'number' &&
    Number.isFinite(lat) &&
    Number.isFinite(lng) &&
    Math.abs(lat) <= 90 &&
    Math.abs(lng) <= 180
  )
}

export function tieneUbicacion(e: Estacion): e is EstacionUbicada {
  return coordenadasValidas(e.latitud, e.longitud)
}

/**
 * Une empresas y plantas ACTIVAS en una lista de estaciones y las separa según
 * tengan o no coordenadas válidas.
 */
export function prepararEstaciones(empresas: Empresa[], plantas: Planta[]) {
  const todas: Estacion[] = [
    ...empresas
      .filter((e) => e.activa)
      .map<Estacion>((e) => ({
        clave: `empresa-${e.id}`,
        id: e.id,
        tipo: 'empresa',
        nombre: e.nombre,
        municipio: e.municipio,
        cantidad: e.oferta,
        latitud: e.latitud,
        longitud: e.longitud,
        ficticio: e.ficticio === true,
      })),
    ...plantas
      .filter((p) => p.activa)
      .map<Estacion>((p) => ({
        clave: `planta-${p.id}`,
        id: p.id,
        tipo: 'planta',
        nombre: p.nombre,
        municipio: p.municipio,
        cantidad: p.capacidad,
        latitud: p.latitud,
        longitud: p.longitud,
        ficticio: p.ficticio === true,
      })),
  ]
  return {
    ubicadas: todas.filter(tieneUbicacion),
    sinUbicacion: todas.filter((e) => !tieneUbicacion(e)),
  }
}

const formato = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 })

/** "45 t/semana" */
export function formatearToneladas(valor: number): string {
  return `${formato.format(valor)} t/semana`
}
