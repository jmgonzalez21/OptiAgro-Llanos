<script setup lang="ts">
/**
 * Menú de acciones (menu button WAI-ARIA): botón con `aria-haspopup="menu"`/`aria-expanded`, ítems `role="menuitem"`,
 * flechas, Inicio/Fin, Esc (devuelve el foco), Tab cierra, clic fuera cierra. El panel se teletransporta a `body`
 * con posición fija para no quedar recortado por tablas con scroll.
 * - Sin `texto`: botón de solo ícono (⋮) con `etiqueta` como nombre accesible ("Acciones de E1 Finca La Esperanza").
 * - Con `texto`: botón secundario con texto + flecha ("Ampliar la red").
 * - Ítem deshabilitado: sigue enfocable (`aria-disabled`) y muestra `motivo` visible, no solo atenuado.
 * Emite `seleccionar(id)`.
 */
import { nextTick, onBeforeUnmount, ref, useId } from 'vue'
import UiIcon from './UiIcon.vue'
import type { NombreIcono } from './icons'

export interface ItemMenu {
  id: string
  etiqueta: string
  icono?: NombreIcono
  peligro?: boolean
  deshabilitado?: boolean
  /** Motivo visible cuando está deshabilitado. */
  motivo?: string
  /** Línea separadora antes del ítem. */
  separador?: boolean
}

const props = withDefaults(
  defineProps<{
    etiqueta: string
    items: ItemMenu[]
    texto?: string
    alinear?: 'inicio' | 'fin'
  }>(),
  { texto: '', alinear: 'fin' },
)

const emit = defineEmits<{ seleccionar: [id: string] }>()

const id = useId()
const abierto = ref(false)
const boton = ref<HTMLButtonElement | null>(null)
const panel = ref<HTMLElement | null>(null)
const posicion = ref<Record<string, string>>({})

function elementos(): HTMLElement[] {
  return Array.from(panel.value?.querySelectorAll<HTMLElement>('[role="menuitem"]') ?? [])
}

function colocar(): void {
  const r = boton.value?.getBoundingClientRect()
  if (!r) return
  const abajo = window.innerHeight - r.bottom
  const arriba = r.top
  const ponerArriba = abajo < 220 && arriba > abajo
  posicion.value = {
    top: ponerArriba ? '' : `${r.bottom + 6}px`,
    bottom: ponerArriba ? `${window.innerHeight - r.top + 6}px` : '',
    ...(props.alinear === 'fin' ? { right: `${Math.max(8, window.innerWidth - r.right)}px` } : { left: `${Math.max(8, r.left)}px` }),
  }
}

function alClicFuera(ev: MouseEvent): void {
  const t = ev.target as Node
  if (!panel.value?.contains(t) && !boton.value?.contains(t)) cerrar(false)
}

function alCambiarVista(): void {
  cerrar(false)
}

async function abrir(foco: 'primero' | 'ultimo' = 'primero'): Promise<void> {
  abierto.value = true
  colocar()
  document.addEventListener('mousedown', alClicFuera)
  window.addEventListener('resize', alCambiarVista)
  window.addEventListener('scroll', alCambiarVista, true)
  await nextTick()
  const lista = elementos()
  ;(foco === 'primero' ? lista[0] : lista[lista.length - 1])?.focus()
}

function cerrar(devolverFoco: boolean): void {
  if (!abierto.value) return
  abierto.value = false
  document.removeEventListener('mousedown', alClicFuera)
  window.removeEventListener('resize', alCambiarVista)
  window.removeEventListener('scroll', alCambiarVista, true)
  if (devolverFoco) boton.value?.focus()
}

function alternar(): void {
  if (abierto.value) cerrar(true)
  else void abrir()
}

function alTecladoBoton(ev: KeyboardEvent): void {
  if (ev.key === 'ArrowDown') {
    ev.preventDefault()
    void abrir('primero')
  } else if (ev.key === 'ArrowUp') {
    ev.preventDefault()
    void abrir('ultimo')
  }
}

function alTecladoMenu(ev: KeyboardEvent): void {
  const lista = elementos()
  const i = lista.indexOf(document.activeElement as HTMLElement)
  if (ev.key === 'ArrowDown') {
    ev.preventDefault()
    lista[(i + 1) % lista.length]?.focus()
  } else if (ev.key === 'ArrowUp') {
    ev.preventDefault()
    lista[(i - 1 + lista.length) % lista.length]?.focus()
  } else if (ev.key === 'Home') {
    ev.preventDefault()
    lista[0]?.focus()
  } else if (ev.key === 'End') {
    ev.preventDefault()
    lista[lista.length - 1]?.focus()
  } else if (ev.key === 'Escape') {
    ev.preventDefault()
    ev.stopPropagation()
    cerrar(true)
  } else if (ev.key === 'Tab') {
    cerrar(false)
  }
}

function elegir(item: ItemMenu): void {
  if (item.deshabilitado) return
  cerrar(true)
  emit('seleccionar', item.id)
}

