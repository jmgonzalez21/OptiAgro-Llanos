/**
 * Utilidades de escala para los gráficos SVG propios (sin dependencias).
 * Puras y probadas: `escalas.test.ts`.
 */
export interface Escala {
  (valor: number): number
  readonly tipo: 'lineal' | 'log'
  readonly dominio: readonly [number, number]
  readonly rango: readonly [number, number]
  /** Valor del dominio para una posición del rango. */
  invertir: (posicion: number) => number
}

export function escalaLineal(dominio: readonly [number, number], rango: readonly [number, number]): Escala {
  const [d0, d1] = dominio
  const [r0, r1] = rango
  const ancho = d1 - d0 || 1
  return Object.assign((v: number) => r0 + ((v - d0) / ancho) * (r1 - r0), {
    tipo: 'lineal' as const,
    dominio,
    rango,
    invertir: (p: number) => d0 + ((p - r0) / (r1 - r0 || 1)) * ancho,
  })
}

/** Escala logarítmica (base 10). El dominio debe ser > 0. */
export function escalaLog(dominio: readonly [number, number], rango: readonly [number, number]): Escala {
  const d0 = Math.log10(Math.max(dominio[0], Number.MIN_VALUE))
  const d1 = Math.log10(Math.max(dominio[1], Number.MIN_VALUE))
  const [r0, r1] = rango
  const ancho = d1 - d0 || 1
  return Object.assign(
    (v: number) => r0 + ((Math.log10(Math.max(v, Number.MIN_VALUE)) - d0) / ancho) * (r1 - r0),
    {
      tipo: 'log' as const,
      dominio,
      rango,
      invertir: (p: number) => 10 ** (d0 + ((p - r0) / (r1 - r0 || 1)) * ancho),
    },
  )
}

/** Paso "bonito" (1, 2, 5 × 10^k) para ~`objetivo` divisiones. */
export function pasoAmigable(rango: number, objetivo = 5): number {
  if (!(rango > 0)) return 1
  const bruto = rango / Math.max(1, objetivo)
  const exp = Math.floor(Math.log10(bruto))
  const f = bruto / 10 ** exp
  const base = f < 1.5 ? 1 : f < 3.5 ? 2 : f < 7.5 ? 5 : 10
  return base * 10 ** exp
}

function redondear(v: number, paso: number): number {
  const decimales = Math.max(0, -Math.floor(Math.log10(paso)) + 2)
  return Number(v.toFixed(Math.min(decimales, 12)))
}

/** Marcas lineales dentro de [min, max] (ambos incluidos si caen en la cuadrícula). */
export function ticksLineales(min: number, max: number, objetivo = 5): number[] {
  if (!(max > min)) return [min]
  const paso = pasoAmigable(max - min, objetivo)
  const inicio = Math.ceil(min / paso - 1e-9) * paso
  const ticks: number[] = []
  for (let v = inicio; v <= max + paso * 1e-9; v += paso) ticks.push(redondear(v, paso))
  return ticks
}

/** Marcas logarítmicas: potencias de 10 y, si hay pocas, también 2 y 5. */
export function ticksLog(min: number, max: number): number[] {
  const lo = Math.floor(Math.log10(Math.max(min, Number.MIN_VALUE)))
  const hi = Math.ceil(Math.log10(Math.max(max, Number.MIN_VALUE)))
  const potencias: number[] = []
  for (let e = lo; e <= hi; e++) potencias.push(10 ** e)
  if (potencias.length >= 4) return potencias
  const ticks: number[] = []
  for (let e = lo; e <= hi; e++) {
    for (const m of [1, 2, 5]) {
      const v = m * 10 ** e
      if (v >= min * 0.999 && v <= max * 1.001) ticks.push(v)
    }
  }
  return ticks.length >= 2 ? ticks : potencias
}

/**
 * Dominio con margen que abarca `valores`. `incluirCero` fuerza el cero (barras);
 * en líneas no se fuerza para no aplastar la variación (se rotula el eje).
 */
