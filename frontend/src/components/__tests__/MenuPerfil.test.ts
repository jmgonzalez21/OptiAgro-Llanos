import { beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import MenuPerfil from '@/components/MenuPerfil.vue'

function montar() {
  return mount(MenuPerfil, {
    props: { nombre: 'Admin Demo', rol: 'Administrador' },
    attachTo: document.body,
  })
}

describe('MenuPerfil', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  it('está cerrado al inicio y declara aria-haspopup/aria-expanded', () => {
    const w = montar()
    const boton = w.get('button.menu-perfil__boton')
    expect(boton.attributes('aria-haspopup')).toBe('menu')
    expect(boton.attributes('aria-expanded')).toBe('false')
    expect(w.get('.menu-perfil__panel').isVisible()).toBe(false)
  })

  it('se abre con la flecha abajo y enfoca el primer elemento', async () => {
    const w = montar()
    await w.get('button.menu-perfil__boton').trigger('keydown', { key: 'ArrowDown' })
    expect(w.get('button.menu-perfil__boton').attributes('aria-expanded')).toBe('true')
    const items = w.findAll('[role="menuitem"]')
    expect(items).toHaveLength(2)
    expect(document.activeElement).toBe(items[0]!.element)
  })

  it('las flechas recorren el menú de forma circular', async () => {
    const w = montar()
    await w.get('button.menu-perfil__boton').trigger('click')
    const items = w.findAll('[role="menuitem"]')
    await w.get('[role="menu"]').trigger('keydown', { key: 'ArrowDown' })
    expect(document.activeElement).toBe(items[1]!.element)
    await w.get('[role="menu"]').trigger('keydown', { key: 'ArrowDown' })
    expect(document.activeElement).toBe(items[0]!.element)
    await w.get('[role="menu"]').trigger('keydown', { key: 'End' })
    expect(document.activeElement).toBe(items[1]!.element)
  })

  it('Esc cierra el menú y devuelve el foco al botón', async () => {
    const w = montar()
    const boton = w.get('button.menu-perfil__boton')
    await boton.trigger('click')
    await w.get('[role="menu"]').trigger('keydown', { key: 'Escape' })
    expect(boton.attributes('aria-expanded')).toBe('false')
    expect(document.activeElement).toBe(boton.element)
  })

  it('"Mi perfil" está deshabilitado con etiqueta Próximamente', async () => {
    const w = montar()
    await w.get('button.menu-perfil__boton').trigger('click')
    const perfil = w.findAll('[role="menuitem"]')[0]!
    expect(perfil.attributes('aria-disabled')).toBe('true')
    expect(perfil.text()).toContain('Próximamente')
  })

  it('"Cerrar sesión" emite el evento y cierra el menú', async () => {
    const w = montar()
    await w.get('button.menu-perfil__boton').trigger('click')
    await w.findAll('[role="menuitem"]')[1]!.trigger('click')
    expect(w.emitted('cerrar-sesion')).toHaveLength(1)
    expect(w.get('button.menu-perfil__boton').attributes('aria-expanded')).toBe('false')
  })
})
