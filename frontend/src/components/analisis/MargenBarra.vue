<script setup lang="ts">
/** Barra simple: tramo verde = valores que no cambian el plan; marca = valor actual. Decorativa (el texto la acompaña). */
import { computed } from 'vue'

const props = defineProps<{ valor: number; minimo: number | null; maximo: number | null }>()

const tope = computed(() => Math.max(props.maximo ?? 0, props.valor * 2, 10) * (props.maximo === null ? 1 : 1.15))
const izq = computed(() => (Math.max(0, props.minimo ?? 0) / tope.value) * 100)
const der = computed(() => (Math.min(props.maximo ?? tope.value, tope.value) / tope.value) * 100)
const marca = computed(() => Math.min(100, (props.valor / tope.value) * 100))
</script>

<template>
  <div class="margen" aria-hidden="true">
    <span class="margen__tramo" :class="{ 'margen__tramo--abierto': maximo === null }" :style="{ left: `${izq}%`, width: `${Math.max(der - izq, 1)}%` }"></span>
    <span class="margen__marca" :style="{ left: `${marca}%` }"></span>
  </div>
</template>

<style scoped>
.margen {
  position: relative;
  height: 0.75rem;
  border-radius: var(--radio-pleno);
  background: var(--color-superficie-2);
  border: 1px solid var(--color-borde);
}

.margen__tramo {
  position: absolute;
  top: 0;
  bottom: 0;
  border-radius: var(--radio-pleno);
  background: var(--color-acento);
  border: 1px solid var(--color-activo-barra);
}

.margen__tramo--abierto {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

.margen__marca {
  position: absolute;
  top: -0.2rem;
  bottom: -0.2rem;
  width: 3px;
  margin-left: -1.5px;
  border-radius: 2px;
  background: var(--color-texto);
}
</style>
