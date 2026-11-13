<script setup lang="ts">
/**
 * Selector (<select> nativo con aspecto del sistema: máxima accesibilidad y teclado/móvil gratis).
 * `v-model` conserva el tipo original del valor (string o number). `placeholder` agrega una opción vacía (valor null).
 * `ocultarEtiqueta`: la etiqueta sigue asociada pero solo para lectores de pantalla (barras de filtros, "Filas por página").
 * Atributos extra (`name`, `disabled`, `@change`) pasan al <select>.
 */
import { computed } from 'vue'
import UiIcon from './UiIcon.vue'

defineOptions({ inheritAttrs: false })

export interface OpcionSelect {
  valor: string | number
  etiqueta: string
  deshabilitada?: boolean
}

const props = withDefaults(
  defineProps<{
    id: string
    label: string
    opciones: OpcionSelect[]
    placeholder?: string
    hint?: string
    error?: string
    ocultarEtiqueta?: boolean
  }>(),
  { placeholder: '', hint: '', error: '', ocultarEtiqueta: false },
)

const valor = defineModel<string | number | null>({ default: null })

const indice = computed<string>({
  get: () => {
    const i = props.opciones.findIndex((o) => o.valor === valor.value)
    return i >= 0 ? String(i) : ''
  },
  set: (v) => {
    valor.value = v === '' ? null : (props.opciones[Number(v)]?.valor ?? null)
  },
})

const describe = computed(() => {
  const ids = [props.hint ? `${props.id}-hint` : '', props.error ? `${props.id}-error` : ''].filter(Boolean)
  return ids.length ? ids.join(' ') : undefined
})
</script>

<template>
  <div class="ui-selector" :class="{ 'ui-selector--error': error }">
    <label :for="id" class="ui-selector__etiqueta" :class="{ 'sr-only': ocultarEtiqueta }">{{ label }}</label>
    <div class="ui-selector__control">
      <select
        :id="id"
        v-model="indice"
        class="ui-selector__entrada"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describe"
        v-bind="$attrs"
      >
        <option v-if="placeholder" value="">{{ placeholder }}</option>
        <option v-for="(o, i) in opciones" :key="String(o.valor)" :value="String(i)" :disabled="o.deshabilitada">{{ o.etiqueta }}</option>
      </select>
      <UiIcon nombre="chevron-abajo" :tamano="18" class="ui-selector__flecha" />
    </div>
    <p v-if="hint" :id="`${id}-hint`" class="ui-selector__ayuda">{{ hint }}</p>
    <p v-if="error" :id="`${id}-error`" class="ui-selector__error">
      <UiIcon nombre="alerta" :tamano="15" />
      <span>{{ error }}</span>
    </p>
  </div>
</template>

<style scoped>
.ui-selector {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  min-width: 0;
}

.ui-selector__etiqueta {
  font-size: var(--texto-sm);
  font-weight: var(--peso-fuerte);
  color: var(--color-texto);
}

.ui-selector__control {
  position: relative;
  display: flex;
  align-items: center;
}

.ui-selector__entrada {
  width: 100%;
  min-height: 3rem;
  padding: 0 2.5rem 0 0.9rem;
  border: 1px solid var(--color-borde-control);
  border-radius: var(--radio-md);
  background: var(--color-superficie);
  color: var(--color-texto);
  font-size: var(--texto-base);
  box-shadow: var(--sombra-xs);
  appearance: none;
  -webkit-appearance: none;
  text-overflow: ellipsis;
  transition:
    border-color var(--trans),
    box-shadow var(--trans);
}

.ui-selector__entrada:hover {
  border-color: var(--color-acento-fuerte);
}

.ui-selector__entrada:focus-visible {
  outline: none;
  border-color: var(--color-foco);
  box-shadow: 0 0 0 4px var(--color-foco-halo);
}

.ui-selector__entrada:disabled {
  color: var(--color-texto-suave);
  cursor: not-allowed;
  opacity: 0.75;
}

.ui-selector--error .ui-selector__entrada {
  border-color: var(--color-error);
  background: var(--color-error-fondo);
}

.ui-selector__flecha {
  position: absolute;
  right: 0.8rem;
  color: var(--color-texto-2);
  pointer-events: none;
}

.ui-selector__ayuda {
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
}

.ui-selector__error {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  color: var(--color-error);
}

.ui-selector__error :deep(.ui-icono) {
  margin-top: 0.15rem;
}
</style>
