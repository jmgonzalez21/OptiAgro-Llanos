<script setup lang="ts">
/**
 * Paginación: "Mostrando 1–10 de 42" (anunciado, `aria-live`), selector de filas y navegación con
 * `aria-current="page"`. `v-model:pagina` (desde 1) y `v-model:tamano`. No renderiza nada si `total` = 0.
 */
import { computed } from 'vue'
import UiIcon from './UiIcon.vue'
import UiSelect from './UiSelect.vue'
import { formatearNumero } from './formato'
import { paginasVisibles } from './paginacion'

const props = withDefaults(
  defineProps<{
    total: number
    opcionesTamano?: number[]
    id?: string
  }>(),
  { opcionesTamano: () => [10, 25, 50], id: 'paginacion' },
)

const pagina = defineModel<number>('pagina', { default: 1 })
const tamano = defineModel<number>('tamano', { default: 10 })

const totalPaginas = computed(() => Math.max(1, Math.ceil(props.total / tamano.value)))
const desde = computed(() => (props.total === 0 ? 0 : (pagina.value - 1) * tamano.value + 1))
const hasta = computed(() => Math.min(props.total, pagina.value * tamano.value))
const paginas = computed(() => paginasVisibles(pagina.value, totalPaginas.value))
const opciones = computed(() => props.opcionesTamano.map((n) => ({ valor: n, etiqueta: String(n) })))

function ir(n: number): void {
  pagina.value = Math.min(Math.max(1, n), totalPaginas.value)
}

function cambiarTamano(v: string | number | null): void {
  if (v === null) return
  tamano.value = Number(v)
  pagina.value = 1
}
</script>

<template>
  <div v-if="total > 0" class="ui-paginacion">
    <p class="ui-paginacion__resumen" aria-live="polite">
      Mostrando {{ formatearNumero(desde) }}–{{ formatearNumero(hasta) }} de {{ formatearNumero(total) }}
    </p>
    <div class="ui-paginacion__controles">
      <div class="ui-paginacion__filas">
        <UiSelect :id="`${id}-filas`" label="Filas por página" :opciones="opciones" :model-value="tamano" @update:model-value="cambiarTamano" />
      </div>
      <nav v-if="totalPaginas > 1" aria-label="Paginación">
        <ul class="ui-paginacion__lista">
          <li>
            <button type="button" class="ui-paginacion__boton" aria-label="Página anterior" :disabled="pagina <= 1" @click="ir(pagina - 1)">
              <UiIcon nombre="chevron-izq" :tamano="18" />
            </button>
          </li>
          <li v-for="(p, i) in paginas" :key="`${p}-${i}`">
            <span v-if="p === null" class="ui-paginacion__elipsis" aria-hidden="true">…</span>
            <button
              v-else
              type="button"
              class="ui-paginacion__boton"
              :class="{ 'ui-paginacion__boton--activo': p === pagina }"
              :aria-label="`Página ${p}`"
              :aria-current="p === pagina ? 'page' : undefined"
              @click="ir(p)"
            >
              {{ p }}
            </button>
          </li>
          <li>
            <button type="button" class="ui-paginacion__boton" aria-label="Página siguiente" :disabled="pagina >= totalPaginas" @click="ir(pagina + 1)">
              <UiIcon nombre="chevron-der" :tamano="18" />
            </button>
          </li>
        </ul>
      </nav>
    </div>
  </div>
</template>

<style scoped>
.ui-paginacion {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-3) var(--espacio-5);
  padding: var(--espacio-3) var(--espacio-4);
  border-top: 1px solid var(--color-borde);
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
}

.ui-paginacion__controles {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--espacio-4);
}

.ui-paginacion__filas {
  display: flex;
  align-items: center;
  gap: var(--espacio-2);
  min-width: 5.5rem;
}

.ui-paginacion__filas :deep(.ui-selector__entrada) {
  min-height: 2.5rem;
  font-size: var(--texto-sm);
}

.ui-paginacion__filas :deep(.ui-selector) {
  flex-direction: row;
  align-items: center;
}

.ui-paginacion__filas :deep(.ui-selector__etiqueta) {
  font-weight: var(--peso-medio);
  white-space: nowrap;
}

.ui-paginacion__lista {
  display: flex;
  align-items: center;
  gap: 2px;
}

.ui-paginacion__boton {
  display: inline-grid;
  place-items: center;
  min-width: 2.5rem;
  height: 2.5rem;
  padding: 0 0.4rem;
  border: 1px solid transparent;
  border-radius: var(--radio-sm);
  background: transparent;
  color: var(--color-texto);
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  font-variant-numeric: tabular-nums;
}

.ui-paginacion__boton:hover:not(:disabled):not(.ui-paginacion__boton--activo) {
  background: var(--color-acento-suave);
}

.ui-paginacion__boton--activo {
  border-color: var(--color-primario);
  background: var(--color-activo-fondo);
  color: var(--color-activo-texto);
  font-weight: var(--peso-fuerte);
}

.ui-paginacion__boton:disabled {
  opacity: 0.4;
}

.ui-paginacion__elipsis {
  display: inline-block;
  min-width: 1.5rem;
  text-align: center;
  color: var(--color-texto-suave);
}
</style>
