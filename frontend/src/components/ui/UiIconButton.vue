<script setup lang="ts">
/** Botón solo-ícono. `etiqueta` es obligatoria: es el nombre accesible y el tooltip. */
import UiIcon from './UiIcon.vue'
import type { NombreIcono } from './icons'

withDefaults(
  defineProps<{
    etiqueta: string
    icono: NombreIcono
    variante?: 'vidrio' | 'fantasma' | 'secundario'
    pulsado?: boolean
    tamano?: number
    type?: 'button' | 'submit'
  }>(),
  { variante: 'fantasma', pulsado: undefined, tamano: 20, type: 'button' },
)
</script>

<template>
  <button
    class="ui-icono-boton"
    :class="`ui-icono-boton--${variante}`"
    :type="type"
    :aria-label="etiqueta"
    :aria-pressed="pulsado === undefined ? undefined : pulsado"
    :title="etiqueta"
  >
    <UiIcon :nombre="icono" :tamano="tamano" />
  </button>
</template>

<style scoped>
.ui-icono-boton {
  display: inline-grid;
  place-items: center;
  width: var(--alto-tactil);
  height: var(--alto-tactil);
  padding: 0;
  border: 1px solid transparent;
  border-radius: var(--radio-md);
  background: transparent;
  color: var(--color-texto-2);
  transition:
    background var(--trans),
    color var(--trans),
    box-shadow var(--trans),
    transform var(--trans);
}

.ui-icono-boton:hover:not(:disabled) {
  background: var(--color-acento-suave);
  color: var(--color-activo-texto);
}

.ui-icono-boton:active:not(:disabled) {
  transform: scale(0.94);
}

.ui-icono-boton[aria-pressed='true'] {
  background: var(--color-activo-fondo);
  color: var(--color-activo-texto);
}

.ui-icono-boton--secundario {
  background: var(--color-superficie);
  border-color: var(--color-borde-control);
  box-shadow: var(--sombra-xs);
}

.ui-icono-boton--vidrio {
  background: var(--color-vidrio);
  border-color: var(--color-vidrio-borde);
  backdrop-filter: blur(12px) saturate(1.4);
  -webkit-backdrop-filter: blur(12px) saturate(1.4);
  box-shadow:
    0 6px 16px -6px var(--color-vidrio-sombra),
    var(--sombra-xs);
}

.ui-icono-boton:disabled {
  opacity: 0.45;
}
</style>
