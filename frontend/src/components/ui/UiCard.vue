<script setup lang="ts">
/** Tarjeta. Variantes: `plana` (borde fino), `elevada` (sombra suave) y `vidrio` (translúcida, sobre el mapa). */
withDefaults(
  defineProps<{
    variante?: 'plana' | 'elevada' | 'vidrio'
    relleno?: 'ninguno' | 'sm' | 'md' | 'lg'
    como?: string
  }>(),
  { variante: 'plana', relleno: 'md', como: 'div' },
)
</script>

<template>
  <component :is="como" class="ui-tarjeta" :class="[`ui-tarjeta--${variante}`, `ui-tarjeta--relleno-${relleno}`]">
    <slot />
  </component>
</template>

<style scoped>
.ui-tarjeta {
  background: var(--color-superficie);
  border: 1px solid var(--color-borde);
  border-radius: var(--radio-lg);
}

.ui-tarjeta--elevada {
  border-color: transparent;
  box-shadow: var(--sombra-lg);
}

.ui-tarjeta--vidrio {
  background: var(--color-vidrio);
  border-color: var(--color-vidrio-borde);
  backdrop-filter: blur(14px) saturate(1.4);
  -webkit-backdrop-filter: blur(14px) saturate(1.4);
  box-shadow:
    0 10px 28px -10px var(--color-vidrio-sombra),
    var(--sombra-xs);
}

.ui-tarjeta--relleno-sm {
  padding: var(--espacio-3);
}

.ui-tarjeta--relleno-md {
  padding: var(--espacio-4);
}

.ui-tarjeta--relleno-lg {
  padding: var(--espacio-6);
}
</style>
