/** Escenarios predefinidos de «¿Qué pasa si…?» y su traducción a frases de negocio. */
import { formatearMoneda, formatearNumero } from '@/components/ui/formato'
import type { EscenarioSensibilidad, Variacion } from '@/types/fase2'

export interface PresetEscenario {
  id: string
  titulo: string
  descripcion: string
  /** Variación que se envía a la API; `planta` solo aplica si `necesitaPlanta`. */
  variacion: (planta: string) => Variacion
  necesitaPlanta?: boolean
}

export const PRESETS: PresetEscenario[] = [
  { id: 'comb10', titulo: 'Combustible +10 %', descripcion: 'El transporte se encarece un 10 %.', variacion: () => ({ tipo: 'combustible', ids: [], porcentajes: [10] }) },
  { id: 'comb20', titulo: 'Combustible +20 %', descripcion: 'El transporte se encarece un 20 %.', variacion: () => ({ tipo: 'combustible', ids: [], porcentajes: [20] }) },
  { id: 'oferta-10', titulo: 'Oferta −10 %', descripcion: 'Las empresas generan 10 % menos residuos.', variacion: () => ({ tipo: 'oferta', ids: [], porcentajes: [-10] }) },
  { id: 'oferta+15', titulo: 'Oferta +15 %', descripcion: 'Las empresas generan 15 % más residuos.', variacion: () => ({ tipo: 'oferta', ids: [], porcentajes: [15] }) },
  {
    id: 'planta-30',
    titulo: 'Una planta pierde 30 % de capacidad',
    descripcion: 'Por una avería o mantenimiento, una planta recibe menos.',
    necesitaPlanta: true,
    variacion: (planta) => ({ tipo: 'capacidad', ids: planta ? [planta] : [], porcentajes: [-30] }),
  },
]

export type Nombres = { empresas: Map<string, string>; plantas: Map<string, string> }

const pct = (n: number): string => `${formatearNumero(Math.abs(n), { maxDecimales: 1 })} %`
const sube = (n: number): string => (n >= 0 ? 'sube' : 'baja')

function lista(ids: string[], mapa: Map<string, string>): string {
  const nombres = ids.map((i) => mapa.get(i) ?? i)
  if (nombres.length <= 1) return nombres.join('')
  return `${nombres.slice(0, -1).join(', ')} y ${nombres[nombres.length - 1]}`
}

/** «el combustible sube 10 %», «la capacidad de Granada baja 30 %»… */
export function condicion(e: Pick<EscenarioSensibilidad, 'tipo' | 'ids' | 'porcentaje'>, n: Nombres): string {
  const p = e.porcentaje
  switch (e.tipo) {
    case 'combustible':
      return e.ids.length ? `el combustible ${sube(p)} ${pct(p)} en ${e.ids.length === 1 ? 'una ruta' : `${e.ids.length} rutas`}` : `el combustible ${sube(p)} ${pct(p)}`
    case 'oferta':
      return e.ids.length ? `la oferta de ${lista(e.ids, n.empresas)} ${sube(p)} ${pct(p)}` : `la oferta de residuos ${sube(p)} ${pct(p)}`
    case 'capacidad':
      return e.ids.length ? `la capacidad de ${lista(e.ids, n.plantas)} ${sube(p)} ${pct(p)}` : `la capacidad de todas las plantas ${sube(p)} ${pct(p)}`
    default:
      return e.ids.length ? `el costo de ${e.ids.length === 1 ? 'una ruta' : `${e.ids.length} rutas`} ${sube(p)} ${pct(p)}` : `el costo de todas las rutas ${sube(p)} ${pct(p)}`
  }
}

export const esFactible = (e: EscenarioSensibilidad): boolean => e.estado_exacto === 'OPTIMAL' && e.costo_exacto !== null

/** Texto del cambio de plan a partir de `base_cambio` y los envíos que cambian. */
export function textoPlan(e: EscenarioSensibilidad): string {
  if (e.base_cambio === null) return '—'
  if (!e.base_cambio) return 'El plan se mantiene'
  return e.asignaciones_cambiadas <= 2 ? 'El plan cambia un poco' : 'El plan cambia'
}

/** Frase completa para la lista de escenarios. */
export function frase(e: EscenarioSensibilidad, n: Nombres): string {
  const cond = condicion(e, n)
  if (!esFactible(e)) return `Si ${cond}, las plantas no alcanzan a recibir toda la oferta.`
  const v = e.variacion_objetivo_pct ?? 0
  const dif = e.variacion_objetivo ?? 0
  const costo = Math.abs(v) < 0.05 ? 'el costo casi no cambia' : `el costo ${v > 0 ? 'sube' : 'baja'} ${pct(v)} (${dif >= 0 ? '+' : '−'}${formatearMoneda(Math.abs(dif))})`
  return `Si ${cond}, ${costo}; ${textoPlan(e).toLowerCase()}.`
}

export type Semaforo = 'verde' | 'ambar' | 'rojo'

/** Impacto del escenario: rojo si no hay solución o el costo cambia ≥ 10 %; ámbar entre 3 % y 10 % o si el plan cambia mucho. */
export function semaforo(e: EscenarioSensibilidad): Semaforo {
  if (!esFactible(e)) return 'rojo'
  const v = Math.abs(e.variacion_objetivo_pct ?? 0)
  if (v >= 10) return 'rojo'
  if (v >= 3 || (e.base_cambio === true && e.asignaciones_cambiadas > 2)) return 'ambar'
  return 'verde'
}

export const ETIQUETA_SEMAFORO: Record<Semaforo, string> = { verde: 'Impacto bajo', ambar: 'Impacto medio', rojo: 'Impacto alto' }

/** Texto del margen de seguridad de una restricción (null = sin límite). */
export function textoMargen(min: number | null, max: number | null): string {
  const f = (v: number): string => `${formatearNumero(v, { maxDecimales: 1 })} t`
  if (min !== null && max !== null) return `puede variar entre ${f(min)} y ${f(max)} sin cambiar el plan`
  if (min === null && max !== null) return `puede variar hasta ${f(max)} sin cambiar el plan (sin límite hacia abajo)`
  if (min !== null) return `puede variar desde ${f(min)} hacia arriba sin cambiar el plan (sin límite)`
  return 'puede tomar cualquier valor sin cambiar el plan (sin límite)'
}

/** Veredicto del reporte: etiqueta según el gap del algoritmo genético. */
export function etiquetaGap(gap: number | null): { texto: 'Excelente' | 'Aceptable' | 'Mejorable'; tono: 'verde' | 'ambar' | 'error' } | null {
  if (gap === null || !Number.isFinite(gap)) return null
  if (gap <= 1) return { texto: 'Excelente', tono: 'verde' }
  if (gap <= 5) return { texto: 'Aceptable', tono: 'ambar' }
  return { texto: 'Mejorable', tono: 'error' }
}
