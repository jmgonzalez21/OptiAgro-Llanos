/** Escenarios de sensibilidad como texto de formulario y su conversión al cuerpo de la API. */
import type { Variacion } from '@/types/fase2'

export interface FilaVariacion {
  tipo: Variacion['tipo']
  /** Códigos separados por coma; vacío = todos. */
  ids: string
  /** Porcentajes separados por espacios o `;` (ej. `-10 10 20`). */
  porcentajes: string
}

export const TIPOS_VARIACION: Array<{ valor: Variacion['tipo']; etiqueta: string; ayuda: string }> = [
  { valor: 'combustible', etiqueta: 'El combustible / transporte', ayuda: 'Códigos de ruta, ej. E1->P2 (vacío = todas las rutas)' },
  { valor: 'oferta', etiqueta: 'Los residuos que generan las empresas', ayuda: 'Códigos de empresa, ej. E1, E2 (vacío = todas)' },
  { valor: 'capacidad', etiqueta: 'Lo que pueden recibir las plantas', ayuda: 'Códigos de planta, ej. P1, P2 (vacío = todas)' },
  { valor: 'costo', etiqueta: 'El costo de rutas puntuales', ayuda: 'Códigos de ruta, ej. E1->P2 (vacío = todas las rutas)' },
]

export function filaVariacionNueva(tipo: Variacion['tipo'] = 'combustible', porcentajes = '-10 10 20'): FilaVariacion {
  return { tipo, ids: '', porcentajes }
}

export function leerPorcentajes(texto: string): number[] {
  return texto
    .split(/[\s;]+/)
    .map((t) => t.replace(/,$/, '').replace(',', '.'))
    .filter((t) => t !== '')
    .map(Number)
    .filter((n) => Number.isFinite(n))
}

export function aVariaciones(filas: FilaVariacion[]): Variacion[] {
  return filas
    .map((f) => ({
      tipo: f.tipo,
      ids: f.ids
        .split(/[,;\s]+/)
        .map((i) => i.trim())
        .filter(Boolean),
      porcentajes: leerPorcentajes(f.porcentajes),
    }))
    .filter((v) => v.porcentajes.length > 0)
}
