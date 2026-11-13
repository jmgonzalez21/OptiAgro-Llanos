/**
 * Exportación CSV pensada para Excel es-CO (docs/ux/fase-2 §9.3, D12): UTF-8 con BOM,
 * separador `;`, decimales con coma, encabezados con unidades, saltos CRLF.
 */
export type CeldaCsv = string | number | boolean | null | undefined

export interface OpcionesCsv {
  separador?: string
  bom?: boolean
}

function celda(valor: CeldaCsv, separador: string): string {
  if (valor === null || valor === undefined) return ''
  if (typeof valor === 'number') {
    if (!Number.isFinite(valor)) return ''
    return String(valor).replace('.', ',')
  }
  const texto = typeof valor === 'boolean' ? (valor ? 'Sí' : 'No') : valor
  // Evita inyección de fórmulas al abrir en Excel (=, +, -, @ al inicio de texto).
  const seguro = /^[=+\-@\t\r]/.test(texto) && !/^-?\d+([.,]\d+)?$/.test(texto) ? `'${texto}` : texto
  return /["\n\r]/.test(seguro) || seguro.includes(separador) ? `"${seguro.replace(/"/g, '""')}"` : seguro
}

export function generarCsv(
  encabezados: readonly string[],
  filas: ReadonlyArray<readonly CeldaCsv[]>,
  opciones: OpcionesCsv = {},
): string {
  const sep = opciones.separador ?? ';'
  const lineas = [encabezados.map((h) => celda(h, sep)).join(sep), ...filas.map((f) => f.map((c) => celda(c, sep)).join(sep))]
  return `${opciones.bom === false ? '' : '﻿'}${lineas.join('\r\n')}\r\n`
}

/** `optiagro-reporte-2026-11-12-1435.csv` */
export function nombreArchivoCsv(prefijo: string, fecha: Date = new Date()): string {
  const p = (n: number): string => String(n).padStart(2, '0')
  return `optiagro-${prefijo}-${fecha.getFullYear()}-${p(fecha.getMonth() + 1)}-${p(fecha.getDate())}-${p(fecha.getHours())}${p(fecha.getMinutes())}.csv`
}

/** Dispara la descarga en el navegador. */
export function descargarArchivo(contenido: string, nombre: string, tipo = 'text/csv;charset=utf-8'): void {
  const blob = new Blob([contenido], { type: tipo })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = nombre
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
