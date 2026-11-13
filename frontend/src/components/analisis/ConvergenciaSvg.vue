<script setup lang="ts">
/** Curva de convergencia del AG: mejor costo por generación (y promedio si existe), como polylines SVG. */
import { computed } from 'vue'
import { formatearMoneda } from '@/components/ui/formato'
import { puntosPolyline } from '@/composables/grafico'

const props = defineProps<{ mejor: number[]; promedio?: number[] }>()

const ANCHO = 600
const ALTO = 220

const rango = computed(() => {
  const todos = [...props.mejor, ...(props.promedio ?? [])]
  return { min: Math.min(...todos), max: Math.max(...todos) }
})
const puntosMejor = computed(() => puntosPolyline(props.mejor, ANCHO, ALTO, 12, rango.value))
const puntosPromedio = computed(() => puntosPolyline(props.promedio ?? [], ANCHO, ALTO, 12, rango.value))
const resumen = computed(
  () =>
    `Convergencia en ${props.mejor.length} generaciones: de ${formatearMoneda(props.mejor[0])} a ${formatearMoneda(props.mejor[props.mejor.length - 1])}.`,
)
</script>

<template>
  <figure v-if="mejor.length > 1">
    <svg class="grafico-linea" :viewBox="`0 0 ${ANCHO} ${ALTO}`" role="img" :aria-label="resumen">
      <polyline v-if="promedio?.length" :points="puntosPromedio" fill="none" stroke="var(--color-texto-suave)" stroke-width="1.5" stroke-dasharray="5 4" />
      <polyline :points="puntosMejor" fill="none" stroke="var(--color-primario)" stroke-width="2.5" stroke-linejoin="round" />
    </svg>
    <figcaption class="nota">
      {{ resumen }} Línea continua: mejor costo; línea punteada: costo promedio. Eje vertical de {{ formatearMoneda(rango.min) }} a
      {{ formatearMoneda(rango.max) }}.
    </figcaption>
  </figure>
</template>
