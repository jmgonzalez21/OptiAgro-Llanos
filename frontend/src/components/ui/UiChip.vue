<script setup lang="ts">
/**
 * Chip conmutable (filtro). Es un <button aria-pressed>; el estado se refuerza con
 * un ícono de verificación (no solo con color). v-model booleano.
 * Slot `simbolo`: ícono o marcador a la izquierda.
 */
import UiIcon from './UiIcon.vue'

const activo = defineModel<boolean>({ default: false })
</script>

<template>
  <button type="button" class="ui-chip" :class="{ 'ui-chip--activo': activo }" :aria-pressed="activo" @click="activo = !activo">
    <span v-if="$slots.simbolo" class="ui-chip__simbolo"><slot name="simbolo" /></span>
    <span class="ui-chip__texto"><slot /></span>
    <UiIcon v-if="activo" nombre="check" :tamano="14" :grosor="2.6" class="ui-chip__check" />
  </button>
</template>

<style scoped>
.ui-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  min-height: 2.5rem;
  padding: 0 0.85rem 0 0.6rem;
  border: 1px solid var(--color-borde-control);
  border-radius: var(--radio-pleno);
  background: var(--color-superficie);
  color: var(--color-texto-2);
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  line-height: 1;
  transition:
    background var(--trans),
    border-color var(--trans),
    color var(--trans),
    box-shadow var(--trans),
    transform var(--trans);
}

.ui-chip:hover {
  border-color: var(--color-acento-fuerte);
  background: var(--color-superficie-hover);
}

.ui-chip:active {
  transform: scale(0.97);
}

.ui-chip--activo {
  background: var(--color-activo-fondo);
  border-color: var(--color-acento-fuerte);
  color: var(--color-activo-texto);
  font-weight: var(--peso-fuerte);
}

.ui-chip__simbolo {
  display: inline-flex;
}

.ui-chip:not(.ui-chip--activo) .ui-chip__simbolo {
  opacity: 0.55;
  filter: grayscale(0.4);
}
</style>
