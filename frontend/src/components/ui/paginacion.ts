/**
 * Páginas a mostrar con elipsis: siempre primera y última, la actual y 1 vecina a cada lado.
 * `null` = elipsis. Ej.: actual 6 de 12 -> [1, null, 5, 6, 7, null, 12].
 */
export function paginasVisibles(actual: number, total: number): Array<number | null> {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const set = new Set<number>([1, total, actual, actual - 1, actual + 1])
  if (actual <= 3) [2, 3, 4].forEach((n) => set.add(n))
  if (actual >= total - 2) [total - 1, total - 2, total - 3].forEach((n) => set.add(n))
  const orden = [...set].filter((n) => n >= 1 && n <= total).sort((a, b) => a - b)
  const salida: Array<number | null> = []
  orden.forEach((n, i) => {
    const previo = orden[i - 1]
    if (previo !== undefined && n - previo > 1) salida.push(n - previo === 2 ? n - 1 : null)
    salida.push(n)
  })
  return salida
}
