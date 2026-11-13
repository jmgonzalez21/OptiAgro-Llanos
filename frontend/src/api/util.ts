/** Utilidades de acceso a la API para las vistas: peticiones, listas paginadas y errores por campo. */
import { obtenerApi } from '@/api'
import { ErrorValidacion, mensajeDeError } from '@/api/errores'
import type { OpcionesSolicitud } from '@/api/http'
import type { Pagina } from '@/types/api'

/** Tiempo máximo para los cálculos largos (AG, sensibilidad, escalabilidad). */
export const TIMEOUT_CALCULO_MS = 300_000

export function solicitar<T>(ruta: string, opciones?: OpcionesSolicitud): Promise<T> {
  return obtenerApi().solicitar<T>(ruta, opciones)
}

/** Pide todas las páginas de un listado paginado. */
export async function listarTodo<T>(ruta: string, consulta: Record<string, string | number | boolean | undefined> = {}): Promise<T[]> {
  const todo: T[] = []
  for (let pagina = 1; pagina <= 50; pagina++) {
    const datos = await solicitar<Pagina<T> | T[]>(ruta, { consulta: { ...consulta, page: pagina, page_size: 200 } })
    if (Array.isArray(datos)) return datos
    todo.push(...datos.results)
    if (!datos.next) break
  }
  return todo
}

export interface ErroresFormulario {
  /** Mensaje por nombre de campo. */
  campos: Record<string, string>
  /** Mensaje general (no asociado a un campo). */
  general: string
}

function aTexto(valor: unknown): string {
  if (typeof valor === 'string') return valor
  if (Array.isArray(valor)) return valor.map(aTexto).filter(Boolean).join(' ')
  if (valor && typeof valor === 'object') {
    return Object.entries(valor as Record<string, unknown>)
      .map(([k, v]) => `${k}: ${aTexto(v)}`)
      .join(' ')
  }
  return valor === null || valor === undefined ? '' : String(valor)
}

/** Convierte un error de la API en mensajes por campo (400) o un mensaje general. */
export function leerErrores(error: unknown): ErroresFormulario {
  if (error instanceof ErrorValidacion) {
    const crudo = error.errores
    if (crudo && typeof crudo === 'object' && !Array.isArray(crudo)) {
      const campos: Record<string, string> = {}
      let general = ''
      for (const [clave, valor] of Object.entries(crudo as Record<string, unknown>)) {
        if (clave === 'non_field_errors' || clave === 'detail') general = `${general} ${aTexto(valor)}`.trim()
        else campos[clave] = aTexto(valor)
      }
      return { campos, general: general || (Object.keys(campos).length ? '' : error.message) }
    }
    return { campos: {}, general: aTexto(crudo) || error.message }
  }
  return { campos: {}, general: mensajeDeError(error) }
}

/** Texto único con el error (campos + general) para alertas de página. */
export function textoDeError(error: unknown): string {
  const { campos, general } = leerErrores(error)
  const partes = Object.entries(campos).map(([k, v]) => `${k}: ${v}`)
  return [general, ...partes].filter(Boolean).join(' · ')
}
