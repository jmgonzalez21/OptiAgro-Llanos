<script setup lang="ts">
/**
 * Interruptor (`role="switch"`, `aria-checked`). `v-model` booleano. El texto (slot) es el nombre accesible.
 * `textoActivo`/`textoInactivo` muestran el estado en texto (no solo posición/color), p. ej. "Activa" / "Inactiva".
 */
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    textoActivo?: string
    textoInactivo?: string
    disabled?: boolean
    /** Descripción asociada (aria-describedby apuntando a un id externo). */
    describedby?: string
  }>(),
  { textoActivo: '', textoInactivo: '', disabled: false, describedby: undefined },
)

const activo = defineModel<boolean>({ default: false })
const estado = computed(() => (activo.value ? props.textoActivo : props.textoInactivo))

function alternar(): void {
  if (!props.disabled) activo.value = !activo.value
}
</script>

<template>
  <button
    type="button"
    class="ui-interruptor"
    :class="{ 'ui-interruptor--activo': activo }"
    role="switch"
    :aria-checked="activo"
    :aria-describedby="describedby"
    :disabled="disabled"
    @click="alternar"
  >
    <span class="ui-interruptor__pista" aria-hidden="true">
      <span class="ui-interruptor__pulgar">
        <svg v-if="activo" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
      </span>
    </span>
    <span class="ui-interruptor__texto"><slot /></span>
    <span v-if="estado" class="ui-interruptor__estado">{{ estado }}</span>
  </button>
</template>

<style scoped>
.ui-interruptor {
  display: inline-flex;
  align-items: center;
  gap: var(--espacio-3);
  min-height: var(--alto-tactil);
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-texto);
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  text-align: left;
}

.ui-interruptor__pista {
  position: relative;
  flex-shrink: 0;
  width: 2.75rem;
  height: 1.6rem;
  border: 1px solid var(--color-borde-control);
  border-radius: var(--radio-pleno);
  background: var(--color-superficie-2);
  transition:
    background var(--trans),
    border-color var(--trans);
}

.ui-interruptor__pulgar {
  position: absolute;
  top: 50%;
  left: 3px;
  display: grid;
  place-items: center;
  width: 1.2rem;
  height: 1.2rem;
  border-radius: 50%;
  background: var(--color-texto-2);
  color: var(--color-sobre-primario);
  transform: translateY(-50%);
  transition:
    transform var(--trans),
    background var(--trans);
}

.ui-interruptor--activo .ui-interruptor__pista {
  border-color: var(--color-primario);
  background: var(--color-primario);
}

.ui-interruptor--activo .ui-interruptor__pulgar {
  background: var(--color-sobre-primario);
  color: var(--color-primario);
  transform: translate(1.15rem, -50%);
}

.ui-interruptor__estado {
  color: var(--color-texto-2);
  font-weight: var(--peso-fuerte);
}

.ui-interruptor:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.ui-interruptor:focus-visible {
  outline-offset: 3px;
}
</style>
