<script setup lang="ts">
/**
 * Tarjeta de métrica: etiqueta, valor grande con unidad, estado/insignia, nota de apoyo y variación.
 * - `valor` llega ya formateado (usa `formatearMoneda`, `formatearDuracion`, …) o como número (se formatea es-CO).
 *   null/undefined -> "—" (nunca 0 ni NaN, p. ej. en un resultado INFEASIBLE).
 * - `variacion` (número con signo, en `unidadVariacion`, por defecto %) muestra ▲/▼ + signo + texto; el color
 *   indica si es bueno o malo según `sentido` ('menor-es-mejor' para costos, 'mayor-es-mejor', 'neutro'), pero el
 *   sentido siempre se dice con flecha, signo y texto ("por encima del exacto").
 * - `cargando` muestra un esqueleto con la forma final (no mueve el layout).
 * Slots: `insignia` (p. ej. <UiStatusBadge/>), `nota`.
 */
import { computed, useId } from 'vue'
import UiSkeleton from './UiSkeleton.vue'
import { formatearConSigno, formatearNumero } from './formato'

const props = withDefaults(
  defineProps<{
    etiqueta: string
    valor?: string | number | null
    unidad?: string
    nota?: string
    variacion?: number | null
    unidadVariacion?: string
    /** Texto tras la variación: "vs. exacto", "respecto del caso base". */
    textoVariacion?: string
    sentido?: 'menor-es-mejor' | 'mayor-es-mejor' | 'neutro'
    cargando?: boolean
    destacada?: boolean
  }>(),
  {
    valor: null,
    unidad: '',
    nota: '',
    variacion: null,
    unidadVariacion: '%',
    textoVariacion: '',
    sentido: 'neutro',
    cargando: false,
    destacada: false,
  },
)

const idEtiqueta = `m-${useId()}`

const valorTexto = computed(() => {
  if (props.valor === null || props.valor === undefined || props.valor === '') return '—'
  return typeof props.valor === 'number' ? formatearNumero(props.valor, { maxDecimales: 2 }) : props.valor
})

const hayVariacion = computed(() => props.variacion !== null && props.variacion !== undefined && Number.isFinite(props.variacion))
const direccion = computed(() => ((props.variacion ?? 0) > 0 ? 'sube' : (props.variacion ?? 0) < 0 ? 'baja' : 'igual'))
const bueno = computed(() => {
  if (props.sentido === 'neutro' || direccion.value === 'igual') return null
  return props.sentido === 'menor-es-mejor' ? direccion.value === 'baja' : direccion.value === 'sube'
})
const variacionTexto = computed(() => {
  const n = formatearConSigno(props.variacion, { maxDecimales: 1 })
  return props.unidadVariacion === '%' ? `${n}\u202F%` : `${n} ${props.unidadVariacion}`
})
const variacionHablada = computed(() => {
  if (direccion.value === 'igual') return 'sin cambio'
  const abs = formatearNumero(Math.abs(props.variacion ?? 0), { maxDecimales: 1 })
  return `${direccion.value === 'sube' ? 'sube' : 'baja'} ${abs} ${props.unidadVariacion === '%' ? 'por ciento' : props.unidadVariacion}`
})
</script>

<template>
  <div class="ui-metrica" :class="{ 'ui-metrica--destacada': destacada }" role="group" :aria-labelledby="idEtiqueta">
    <p :id="idEtiqueta" class="ui-metrica__etiqueta">{{ etiqueta }}</p>
    <template v-if="cargando">
      <UiSkeleton ancho="70%" alto="2rem" />
      <span class="sr-only" role="status">Cargando {{ etiqueta }}…</span>
    </template>
    <template v-else>
      <p class="ui-metrica__valor">
        <span class="ui-metrica__numero">{{ valorTexto }}</span>
        <span v-if="unidad && valorTexto !== '—'" class="ui-metrica__unidad">{{ unidad }}</span>
      </p>
      <div v-if="$slots.insignia" class="ui-metrica__insignia"><slot name="insignia" /></div>
      <p
        v-if="hayVariacion"
        class="ui-metrica__variacion"
        :class="{ 'ui-metrica__variacion--bueno': bueno === true, 'ui-metrica__variacion--malo': bueno === false }"
      >
        <span aria-hidden="true">{{ direccion === 'sube' ? '▲' : direccion === 'baja' ? '▼' : '=' }}</span>
        <span class="ui-metrica__delta">{{ variacionTexto }}</span>
        <span v-if="textoVariacion" class="ui-metrica__texto-variacion">{{ textoVariacion }}</span>
        <span class="sr-only">({{ variacionHablada }}{{ textoVariacion ? ` ${textoVariacion}` : '' }})</span>
      </p>
      <p v-if="nota || $slots.nota" class="ui-metrica__nota"><slot name="nota">{{ nota }}</slot></p>
    </template>
  </div>
</template>

<style scoped>
.ui-metrica {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-1);
  min-width: 0;
  padding: var(--espacio-4);
  border: 1px solid var(--color-borde);
  border-radius: var(--radio-lg);
  background: var(--color-superficie);
  box-shadow: var(--sombra-xs);
}

.ui-metrica--destacada {
  border-color: var(--color-acento-fuerte);
  background: var(--color-acento-suave);
}

.ui-metrica__etiqueta {
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  color: var(--color-texto-2);
}

.ui-metrica__valor {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.35rem;
  line-height: 1.15;
}

.ui-metrica__numero {
  font-size: var(--texto-2xl);
  font-weight: var(--peso-fuerte);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  color: var(--color-texto);
  overflow-wrap: anywhere;
}

.ui-metrica__unidad {
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  color: var(--color-texto-2);
}

.ui-metrica__insignia {
  margin-top: var(--espacio-1);
}

.ui-metrica__variacion {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.35rem;
  font-size: var(--texto-sm);
  font-weight: var(--peso-fuerte);
  color: var(--color-texto-2);
}

.ui-metrica__variacion--bueno {
  color: var(--color-exito);
}

.ui-metrica__variacion--malo {
  color: var(--color-error);
}

.ui-metrica__delta {
  font-variant-numeric: tabular-nums;
}

.ui-metrica__texto-variacion {
  font-weight: var(--peso-normal);
  color: var(--color-texto-suave);
}

.ui-metrica__nota {
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
}
</style>
