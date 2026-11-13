<script setup lang="ts">
/** Símbolo de estación (mismo dibujo que los marcadores del mapa): leyenda, listas, fichas. */
import { GLIFO_RUTAS, GLIFO_TRANSFORM, type TipoMarcador } from './marcadores'

withDefaults(defineProps<{ tipo: TipoMarcador; tamano?: number }>(), { tamano: 28 })
</script>

<template>
  <span class="marcador" :class="`marcador--${tipo}`">
    <svg class="marcador__svg" viewBox="0 0 40 40" :width="tamano" :height="tamano" aria-hidden="true" focusable="false">
      <circle v-if="tipo === 'empresa'" class="marcador__base" cx="20" cy="20" r="16" />
      <rect v-else class="marcador__base" x="3" y="3" width="34" height="34" rx="11" />
      <g class="marcador__glifo" :transform="GLIFO_TRANSFORM[tipo]" stroke-width="2.2">
        <path v-for="(d, i) in GLIFO_RUTAS[tipo]" :key="i" :d="d" />
      </g>
    </svg>
  </span>
</template>

<style scoped>
.marcador {
  display: inline-flex;
}
</style>
