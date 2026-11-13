/** Puntos de un `<polyline>` SVG para una serie, escalada a un área ancho x alto con margen. */
export function puntosPolyline(
  valores: readonly number[],
  ancho: number,
  alto: number,
  margen = 8,
  rango?: { min: number; max: number },
): string {
  if (valores.length === 0) return ''
  const min = rango?.min ?? Math.min(...valores)
  const max = rango?.max ?? Math.max(...valores)
  const span = max - min || 1
  const util = { x: ancho - margen * 2, y: alto - margen * 2 }
  return valores
    .map((v, i) => {
      const x = margen + (valores.length === 1 ? util.x / 2 : (i / (valores.length - 1)) * util.x)
      const y = margen + (1 - (v - min) / span) * util.y
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

/** Convierte una serie desconocida (de `metricas`) en números válidos. */
export function serieNumerica(valor: unknown): number[] {
  return Array.isArray(valor) ? valor.filter((v): v is number => typeof v === 'number' && Number.isFinite(v)) : []
}
