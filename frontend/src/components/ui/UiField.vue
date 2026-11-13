<script setup lang="ts">
/**
 * Campo de texto con etiqueta visible, ayuda y error en línea.
 * - `id` es obligatorio (enlaza label/for y los ids de ayuda/error: `${id}-hint`, `${id}-error`).
 * - Los atributos no declarados (name, autocomplete, disabled, @blur, etc.) pasan al <input>.
 * - Slot `suffix`: contenido al final del control (p. ej. botón de mostrar contraseña).
 */
import { computed, ref } from 'vue'
import UiIcon from './UiIcon.vue'
import type { NombreIcono } from './icons'

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    id: string
    label: string
    type?: string
    hint?: string
    error?: string
    icono?: NombreIcono
  }>(),
  { type: 'text', hint: '', error: '', icono: undefined },
)

const valor = defineModel<string>({ default: '' })
const entrada = ref<HTMLInputElement | null>(null)

const idAyuda = computed(() => `${props.id}-hint`)
const idError = computed(() => `${props.id}-error`)
const describe = computed(() => {
  const ids = [props.hint ? idAyuda.value : '', props.error ? idError.value : ''].filter(Boolean)
  return ids.length ? ids.join(' ') : undefined
})

defineExpose({ focus: () => entrada.value?.focus(), entrada })
</script>

<template>
  <div class="ui-campo" :class="{ 'ui-campo--error': error }">
    <label :for="id" class="ui-campo__etiqueta">{{ label }}</label>
    <div class="ui-campo__control" :class="{ 'ui-campo__control--con-icono': icono }">
      <UiIcon v-if="icono" :nombre="icono" :tamano="18" class="ui-campo__icono" />
      <input
        :id="id"
        ref="entrada"
        v-model="valor"
        class="ui-campo__entrada"
        :type="type"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describe"
        v-bind="$attrs"
      />
      <slot name="suffix" />
    </div>
    <p v-if="hint" :id="idAyuda" class="ui-campo__ayuda">{{ hint }}</p>
    <p v-if="error" :id="idError" class="ui-campo__error">
      <UiIcon nombre="alerta" :tamano="15" />
      <span>{{ error }}</span>
    </p>
  </div>
</template>

<style scoped>
.ui-campo {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.ui-campo__etiqueta {
  font-size: var(--texto-sm);
  font-weight: var(--peso-fuerte);
  color: var(--color-texto);
}

.ui-campo__control {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 3rem;
  background: var(--color-superficie);
  border: 1px solid var(--color-borde-control);
  border-radius: var(--radio-md);
  box-shadow: var(--sombra-xs);
  transition:
    border-color var(--trans),
    box-shadow var(--trans),
    background var(--trans);
}

.ui-campo__control:hover {
  border-color: var(--color-acento-fuerte);
}

.ui-campo__control:focus-within {
  border-color: var(--color-foco);
  box-shadow: 0 0 0 4px var(--color-foco-halo);
}

.ui-campo--error .ui-campo__control {
  border-color: var(--color-error);
  background: var(--color-error-fondo);
}

.ui-campo--error .ui-campo__control:focus-within {
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-error) 22%, transparent);
}

.ui-campo__icono {
  margin-left: 0.9rem;
  color: var(--color-texto-suave);
}

.ui-campo__entrada {
  flex: 1;
  min-width: 0;
  min-height: 2.75rem;
  padding: 0 0.9rem;
  border: 0;
  background: transparent;
  color: var(--color-texto);
  font-size: var(--texto-base);
  box-shadow: none;
}

.ui-campo__control--con-icono .ui-campo__entrada {
  padding-left: 0.65rem;
}

/* El anillo de foco lo dibuja el contenedor (focus-within) */
.ui-campo__entrada:focus-visible {
  outline: none;
  box-shadow: none;
}

.ui-campo__entrada:disabled {
  color: var(--color-texto-suave);
  cursor: not-allowed;
}

.ui-campo__ayuda {
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
}

.ui-campo__error {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  color: var(--color-error);
  animation: ui-aparecer var(--trans) both;
}

.ui-campo__error :deep(.ui-icono) {
  margin-top: 0.15rem;
}
</style>
