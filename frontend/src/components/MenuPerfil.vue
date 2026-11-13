<script setup lang="ts">
/**
 * Menú de perfil (patrón "menu button" de WAI-ARIA).
 * Teclado: Enter/Espacio/Flecha abajo abren; flechas, Inicio y Fin navegan;
 * Esc cierra y devuelve el foco al botón; Tab cierra.
 */
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import UiAvatar from '@/components/ui/UiAvatar.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiIcon from '@/components/ui/UiIcon.vue'

defineProps<{
  nombre: string
  rol: string
}>()

const emit = defineEmits<{ (e: 'cerrar-sesion'): void }>()

const abierto = ref(false)
const raiz = ref<HTMLElement | null>(null)
const boton = ref<HTMLButtonElement | null>(null)
const menu = ref<HTMLElement | null>(null)

function items(): HTMLElement[] {
  return Array.from(menu.value?.querySelectorAll<HTMLElement>('[role="menuitem"]') ?? [])
}

function enfocar(indice: number): void {
  const lista = items()
  if (lista.length === 0) return
  const i = (indice + lista.length) % lista.length
  lista[i]?.focus()
}

async function abrir(enfocarUltimo = false): Promise<void> {
  abierto.value = true
  await nextTick()
  enfocar(enfocarUltimo ? -1 : 0)
}

function cerrar(devolverFoco = true): void {
  if (!abierto.value) return
  abierto.value = false
  if (devolverFoco) void nextTick(() => boton.value?.focus())
}

function alternar(): void {
  if (abierto.value) cerrar()
  else void abrir()
}

function teclaBoton(e: KeyboardEvent): void {
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    void abrir()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    void abrir(true)
  }
}

function teclaMenu(e: KeyboardEvent): void {
  const lista = items()
  const actual = lista.indexOf(document.activeElement as HTMLElement)
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      enfocar(actual + 1)
      break
    case 'ArrowUp':
      e.preventDefault()
      enfocar(actual - 1)
      break
    case 'Home':
      e.preventDefault()
      enfocar(0)
      break
    case 'End':
      e.preventDefault()
      enfocar(-1)
      break
    case 'Escape':
      e.preventDefault()
      e.stopPropagation()
      cerrar()
      break
    case 'Tab':
      cerrar(false)
      break
  }
}

function alCerrarSesion(): void {
  cerrar(false)
  emit('cerrar-sesion')
}

function clicFuera(e: MouseEvent): void {
  if (abierto.value && raiz.value && !raiz.value.contains(e.target as Node)) cerrar(false)
}

onMounted(() => document.addEventListener('click', clicFuera))
onBeforeUnmount(() => document.removeEventListener('click', clicFuera))
</script>

<template>
  <div ref="raiz" class="menu-perfil">
    <button
      id="menu-perfil-boton"
      ref="boton"
      type="button"
      class="menu-perfil__boton"
      aria-haspopup="menu"
      aria-controls="menu-perfil-lista"
      :aria-expanded="abierto"
      @click="alternar"
      @keydown="teclaBoton"
    >
      <UiAvatar :nombre="nombre" :tamano="38" />
      <span class="menu-perfil__etiqueta">
        <span class="menu-perfil__nombre">{{ nombre }}</span>
        <span class="menu-perfil__rol">{{ rol }}</span>
      </span>
      <UiIcon nombre="chevron-abajo" :tamano="16" class="menu-perfil__flecha" />
      <span class="sr-only">Menú de perfil</span>
    </button>

    <Transition name="menu-perfil">
      <div v-show="abierto" class="menu-perfil__panel">
        <div class="menu-perfil__resumen">
          <UiAvatar :nombre="nombre" :tamano="44" />
          <p class="menu-perfil__resumen-texto">
            <span class="menu-perfil__resumen-nombre">{{ nombre }}</span>
            <UiBadge tono="verde" class="menu-perfil__resumen-rol">{{ rol }}</UiBadge>
          </p>
        </div>
        <div
          id="menu-perfil-lista"
          ref="menu"
          class="menu-perfil__lista"
          role="menu"
          aria-labelledby="menu-perfil-boton"
          @keydown="teclaMenu"
        >
          <button type="button" role="menuitem" class="menu-perfil__item menu-perfil__item--deshabilitado" aria-disabled="true" tabindex="-1">
            <UiIcon nombre="usuario" :tamano="18" />
            <span class="menu-perfil__item-texto">Mi perfil</span>
            <UiBadge class="etiqueta-proximamente">Próximamente</UiBadge>
          </button>
          <button type="button" role="menuitem" class="menu-perfil__item menu-perfil__item--salir" tabindex="-1" @click="alCerrarSesion">
            <UiIcon nombre="salir" :tamano="18" />
            <span class="menu-perfil__item-texto">Cerrar sesión</span>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.menu-perfil {
  position: relative;
}

