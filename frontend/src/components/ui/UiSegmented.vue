<script setup lang="ts">
/**
 * Control segmentado = grupo de radios nativos (`role="radiogroup"`): flechas, Tab y lectores funcionan sin código extra.
 * `v-model` conserva el tipo (string | number). `etiqueta` nombra el grupo (obligatoria). La opción activa se
 * distingue por fondo + borde + peso + marca de verificación (no solo color).
 */
import { useId } from 'vue'
import UiIcon from './UiIcon.vue'
import type { NombreIcono } from './icons'

export interface OpcionSegmento {
  valor: string | number
  etiqueta: string
  icono?: NombreIcono
  deshabilitada?: boolean
}

withDefaults(
  defineProps<{
    opciones: OpcionSegmento[]
    etiqueta: string
    tamano?: 'sm' | 'md'
    bloque?: boolean
  }>(),
  { tamano: 'md', bloque: false },
)

const modelo = defineModel<string | number>({ required: true })
const nombre = `segmentado-${useId()}`
</script>

<template>
  <div class="ui-segmentado" :class="[`ui-segmentado--${tamano}`, { 'ui-segmentado--bloque': bloque }]" role="radiogroup" :aria-label="etiqueta">
    <label
      v-for="o in opciones"
      :key="String(o.valor)"
      class="ui-segmentado__opcion"
      :class="{ 'ui-segmentado__opcion--activa': o.valor === modelo, 'ui-segmentado__opcion--deshabilitada': o.deshabilitada }"
    >
      <input
        v-model="modelo"
        class="ui-segmentado__radio"
        type="radio"
        :name="nombre"
        :value="o.valor"
        :disabled="o.deshabilitada"
      />
      <UiIcon v-if="o.valor === modelo" nombre="check" :tamano="15" :grosor="2.6" class="ui-segmentado__check" />
      <UiIcon v-else-if="o.icono" :nombre="o.icono" :tamano="16" />
      <span>{{ o.etiqueta }}</span>
    </label>
  </div>
</template>

<style scoped>
.ui-segmentado {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 2px;
  padding: 3px;
  border: 1px solid var(--color-borde-control);
  border-radius: var(--radio-md);
  background: var(--color-superficie-2);
}

.ui-segmentado--bloque {
  display: flex;
}

.ui-segmentado--bloque .ui-segmentado__opcion {
  flex: 1;
}

.ui-segmentado__opcion {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  min-height: 2.5rem;
  padding: 0 var(--espacio-4);
  border: 1px solid transparent;
  border-radius: calc(var(--radio-md) - 3px);
  color: var(--color-texto-2);
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  white-space: nowrap;
  cursor: pointer;
  transition:
    background var(--trans),
    color var(--trans);
}

.ui-segmentado--sm .ui-segmentado__opcion {
  min-height: 2rem;
  padding: 0 var(--espacio-3);
  font-size: var(--texto-xs);
}

.ui-segmentado__opcion:hover:not(.ui-segmentado__opcion--activa):not(.ui-segmentado__opcion--deshabilitada) {
  background: var(--color-acento-suave);
  color: var(--color-activo-texto);
}

.ui-segmentado__opcion--activa {
  border-color: var(--color-primario);
  background: var(--color-superficie);
  color: var(--color-activo-texto);
  font-weight: var(--peso-fuerte);
  box-shadow: var(--sombra-sm);
}

.ui-segmentado__opcion--deshabilitada {
  opacity: 0.5;
  cursor: not-allowed;
}

.ui-segmentado__radio {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  opacity: 0;
  cursor: inherit;
}

/* El anillo de foco lo dibuja la etiqueta cuando el radio interno recibe foco por teclado */
.ui-segmentado__opcion:has(.ui-segmentado__radio:focus-visible) {
  outline: 2px solid var(--color-foco);
  outline-offset: 1px;
  box-shadow: 0 0 0 5px var(--color-foco-halo);
}
</style>
