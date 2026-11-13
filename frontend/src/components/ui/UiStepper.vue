<script setup lang="ts">
/**
 * Indicador de pasos ("Paso 2 de 3 · Define las rutas"), para el flujo "Ampliar la red".
 * Lista ordenada con `aria-current="step"`; completado = check + texto "completado" (no solo color).
 * `pendientes` + `etiquetaPendientes` muestran un contador vivo ("Faltan 4 rutas por definir", `aria-live="polite"`).
 * Es solo indicador (no navega): los botones Atrás/Siguiente son del formulario.
 */
import { computed } from 'vue'
import UiIcon from './UiIcon.vue'

export interface PasoStepper {
  id: string
  titulo: string
  descripcion?: string
}

const props = defineProps<{
  pasos: PasoStepper[]
  /** Paso actual, desde 1. */
  actual: number
  pendientes?: number
  /** Texto tras el número en plural, p. ej. "rutas por definir". */
  etiquetaPendientes?: string
  etiqueta?: string
}>()

const tituloActual = computed(() => props.pasos[props.actual - 1]?.titulo ?? '')
const textoPendientes = computed(() => {
  if (props.pendientes === undefined || !props.etiquetaPendientes) return ''
  if (props.pendientes === 0) return 'No falta nada por definir'
  return `${props.pendientes === 1 ? 'Falta' : 'Faltan'} ${props.pendientes} ${props.etiquetaPendientes}`
})

function estado(i: number): 'completado' | 'activo' | 'pendiente' {
  const n = i + 1
  return n < props.actual ? 'completado' : n === props.actual ? 'activo' : 'pendiente'
}
</script>

<template>
  <div class="ui-pasos">
    <p class="ui-pasos__resumen">
      <strong>Paso {{ actual }} de {{ pasos.length }}</strong>
      <span v-if="tituloActual"> · {{ tituloActual }}</span>
    </p>
    <ol class="ui-pasos__lista" :aria-label="etiqueta ?? 'Pasos'">
      <li
        v-for="(p, i) in pasos"
        :key="p.id"
        class="ui-pasos__paso"
        :class="`ui-pasos__paso--${estado(i)}`"
        :aria-current="estado(i) === 'activo' ? 'step' : undefined"
      >
        <span class="ui-pasos__marca" aria-hidden="true">
          <UiIcon v-if="estado(i) === 'completado'" nombre="check" :tamano="14" :grosor="3" />
          <template v-else>{{ i + 1 }}</template>
        </span>
        <span class="ui-pasos__texto">
          {{ p.titulo }}
          <span v-if="estado(i) === 'completado'" class="sr-only"> (completado)</span>
          <span v-else-if="estado(i) === 'activo'" class="sr-only"> (paso actual)</span>
        </span>
      </li>
    </ol>
    <p v-if="textoPendientes" class="ui-pasos__pendientes" aria-live="polite">{{ textoPendientes }}</p>
  </div>
</template>

<style scoped>
.ui-pasos {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
}

.ui-pasos__resumen {
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
}

.ui-pasos__resumen strong {
  color: var(--color-texto);
}

.ui-pasos__lista {
  display: flex;
  gap: var(--espacio-2);
}

.ui-pasos__paso {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--espacio-1);
  min-width: 0;
  padding-top: var(--espacio-2);
  border-top: 3px solid var(--color-borde-fuerte);
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
}

.ui-pasos__paso--completado {
  border-top-color: var(--color-primario);
  color: var(--color-texto-2);
}

.ui-pasos__paso--activo {
  border-top-color: var(--color-activo-barra);
  color: var(--color-texto);
  font-weight: var(--peso-fuerte);
}

.ui-pasos__marca {
  display: inline-grid;
  place-items: center;
  width: 1.4rem;
  height: 1.4rem;
  border: 1.5px solid currentColor;
  border-radius: 50%;
  font-size: var(--texto-xs);
  font-weight: var(--peso-fuerte);
}

.ui-pasos__paso--completado .ui-pasos__marca {
  border-color: var(--color-primario);
  background: var(--color-primario);
  color: var(--color-sobre-primario);
}

.ui-pasos__paso--activo .ui-pasos__marca {
  border-color: var(--color-primario);
  background: var(--color-activo-fondo);
  color: var(--color-activo-texto);
}

.ui-pasos__pendientes {
  font-size: var(--texto-sm);
  font-weight: var(--peso-fuerte);
  color: var(--color-aviso);
}

@media (max-width: 30rem) {
  .ui-pasos__texto {
    display: none;
  }
}
</style>
