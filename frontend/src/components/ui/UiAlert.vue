<script setup lang="ts">
/**
 * Alerta en línea. Siempre con ícono + texto (no depende solo del color).
 * `error` usa role="alert"; los demás tonos usan role="status". Expone `focus()`.
 */
import { computed, ref } from 'vue'
import UiIcon from './UiIcon.vue'
import type { NombreIcono } from './icons'

const props = withDefaults(
  defineProps<{
    tono?: 'error' | 'aviso' | 'info' | 'exito'
    titulo?: string
    rol?: 'alert' | 'status'
  }>(),
  { tono: 'info', titulo: '', rol: undefined },
)

const ICONOS_TONO: Record<'error' | 'aviso' | 'info' | 'exito', NombreIcono> = {
  error: 'alerta',
  aviso: 'aviso',
  info: 'info',
  exito: 'exito',
}

const rolEfectivo = computed(() => props.rol ?? (props.tono === 'error' ? 'alert' : 'status'))
const raiz = ref<HTMLElement | null>(null)

defineExpose({ focus: () => raiz.value?.focus() })
</script>

<template>
  <div ref="raiz" class="ui-alerta" :class="`ui-alerta--${tono}`" :role="rolEfectivo" tabindex="-1">
    <UiIcon :nombre="ICONOS_TONO[tono]" :tamano="20" class="ui-alerta__icono" />
    <div class="ui-alerta__cuerpo">
      <p v-if="titulo" class="ui-alerta__titulo">{{ titulo }}</p>
      <div class="ui-alerta__texto"><slot /></div>
      <div v-if="$slots.acciones" class="ui-alerta__acciones"><slot name="acciones" /></div>
    </div>
  </div>
</template>

<style scoped>
.ui-alerta {
  display: flex;
  gap: var(--espacio-3);
  padding: 0.85rem var(--espacio-4);
  border: 1px solid var(--borde);
  border-radius: var(--radio-md);
  background: var(--fondo);
  color: var(--texto);
  font-size: var(--texto-sm);
  line-height: 1.45;
  animation: ui-aparecer var(--trans-lenta) both;
}

.ui-alerta:focus-visible {
  outline: 2px solid var(--texto);
  outline-offset: 2px;
  box-shadow: none;
}

.ui-alerta--error {
  --fondo: var(--color-error-fondo);
  --borde: var(--color-error-borde);
  --texto: var(--color-error);
}

.ui-alerta--aviso {
  --fondo: var(--color-aviso-fondo);
  --borde: var(--color-aviso-borde);
  --texto: var(--color-aviso);
}

.ui-alerta--info {
  --fondo: var(--color-info-fondo);
  --borde: var(--color-info-borde);
  --texto: var(--color-info);
}

.ui-alerta--exito {
  --fondo: var(--color-exito-fondo);
  --borde: var(--color-exito-borde);
  --texto: var(--color-exito);
}

.ui-alerta__icono {
  margin-top: 0.1rem;
}

.ui-alerta__cuerpo {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.ui-alerta__titulo {
  font-weight: var(--peso-fuerte);
}

.ui-alerta__texto {
  font-weight: var(--peso-medio);
}

.ui-alerta__acciones {
  margin-top: var(--espacio-2);
}
</style>
