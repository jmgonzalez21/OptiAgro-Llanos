<script setup lang="ts">
/** Avatar con iniciales (máx. 2). Decorativo: el nombre accesible lo da quien lo contiene. */
import { computed } from 'vue'

const props = withDefaults(defineProps<{ nombre: string; tamano?: number }>(), { tamano: 40 })

const iniciales = computed(() => {
  const partes = props.nombre.trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) return '?'
  const primera = partes[0] ?? ''
  const segunda = partes[1] ?? ''
  return (primera.charAt(0) + segunda.charAt(0)).toUpperCase()
})
</script>

<template>
  <span
    class="ui-avatar"
    :style="{ width: `${tamano}px`, height: `${tamano}px`, fontSize: `${Math.round(tamano * 0.38)}px` }"
    aria-hidden="true"
  >
    {{ iniciales }}
  </span>
</template>

<style scoped>
.ui-avatar {
  display: inline-grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 50%;
  background: linear-gradient(145deg, var(--color-acento) 0%, var(--color-acento-fuerte) 140%);
  color: var(--color-activo-texto);
  font-weight: var(--peso-fuerte);
  letter-spacing: 0.02em;
  box-shadow:
    inset 0 0 0 1px rgb(255 255 255 / 0.55),
    var(--sombra-xs);
  user-select: none;
}
</style>