export function dominioLineal(
  valores: readonly number[],
  opciones: { incluirCero?: boolean; margen?: number; objetivo?: number } = {},
): [number, number] {
  const finitos = valores.filter((v) => Number.isFinite(v))
  if (finitos.length === 0) return [0, 1]
  let min = Math.min(...finitos)
  let max = Math.max(...finitos)
  if (opciones.incluirCero) {
    min = Math.min(min, 0)
    max = Math.max(max, 0)
  }
  if (min === max) {
    const d = Math.abs(min) * 0.1 || 1
    min -= d
    max += d
  } else if (!opciones.incluirCero) {
    const m = (max - min) * (opciones.margen ?? 0.08)
    min -= m
    max += m
  }
  const paso = pasoAmigable(max - min, opciones.objetivo ?? 5)
  let lo = Math.floor(min / paso + 1e-9) * paso
  const hi = Math.ceil(max / paso - 1e-9) * paso
  if (min >= 0 && lo < 0) lo = 0
  return [redondear(lo, paso), redondear(hi, paso)]
}

/** Dominio logarítmico (potencias de 10 que abarcan los valores positivos). */
export function dominioLog(valores: readonly number[]): [number, number] {
  const pos = valores.filter((v) => v > 0 && Number.isFinite(v))
  if (pos.length === 0) return [1, 10]
  const lo = 10 ** Math.floor(Math.log10(Math.min(...pos)))
  const hi = 10 ** Math.ceil(Math.log10(Math.max(...pos)))
  return lo === hi ? [lo, lo * 10] : [lo, hi]
}

export interface Banda {
  inicio: number
  ancho: number
}

/** Reparte `n` bandas iguales en [0, total] con relleno proporcional entre ellas. */
export function bandas(n: number, total: number, relleno = 0.25): Banda[] {
  if (n <= 0) return []
  const paso = total / n
  const ancho = paso * (1 - relleno)
  return Array.from({ length: n }, (_, i) => ({ inicio: i * paso + (paso - ancho) / 2, ancho }))
}

// ---------------------------------------------------------------------------------------------
// Barras de rango (UiRangeBars): rango [mínimo, máximo] con extremos posiblemente infinitos.
// ---------------------------------------------------------------------------------------------
export interface MarcaRango {
  valor: number
  etiqueta: string
}

export interface EntradaRango {
  actual: number
  /** null o -Infinity = sin límite inferior. */
  minimo: number | null
  /** null o +Infinity = sin límite superior. */
  maximo: number | null
  marcas?: readonly MarcaRango[]
  ejeMin?: number
  ejeMax?: number
}

export interface GeometriaRango {
  dominio: [number, number]
  /** Fracción 0–1 del segmento verde (rango en el que el plan óptimo se mantiene). */
  desde: number
  hasta: number
  actual: number
  abiertoIzq: boolean
  abiertoDer: boolean
  marcas: Array<MarcaRango & { pos: number; dentro: boolean }>
  /** Fracción de un valor cualquiera dentro del dominio (recortada a 0–1). */
  posicion: (valor: number) => number
}

export function calcularRango(e: EntradaRango): GeometriaRango {
  const min = e.minimo !== null && Number.isFinite(e.minimo) ? e.minimo : null
  const max = e.maximo !== null && Number.isFinite(e.maximo) ? e.maximo : null
  const marcas = e.marcas ?? []
  const finitos = [e.actual, ...(min !== null ? [min] : []), ...(max !== null ? [max] : []), ...marcas.map((m) => m.valor)]
  const lo = Math.min(...finitos)
  const hi = Math.max(...finitos)
  const span = hi - lo || Math.abs(e.actual) * 0.2 || 1
  const pad = span * 0.18
  const noNegativo = finitos.every((v) => v >= 0)
  let d0 = e.ejeMin ?? lo - pad
  const d1 = e.ejeMax ?? hi + pad
  if (e.ejeMin === undefined && noNegativo && d0 < 0) d0 = 0
  const dominio: [number, number] = [d0, d1 > d0 ? d1 : d0 + 1]
  const ancho = dominio[1] - dominio[0]
  const posicion = (v: number): number => Math.min(1, Math.max(0, (v - dominio[0]) / ancho))
  return {
    dominio,
    desde: min === null ? 0 : posicion(min),
    hasta: max === null ? 1 : posicion(max),
    actual: posicion(e.actual),
    abiertoIzq: min === null,
    abiertoDer: max === null,
    marcas: marcas.map((m) => ({
      ...m,
      pos: posicion(m.valor),
      dentro: (min === null || m.valor >= min) && (max === null || m.valor <= max),
    })),
    posicion,
  }
}
