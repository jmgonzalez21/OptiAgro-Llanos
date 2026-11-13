<script setup lang="ts">
/**
 * Campo de contraseña con botón Mostrar/Ocultar (aria-pressed, aria-controls).
 * Sin límites de pegado; admite autocomplete del gestor de contraseñas (atributos pasan al <input>).
 */
import { ref } from 'vue'
import UiField from './UiField.vue'
import UiIcon from './UiIcon.vue'

defineProps<{ id: string; label: string; error?: string; hint?: string }>()

const valor = defineModel<string>({ default: '' })
const visible = ref(false)
const campo = ref<InstanceType<typeof UiField> | null>(null)

defineExpose({ focus: () => campo.value?.focus() })
</script>

<template>
  <UiField
    :id="id"
    ref="campo"
    v-model="valor"
    :label="label"
    :error="error"
    :hint="hint"
    icono="candado"
    :type="visible ? 'text' : 'password'"
  >
    <template #suffix>
      <button
        type="button"
        class="campo__alternar"
        :aria-pressed="visible"
        :aria-controls="id"
        @click="visible = !visible"
      >
        <UiIcon :nombre="visible ? 'ojo-tachado' : 'ojo'" :tamano="19" />
        <span class="sr-only">{{ visible ? 'Ocultar contraseña' : 'Mostrar contraseña' }}</span>
      </button>
    </template>
  </UiField>
</template>

<style scoped>
.campo__alternar {
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  margin-right: 0.25rem;
  padding: 0;
  border: 0;
  border-radius: var(--radio-sm);
  background: transparent;
  color: var(--color-texto-suave);
  transition:
    background var(--trans-rapida),
    color var(--trans-rapida);
}

.campo__alternar:hover {
  background: var(--color-acento-suave);
  color: var(--color-activo-texto);
}

.campo__alternar[aria-pressed='true'] {
  color: var(--color-activo-texto);
}
</style>
