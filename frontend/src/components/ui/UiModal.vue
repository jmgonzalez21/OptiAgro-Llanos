<script setup lang="ts">
/**
 * Diálogo modal accesible. `role="dialog"` (o `alertdialog`), `aria-modal`, nombre = título, foco atrapado,
 * Esc, foco devuelto al disparador y scroll del documento bloqueado.
 *
 * Controlado por el padre: `:abierto`. Al intentar cerrar (Esc, velo, ×) emite `cerrar` (con el motivo) y
 * `update:abierto(false)`; con `bloquearCierre` solo emite `cerrar` para que el padre decida (p. ej. cambios sin guardar).
 * Foco inicial: el elemento con `data-autofocus`; si no hay, el primer control del cuerpo.
 * Slots: default (cuerpo), `pie` (acciones, fijo abajo), `titulo` (sustituye al texto del título).
 */
import { computed, ref, toRef, useId, useSlots } from 'vue'
import UiIcon from './UiIcon.vue'
import { useDialogo } from './useDialogo'

export type MotivoCierre = 'esc' | 'velo' | 'boton'

const props = withDefaults(
  defineProps<{
    abierto: boolean
    titulo: string
    descripcion?: string
    rol?: 'dialog' | 'alertdialog'
    ancho?: 'sm' | 'md' | 'lg'
    cerrarConVelo?: boolean
    ocultarCerrar?: boolean
    bloquearCierre?: boolean
  }>(),
  { descripcion: '', rol: 'dialog', ancho: 'md', cerrarConVelo: true, ocultarCerrar: false, bloquearCierre: false },
)

const emit = defineEmits<{
  'update:abierto': [valor: boolean]
  cerrar: [motivo: MotivoCierre]
}>()

const slots = useSlots()
const id = useId()
const idTitulo = `${id}-titulo`
const idDescripcion = `${id}-desc`
const caja = ref<HTMLElement | null>(null)

function solicitarCierre(motivo: MotivoCierre): void {
  emit('cerrar', motivo)
  if (!props.bloquearCierre) emit('update:abierto', false)
}

const { alTeclado } = useDialogo({
  contenedor: caja,
  abierto: toRef(props, 'abierto'),
  alEscape: () => solicitarCierre('esc'),
})

const tieneDescripcion = computed(() => props.descripcion !== '' || !!slots.descripcion)
</script>

<template>
  <Teleport to="body">
    <Transition name="ui-modal">
      <div v-if="abierto" class="ui-modal" @keydown="alTeclado">
        <div class="ui-modal__velo" aria-hidden="true" @click="cerrarConVelo && solicitarCierre('velo')"></div>
        <div
          ref="caja"
          class="ui-modal__caja"
          :class="`ui-modal__caja--${ancho}`"
          :role="rol"
          aria-modal="true"
          :aria-labelledby="idTitulo"
          :aria-describedby="tieneDescripcion ? idDescripcion : undefined"
          tabindex="-1"
        >
          <header class="ui-modal__cabecera">
            <h2 :id="idTitulo" class="ui-modal__titulo"><slot name="titulo">{{ titulo }}</slot></h2>
            <button v-if="!ocultarCerrar" type="button" class="ui-modal__cerrar" data-cerrar aria-label="Cerrar" @click="solicitarCierre('boton')">
              <UiIcon nombre="cerrar" :tamano="20" />
            </button>
          </header>
          <div class="ui-modal__cuerpo">
            <div v-if="tieneDescripcion" :id="idDescripcion" class="ui-modal__descripcion">
              <slot name="descripcion">{{ descripcion }}</slot>
            </div>
            <slot />
          </div>
          <footer v-if="$slots.pie" class="ui-modal__pie"><slot name="pie" /></footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.ui-modal {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  display: grid;
  place-items: center;
  padding: var(--espacio-4);
}

.ui-modal__velo {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: var(--color-velo);
  backdrop-filter: blur(2px);
}

.ui-modal__caja {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-height: min(90vh, 52rem);
  border: 1px solid var(--color-borde);
  border-radius: var(--radio-lg);
  background: var(--color-superficie);
  color: var(--color-texto);
  box-shadow: var(--sombra-lg);
}

.ui-modal__caja:focus-visible {
  outline: none;
  box-shadow: var(--sombra-lg);
}

.ui-modal__caja--sm {
  max-width: 26rem;
}

.ui-modal__caja--md {
  max-width: 34rem;
}

.ui-modal__caja--lg {
  max-width: 50rem;
}

.ui-modal__cabecera {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--espacio-3);
  padding: var(--espacio-4) var(--espacio-4) var(--espacio-2) var(--espacio-5);
}

.ui-modal__titulo {
  padding-top: 0.35rem;
  font-size: var(--texto-lg);
}

.ui-modal__cerrar {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: var(--alto-tactil);
  height: var(--alto-tactil);
  margin-top: -0.25rem;
  border: 0;
  border-radius: var(--radio-md);
  background: transparent;
  color: var(--color-texto-2);
}

.ui-modal__cerrar:hover {
  background: var(--color-acento-suave);
  color: var(--color-activo-texto);
}

.ui-modal__cuerpo {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-3);
  flex: 1;
  min-height: 0;
  padding: var(--espacio-2) var(--espacio-5) var(--espacio-4);
  overflow-y: auto;
  scroll-padding-bottom: 6rem;
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
}

.ui-modal__descripcion {
  color: var(--color-texto-2);
}

.ui-modal__pie {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--espacio-2);
  padding: var(--espacio-3) var(--espacio-5) var(--espacio-4);
  border-top: 1px solid var(--color-borde);
  background: var(--color-superficie);
  border-radius: 0 0 var(--radio-lg) var(--radio-lg);
}

.ui-modal-enter-active,
.ui-modal-leave-active {
  transition: opacity var(--trans);
}

.ui-modal-enter-active .ui-modal__caja,
.ui-modal-leave-active .ui-modal__caja {
  transition:
    transform var(--trans),
    opacity var(--trans);
}

.ui-modal-enter-from,
.ui-modal-leave-to {
  opacity: 0;
}

.ui-modal-enter-from .ui-modal__caja,
.ui-modal-leave-to .ui-modal__caja {
  transform: translateY(10px) scale(0.98);
}

@media (max-width: 30rem) {
  .ui-modal {
    padding: var(--espacio-2);
    align-items: end;
  }
}
</style>
