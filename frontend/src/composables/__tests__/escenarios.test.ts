import { describe, expect, it } from 'vitest'
import { etiquetaGap, frase, semaforo, textoMargen, type Nombres } from '../escenarios'
import type { EscenarioSensibilidad } from '@/types/fase2'

const nombres: Nombres = { empresas: new Map(), plantas: new Map([['P3', 'Granada']]) }
const base: EscenarioSensibilidad = {
  nombre: 'x', tipo: 'combustible', ids: [], porcentaje: 10, variacion_objetivo: 184651, variacion_objetivo_pct: 9, gap_pct: null,
  base_cambio: false, dentro_de_rango: null, asignaciones_cambiadas: 0, costo_exacto: 2236166, costo_ag: null,
  tiempo_exacto_ms: 1, tiempo_ag_ms: null, estado_exacto: 'OPTIMAL', estado_ag: null,
}

describe('escenarios', () => {
  it('redacta la frase en lenguaje de negocio', () => {
    expect(frase(base, nombres)).toBe('Si el combustible sube 10 %, el costo sube 9 % (+$\u00A0184.651); el plan se mantiene.')
    expect(frase({ ...base, tipo: 'capacidad', ids: ['P3'], porcentaje: -30, estado_exacto: 'INFEASIBLE', costo_exacto: null }, nombres)).toContain('la capacidad de Granada baja 30 %')
  })

  it('asigna el semáforo según el impacto', () => {
    expect(semaforo(base)).toBe('ambar')
    expect(semaforo({ ...base, variacion_objetivo_pct: 1 })).toBe('verde')
    expect(semaforo({ ...base, variacion_objetivo_pct: 12 })).toBe('rojo')
    expect(semaforo({ ...base, costo_exacto: null })).toBe('rojo')
  })

  it('traduce los rangos y el gap', () => {
    expect(textoMargen(10, 12)).toBe('puede variar entre 10 t y 12 t sin cambiar el plan')
    expect(textoMargen(null, null)).toContain('sin límite')
    expect(etiquetaGap(0.2)?.texto).toBe('Excelente')
    expect(etiquetaGap(3)?.texto).toBe('Aceptable')
    expect(etiquetaGap(8)?.texto).toBe('Mejorable')
    expect(etiquetaGap(null)).toBeNull()
  })
})
