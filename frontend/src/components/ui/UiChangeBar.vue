<script setup lang="ts">
/**
 * Barra fija de cambios sin guardar (matriz de costos): "● 3 cambios sin guardar" (`role="status"`),
 * Deshacer / Rehacer (con el nombre del paso), Descartar y Guardar (N). Se muestra solo con `cambios > 0`.
 * Eventos: `deshacer`, `rehacer`, `descartar`, `guardar`. Sticky al borde inferior del contenedor con scroll:
 * el contenedor de la cuadrícula debe tener `scroll-padding-bottom` ≥ alto de la barra (la UiEditableGrid ya lo hace).
 */
import { computed } from 'vue'
import UiButton from './UiButton.vue'
import UiIcon from './UiIcon.vue'

const props = withDefaults(
  defineProps<{
    cambios: number
    puedeDeshacer?: boolean
    puedeRehacer?: boolean
    etiquetaDeshacer?: string
    etiquetaRehacer?: string
    guardando?: boolean
  }>(),
  { puedeDeshacer: false, puedeRehacer: false, etiquetaDeshacer: '', etiquetaRehacer: '', guardando: false },
)

defineEmits<{ deshacer: []; rehacer: []; descartar: []; guardar: [] }>()

const texto = computed(() => `${props.cambios} ${props.cambios === 1 ? 'cambio' : 'cambios'} sin guardar`)
const nombreDeshacer = computed(() => (props.etiquetaDeshacer ? `Deshacer: ${props.etiquetaDeshacer}` : 'Deshacer'))
const nombreRehacer = computed(() => (props.etiquetaRehacer ? `Rehacer: ${props.etiquetaRehacer}` : 'Rehacer'))
</script>

<template>
  <div class="ui-cambios" :class="{ 'ui-cambios--oculta': cambios === 0 }">
    <p class="ui-cambios__estado" role="status">
      <template v-if="cambios > 0">
        <span class="ui-cambios__punto" aria-hidden="true"></span>
        {{ texto }}
      </template>
    </p>
    <div v-if="cambios > 0" class="ui-cambios__acciones">
      <UiButton variante="fantasma" tamano="sm" :disabled="!puedeDeshacer || guardando" :aria-label="nombreDeshacer" :title="nombreDeshacer" @click="$emit('deshacer')">
        <template #icono><UiIcon nombre="deshacer" :tamano="16" /></template>
        Deshacer
      </UiButton>
      <UiButton variante="fantasma" tamano="sm" :disabled="!puedeRehacer || guardando" :aria-label="nombreRehacer" :title="nombreRehacer" @click="$emit('rehacer')">
        <template #icono><UiIcon nombre="rehacer" :tamano="16" /></template>
        Rehacer
      </UiButton>
      <UiButton variante="secundario" tamano="sm" :disabled="guardando" @click="$emit('descartar')">Descartar</UiButton>
      <UiButton tamano="sm" :loading="guardando" @click="$emit('guardar')">Guardar cambios ({{ cambios }})</UiButton>
    </div>
  </div>
</template>

<style scoped>
.ui-cambios {
  position: sticky;
  bottom: 0;
  z-index: 5;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-2) var(--espacio-4);
  padding: var(--espacio-2) var(--espacio-4);
  border: 1px solid var(--color-aviso-borde);
  border-radius: var(--radio-md);
  background: var(--color-superficie);
  box-shadow: var(--sombra-lg);
}

.ui-cambios--oculta {
  display: none;
}

.ui-cambios__estado {
  display: flex;
  align-items: center;
  gap: var(--espacio-2);
  font-size: var(--texto-sm);
  font-weight: var(--peso-fuerte);
  color: var(--color-aviso);
}

.ui-cambios__punto {
  width: 0.6rem;
  height: 0.6rem;
  border-radius: 50%;
  background: currentColor;
}

.ui-cambios__acciones {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--espacio-2);
}
</style>
