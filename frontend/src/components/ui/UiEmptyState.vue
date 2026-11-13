<script setup lang="ts">
/** Estado vacío / error / sin resultados: ícono, título, descripción y acciones (slot). */
import UiIcon from './UiIcon.vue'
import type { NombreIcono } from './icons'

withDefaults(
  defineProps<{
    icono?: NombreIcono
    titulo: string
    descripcion?: string
    tono?: 'neutro' | 'error'
  }>(),
  { icono: 'mapa', descripcion: '', tono: 'neutro' },
)
</script>

<template>
  <div class="ui-vacio" :class="`ui-vacio--${tono}`">
    <span class="ui-vacio__icono"><UiIcon :nombre="icono" :tamano="26" /></span>
    <p class="ui-vacio__titulo">{{ titulo }}</p>
    <p v-if="descripcion" class="ui-vacio__descripcion">{{ descripcion }}</p>
    <div v-if="$slots.default" class="ui-vacio__acciones"><slot /></div>
  </div>
</template>

<style scoped>
.ui-vacio {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--espacio-2);
  padding: var(--espacio-5);
  text-align: center;
}

.ui-vacio__icono {
  display: grid;
  place-items: center;
  width: 3.5rem;
  height: 3.5rem;
  margin-bottom: var(--espacio-2);
  border-radius: 50%;
  background: var(--color-activo-fondo);
  color: var(--color-activo-texto);
  box-shadow: 0 0 0 8px color-mix(in srgb, var(--color-acento) 45%, transparent);
}

.ui-vacio--error .ui-vacio__icono {
  background: var(--color-error-fondo);
  color: var(--color-error);
  box-shadow: 0 0 0 8px color-mix(in srgb, var(--color-error-borde) 45%, transparent);
}

.ui-vacio__titulo {
  font-size: var(--texto-lg);
  font-weight: var(--peso-fuerte);
  color: var(--color-texto);
}

.ui-vacio__descripcion {
  max-width: 26rem;
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
}

.ui-vacio__acciones {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--espacio-2);
  margin-top: var(--espacio-3);
}
</style>
