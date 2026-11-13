import { describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import MapaRed from '@/components/mapa/MapaRed.vue'
import { prepararEstaciones } from '@/composables/useEstaciones'
import { EMPRESAS_MOCK, PLANTAS_MOCK } from '@/api/mock/datos'

const todas = () => prepararEstaciones(EMPRESAS_MOCK, PLANTAS_MOCK).ubicadas

describe('MapaRed', () => {
  it('dibuja un marcador por estación y reacciona cuando una desaparece', async () => {
    const w = mount(MapaRed, { props: { estaciones: todas() }, attachTo: document.body })
    await flushPromises()
    expect(w.get('.mapa-red').attributes('data-marcadores')).toBe('14')
    expect(w.findAll('.marcador--empresa')).toHaveLength(10)
    expect(w.findAll('.marcador--planta')).toHaveLength(4)

    await w.setProps({ estaciones: todas().slice(1) }) // una estación deja de venir activa
    expect(w.get('.mapa-red').attributes('data-marcadores')).toBe('13')
    expect(w.findAll('.marcador')).toHaveLength(13)

    await w.setProps({ estaciones: [] })
    expect(w.findAll('.marcador')).toHaveLength(0)
    w.unmount()
  })

  it('cada marcador tiene un título accesible con tipo y nombre', () => {
    const w = mount(MapaRed, { props: { estaciones: todas() }, attachTo: document.body })
    const titulos = w.findAll('.marcador').map((m) => m.attributes('title'))
    expect(titulos).toContain('Planta: Planta Granada')
    expect(titulos.some((t) => t?.startsWith('Agroempresa: Agroempresa Ficticia'))).toBe(true)
    w.unmount()
  })
})
