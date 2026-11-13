<script setup lang="ts">
/** Ícono SVG inline (decorativo por defecto: `aria-hidden`). */
import { computed } from 'vue'
import { ICONOS, type NombreIcono } from './icons'

const props = withDefaults(
  defineProps<{
    nombre: NombreIcono
    tamano?: number | string
    grosor?: number | string
  }>(),
  { tamano: 20, grosor: 1.8 },
)

const rutas = computed(() => ICONOS[props.nombre])
</script>

<template>
  <svg
    class="ui-icono"
    :width="tamano"
    :height="tamano"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="grosor"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="(d, i) in rutas" :key="i" :d="d" />
  </svg>
</template>

<style scoped>
.ui-icono {
  display: inline-block;
  flex-shrink: 0;
  vertical-align: middle;
}
</style>
