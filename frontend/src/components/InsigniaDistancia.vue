<script setup lang="ts">
/** Distancia en km con insignia de origen: por carretera, estimada o manual (con explicación al pasar el cursor). */
import { computed } from 'vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import { formatearNumero } from '@/components/ui/formato'

export type FuenteDistancia = 'carretera' | 'estimada' | 'manual'

const props = defineProps<{ km: number | null | undefined; fuente?: FuenteDistancia | string | null; soloInsignia?: boolean }>()

const INFO: Record<string, { texto: string; tono: 'verde' | 'ambar' | 'neutro'; ayuda: string }> = {
  carretera: { texto: 'Por carretera', tono: 'verde', ayuda: 'Por carretera: calculada sobre las vías de OpenStreetMap.' },
  estimada: { texto: 'Estimada', tono: 'ambar', ayuda: 'Estimada: aproximación en línea recta × 1,3, porque el servicio de mapas no respondió. Puedes recalcularla.' },
  manual: { texto: 'Manual', tono: 'neutro', ayuda: 'Manual: la distancia fue ingresada a mano.' },
}
const info = computed(() => (props.fuente ? INFO[props.fuente] : undefined))
</script>

<template>
  <span class="distancia">
    <template v-if="!soloInsignia">{{ km === null || km === undefined ? '—' : `${formatearNumero(km, { maxDecimales: 1 })} km` }}</template>
    <UiBadge v-if="info && km !== null && km !== undefined" :tono="info.tono" :title="info.ayuda" :aria-label="info.ayuda">{{ info.texto }}</UiBadge>
  </span>
</template>

<style scoped>
.distancia {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 0.4rem;
}
</style>
