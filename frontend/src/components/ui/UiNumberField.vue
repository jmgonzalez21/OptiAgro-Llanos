<script setup lang="ts">
/**
 * Campo numérico es-CO. Acepta `12500`, `12.500`, `12.500,5`; rechaza `1.5` ("Usa coma para decimales…").
 * `v-model` es `number | null` (null = vacío). Mientras se escribe emite el número si es válido; al salir
 * del campo vuelve a formatear (`1.250,5`) y valida rango/entero/obligatorio.
 * - `unidad`: sufijo visible ("t/semana", "COP/t"). `decimales`: máximo al formatear (por defecto 2; 0 = entero).
 * - `min`/`max`: rango (mensaje "Debe estar entre …"; con min >= 0: "No puede ser negativo."). `estricto`: min exclusivo ("debe ser mayor que").
 * - `error` externo (servidor) tiene prioridad sobre el interno. Emite `invalido(mensaje | null)` para que el padre sepa si puede enviar.
 * - Expone `focus()`, `validar()` (devuelve true/false y muestra el error: úsalo al enviar el formulario).
 */
import { computed, ref, useAttrs, watch } from 'vue'
import UiField from './UiField.vue'
import { formatearNumero, leerNumero } from './formato'

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    id: string
    label: string
    unidad?: string
    decimales?: number
    min?: number
    max?: number
    estricto?: boolean
    requerido?: boolean
    hint?: string
    error?: string
    /** Texto del mensaje para valores < min, p. ej. "La oferta debe ser mayor que 0 t/semana." */
    mensajeMin?: string
  }>(),
  { unidad: '', decimales: 2, min: undefined, max: undefined, estricto: false, requerido: false, hint: '', error: '', mensajeMin: '' },
)

const valor = defineModel<number | null>({ default: null })
const emit = defineEmits<{ invalido: [mensaje: string | null] }>()

const texto = ref(valor.value === null ? '' : formatearNumero(valor.value, { maxDecimales: props.decimales }))
const errorInterno = ref('')
const campo = ref<InstanceType<typeof UiField> | null>(null)
let editando = false

// Cambios externos del modelo (reset, carga) se reflejan, salvo mientras se escribe.
watch(valor, (nuevo) => {
  if (editando) return
  texto.value = nuevo === null ? '' : formatearNumero(nuevo, { maxDecimales: props.decimales })
})

function evaluar(t: string): { error: string; valor: number | null } {
  const lectura = leerNumero(t)
  if (!lectura.ok) return { error: lectura.error, valor: null }
  const v = lectura.valor
  if (v === null) return { error: props.requerido ? 'Ingresa un valor.' : '', valor: null }
  if (props.decimales === 0 && !Number.isInteger(v)) return { error: 'Usa un número entero.', valor: null }
  const { min, max } = props
  if (min !== undefined && (props.estricto ? v <= min : v < min)) {
    if (props.mensajeMin) return { error: props.mensajeMin, valor: null }
    if (props.estricto) return { error: `Debe ser mayor que ${formatearNumero(min, { maxDecimales: props.decimales })}.`, valor: null }
    return { error: min === 0 ? 'No puede ser negativo.' : `Debe ser al menos ${formatearNumero(min, { maxDecimales: props.decimales })}.`, valor: null }
  }
  if (max !== undefined && v > max) {
    return {
      error: min !== undefined ? `Debe estar entre ${formatearNumero(min, { maxDecimales: props.decimales })} y ${formatearNumero(max, { maxDecimales: props.decimales })}.` : `No puede superar ${formatearNumero(max, { maxDecimales: props.decimales })}.`,
      valor: null,
    }
  }
  return { error: '', valor: v }
}

function alEscribir(t: string): void {
  editando = true
  texto.value = t
  const r = evaluar(t)
  // Tras un primer error se corrige en vivo (patrón §4.3); antes, solo se emite lo válido.
  if (errorInterno.value || r.error === '') errorInterno.value = r.error
  if (r.error === '') valor.value = r.valor
  emit('invalido', r.error || null)
}

function alSalir(): void {
  editando = false
  const r = evaluar(texto.value)
  errorInterno.value = r.error
  if (r.error === '') {
    valor.value = r.valor
    texto.value = r.valor === null ? '' : formatearNumero(r.valor, { maxDecimales: props.decimales })
  }
  emit('invalido', r.error || null)
}

function validar(): boolean {
  alSalir()
  return errorInterno.value === '' && props.error === ''
}

const mensaje = computed(() => props.error || errorInterno.value)

const atributos = useAttrs()
/** `name`, `disabled`, `autocomplete`… van al <input>; `class` y `style` al contenedor. */
const atributosEntrada = computed(() => {
  const { class: _c, style: _s, ...resto } = atributos
  return resto
})

defineExpose({ focus: () => campo.value?.focus(), validar })
</script>

<template>
  <div class="ui-numero" :class="atributos.class" :style="atributos.style as string">
    <UiField
      :id="id"
      ref="campo"
      :model-value="texto"
      :label="label"
      :hint="hint"
      :error="mensaje"
      type="text"
      :inputmode="decimales === 0 ? 'numeric' : 'decimal'"
      autocomplete="off"
      v-bind="atributosEntrada"
      @update:model-value="alEscribir"
      @blur="alSalir"
    >
      <template v-if="unidad" #suffix>
        <span class="ui-numero__unidad">{{ unidad }}</span>
      </template>
    </UiField>
  </div>
</template>

<style scoped>
.ui-numero :deep(.ui-campo__entrada) {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.ui-numero__unidad {
  align-self: stretch;
  display: flex;
  align-items: center;
  padding: 0 0.9rem 0 0.6rem;
  border-left: 1px solid var(--color-borde);
  color: var(--color-texto-2);
  font-size: var(--texto-sm);
  white-space: nowrap;
  user-select: none;
}
</style>
