/** Utilidades de alta de red: códigos automáticos, tarifa por defecto y rutas propuestas (la distancia la calcula el backend por carretera). */

/** Tarifa de respaldo (COP por tonelada y km) si todavía no hay rutas de referencia. */
export const TARIFA_POR_DEFECTO = 500

export function mediana(valores: number[]): number | null {
  const v = valores.filter((x) => Number.isFinite(x)).sort((a, b) => a - b)
  if (v.length === 0) return null
  const m = Math.floor(v.length / 2)
  return v.length % 2 ? (v[m] as number) : ((v[m - 1] as number) + (v[m] as number)) / 2
}

/** Tarifa por defecto: mediana de las tarifas de las rutas existentes (redondeada) o un valor razonable. */
export function tarifaSugerida(tarifas: Array<number | null | undefined>): number {
  const m = mediana(tarifas.filter((t): t is number => typeof t === 'number' && t > 0))
  return m === null ? TARIFA_POR_DEFECTO : Math.round(m)
}

/** Siguiente código libre con el prefijo dado (E11, P5…). Considera también los códigos de estaciones inactivas. */
export function siguienteCodigo(prefijo: string, existentes: string[]): string {
  const usados = new Set(existentes.map((c) => c.toUpperCase()))
  let max = 0
  for (const c of usados) {
    const m = new RegExp(`^${prefijo}(\\d+)$`).exec(c)
    if (m) max = Math.max(max, Number(m[1]))
  }
  let n = max + 1
  while (usados.has(`${prefijo}${n}`)) n++
  return `${prefijo}${n}`
}

export interface PuntoConCodigo {
  codigo: string
  latitud: number | null
  longitud: number | null
}

export interface RutaPropuesta {
  empresa: string
  planta: string
  tarifa_km_ton: number
}

/**
 * Rutas que se crearían entre una estación nueva y todas las del tipo contrario que tengan coordenadas.
 * `sinUbicacion` cuenta las que no se pudieron estimar.
 */
export function proponerRutas(
  tipoNueva: 'empresa' | 'planta',
  nueva: PuntoConCodigo & { latitud: number; longitud: number },
  contrarias: PuntoConCodigo[],
  tarifa: number,
): { rutas: RutaPropuesta[]; sinUbicacion: number } {
  const rutas: RutaPropuesta[] = []
  let sinUbicacion = 0
  for (const o of contrarias) {
    if (typeof o.latitud !== 'number' || typeof o.longitud !== 'number') {
      sinUbicacion++
      continue
    }
    rutas.push({
      empresa: tipoNueva === 'empresa' ? nueva.codigo : o.codigo,
      planta: tipoNueva === 'planta' ? nueva.codigo : o.codigo,
      tarifa_km_ton: tarifa,
    })
  }
  return { rutas, sinUbicacion }
}
