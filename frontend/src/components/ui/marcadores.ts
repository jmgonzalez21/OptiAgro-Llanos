/**
 * Geometría compartida de los marcadores de estación (mapa y leyenda).
 * - Agroempresa: círculo verde con hoja.
 * - Planta: cuadrado redondeado (más grande), verde profundo, con fábrica/chimenea.
 * La forma + el glifo permiten distinguirlos sin depender del color.
 */
import { ICONOS } from './icons'

export type TipoMarcador = 'empresa' | 'planta'

/** viewBox común 0 0 40 40 */
export const BASE_MARCADOR = {
  empresa: { tag: 'circle', atributos: { cx: 20, cy: 20, r: 16 } },
  planta: { tag: 'rect', atributos: { x: 3, y: 3, width: 34, height: 34, rx: 11 } },
} as const

/** Transformación que coloca el glifo (24x24) centrado dentro de la base. */
export const GLIFO_TRANSFORM: Record<TipoMarcador, string> = {
  empresa: 'translate(10 10) scale(0.833)',
  planta: 'translate(9.5 9.5) scale(0.875)',
}

export const GLIFO_RUTAS: Record<TipoMarcador, readonly string[]> = {
  empresa: ICONOS.hoja,
  planta: ICONOS.fabrica,
}

/** Tamaño en píxeles del elemento (área táctil) para Leaflet. */
export const TAMANO_MARCADOR: Record<TipoMarcador, number> = { empresa: 40, planta: 46 }

function atributosBase(tipo: TipoMarcador): string {
  return Object.entries(BASE_MARCADOR[tipo].atributos)
    .map(([k, v]) => `${k}="${v}"`)
    .join(' ')
}

/** Cadena SVG para `L.divIcon` (contenido estático y de confianza). */
export function svgMarcador(tipo: TipoMarcador, px: number = TAMANO_MARCADOR[tipo]): string {
  const rutas = GLIFO_RUTAS[tipo].map((d) => `<path d="${d}" />`).join('')
  return (
    `<svg class="marcador__svg" viewBox="0 0 40 40" width="${px}" height="${px}" aria-hidden="true" focusable="false">` +
    `<${BASE_MARCADOR[tipo].tag} class="marcador__base" ${atributosBase(tipo)} />` +
    `<g class="marcador__glifo" transform="${GLIFO_TRANSFORM[tipo]}" stroke-width="2.2">${rutas}</g>` +
    `</svg>`
  )
}
