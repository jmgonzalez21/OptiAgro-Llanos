import { describe, expect, it } from 'vitest'
import { ErrorValidacion } from '@/api/errores'
import { leerErrores } from '@/api/util'
import { puntosPolyline } from '@/composables/grafico'
import { aVariaciones, leerPorcentajes } from '@/composables/variaciones'

describe('leerErrores', () => {
  it('separa los errores 400 por campo y el mensaje general', () => {
    const e = new ErrorValidacion('Datos inválidos.', { codigo: ['Ya existe.'], non_field_errors: ['Revisa los datos.'] })
    const r = leerErrores(e)
    expect(r.campos.codigo).toBe('Ya existe.')
    expect(r.general).toBe('Revisa los datos.')
  })

  it('una lista de errores pasa como mensaje general', () => {
    expect(leerErrores(new ErrorValidacion('x', ['No se puede eliminarse a sí mismo.'])).general).toContain('sí mismo')
  })
})

describe('gráfico y variaciones', () => {
  it('puntosPolyline escala la serie al área', () => {
    expect(puntosPolyline([0, 10], 100, 50, 0)).toBe('0.0,50.0 100.0,0.0')
    expect(puntosPolyline([], 100, 50)).toBe('')
  })

  it('lee porcentajes con espacios, punto y coma y coma decimal', () => {
    expect(leerPorcentajes('-10 10; 2,5')).toEqual([-10, 10, 2.5])
    expect(aVariaciones([{ tipo: 'oferta', ids: 'E1, E2', porcentajes: '10 20' }])).toEqual([{ tipo: 'oferta', ids: ['E1', 'E2'], porcentajes: [10, 20] }])
  })
})
