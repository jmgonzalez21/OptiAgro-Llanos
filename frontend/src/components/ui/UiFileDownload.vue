<script setup lang="ts">
/**
 * Botón "Exportar CSV". Genera el CSV en el cliente (UTF-8 con BOM, `;`, decimales con coma) con los datos que se le pasan
 * y dispara la descarga con el nombre `optiagro-<prefijo>-AAAA-MM-DD-HHMM.csv`.
 * - `encabezados` con unidades ("Costo (COP/t)"), `filas` con números CRUDOS (el formato es-CO lo aplica el CSV).
 * - `generar` (opcional) permite construir encabezados/filas al hacer clic (tablas grandes, datos filtrados).
 * Emite `exportado(nombreDeArchivo)` para que el padre muestre el toast "Exportado …".
 * Deshabilitado sin datos, con el motivo en `title`.
 */
import { computed } from 'vue'
import UiButton from './UiButton.vue'
import UiIcon from './UiIcon.vue'
import { descargarArchivo, generarCsv, nombreArchivoCsv, type CeldaCsv } from './csv'

const props = withDefaults(
  defineProps<{
    prefijo: string
    encabezados?: string[]
    filas?: CeldaCsv[][]
    generar?: () => { encabezados: string[]; filas: CeldaCsv[][] }
    etiqueta?: string
    variante?: 'primario' | 'secundario' | 'fantasma'
    tamano?: 'sm' | 'md' | 'lg'
  }>(),
  { encabezados: () => [], filas: () => [], generar: undefined, etiqueta: 'Exportar CSV', variante: 'secundario', tamano: 'md' },
)

const emit = defineEmits<{ exportado: [nombre: string] }>()

const sinDatos = computed(() => !props.generar && props.filas.length === 0)

function exportar(): void {
  const datos = props.generar ? props.generar() : { encabezados: props.encabezados, filas: props.filas }
  const nombre = nombreArchivoCsv(props.prefijo)
  descargarArchivo(generarCsv(datos.encabezados, datos.filas), nombre)
  emit('exportado', nombre)
}
</script>

<template>
  <UiButton :variante="variante" :tamano="tamano" :disabled="sinDatos" :title="sinDatos ? 'No hay datos para exportar' : undefined" @click="exportar">
    <template #icono><UiIcon nombre="descargar" :tamano="18" /></template>
    {{ etiqueta }}
  </UiButton>
</template>
