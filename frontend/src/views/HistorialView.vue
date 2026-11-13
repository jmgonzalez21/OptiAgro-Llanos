<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import EscalabilidadTabla from '@/components/analisis/EscalabilidadTabla.vue'
import ReporteTablas from '@/components/analisis/ReporteTablas.vue'
import ResultadoPanel from '@/components/analisis/ResultadoPanel.vue'
import SensibilidadResultados from '@/components/analisis/SensibilidadResultados.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiEmptyState from '@/components/ui/UiEmptyState.vue'
import UiField from '@/components/ui/UiField.vue'
import UiModal from '@/components/ui/UiModal.vue'
import UiPageHeader from '@/components/ui/UiPageHeader.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiSpinner from '@/components/ui/UiSpinner.vue'
import { formatearDuracion, formatearMoneda } from '@/components/ui/formato'
import { solicitar, textoDeError } from '@/api/util'
import { useRedStore } from '@/stores/red'
import type { Pagina } from '@/types/api'
import type {
  EjecucionDetalle,
  EjecucionLista,
  EscalabilidadResultado,
  ReporteResultado,
  ResultadoOptimizacion,
  SensibilidadResultado,
} from '@/types/fase2'

const TAMANO = 15
const NOMBRES: Record<string, string> = {
  exacto: 'Exacto',
  genetico: 'Algoritmo genético',
  sensibilidad: 'Sensibilidad',
  reporte: 'Reporte comparativo',
  escalabilidad: 'Escalabilidad',
}

const metodo = ref<string>('')
const estado = ref<string>('')
const desde = ref('')
const hasta = ref('')
const pagina = ref(1)

const filas = ref<EjecucionLista[]>([])
const total = ref(0)
const cargando = ref(true)
const error = ref('')

const totalPaginas = computed(() => Math.max(1, Math.ceil(total.value / TAMANO)))

async function cargar(): Promise<void> {
  cargando.value = true
  error.value = ''
  try {
    const r = await solicitar<Pagina<EjecucionLista>>('/ejecuciones/', {
      consulta: {
        page: pagina.value,
        page_size: TAMANO,
        metodo: metodo.value || undefined,
        estado: estado.value || undefined,
        desde: desde.value || undefined,
        hasta: hasta.value || undefined,
      },
    })
    filas.value = r.results
    total.value = r.count
  } catch (e) {
    error.value = textoDeError(e)
  } finally {
    cargando.value = false
  }
}
const red = useRedStore()
const ESTADOS: Record<string, string> = { OPTIMAL: 'Calculada', FEASIBLE: 'Calculada', INFEASIBLE: 'Sin solución', UNBOUNDED: 'Sin solución' }
const estadoTexto = (e: string): string => ESTADOS[e] ?? e
onMounted(() => {
  void red.cargar() // los nombres de empresas y plantas del detalle salen de la red actual
  void cargar()
})

function filtrar(): void {
  pagina.value = 1
  void cargar()
}
function limpiar(): void {
  metodo.value = ''
  estado.value = ''
  desde.value = ''
  hasta.value = ''
  filtrar()
}
function irA(p: number): void {
  pagina.value = Math.min(Math.max(1, p), totalPaginas.value)
  void cargar()
}

const fecha = (iso: string): string => new Date(iso).toLocaleString('es-CO')

/* ---- Detalle ---- */
const abierto = ref(false)
const detalle = ref<EjecucionDetalle | null>(null)
const cargandoDetalle = ref(false)
const errorDetalle = ref('')

async function abrir(f: EjecucionLista): Promise<void> {
  abierto.value = true
  detalle.value = null
  errorDetalle.value = ''
  cargandoDetalle.value = true
  try {
    detalle.value = await solicitar<EjecucionDetalle>(`/ejecuciones/${f.id}/`)
  } catch (e) {
    errorDetalle.value = textoDeError(e)
  } finally {
    cargandoDetalle.value = false
  }
}
</script>

