<script setup lang="ts">
/** Indicador de carga decorativo. El texto accesible lo aporta quien lo usa (role="status"). */
withDefaults(defineProps<{ tamano?: number | string }>(), { tamano: 20 })
</script>

<template>
  <span class="ui-spinner" :style="{ width: `${tamano}px`, height: `${tamano}px` }" aria-hidden="true"></span>
</template>

<style scoped>
.ui-spinner {
  display: inline-block;
  flex-shrink: 0;
  border-radius: 50%;
  border: 2px solid color-mix(in srgb, currentColor 22%, transparent);
  border-top-color: currentColor;
  animation: ui-girar 0.75s linear infinite;
}
</style>
