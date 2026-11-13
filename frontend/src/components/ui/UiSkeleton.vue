<script setup lang="ts">
/** Esqueleto de carga (decorativo). */
withDefaults(defineProps<{ ancho?: string; alto?: string }>(), { ancho: '100%', alto: '1rem' })
</script>

<template>
  <span class="ui-esqueleto" :style="{ width: ancho, height: alto }" aria-hidden="true"></span>
</template>

<style scoped>
.ui-esqueleto {
  display: block;
  border-radius: var(--radio-sm);
  background: linear-gradient(90deg, var(--color-superficie-2) 25%, var(--color-acento-suave) 50%, var(--color-superficie-2) 75%);
  background-size: 200% 100%;
  animation: ui-brillo 1.6s linear infinite;
}
</style>