<template>
  <section class="vista">
    <UiPageHeader titulo="Historial de ejecuciones" descripcion="Aquí puedes consultar los cálculos que se han hecho y abrir cualquiera para ver su resultado. Los analistas ven solo los suyos." />

    <form class="herramientas" @submit.prevent="filtrar">
      <UiSelect
        id="h-metodo"
        v-model="metodo"
        label="Método"
        :opciones="[
          { valor: '', etiqueta: 'Todos' },
          { valor: 'exacto', etiqueta: 'Exacto' },
          { valor: 'genetico', etiqueta: 'Algoritmo genético' },
          { valor: 'sensibilidad', etiqueta: 'Sensibilidad' },
          { valor: 'reporte', etiqueta: 'Reporte comparativo' },
          { valor: 'escalabilidad', etiqueta: 'Escalabilidad' },
        ]"
      />
      <UiSelect
        id="h-estado"
        v-model="estado"
        label="Estado"
        :opciones="[
          { valor: '', etiqueta: 'Todos' },
          { valor: 'OPTIMAL', etiqueta: 'OPTIMAL' },
          { valor: 'FEASIBLE', etiqueta: 'FEASIBLE' },
          { valor: 'INFEASIBLE', etiqueta: 'INFEASIBLE' },
          { valor: 'COMPLETADA', etiqueta: 'COMPLETADA' },
        ]"
      />
      <UiField id="h-desde" v-model="desde" label="Desde" type="date" />
      <UiField id="h-hasta" v-model="hasta" label="Hasta" type="date" />
      <UiButton type="submit" :loading="cargando">Filtrar</UiButton>
      <UiButton variante="fantasma" :disabled="cargando" @click="limpiar">Limpiar</UiButton>
    </form>

    <UiAlert v-if="error" tono="error" titulo="No se pudo cargar el historial">
      {{ error }}
      <template #acciones><UiButton variante="secundario" tamano="sm" @click="cargar">Reintentar</UiButton></template>
    </UiAlert>
    <p v-if="cargando" class="nota" role="status"><UiSpinner :tamano="16" /> Cargando el historial…</p>
    <UiEmptyState v-else-if="filas.length === 0 && !error" icono="lista" titulo="Sin ejecuciones" descripcion="No hay ejecuciones que coincidan con los filtros." />
    <div v-else-if="filas.length" class="tabla-scroll">
      <table class="tabla">
        <caption class="sr-only">Ejecuciones</caption>
        <thead>
          <tr>
            <th scope="col">N.º</th>
            <th scope="col">Fecha</th>
            <th scope="col">Método</th>
            <th scope="col">Estado</th>
            <th scope="col" class="num">Costo (COP)</th>
            <th scope="col" class="num">Duración</th>
            <th scope="col">Usuario</th>
            <th scope="col"><span class="sr-only">Detalle</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="f in filas" :key="f.id">
            <td>{{ f.id }}</td>
            <td>{{ fecha(f.creada_en) }}</td>
            <td>{{ NOMBRES[f.metodo] ?? f.metodo }} <UiBadge v-if="f.incluye_ficticios" tono="ambar">Demo</UiBadge></td>
            <td>{{ estadoTexto(f.estado) }}</td>
            <td class="num">{{ formatearMoneda(f.objetivo) }}</td>
            <td class="num">{{ formatearDuracion(f.duracion_ms) }}</td>
            <td>{{ f.usuario }}</td>
            <td><UiButton variante="secundario" tamano="sm" @click="abrir(f)">Ver detalle</UiButton></td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="total > TAMANO" class="fila-botones">
      <UiButton variante="secundario" tamano="sm" :disabled="pagina <= 1 || cargando" @click="irA(pagina - 1)">Anterior</UiButton>
      <span class="nota">Página {{ pagina }} de {{ totalPaginas }} ({{ total }} ejecuciones)</span>
      <UiButton variante="secundario" tamano="sm" :disabled="pagina >= totalPaginas || cargando" @click="irA(pagina + 1)">Siguiente</UiButton>
    </div>

    <UiModal v-model:abierto="abierto" :titulo="detalle ? `Ejecución ${detalle.id} · ${NOMBRES[detalle.metodo] ?? detalle.metodo}` : 'Detalle de la ejecución'" ancho="lg">
      <p v-if="cargandoDetalle" class="nota" role="status"><UiSpinner :tamano="16" /> Cargando el detalle…</p>
      <UiAlert v-else-if="errorDetalle" tono="error">{{ errorDetalle }}</UiAlert>
      <div v-else-if="detalle" class="vista__seccion">
        <p class="nota">
          {{ fecha(detalle.creada_en) }} · {{ detalle.usuario }} · {{ estadoTexto(detalle.estado) }} · {{ formatearDuracion(detalle.duracion_ms) }}
          <template v-if="detalle.incluye_ficticios"> · usa datos de demostración</template>
        </p>
        <ResultadoPanel v-if="detalle.metodo === 'exacto' || detalle.metodo === 'genetico'" :resultado="detalle.resultado as ResultadoOptimizacion" />
        <SensibilidadResultados v-else-if="detalle.metodo === 'sensibilidad'" :datos="detalle.resultado as SensibilidadResultado" />
        <ReporteTablas v-else-if="detalle.metodo === 'reporte'" :datos="detalle.resultado as ReporteResultado" />
        <EscalabilidadTabla v-else-if="detalle.metodo === 'escalabilidad'" :datos="detalle.resultado as EscalabilidadResultado" />
        <details class="avanzadas">
          <summary>Detalle técnico de la ejecución</summary>
          <pre class="nota" style="white-space: pre-wrap">{{ JSON.stringify(detalle.parametros ?? detalle.configuracion, null, 2) }}</pre>
        </details>
      </div>
    </UiModal>
  </section>
</template>
