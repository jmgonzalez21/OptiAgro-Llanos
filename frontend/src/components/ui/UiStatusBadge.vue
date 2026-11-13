<script setup lang="ts">
/**
 * Estado de un cálculo. Ícono + texto en español (no solo color). Estados del contrato:
 * OPTIMAL -> "Óptimo", FEASIBLE -> "Solución factible", INFEASIBLE -> "Sin solución", ERROR -> "Error".
 * Otros conocidos: UNBOUNDED ("No acotado"), COMPLETED ("Completada"). Desconocidos: se muestra el valor tal cual (neutro).
 * `etiqueta` sustituye el texto.
 */
import { computed } from 'vue'
import UiBadge from './UiBadge.vue'
import UiIcon from './UiIcon.vue'
import type { NombreIcono } from './icons'

type Tono = 'neutro' | 'verde' | 'ambar' | 'info' | 'error'

const props = defineProps<{ estado: string; etiqueta?: string }>()

const CATALOGO: Record<string, { texto: string; tono: Tono; icono: NombreIcono }> = {
  OPTIMAL: { texto: 'Óptimo', tono: 'verde', icono: 'exito' },
  FEASIBLE: { texto: 'Solución factible', tono: 'info', icono: 'info' },
  INFEASIBLE: { texto: 'Sin solución', tono: 'ambar', icono: 'aviso' },
  ERROR: { texto: 'Error', tono: 'error', icono: 'alerta' },
  UNBOUNDED: { texto: 'No acotado', tono: 'ambar', icono: 'aviso' },
  COMPLETED: { texto: 'Completada', tono: 'verde', icono: 'exito' },
}

const info = computed(() => CATALOGO[props.estado.toUpperCase()] ?? { texto: props.estado, tono: 'neutro' as Tono, icono: 'info' as NombreIcono })
</script>

<template>
  <UiBadge :tono="info.tono" class="ui-estado" :data-estado="estado">
    <UiIcon :nombre="info.icono" :tamano="14" :grosor="2.2" />
    {{ etiqueta ?? info.texto }}
  </UiBadge>
</template>
