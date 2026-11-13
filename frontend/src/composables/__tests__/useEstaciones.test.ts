import { describe, expect, it } from 'vitest'
import { coordenadasValidas, prepararEstaciones } from '@/composables/useEstaciones'
import { aNumeroONull, normalizarEmpresa } from '@/api/servicios'
import type { Empresa, Planta } from '@/types/api'

const empresa = (o: Partial<Empresa> = {}): Empresa => ({
  id: 1, nombre: 'E', municipio: 'M', latitud: 4, longitud: -73, oferta: 10, activa: true, ...o,
})
const planta = (o: Partial<Planta> = {}): Planta => ({
  id: 1, nombre: 'P', municipio: 'M', latitud: 4, longitud: -73, capacidad: 50, activa: true, ...o,
})

describe('prepararEstaciones', () => {
  it('separa estaciones con y sin coordenadas', () => {
    const r = prepararEstaciones(
      [empresa({ id: 1 }), empresa({ id: 2, latitud: null, longitud: null })],
      [planta({ id: 1 })],
    )
    expect(r.ubicadas.map((e) => e.clave)).toEqual(['empresa-1', 'planta-1'])
    expect(r.sinUbicacion.map((e) => e.clave)).toEqual(['empresa-2'])
  })

  it('excluye las inactivas', () => {
    const r = prepararEstaciones([empresa({ activa: false })], [planta({ activa: false })])
    expect(r.ubicadas).toHaveLength(0)
    expect(r.sinUbicacion).toHaveLength(0)
  })

  it('usa oferta para empresas y capacidad para plantas', () => {
    const r = prepararEstaciones([empresa({ oferta: 33 })], [planta({ capacidad: 77 })])
    expect(r.ubicadas.map((e) => e.cantidad)).toEqual([33, 77])
  })

  it('rechaza coordenadas fuera de rango', () => {
    expect(coordenadasValidas(91, 0)).toBe(false)
    expect(coordenadasValidas(4, -73)).toBe(true)
    expect(coordenadasValidas(null, -73)).toBe(false)
  })
})

describe('normalización del contrato', () => {
  it('convierte decimales como texto a número y vacíos a null', () => {
    expect(aNumeroONull('4.1420')).toBe(4.142)
    expect(aNumeroONull('')).toBeNull()
    expect(aNumeroONull(null)).toBeNull()
    expect(aNumeroONull('abc')).toBeNull()
    const e = normalizarEmpresa({ id: 1, nombre: 'X', latitud: '4.5', longitud: null, oferta: '12.5', activa: true })
    expect(e).toMatchObject({ latitud: 4.5, longitud: null, oferta: 12.5 })
  })
})
