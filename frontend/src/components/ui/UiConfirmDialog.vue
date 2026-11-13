<script setup lang="ts">
/**
 * Diálogo de confirmación (docs/ux/fase-2 §4.5). Foco inicial SIEMPRE en la opción segura (Cancelar).
 * - `tono="peligro"` -> `role="alertdialog"` y botón rojo; `normal` -> `role="dialog"`.
 * - `impacto`: lista de consecuencias (se anuncia como descripción).
 * - `codigoConfirmacion`: la persona debe escribir el código para habilitar el botón rojo (eliminar empresa/planta).
 * - `textoAlterno`: tercera opción ("Salir sin guardar"); el flujo de 3 opciones usa
 *   `textoConfirmar="Guardar y salir"`, `textoAlterno="Salir sin guardar"`, `textoCancelar="Seguir editando"`.
 * Emite: `confirmar`, `alterno`, `cancelar` (Esc, velo, ×, Cancelar) y `update:abierto`.
 * El padre cierra tras la acción (puede ser asíncrona: usa `cargando`).
 */
import { computed, ref, useId, watch } from 'vue'
import UiAlert from './UiAlert.vue'
import UiButton from './UiButton.vue'
import UiField from './UiField.vue'
import UiModal from './UiModal.vue'

const props = withDefaults(
  defineProps<{
    abierto: boolean
    titulo: string
    descripcion?: string
    impacto?: string[]
    aviso?: string
    tono?: 'normal' | 'peligro'
    textoConfirmar: string
    textoCancelar?: string
    textoAlterno?: string
    codigoConfirmacion?: string
    cargando?: boolean
  }>(),
  {
    descripcion: '',
    impacto: () => [],
    aviso: '',
    tono: 'normal',
    textoCancelar: 'Cancelar',
    textoAlterno: '',
    codigoConfirmacion: '',
    cargando: false,
  },
)

const emit = defineEmits<{
  confirmar: []
  alterno: []
  cancelar: []
  'update:abierto': [valor: boolean]
}>()

const idCodigo = `confirmar-${useId()}`
const codigo = ref('')

watch(
  () => props.abierto,
  (abierto) => {
    if (!abierto) codigo.value = ''
  },
)

const codigoValido = computed(
  () => props.codigoConfirmacion === '' || codigo.value.trim().toLowerCase() === props.codigoConfirmacion.toLowerCase(),
)

function alCerrar(): void {
  if (!props.cargando) emit('cancelar')
}

function cancelar(): void {
  emit('cancelar')
  emit('update:abierto', false)
}

function confirmar(): void {
  if (codigoValido.value && !props.cargando) emit('confirmar')
}
</script>

<template>
  <UiModal
    :abierto="abierto"
    :titulo="titulo"
    :rol="tono === 'peligro' ? 'alertdialog' : 'dialog'"
    ancho="sm"
    :cerrar-con-velo="tono !== 'peligro'"
    :bloquear-cierre="cargando"
    @cerrar="alCerrar"
    @update:abierto="emit('update:abierto', $event)"
  >
    <template v-if="descripcion || impacto.length" #descripcion>
      <template v-if="descripcion">{{ descripcion }}</template>
      <ul v-if="impacto.length" class="ui-confirmar__impacto">
        <li v-for="(linea, i) in impacto" :key="i">{{ linea }}</li>
      </ul>
    </template>

    <UiAlert v-if="aviso" tono="aviso">{{ aviso }}</UiAlert>
    <slot />

    <UiField
      v-if="codigoConfirmacion"
      :id="idCodigo"
      v-model="codigo"
      :label="`Para confirmar, escribe el código ${codigoConfirmacion}`"
      autocomplete="off"
      autocapitalize="off"
      spellcheck="false"
      @keydown.enter.prevent="confirmar"
    />

    <template #pie>
      <UiButton variante="secundario" data-autofocus :disabled="cargando" @click="cancelar">{{ textoCancelar }}</UiButton>
      <UiButton v-if="textoAlterno" variante="secundario" :disabled="cargando" @click="emit('alterno')">{{ textoAlterno }}</UiButton>
      <UiButton :variante="tono === 'peligro' ? 'peligro' : 'primario'" :disabled="!codigoValido" :loading="cargando" @click="confirmar">
        {{ textoConfirmar }}
      </UiButton>
    </template>
  </UiModal>
</template>

<style scoped>
.ui-confirmar__impacto {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
  margin-top: var(--espacio-2);
  padding-left: var(--espacio-4);
  list-style: disc;
}
</style>
