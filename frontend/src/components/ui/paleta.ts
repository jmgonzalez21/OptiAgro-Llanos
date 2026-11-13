/**
 * Estilo de series para los gráficos: color (token), forma de marcador, trazo y patrón.
 * El color nunca es el único canal: forma + trazo/patrón + rótulo directo (WCAG 1.4.1).
 */
export type FormaMarcador = 'circulo' | 'rombo' | 'cuadrado' | 'triangulo' | 'triangulo-inv' | 'cruz'

export interface EstiloSerie {
  /** Valor CSS: `var(--grafico-cat-N)`. */
  color: string
  marcador: FormaMarcador
  /** `stroke-dasharray` ('' = continuo). */
  trazo: string
  /** Índice de patrón de relleno (0 = sólido) para barras. */
  patron: number
  /** Nombre del color para describirlo en texto, p. ej. en la leyenda. */
  nombreColor: string
}

const ESTILOS: readonly EstiloSerie[] = [
  { color: 'var(--grafico-cat-1)', marcador: 'circulo', trazo: '', patron: 0, nombreColor: 'verde' },
  { color: 'var(--grafico-cat-2)', marcador: 'rombo', trazo: '7 4', patron: 1, nombreColor: 'azul' },
  { color: 'var(--grafico-cat-3)', marcador: 'cuadrado', trazo: '2 3', patron: 2, nombreColor: 'naranja' },
  { color: 'var(--grafico-cat-4)', marcador: 'triangulo', trazo: '10 3 2 3', patron: 3, nombreColor: 'violeta' },
  { color: 'var(--grafico-cat-5)', marcador: 'triangulo-inv', trazo: '1 4', patron: 4, nombreColor: 'rosa' },
  { color: 'var(--grafico-cat-6)', marcador: 'cruz', trazo: '14 4', patron: 5, nombreColor: 'turquesa' },
]

/** Estilo de la serie `i` (cicla; con más de 6 series se repite y el rótulo directo desambigua). */
export function estiloSerie(i: number): EstiloSerie {
  return ESTILOS[((i % ESTILOS.length) + ESTILOS.length) % ESTILOS.length]!
}

export const SERIE_EXACTO = 0
export const SERIE_AG = 1
export const MAX_SERIES = ESTILOS.length

/** Ruta SVG (`d`) de un marcador centrado en (cx, cy) con radio r. */
export function rutaMarcador(forma: FormaMarcador, cx: number, cy: number, r: number): string {
  switch (forma) {
    case 'circulo':
      return `M${cx - r} ${cy}a${r} ${r} 0 1 0 ${r * 2} 0a${r} ${r} 0 1 0 ${-r * 2} 0Z`
    case 'rombo':
      return `M${cx} ${cy - r * 1.25}L${cx + r * 1.25} ${cy}L${cx} ${cy + r * 1.25}L${cx - r * 1.25} ${cy}Z`
    case 'cuadrado':
      return `M${cx - r} ${cy - r}h${r * 2}v${r * 2}h${-r * 2}Z`
    case 'triangulo':
      return `M${cx} ${cy - r * 1.2}L${cx + r * 1.15} ${cy + r * 0.9}L${cx - r * 1.15} ${cy + r * 0.9}Z`
    case 'triangulo-inv':
      return `M${cx} ${cy + r * 1.2}L${cx + r * 1.15} ${cy - r * 0.9}L${cx - r * 1.15} ${cy - r * 0.9}Z`
    case 'cruz':
      return `M${cx - r} ${cy - r}L${cx + r} ${cy + r}M${cx + r} ${cy - r}L${cx - r} ${cy + r}`
  }
}

/** La cruz es solo trazo; el resto son formas rellenas. */
export function marcadorRelleno(forma: FormaMarcador): boolean {
  return forma !== 'cruz'
}
