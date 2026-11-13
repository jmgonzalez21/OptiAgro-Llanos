import { describe, expect, it } from 'vitest'
import { coincide, equilibrio, llena, planPorCeldas, sumar } from '../tablaTransporte'

describe('tabla de transporte', () => {
  it('suma ignorando vacíos y calcula el equilibrio oferta/capacidad', () => {
    expect(sumar([10, null, 5.5, undefined])).toBe(15.5)
    expect(equilibrio(100, 130)).toEqual({ alcanza: true, diferencia: 30 })
    expect(equilibrio(100, 100)).toEqual({ alcanza: true, diferencia: 0 })
    expect(equilibrio(100, 70)).toEqual({ alcanza: false, diferencia: 30 })
  })

  it('reparte las asignaciones en celdas y totaliza por empresa, planta y costo', () => {
    const plan = planPorCeldas(
      ['E1', 'E2'],
      ['P1', 'P2'],
      [
        { empresa_id: 'E1', planta_id: 'P1', cantidad: 10, costo_unitario: 100 },
        { empresa_id: 'E1', planta_id: 'P2', cantidad: 5, costo_unitario: 200 },
        { empresa_id: 'E2', planta_id: 'P1', cantidad: 20, costo_unitario: 50 },
        { empresa_id: 'X', planta_id: 'P1', cantidad: 99, costo_unitario: 1 },
      ],
    )
    expect(plan.toneladas).toEqual([[10, 5], [20, 0]])
    expect(plan.porEmpresa).toEqual([15, 20])
    expect(plan.porPlanta).toEqual([30, 5])
    expect(plan.costoTotal).toBe(3000)
    expect(coincide(15.00001, 15)).toBe(true)
    expect(llena(30, 30)).toBe(true)
    expect(llena(5, 30)).toBe(false)
  })
})
