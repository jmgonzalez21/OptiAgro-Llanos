/** Lógica pura de UiDataTable: orden, búsqueda y paginación en cliente. Probada en `tabla.test.ts`. */
export type Direccion = 'asc' | 'desc'

export interface Orden {
  clave: string
  direccion: Direccion
}

export type ValorCelda = string | number | boolean | null | undefined

const colador = new Intl.Collator('es-CO', { numeric: true, sensitivity: 'base' })

/** Minúsculas y sin tildes: "Acacías" coincide con "acacias". */
export function normalizarTexto(v: ValorCelda): string {
  if (v === null || v === undefined) return ''
  return String(v)
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

/** Compara dos valores: números por valor, texto con collation es-CO (naturales), vacíos siempre al final. */
export function compararValores(a: ValorCelda, b: ValorCelda, direccion: Direccion): number {
  const vacioA = a === null || a === undefined || a === ''
  const vacioB = b === null || b === undefined || b === ''
  if (vacioA || vacioB) return vacioA === vacioB ? 0 : vacioA ? 1 : -1
  let r: number
  if (typeof a === 'number' && typeof b === 'number') r = a - b
  else if (typeof a === 'boolean' && typeof b === 'boolean') r = Number(a) - Number(b)
  else r = colador.compare(String(a), String(b))
  return direccion === 'asc' ? r : -r
}

/** Orden estable (no muta la entrada). */
export function ordenarFilas<T>(filas: readonly T[], valor: (fila: T) => ValorCelda, direccion: Direccion): T[] {
  return filas
    .map((fila, i) => ({ fila, i }))
    .sort((x, y) => compararValores(valor(x.fila), valor(y.fila), direccion) || x.i - y.i)
    .map((x) => x.fila)
}

/** Filtra por texto en cualquiera de las columnas (todas las palabras deben aparecer). */
export function filtrarFilas<T>(filas: readonly T[], consulta: string, textos: (fila: T) => ValorCelda[]): T[] {
  const palabras = normalizarTexto(consulta).split(/\s+/).filter(Boolean)
  if (palabras.length === 0) return [...filas]
  return filas.filter((fila) => {
    const pajar = textos(fila).map(normalizarTexto).join(' ')
    return palabras.every((p) => pajar.includes(p))
  })
}

export function paginar<T>(filas: readonly T[], pagina: number, tamano: number): T[] {
  const inicio = (Math.max(1, pagina) - 1) * tamano
  return filas.slice(inicio, inicio + tamano)
}
