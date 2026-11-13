<script setup lang="ts">
/** Reporte comparativo exacto vs algoritmo genético: veredicto, métricas, barras y detalle. */
import { computed } from 'vue'
import BarrasComparacion from './BarrasComparacion.vue'
import ConvergenciaSvg from './ConvergenciaSvg.vue'
import SensibilidadResultados from './SensibilidadResultados.vue'
import UsoPlantas from './UsoPlantas.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiCard from '@/components/ui/UiCard.vue'
import { formatearDuracion, formatearMoneda, formatearNumero, formatearPorcentaje } from '@/components/ui/formato'
import { etiquetaGap } from '@/composables/escenarios'
import type { ReporteResultado } from '@/types/fase2'

const props = defineProps<{ datos: ReporteResultado }>()

const ambosFactibles = computed(() => props.datos.exacto.factible && props.datos.genetico.factible)
const gap = computed(() => props.datos.comparacion.gap_pct)
const etiqueta = computed(() => etiquetaGap(gap.value))

const veces = (n: number): string => formatearNumero(n, { maxDecimales: n >= 10 ? 0 : 1 })

const veredicto = computed(() => {
  const g = gap.value
  const r = props.datos.comparacion.ratio_tiempo
  const costo = g === null ? 'encontró una solución' : g < 0.05 ? 'igualó el costo óptimo' : `quedó a solo ${formatearNumero(g, { maxDecimales: 1 })} % por encima del costo óptimo`
  let tiempo = ''
  if (r !== null && Number.isFinite(r)) {
    if (r >= 1.5) tiempo = `, pero tardó ${veces(r)} veces más`
    else if (r <= 0.67) tiempo = `, y además fue ${veces(1 / r)} veces más rápido`
    else tiempo = ', y tardó un tiempo parecido'
  }
  return `El algoritmo genético ${costo}${tiempo}.`
})

const itemsCosto = computed(() => [
  { etiqueta: 'Método exacto', valor: props.datos.exacto.objetivo ?? 0, texto: formatearMoneda(props.datos.exacto.objetivo) },
  { etiqueta: 'Algoritmo genético', valor: props.datos.genetico.objetivo ?? 0, texto: formatearMoneda(props.datos.genetico.objetivo) },
])
const itemsTiempo = computed(() => [
  { etiqueta: 'Método exacto', valor: props.datos.exacto.duracion_ms, texto: formatearDuracion(props.datos.exacto.duracion_ms) },
  { etiqueta: 'Algoritmo genético', valor: props.datos.genetico.duracion_ms, texto: formatearDuracion(props.datos.genetico.duracion_ms) },
])
const uso = computed(() => props.datos.plantas.map((p) => ({ nombre: p.nombre, usado: p.flujo, capacidad: p.capacidad })))
</script>

<template>
  <div class="vista__seccion reporte">
    <p class="nota">
      Red analizada: {{ datos.modelo.empresas }} empresas, {{ datos.modelo.plantas }} plantas y {{ datos.modelo.rutas }} rutas; se generan
      {{ formatearNumero(datos.modelo.oferta_total, { maxDecimales: 1 }) }} t por semana y las plantas reciben hasta
      {{ formatearNumero(datos.modelo.capacidad_total, { maxDecimales: 1 }) }} t.
    </p>

    <UiAlert v-if="!ambosFactibles" tono="aviso" titulo="No se pudo comparar">
      Alguno de los dos métodos no encontró una distribución posible con los datos actuales. Revisa que las plantas alcancen a recibir toda la oferta.
    </UiAlert>

    <template v-else>
      <UiCard variante="elevada" relleno="lg" class="veredicto">
        <UiBadge v-if="etiqueta" :tono="etiqueta.tono" punto>{{ etiqueta.texto }}</UiBadge>
        <p class="veredicto__frase">{{ veredicto }}</p>
        <p class="nota">
          <strong>Excelente</strong>: hasta 1 % sobre el óptimo · <strong>Aceptable</strong>: de 1 % a 5 % · <strong>Mejorable</strong>: más de 5 %.
          El método exacto siempre encuentra el menor costo posible; el algoritmo genético es una búsqueda aproximada.
        </p>
      </UiCard>

      <div class="kpis">
        <div class="kpi">
          <span class="kpi__etiqueta">Costo con el método exacto</span>
          <span class="kpi__valor">{{ formatearMoneda(datos.exacto.objetivo) }}</span>
        </div>
        <div class="kpi">
          <span class="kpi__etiqueta">Costo con el algoritmo genético</span>
          <span class="kpi__valor">{{ formatearMoneda(datos.genetico.objetivo) }}</span>
        </div>
        <div class="kpi">
          <span class="kpi__etiqueta">Diferencia de costo</span>
          <span class="kpi__valor">{{ formatearMoneda(datos.comparacion.diferencia_costo) }}</span>
          <span class="nota">{{ formatearPorcentaje(gap, { decimales: 2 }) }} sobre el óptimo</span>
        </div>
        <div class="kpi">
          <span class="kpi__etiqueta">Tiempo del método exacto</span>
          <span class="kpi__valor">{{ formatearDuracion(datos.exacto.duracion_ms) }}</span>
        </div>
        <div class="kpi">
          <span class="kpi__etiqueta">Tiempo del algoritmo genético</span>
          <span class="kpi__valor">{{ formatearDuracion(datos.genetico.duracion_ms) }}</span>
        </div>
      </div>

      <UiCard class="imprimir-bloque">
        <BarrasComparacion titulo="Costo semanal (COP): más corto es mejor" :items="itemsCosto" />
        <BarrasComparacion titulo="Tiempo de cálculo: más corto es mejor" :items="itemsTiempo" />
      </UiCard>

      <details v-if="(datos.genetico.convergencia?.length ?? 0) > 1" class="avanzadas">
        <summary>Cómo evolucionó el cálculo</summary>
        <p class="nota">Cada punto es una ronda de búsqueda del algoritmo genético; la línea baja a medida que encuentra distribuciones más baratas.</p>
        <ConvergenciaSvg :mejor="datos.genetico.convergencia ?? []" :promedio="datos.genetico.convergencia_promedio" />
      </details>

      <UiCard class="imprimir-bloque">
        <h2>Uso de las plantas con la mejor distribución</h2>
        <UsoPlantas :plantas="uso" />
      </UiCard>
    </template>

    <template v-if="datos.sensibilidad">
      <h2 class="imprimir-salto">¿Qué pasa si…? Comportamiento ante cambios</h2>
      <SensibilidadResultados :datos="datos.sensibilidad" />
    </template>
  </div>
</template>

<style scoped>
.reporte h2 {
  font-size: var(--texto-lg);
}

.veredicto {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--espacio-3);
}

.veredicto__frase {
  font-size: var(--texto-xl);
  font-weight: var(--peso-fuerte);
  letter-spacing: -0.02em;
}

.reporte :deep(.ui-tarjeta) > * + * {
  margin-top: var(--espacio-4);
}

.kpi .nota {
  display: block;
}
</style>