.menu-perfil__boton {
  display: inline-flex;
  align-items: center;
  gap: var(--espacio-3);
  padding: 0.2rem;
  border: 1px solid transparent;
  border-radius: var(--radio-pleno);
  background: transparent;
  transition:
    background var(--trans),
    border-color var(--trans),
    box-shadow var(--trans);
}

.menu-perfil__boton:hover,
.menu-perfil__boton[aria-expanded='true'] {
  background: var(--color-superficie);
  border-color: var(--color-borde);
  box-shadow: var(--sombra-sm);
}

.menu-perfil__etiqueta {
  display: none;
  flex-direction: column;
  text-align: left;
  line-height: 1.2;
}

.menu-perfil__nombre {
  font-size: var(--texto-sm);
  font-weight: var(--peso-fuerte);
  color: var(--color-texto);
  max-width: 11rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-perfil__rol {
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
}

.menu-perfil__flecha {
  display: none;
  color: var(--color-texto-suave);
  transition: transform var(--trans);
}

.menu-perfil__boton[aria-expanded='true'] .menu-perfil__flecha {
  transform: rotate(180deg);
}

.menu-perfil__panel {
  position: absolute;
  top: calc(100% + 0.6rem);
  right: 0;
  z-index: var(--z-menu);
  width: 17rem;
  max-width: calc(100vw - 2rem);
  padding: 0.4rem;
  border: 1px solid var(--color-borde);
  border-radius: var(--radio-lg);
  background: var(--color-superficie);
  box-shadow: var(--sombra-lg);
  transform-origin: top right;
}

.menu-perfil-enter-active,
.menu-perfil-leave-active {
  transition:
    opacity var(--trans),
    transform var(--trans);
}

.menu-perfil-enter-from,
.menu-perfil-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}

.menu-perfil__resumen {
  display: flex;
  align-items: center;
  gap: var(--espacio-3);
  margin-bottom: 0.4rem;
  padding: var(--espacio-3);
  border-radius: var(--radio-md);
  background: linear-gradient(135deg, var(--color-acento-suave), var(--color-superficie));
}

.menu-perfil__resumen-texto {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.25rem;
  min-width: 0;
}

.menu-perfil__resumen-nombre {
  max-width: 11rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: var(--peso-fuerte);
  line-height: 1.2;
}

.menu-perfil__lista {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-top: 0.4rem;
  border-top: 1px solid var(--color-borde);
}

.menu-perfil__item {
  display: flex;
  align-items: center;
  gap: var(--espacio-3);
  min-height: var(--alto-tactil);
  padding: 0 var(--espacio-3);
  border: 0;
  border-radius: var(--radio-md);
  background: transparent;
  color: var(--color-texto);
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  text-align: left;
  transition: background var(--trans-rapida);
}

.menu-perfil__item-texto {
  flex: 1;
}

.menu-perfil__item:hover:not([aria-disabled='true']),
.menu-perfil__item:focus-visible {
  background: var(--color-acento-suave);
}

.menu-perfil__item:focus-visible {
  outline-offset: -2px;
  box-shadow: none;
}

.menu-perfil__item--deshabilitado {
  color: var(--color-texto-suave);
  cursor: not-allowed;
}

.menu-perfil__item.menu-perfil__item--salir:hover:not([aria-disabled='true']) {
  background: var(--color-error-fondo);
  color: var(--color-error);
}

@media (min-width: 40rem) {
  .menu-perfil__boton {
    padding-right: 0.6rem;
  }

  .menu-perfil__flecha {
    display: inline-block;
  }

  .menu-perfil__etiqueta {
    display: inline-flex;
  }
}
</style>
