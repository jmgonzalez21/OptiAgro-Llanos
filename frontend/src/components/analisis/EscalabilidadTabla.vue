<script setup lang="ts">
/** Prueba de escalabilidad: redes de tamaño creciente, método exacto frente al algoritmo genético. */
import { computed } from 'vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import { formatearDuracion, formatearMoneda, formatearNumero, formatearPorcentaje } from '@/components/ui/formato'
import type { EscalabilidadResultado } from '@/types/fase2'

const props = defineProps<{ datos: EscalabilidadResultado }>()

const explicacion = computed(() => {
  const gaps = props.datos.tamanos.map((t) => t.gap_pct).filter((g): g is number => g !== null)
  if (gaps.length < 2) return 'Se comparan redes de distinto tamaño para ver cómo se comporta cada método.'
  const primero = gaps[0] as number
  const ultimo = gaps[gaps.length - 1] as number
  if (ultimo > primero + 0.5) return 'A mayor tamaño de red, el algoritmo genético se aleja más del costo óptimo y tarda más; el método exacto sigue siendo rápido y preciso.'
  return 'El algoritmo genético se mantiene cerca del costo óptimo aunque la red crezca, pero tarda mucho más que el método exacto.'
})
</script>

<template>
  <div class="vista__seccion">
    <UiAlert v-if="datos.ficticio" tono="info">Se usaron redes de ejemplo (ficticias): no se usa ni se modifica tu red guardada.</UiAlert>
    <p class="nota"><strong>{{ explicacion }}</strong></p>
    <div class="tabla-scroll">
      <table class="tabla">
        <caption class="sr-only">Escalabilidad: empresas por plantas</caption>
        <thead>
          <tr>
            <th scope="col">Tamaño de la red</th>
            <th scope="col" class="num">Costo exacto</th>
            <th scope="col" class="num">Costo algoritmo genético</th>
            <th scope="col" class="num">Por encima del óptimo</th>
            <th scope="col" class="num">Tiempo exacto</th>
            <th scope="col" class="num">Tiempo algoritmo genético</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="f in datos.tamanos" :key="`${f.empresas}x${f.plantas}`">
            <td>{{ f.empresas }} empresas × {{ f.plantas }} plantas <small class="nota">({{ formatearNumero(f.rutas) }} rutas)</small></td>
            <td class="num">{{ formatearMoneda(f.exacto.objetivo) }}</td>
            <td class="num">{{ formatearMoneda(f.genetico.objetivo) }}</td>
            <td class="num">{{ formatearPorcentaje(f.gap_pct, { decimales: 2 }) }}</td>
            <td class="num">{{ formatearDuracion(f.exacto.duracion_ms) }}</td>
            <td class="num">{{ formatearDuracion(f.genetico.duracion_ms) }}<small v-if="f.ratio_tiempo !== null" class="nota"> ({{ formatearNumero(f.ratio_tiempo, { maxDecimales: f.ratio_tiempo >= 10 ? 0 : 1 }) }} veces)</small></td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="nota">Tiempo total de la prueba: {{ formatearDuracion(datos.duracion_total_ms) }}.</p>
  </div>
</template>
