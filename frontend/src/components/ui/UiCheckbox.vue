<script setup lang="ts">
/**
 * Casilla con etiqueta. Usa un <input type="checkbox"> real, estilizado; v-model booleano.
 * `etiqueta`: nombre accesible cuando no hay texto visible (casillas de tablas: "Seleccionar fila E1").
 * `indeterminado`: estado mixto (casilla de "seleccionar todas"), con guion además del color.
 */
import { ref, watchEffect } from 'vue'
import UiIcon from './UiIcon.vue'

const props = defineProps<{ id?: string; etiqueta?: string; indeterminado?: boolean; disabled?: boolean }>()
const marcado = defineModel<boolean>({ default: false })
const entrada = ref<HTMLInputElement | null>(null)

watchEffect(() => {
  if (entrada.value) entrada.value.indeterminate = !!props.indeterminado
})
</script>

<template>
  <label class="ui-casilla">
    <input
      :id="id"
      ref="entrada"
      v-model="marcado"
      class="ui-casilla__entrada"
      type="checkbox"
      :aria-label="etiqueta"
      :aria-checked="indeterminado ? 'mixed' : undefined"
      :disabled="disabled"
    />
    <span class="ui-casilla__caja" :class="{ 'ui-casilla__caja--mixta': indeterminado }" aria-hidden="true">
      <UiIcon :nombre="indeterminado ? 'menos' : 'check'" :tamano="14" :grosor="3" />
    </span>
    <span v-if="$slots.default" class="ui-casilla__texto"><slot /></span>
  </label>
</template>

<style scoped>
.ui-casilla {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: var(--espacio-2);
  min-height: 1.75rem;
  cursor: pointer;
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
}

.ui-casilla__entrada {
  position: absolute;
  opacity: 0;
  width: 1.25rem;
  height: 1.25rem;
  margin: 0;
}

.ui-casilla__caja {
  display: grid;
  place-items: center;
  width: 1.25rem;
  height: 1.25rem;
  border: 1.5px solid var(--color-borde-control);
  border-radius: 6px;
  background: var(--color-superficie);
  color: transparent;
  transition:
    background var(--trans),
    border-color var(--trans),
    color var(--trans);
}

.ui-casilla:hover .ui-casilla__caja {
  border-color: var(--color-acento-fuerte);
}

.ui-casilla__entrada:checked + .ui-casilla__caja,
.ui-casilla__caja--mixta {
  background: var(--color-primario);
  border-color: var(--color-primario);
  color: var(--color-sobre-primario);
}

.ui-casilla__entrada:disabled + .ui-casilla__caja {
  opacity: 0.45;
}

.ui-casilla__entrada:focus-visible + .ui-casilla__caja {
  outline: 2px solid var(--color-foco);
  outline-offset: 2px;
  box-shadow: 0 0 0 5px var(--color-foco-halo);
}
</style>
