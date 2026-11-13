/**
 * Formato y lectura de números en es-CO (docs/ux/fase-2 §4.2).
 * Miles con punto, decimales con coma, signo menos U+2212 en variaciones, % con espacio fino.
 */
export const MENOS = '−'
export const ESPACIO_FINO = '\u202F'

const cacheFormatos = new Map<string, Intl.NumberFormat>()

function formateador(min: number, max: number): Intl.NumberFormat {
  const clave = `${min}-${max}`
  let f = cacheFormatos.get(clave)
  if (!f) {
    f = new Intl.NumberFormat('es-CO', {
      minimumFractionDigits: min,
      maximumFractionDigits: max,
      useGrouping: true,
    })
    cacheFormatos.set(clave, f)
  }
  return f
}

export interface OpcionesNumero {
  /** Decimales fijos (min = max). */
  decimales?: number
  /** Máximo de decimales (los ceros sobrantes se omiten). Por defecto 2. */
  maxDecimales?: number
}

/** `1234567.5` -> `1.234.567,5`. Devuelve `—` para null/undefined/NaN. */
export function formatearNumero(valor: number | null | undefined, opciones: OpcionesNumero = {}): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return '—'
  const min = opciones.decimales ?? 0
  const max = opciones.decimales ?? opciones.maxDecimales ?? 2
  const texto = formateador(min, Math.max(min, max)).format(Math.abs(valor))
  const esCero = Number(texto.replace(/\./g, '').replace(',', '.')) === 0
  return valor < 0 && !esCero ? `${MENOS}${texto}` : texto
}

/** Con signo explícito: `+4,2` / `−3,0` / `0`. */
export function formatearConSigno(valor: number | null | undefined, opciones: OpcionesNumero = {}): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return '—'
  const texto = formatearNumero(Math.abs(valor), opciones)
  const esCero = Number(texto.replace(/\./g, '').replace(',', '.')) === 0
  if (esCero) return texto
  return `${valor > 0 ? '+' : MENOS}${texto}`
}

/** `4,2 %` (espacio fino). `conSigno` para variaciones. */
export function formatearPorcentaje(
  valor: number | null | undefined,
  opciones: OpcionesNumero & { conSigno?: boolean } = {},
): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return '—'
  const { conSigno, ...resto } = opciones
  const n = conSigno ? formatearConSigno(valor, { maxDecimales: 1, ...resto }) : formatearNumero(valor, { maxDecimales: 1, ...resto })
  return `${n}${ESPACIO_FINO}%`
}

/** `$ 1.234.567` (sin la sigla COP: la unidad va en el encabezado o junto al valor). */
export function formatearMoneda(valor: number | null | undefined, opciones: OpcionesNumero = {}): string {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) return '—'
  return `$\u00A0${formatearNumero(valor, { maxDecimales: 0, ...opciones })}`
}

/** `< 1 ms`, `12 ms`, `1,4 s`, `1 min 12 s`. */
export function formatearDuracion(ms: number | null | undefined): string {
  if (ms === null || ms === undefined || !Number.isFinite(ms)) return '—'
  if (ms < 1) return '< 1 ms'
  if (ms < 1000) return `${Math.round(ms)} ms`
  const s = ms / 1000
  if (s < 60) return `${formatearNumero(s, { maxDecimales: 1 })} s`
  const min = Math.floor(s / 60)
  const resto = Math.round(s - min * 60)
  return resto === 0 ? `${min} min` : `${min} min ${resto} s`
}

/** Cifra compacta para ejes de gráficos: `1,2 M`, `350 k`. La cifra exacta va en tooltip/tabla. */
export function formatearCompacto(valor: number): string {
  const abs = Math.abs(valor)
  const signo = valor < 0 ? MENOS : ''
  if (abs >= 1e9) return `${signo}${formatearNumero(abs / 1e9, { maxDecimales: 1 })}${ESPACIO_FINO}MM`
  if (abs >= 1e6) return `${signo}${formatearNumero(abs / 1e6, { maxDecimales: 1 })}${ESPACIO_FINO}M`
  if (abs >= 1e4) return `${signo}${formatearNumero(abs / 1e3, { maxDecimales: 1 })}${ESPACIO_FINO}k`
  return formatearNumero(valor, { maxDecimales: abs < 10 ? 2 : 1 })
}

export type ResultadoLectura = { ok: true; valor: number | null } | { ok: false; error: string }

/**
 * Lee un número escrito a la colombiana.
 * Acepta `12500`, `12.500`, `12.500,5`, `12,5`, `-3`, `−3`. Vacío -> `{ ok: true, valor: null }`.
 * Rechaza `1.5` (punto decimal): "Usa coma para decimales, por ejemplo 1,5."
 */
export function leerNumero(texto: string): ResultadoLectura {
  let t = texto.trim().replace(/\s+/g, '').replace(/−/g, '-')
  if (t === '') return { ok: true, valor: null }
  let negativo = false
  if (t.startsWith('-')) {
    negativo = true
    t = t.slice(1)
  } else if (t.startsWith('+')) {
    t = t.slice(1)
  }
  const mensajeGeneral = 'Escribe un número, por ejemplo 120 o 1.250,5.'
  if (!/^[\d.,]+$/.test(t)) return { ok: false, error: mensajeGeneral }

  const comas = (t.match(/,/g) ?? []).length
  if (comas > 1) return { ok: false, error: mensajeGeneral }

  let entera: string
  let decimal = ''
  if (comas === 1) {
    const partes = t.split(',') as [string, string]
    entera = partes[0]
    decimal = partes[1]
    if (decimal === '' || !/^\d+$/.test(decimal)) return { ok: false, error: mensajeGeneral }
    if (entera.includes('.') && !/^\d{1,3}(\.\d{3})+$/.test(entera)) return { ok: false, error: mensajeGeneral }
    if (entera === '') return { ok: false, error: mensajeGeneral }
  } else if (t.includes('.')) {
    // Sin coma: el punto solo es válido como separador de miles (grupos de 3).
    if (!/^\d{1,3}(\.\d{3})+$/.test(t)) {
      return { ok: false, error: 'Usa coma para decimales, por ejemplo 1,5.' }
    }
    entera = t
  } else {
    entera = t
  }
  const numero = Number(`${entera.replace(/\./g, '')}${decimal ? `.${decimal}` : ''}`)
  if (!Number.isFinite(numero)) return { ok: false, error: mensajeGeneral }
  return { ok: true, valor: negativo ? -numero : numero }
}
