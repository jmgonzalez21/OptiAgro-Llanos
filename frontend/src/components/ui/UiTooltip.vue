<script setup lang="ts">
/**
 * Tooltip accesible (WCAG 1.4.13): aparece con hover y con foco, se puede descartar con Esc, el puntero puede
 * pasar sobre el globo sin que desaparezca, y persiste mientras haya hover/foco. NO es el único canal de la
 * información: úsalo para ayudas complementarias (el contenido esencial va siempre en texto visible).
 * Envuelve a UN elemento enfocable (botón, enlace, campo); el componente le añade `aria-describedby`.
 * Posicionado con CSS (no detecta colisiones con el borde de la ventana; elige `lado` acorde).
 */
import { onMounted, ref, useId, watchEffect } from 'vue'

const props = withDefaults(
  defineProps<{
    texto: string
    lado?: 'arriba' | 'abajo' | 'izquierda' | 'derecha'
  }>(),
  { lado: 'arriba' },
)

const id = `tt-${useId()}`
const raiz = ref<HTMLElement | null>(null)
const hover = ref(false)
const foco = ref(false)
const descartado = ref(false)

function visible(): boolean {
  return (hover.value || foco.value) && !descartado.value
}

function vincular(): void {
  const hijo = raiz.value?.firstElementChild as HTMLElement | null
  if (!hijo || hijo.classList.contains('ui-tooltip__globo')) return
  const previo = hijo.getAttribute('aria-describedby')
  if (!previo?.split(' ').includes(id)) hijo.setAttribute('aria-describedby', previo ? `${previo} ${id}` : id)
}

onMounted(vincular)
watchEffect(() => {
  void props.texto
  vincular()
})

function entrarHover(): void {
  hover.value = true
  descartado.value = false
}

function salirHover(): void {
  hover.value = false
}

function entrarFoco(): void {
  foco.value = true
  descartado.value = false
}

function salirFoco(): void {
  foco.value = false
}

function alTeclado(ev: KeyboardEvent): void {
  if (ev.key === 'Escape' && visible()) {
    descartado.value = true
    // Esc cierra el tooltip sin cerrar el diálogo que lo contenga.
    ev.stopPropagation()
  }
}
</script>

<template>
  <span
    ref="raiz"
    class="ui-tooltip"
    @mouseenter="entrarHover"
    @mouseleave="salirHover"
    @focusin="entrarFoco"
    @focusout="salirFoco"
    @keydown="alTeclado"
  >
    <slot />
    <span :id="id" role="tooltip" class="ui-tooltip__globo" :class="[`ui-tooltip__globo--${lado}`, { 'ui-tooltip__globo--visible': hover || foco, 'ui-tooltip__globo--descartado': descartado }]">{{ texto }}</span>
  </span>
</template>

<style scoped>
.ui-tooltip {
  position: relative;
  display: inline-flex;
}

.ui-tooltip__globo {
  position: absolute;
  z-index: var(--z-tooltip);
  width: max-content;
  max-width: 16rem;
  padding: 0.4rem 0.65rem;
  border-radius: var(--radio-sm);
  background: var(--color-texto);
  color: var(--color-fondo);
  font-size: var(--texto-xs);
  font-weight: var(--peso-medio);
  line-height: 1.4;
  text-align: left;
  white-space: normal;
  box-shadow: var(--sombra-md);
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition:
    opacity var(--trans-rapida),
    visibility var(--trans-rapida);
}

/* Puente invisible sobre el hueco entre el elemento y el globo (el puntero puede cruzarlo) */
.ui-tooltip__globo::before {
  content: '';
  position: absolute;
  inset: -8px;
}

/* Con el puntero encima, el globo recibe eventos para poder "mantenerlo" (1.4.13) */
.ui-tooltip__globo--visible:not(.ui-tooltip__globo--descartado) {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
}

.ui-tooltip__globo--arriba {
  bottom: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
}

.ui-tooltip__globo--abajo {
  top: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
}

.ui-tooltip__globo--izquierda {
  right: calc(100% + 6px);
  top: 50%;
  transform: translateY(-50%);
}

.ui-tooltip__globo--derecha {
  left: calc(100% + 6px);
  top: 50%;
  transform: translateY(-50%);
}
</style>
