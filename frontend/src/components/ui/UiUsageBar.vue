<script setup lang="ts">
/**
 * Barra de uso (%) para la capacidad de plantas. El porcentaje SIEMPRE va en texto; la barra es redundante
 * (`role="meter"` con valor y rango). `critico` marca "Cuello de botella" (ícono + texto, no solo color).
 * Pasa `valor` y `maximo` (mismas unidades) o `porcentaje` directo.
 */
import { computed } from 'vue'
import UiIcon from './UiIcon.vue'
import { formatearPorcentaje } from './formato'

const props = withDefaults(
  defineProps<{
    etiqueta: string
    valor?: number
    maximo?: number
    porcentaje?: number
    /** Marca la barra como llena/limitante: "Cuello de botella". */
    critico?: boolean
    textoCritico?: string
  }>(),
  { valor: 0, maximo: 0, porcentaje: undefined, critico: false, textoCritico: 'Cuello de botella' },
)

const pct = computed(() => {
  const p = props.porcentaje ?? (props.maximo > 0 ? (props.valor / props.maximo) * 100 : 0)
  return Math.max(0, Math.min(100, p))
})
</script>

<template>
  <div class="ui-uso">
    <div
      class="ui-uso__pista"
      role="meter"
      :aria-label="etiqueta"
      aria-valuemin="0"
      aria-valuemax="100"
      :aria-valuenow="Math.round(pct)"
      :aria-valuetext="`${formatearPorcentaje(pct, { maxDecimales: 0 })}${critico ? `, ${textoCritico}` : ''}`"
    >
      <span class="ui-uso__relleno" :class="{ 'ui-uso__relleno--critico': critico }" :style="{ width: `${pct}%` }"></span>
    </div>
    <span class="ui-uso__texto">{{ formatearPorcentaje(pct, { maxDecimales: 0 }) }}</span>
    <span v-if="critico" class="ui-uso__critico"><UiIcon nombre="aviso" :tamano="14" :grosor="2.2" />{{ textoCritico }}</span>
  </div>
</template>

<style scoped>
.ui-uso {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--espacio-2);
}

.ui-uso__pista {
  flex: 1 1 5rem;
  min-width: 5rem;
  height: 0.65rem;
  overflow: hidden;
  border: 1px solid var(--color-borde-control);
  border-radius: var(--radio-pleno);
  background: var(--color-superficie-2);
}

.ui-uso__relleno {
  display: block;
  height: 100%;
  border-radius: var(--radio-pleno);
  background: var(--color-primario);
  transition: width var(--trans-lenta);
}

/* Cuello de botella: relleno a rayas (patrón, no solo color) */
.ui-uso__relleno--critico {
  background: repeating-linear-gradient(135deg, var(--color-aviso) 0 5px, color-mix(in srgb, var(--color-aviso) 55%, var(--color-superficie)) 5px 9px);
}

.ui-uso__texto {
  min-width: 2.75rem;
  font-size: var(--texto-sm);
  font-weight: var(--peso-fuerte);
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.ui-uso__critico {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.1rem 0.55rem;
  border: 1px solid var(--color-aviso-borde);
  border-radius: var(--radio-pleno);
  background: var(--color-aviso-fondo);
  color: var(--color-aviso);
  font-size: var(--texto-xs);
  font-weight: var(--peso-fuerte);
  white-space: nowrap;
}
</style>
