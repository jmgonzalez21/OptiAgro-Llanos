import { describe, expect, it } from 'vitest'
import { mediana, proponerRutas, siguienteCodigo, tarifaSugerida, TARIFA_POR_DEFECTO } from '../geo'

describe('geo', () => {
  it('genera códigos únicos con el siguiente número libre', () => {
    expect(siguienteCodigo('E', ['E1', 'E2', 'E10'])).toBe('E11')
    expect(siguienteCodigo('P', [])).toBe('P1')
    expect(siguienteCodigo('P', ['p4', 'P2'])).toBe('P5')
  })

  it('usa la mediana de las tarifas o un valor por defecto', () => {
    expect(mediana([3, 1, 2])).toBe(2)
    expect(mediana([1, 2, 3, 4])).toBe(2.5)
    expect(tarifaSugerida([400, null, 600, 800])).toBe(600)
    expect(tarifaSugerida([])).toBe(TARIFA_POR_DEFECTO)
  })

  it('propone rutas hacia las estaciones ubicadas y cuenta las que no tienen coordenadas', () => {
    const { rutas, sinUbicacion } = proponerRutas(
      'empresa',
      { codigo: 'E11', latitud: 4.2, longitud: -73.5 },
      [
        { codigo: 'P1', latitud: 4.142, longitud: -73.627 },
        { codigo: 'P2', latitud: null, longitud: null },
      ],
      500,
    )
    expect(sinUbicacion).toBe(1)
    expect(rutas).toHaveLength(1)
    expect(rutas[0]).toMatchObject({ empresa: 'E11', planta: 'P1', tarifa_km_ton: 500 })
    expect(rutas[0]).not.toHaveProperty('distancia_km')
  })
})
