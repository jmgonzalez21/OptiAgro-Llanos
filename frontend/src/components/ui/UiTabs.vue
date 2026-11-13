<script setup lang="ts">
/**
 * Pestañas (WAI-ARIA tabs, activación automática). Flechas ←/→, Inicio/Fin; roving tabindex.
 * - `v-model`: id de la pestaña activa (el padre puede sincronizarlo con `?tab=` de la URL).
 * - Paneles: slot `panel-<id>` o, si no existe, el slot por defecto con `{ activa }`.
 * - `conservar`: mantiene montados todos los paneles (v-show) para no perder estado interno (búsqueda, filtros).
 * - Slot `tab` ({ tab, activa }) personaliza el contenido de cada pestaña.
 */
import { computed, nextTick, useId } from 'vue'
import UiBadge from './UiBadge.vue'

export interface PestanaItem {
  id: string
  etiqueta: string
  /** Conteo visible en la pestaña ("Empresas 10"). */
  conteo?: number
  deshabilitada?: boolean
}

const props = withDefaults(
  defineProps<{
    pestanas: PestanaItem[]
    /** Nombre accesible de la lista de pestañas. */
    etiqueta: string
    conservar?: boolean
  }>(),
  { conservar: false },
)

const activa = defineModel<string>({ required: true })
const base = useId()

const idTab = (id: string): string => `${base}-tab-${id}`
const idPanel = (id: string): string => `${base}-panel-${id}`
const habilitadas = computed(() => props.pestanas.filter((p) => !p.deshabilitada))

function activar(id: string, enfocar = false): void {
  activa.value = id
  if (enfocar) {
    void nextTick(() => document.getElementById(idTab(id))?.focus())
  }
}

function alTeclado(ev: KeyboardEvent): void {
  const lista = habilitadas.value
  if (lista.length === 0) return
  const i = lista.findIndex((p) => p.id === activa.value)
  let destino: number | null = null
  if (ev.key === 'ArrowRight') destino = (i + 1) % lista.length
  else if (ev.key === 'ArrowLeft') destino = (i - 1 + lista.length) % lista.length
  else if (ev.key === 'Home') destino = 0
  else if (ev.key === 'End') destino = lista.length - 1
  if (destino === null) return
  ev.preventDefault()
  activar(lista[destino]!.id, true)
}
</script>

<template>
  <div class="ui-tabs">
    <div class="ui-tabs__lista" role="tablist" :aria-label="etiqueta" @keydown="alTeclado">
      <button
        v-for="p in pestanas"
        :id="idTab(p.id)"
        :key="p.id"
        type="button"
        role="tab"
        class="ui-tabs__tab"
        :class="{ 'ui-tabs__tab--activa': p.id === activa }"
        :aria-selected="p.id === activa"
        :aria-controls="idPanel(p.id)"
        :tabindex="p.id === activa ? 0 : -1"
        :disabled="p.deshabilitada"
        @click="activar(p.id)"
      >
        <slot name="tab" :tab="p" :activa="p.id === activa">
          <span>{{ p.etiqueta }}</span>
          <UiBadge v-if="p.conteo !== undefined" :tono="p.id === activa ? 'verde' : 'neutro'" class="ui-tabs__conteo">{{ p.conteo }}</UiBadge>
        </slot>
      </button>
    </div>

    <template v-for="p in pestanas" :key="p.id">
      <div
        v-if="conservar || p.id === activa"
        v-show="p.id === activa"
        :id="idPanel(p.id)"
        class="ui-tabs__panel"
        role="tabpanel"
        :aria-labelledby="idTab(p.id)"
        tabindex="0"
      >
        <slot :name="`panel-${p.id}`" :activa="p.id === activa">
          <slot :activa="p.id === activa" :pestana="p" />
        </slot>
      </div>
    </template>
  </div>
</template>

<style scoped>
.ui-tabs__lista {
  display: flex;
  gap: var(--espacio-1);
  overflow-x: auto;
  border-bottom: 1px solid var(--color-borde-fuerte);
}

.ui-tabs__tab {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: var(--espacio-2);
  min-height: var(--alto-tactil);
  padding: 0 var(--espacio-4);
  border: 0;
  border-radius: var(--radio-sm) var(--radio-sm) 0 0;
  background: transparent;
  color: var(--color-texto-2);
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  white-space: nowrap;
  transition:
    background var(--trans),
    color var(--trans);
}

.ui-tabs__tab::after {
  content: '';
  position: absolute;
  inset: auto var(--espacio-3) -1px;
  height: 3px;
  border-radius: 3px 3px 0 0;
  background: transparent;
  transition: background var(--trans);
}

.ui-tabs__tab:hover:not(:disabled) {
  background: var(--color-acento-suave);
  color: var(--color-activo-texto);
}

.ui-tabs__tab--activa {
  color: var(--color-activo-texto);
  font-weight: var(--peso-fuerte);
}

.ui-tabs__tab--activa::after {
  background: var(--color-activo-barra);
}

.ui-tabs__tab:disabled {
  opacity: 0.5;
}

.ui-tabs__tab:focus-visible {
  outline-offset: -2px;
}

.ui-tabs__panel {
  padding-top: var(--espacio-4);
}

.ui-tabs__panel:focus-visible {
  outline-offset: 2px;
}
</style>