onBeforeUnmount(() => cerrar(false))
</script>

<template>
  <span class="ui-menu">
    <button
      v-if="!texto"
      ref="boton"
      type="button"
      class="ui-menu__boton ui-menu__boton--icono"
      aria-haspopup="menu"
      :aria-expanded="abierto"
      :aria-controls="abierto ? `${id}-menu` : undefined"
      :aria-label="etiqueta"
      :title="etiqueta"
      @click="alternar"
      @keydown="alTecladoBoton"
    >
      <UiIcon nombre="mas-vertical" :tamano="20" :grosor="2.6" />
    </button>
    <button
      v-else
      ref="boton"
      type="button"
      class="ui-menu__boton ui-menu__boton--texto"
      aria-haspopup="menu"
      :aria-expanded="abierto"
      :aria-controls="abierto ? `${id}-menu` : undefined"
      :aria-label="etiqueta === texto ? undefined : etiqueta"
      @click="alternar"
      @keydown="alTecladoBoton"
    >
      <span>{{ texto }}</span>
      <UiIcon nombre="chevron-abajo" :tamano="16" />
    </button>

    <Teleport to="body">
      <ul v-if="abierto" :id="`${id}-menu`" ref="panel" class="ui-menu__panel" role="menu" :aria-label="etiqueta" :style="posicion" @keydown="alTecladoMenu">
        <template v-for="item in items" :key="item.id">
          <li v-if="item.separador" role="separator" class="ui-menu__separador"></li>
          <li role="none">
            <button
              type="button"
              role="menuitem"
              class="ui-menu__item"
              :class="{ 'ui-menu__item--peligro': item.peligro, 'ui-menu__item--deshabilitado': item.deshabilitado }"
              :aria-disabled="item.deshabilitado ? 'true' : undefined"
              tabindex="-1"
              @click="elegir(item)"
            >
              <UiIcon v-if="item.icono" :nombre="item.icono" :tamano="18" />
              <span class="ui-menu__texto">
                {{ item.etiqueta }}
                <span v-if="item.deshabilitado && item.motivo" class="ui-menu__motivo">{{ item.motivo }}</span>
              </span>
            </button>
          </li>
        </template>
      </ul>
    </Teleport>
  </span>
</template>

<style scoped>
.ui-menu {
  display: inline-flex;
}

.ui-menu__boton {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--espacio-2);
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-texto-2);
  transition:
    background var(--trans),
    color var(--trans);
}

.ui-menu__boton--icono {
  width: var(--alto-tactil);
  height: var(--alto-tactil);
  border-radius: var(--radio-md);
}

.ui-menu__boton--texto {
  min-height: var(--alto-tactil);
  padding: 0 var(--espacio-4);
  border-color: var(--color-borde-control);
  border-radius: var(--radio-md);
  background: var(--color-superficie);
  color: var(--color-activo-texto);
  font-size: var(--texto-sm);
  font-weight: var(--peso-fuerte);
  box-shadow: var(--sombra-xs);
}

.ui-menu__boton:hover {
  background: var(--color-acento-suave);
  color: var(--color-activo-texto);
}

.ui-menu__boton[aria-expanded='true'] {
  background: var(--color-activo-fondo);
  color: var(--color-activo-texto);
}
</style>

<style>
/* El panel vive en <body> (Teleport): estilos sin `scoped` */
.ui-menu__panel {
  position: fixed;
  z-index: var(--z-menu);
  min-width: 13rem;
  max-width: 20rem;
  padding: var(--espacio-1);
  border: 1px solid var(--color-borde);
  border-radius: var(--radio-md);
  background: var(--color-superficie);
  box-shadow: var(--sombra-lg);
  animation: ui-aparecer var(--trans) both;
}

.ui-menu__item {
  display: flex;
  align-items: center;
  gap: var(--espacio-3);
  width: 100%;
  min-height: var(--alto-tactil);
  padding: 0.4rem var(--espacio-3);
  border: 0;
  border-radius: var(--radio-sm);
  background: transparent;
  color: var(--color-texto);
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  text-align: left;
}

.ui-menu__item:hover,
.ui-menu__item:focus-visible {
  background: var(--color-acento-suave);
}

.ui-menu__item:focus-visible {
  outline-offset: -2px;
}

.ui-menu__item--peligro {
  color: var(--color-error);
}

.ui-menu__item--deshabilitado {
  color: var(--color-texto-suave);
  cursor: not-allowed;
}

.ui-menu__item--deshabilitado:hover {
  background: transparent;
}

.ui-menu__texto {
  display: flex;
  flex-direction: column;
}

.ui-menu__motivo {
  font-size: var(--texto-xs);
  font-weight: var(--peso-normal);
  color: var(--color-texto-suave);
}

.ui-menu__separador {
  height: 1px;
  margin: var(--espacio-1) 0;
  background: var(--color-borde);
}
</style>
