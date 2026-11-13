<script setup lang="ts">
/**
 * Botón. Variantes: primario (acción principal), secundario, fantasma y peligro (acciones destructivas).
 * `loading` muestra el spinner, bloquea el botón y marca aria-busy.
 */
import { computed } from 'vue'
import UiSpinner from './UiSpinner.vue'

const props = withDefaults(
  defineProps<{
    variante?: 'primario' | 'secundario' | 'fantasma' | 'peligro'
    tamano?: 'sm' | 'md' | 'lg'
    type?: 'button' | 'submit' | 'reset'
    loading?: boolean
    bloque?: boolean
    disabled?: boolean
  }>(),
  { variante: 'primario', tamano: 'md', type: 'button', loading: false, bloque: false, disabled: false },
)

const bloqueado = computed(() => props.disabled || props.loading)
</script>

<template>
  <button
    class="ui-boton"
    :class="[`ui-boton--${variante}`, `ui-boton--${tamano}`, { 'ui-boton--bloque': bloque, 'ui-boton--cargando': loading }]"
    :type="type"
    :disabled="bloqueado"
    :aria-busy="loading ? 'true' : undefined"
  >
    <UiSpinner v-if="loading" :tamano="16" />
    <span v-else-if="$slots.icono" class="ui-boton__icono"><slot name="icono" /></span>
    <span class="ui-boton__texto"><slot /></span>
  </button>
</template>

<style scoped>
.ui-boton {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--espacio-2);
  min-height: var(--alto-tactil);
  padding: 0 var(--espacio-5);
  border: 1px solid transparent;
  border-radius: var(--radio-md);
  font-weight: var(--peso-fuerte);
  font-size: var(--texto-sm);
  line-height: 1;
  white-space: nowrap;
  text-decoration: none;
  transition:
    background var(--trans),
    border-color var(--trans),
    box-shadow var(--trans),
    transform var(--trans),
    color var(--trans);
  -webkit-tap-highlight-color: transparent;
}

.ui-boton--sm {
  min-height: 2.25rem;
  padding: 0 var(--espacio-4);
  font-size: var(--texto-xs);
}

.ui-boton--lg {
  min-height: 3.25rem;
  padding: 0 var(--espacio-6);
  font-size: var(--texto-base);
  border-radius: 14px;
}

.ui-boton--bloque {
  display: flex;
  width: 100%;
}

.ui-boton__icono {
  display: inline-flex;
}

/* Primario */
.ui-boton--primario {
  background: var(--color-primario);
  color: var(--color-sobre-primario);
  box-shadow: var(--sombra-boton);
}

.ui-boton--primario:hover:not(:disabled) {
  background: var(--color-primario-hover);
  transform: translateY(-1px);
  box-shadow:
    0 6px 14px -4px rgb(18 74 45 / 0.4),
    inset 0 1px 0 rgb(255 255 255 / 0.14);
}

.ui-boton--primario:active:not(:disabled) {
  background: var(--color-primario-activo);
  transform: translateY(0);
  box-shadow: var(--sombra-xs);
}

/* Peligro (acciones destructivas: eliminar, desactivar) */
.ui-boton--peligro {
  background: var(--color-error);
  color: var(--color-sobre-primario);
  box-shadow: var(--sombra-boton);
}

.ui-boton--peligro:hover:not(:disabled) {
  background: color-mix(in srgb, var(--color-error) 88%, #000);
  transform: translateY(-1px);
}

.ui-boton--peligro:active:not(:disabled) {
  background: color-mix(in srgb, var(--color-error) 76%, #000);
  transform: translateY(0);
}

/* Secundario */
.ui-boton--secundario {
  background: var(--color-superficie);
  color: var(--color-activo-texto);
  border-color: var(--color-borde-control);
  box-shadow: var(--sombra-xs);
}

.ui-boton--secundario:hover:not(:disabled) {
  background: var(--color-acento-suave);
  border-color: var(--color-acento-fuerte);
}

.ui-boton--secundario:active:not(:disabled) {
  background: var(--color-acento);
}

/* Fantasma */
.ui-boton--fantasma {
  background: transparent;
  color: var(--color-activo-texto);
}

.ui-boton--fantasma:hover:not(:disabled) {
  background: var(--color-acento-suave);
}

.ui-boton--fantasma:active:not(:disabled) {
  background: var(--color-acento);
}

.ui-boton:disabled {
  opacity: 0.62;
  transform: none;
}

.ui-boton--cargando:disabled {
  opacity: 1;
  cursor: progress;
}

.ui-boton--primario.ui-boton--cargando:disabled {
  background: var(--color-primario-hover);
}
</style>
