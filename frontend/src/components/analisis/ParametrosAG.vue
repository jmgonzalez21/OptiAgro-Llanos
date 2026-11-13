<script setup lang="ts">
/** Formulario de parámetros del algoritmo genético. Los errores 400 llegan por campo en `errores`. */
import UiField from '@/components/ui/UiField.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import type { ParamsAGForm } from '@/composables/paramsAG'

defineProps<{ errores?: Record<string, string>; prefijo?: string }>()
const modelo = defineModel<ParamsAGForm>({ required: true })

const SELECCION = [
  { valor: 'torneo', etiqueta: 'Torneo' },
  { valor: 'ruleta', etiqueta: 'Ruleta' },
]
const CRUCE = [
  { valor: 'un_punto', etiqueta: 'Un punto' },
  { valor: 'dos_puntos', etiqueta: 'Dos puntos' },
]
const INICIALIZACION = [
  { valor: 'aleatoria', etiqueta: 'Aleatorio' },
  { valor: 'heuristica', etiqueta: 'Favorece las rutas baratas' },
]
</script>

<template>
  <div class="formulario-grid">
    <UiField :id="`${prefijo ?? 'ag'}-poblacion`" v-model="modelo.poblacion" label="Población" type="number" min="2" max="300" step="1" :error="errores?.poblacion" hint="Cuántas distribuciones se comparan en cada ronda (2 a 300). Más = mejor búsqueda, pero más lento." />
    <UiField :id="`${prefijo ?? 'ag'}-generaciones`" v-model="modelo.generaciones" label="Generaciones" type="number" min="1" max="1000" step="1" :error="errores?.generaciones" hint="Número de rondas de mejora (1 a 1000)." />
    <UiField :id="`${prefijo ?? 'ag'}-cruce`" v-model="modelo.cruce" label="Tasa de cruce" type="number" min="0" max="1" step="any" :error="errores?.cruce" hint="Qué tan seguido se combinan dos soluciones para crear una nueva (0 a 1)." />
    <UiField :id="`${prefijo ?? 'ag'}-mutacion`" v-model="modelo.mutacion" label="Tasa de mutación" type="number" min="0" max="1" step="any" :error="errores?.mutacion" hint="Qué tan seguido se cambia algo al azar para explorar otras opciones (0 a 1)." />
    <UiField :id="`${prefijo ?? 'ag'}-semilla`" v-model="modelo.semilla" label="Semilla" type="number" min="0" step="1" :error="errores?.semilla" hint="Con la misma semilla se obtiene siempre el mismo resultado." />
    <UiField :id="`${prefijo ?? 'ag'}-elitismo`" v-model="modelo.elitismo" label="Mejores que se conservan" type="number" min="0" step="1" :error="errores?.elitismo" hint="Las mejores soluciones pasan intactas a la siguiente ronda." />
    <UiSelect :id="`${prefijo ?? 'ag'}-seleccion`" v-model="modelo.seleccion" label="Cómo se eligen las soluciones" :opciones="SELECCION" :error="errores?.seleccion" />
    <UiField
      :id="`${prefijo ?? 'ag'}-torneo`"
      v-model="modelo.tamano_torneo"
      label="Soluciones que compiten en cada elección"
      type="number"
      min="2"
      step="1"
      :disabled="modelo.seleccion !== 'torneo'"
      :error="errores?.tamano_torneo"
    />
    <UiSelect :id="`${prefijo ?? 'ag'}-tipo-cruce`" v-model="modelo.tipo_cruce" label="Forma de combinar" :opciones="CRUCE" :error="errores?.tipo_cruce" />
    <UiSelect :id="`${prefijo ?? 'ag'}-inicializacion`" v-model="modelo.inicializacion" label="Punto de partida" :opciones="INICIALIZACION" :error="errores?.inicializacion" />
  </div>
</template>
