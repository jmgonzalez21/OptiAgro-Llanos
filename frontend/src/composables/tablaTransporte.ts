/** Lógica pura de la tabla de transporte: totales, equilibrio oferta/capacidad y plan de asignación por celda. */
import type { Asignacion } from '@/types/fase2'

const EPS = 1e-6

export interface Equilibrio {
  alcanza: boolean
  /** Toneladas de capacidad que sobran (si alcanza) o que faltan (si no). */
  diferencia: number
}

export const sumar = (valores: Array<number | null | undefined>): number => valores.reduce<number>((s, v) => s + (typeof v === 'number' && Number.isFinite(v) ? v : 0), 0)

/** La red alcanza si la capacidad total cubre toda la oferta (la oferta se recibe completa). */
export function equilibrio(oferta: number, capacidad: number): Equilibrio {
  const d = capacidad - oferta
  return d >= -EPS ? { alcanza: true, diferencia: Math.max(0, d) } : { alcanza: false, diferencia: -d }
}

export interface PlanTabla {
  /** toneladas[i][j] para empresas[i] y plantas[j]. */
  toneladas: number[][]
  porEmpresa: number[]
  porPlanta: number[]
  costoTotal: number
}

/** Ordena las asignaciones del optimizador en las filas/columnas de la matriz (por código). */
export function planPorCeldas(empresas: string[], plantas: string[], asignaciones: Asignacion[]): PlanTabla {
  const fila = new Map(empresas.map((c, i) => [c, i]))
  const col = new Map(plantas.map((c, j) => [c, j]))
  const toneladas = empresas.map(() => plantas.map(() => 0))
  let costoTotal = 0
  for (const a of asignaciones) {
    const i = fila.get(a.empresa_id)
    const j = col.get(a.planta_id)
    if (i === undefined || j === undefined) continue
    ;(toneladas[i] as number[])[j] = ((toneladas[i] as number[])[j] ?? 0) + a.cantidad
    costoTotal += a.cantidad * a.costo_unitario
  }
  return {
    toneladas,
    porEmpresa: toneladas.map((f) => sumar(f)),
    porPlanta: plantas.map((_, j) => sumar(toneladas.map((f) => f[j]))),
    costoTotal,
  }
}

/** ¿El valor coincide con la meta (tolerancia de redondeo)? */
export const coincide = (a: number, b: number): boolean => Math.abs(a - b) <= 1e-4 * Math.max(1, Math.abs(b))
export const llena = (usado: number, capacidad: number): boolean => capacidad > 0 && usado >= capacidad - 1e-4 * Math.max(1, capacidad)
