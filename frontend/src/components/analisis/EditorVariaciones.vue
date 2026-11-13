<script setup lang="ts">
/** Constructor de escenarios de sensibilidad: cada fila es una variación (tipo, códigos afectados y porcentajes). */
import UiButton from '@/components/ui/UiButton.vue'
import UiField from '@/components/ui/UiField.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import { filaVariacionNueva, TIPOS_VARIACION, type FilaVariacion } from '@/composables/variaciones'

const filas = defineModel<FilaVariacion[]>({ required: true })

function agregar(): void {
  filas.value = [...filas.value, filaVariacionNueva('oferta', '-10 10')]
}
function quitar(i: number): void {
  filas.value = filas.value.filter((_, k) => k !== i)
}
function ayuda(tipo: string): string {
  return TIPOS_VARIACION.find((t) => t.valor === tipo)?.ayuda ?? ''
}
</script>

<template>
  <div class="vista__seccion">
    <fieldset v-for="(fila, i) in filas" :key="i" class="formulario-grid" style="border: 1px solid var(--color-borde); border-radius: var(--radio-md); padding: var(--espacio-3)">
      <legend>Caso propio {{ i + 1 }}</legend>
      <UiSelect :id="`var-tipo-${i}`" v-model="fila.tipo" label="Qué cambia" :opciones="TIPOS_VARIACION.map((t) => ({ valor: t.valor, etiqueta: t.etiqueta }))" />
      <UiField :id="`var-ids-${i}`" v-model="fila.ids" label="Dónde aplica" :hint="ayuda(fila.tipo)" placeholder="Todos" />
      <UiField :id="`var-pct-${i}`" v-model="fila.porcentajes" label="Cambio en % (cada valor es un caso)" hint="Separa con espacios. Ej.: -20 10 (negativo = baja, positivo = sube)." />
      <div class="fila-botones">
        <UiButton variante="fantasma" tamano="sm" :disabled="filas.length <= 1" @click="quitar(i)">Quitar</UiButton>
      </div>
    </fieldset>
    <div><UiButton variante="secundario" tamano="sm" @click="agregar">Agregar otro caso</UiButton></div>
  </div>
</template>
