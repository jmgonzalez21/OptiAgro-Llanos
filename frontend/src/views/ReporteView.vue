<script setup lang="ts">
import { computed, ref } from 'vue'
import EditorVariaciones from '@/components/analisis/EditorVariaciones.vue'
import EscalabilidadTabla from '@/components/analisis/EscalabilidadTabla.vue'
import ParametrosAG from '@/components/analisis/ParametrosAG.vue'
import ReporteTablas from '@/components/analisis/ReporteTablas.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCheckbox from '@/components/ui/UiCheckbox.vue'
import UiPageHeader from '@/components/ui/UiPageHeader.vue'
import { descargarArchivo, generarCsv, nombreArchivoCsv } from '@/components/ui/csv'
import { aPayloadAG, paramsAGPorDefecto } from '@/composables/paramsAG'
import { aVariaciones, filaVariacionNueva, type FilaVariacion } from '@/composables/variaciones'
import { solicitar, textoDeError, TIMEOUT_CALCULO_MS } from '@/api/util'
import type { EscalabilidadResultado, ReporteResultado } from '@/types/fase2'

const params = ref(paramsAGPorDefecto())
const conSensibilidad = ref(false)
const filas = ref<FilaVariacion[]>([filaVariacionNueva('combustible', '10 20')])

const cargandoReporte = ref(false)
const cargandoEsc = ref(false)
const errorReporte = ref('')
const errorEsc = ref('')
const reporte = ref<ReporteResultado | null>(null)
const escalabilidad = ref<EscalabilidadResultado | null>(null)

async function generarReporte(): Promise<void> {
  errorReporte.value = ''
  const cuerpo: Record<string, unknown> = { config_ag: aPayloadAG(params.value) }
  if (conSensibilidad.value) {
    const variaciones = aVariaciones(filas.value)
    if (variaciones.length === 0) {
      errorReporte.value = 'Agrega al menos una variación con porcentajes válidos o desactiva la sensibilidad.'
      return
    }
    cuerpo.variaciones = variaciones
  }
  cargandoReporte.value = true
  try {
    const r = await solicitar<{ resultado: ReporteResultado }>('/optimizacion/reporte/', {
      metodo: 'POST',
      cuerpo,
      timeoutMs: TIMEOUT_CALCULO_MS,
    })
    reporte.value = r.resultado
  } catch (e) {
    reporte.value = null
    errorReporte.value = textoDeError(e)
  } finally {
    cargandoReporte.value = false
  }
}

async function ejecutarEscalabilidad(): Promise<void> {
  errorEsc.value = ''
  cargandoEsc.value = true
  try {
    const r = await solicitar<{ resultado: EscalabilidadResultado }>('/optimizacion/escalabilidad/', {
      metodo: 'POST',
      cuerpo: {},
      timeoutMs: TIMEOUT_CALCULO_MS,
    })
    escalabilidad.value = r.resultado
  } catch (e) {
    escalabilidad.value = null
    errorEsc.value = textoDeError(e)
  } finally {
    cargandoEsc.value = false
  }
}

function imprimir(): void {
  window.print()
}

const hayDatos = computed(() => reporte.value !== null || escalabilidad.value !== null)

/** CSV con separador `;` y BOM UTF-8: una sección por tabla, separadas por una línea en blanco. */
function exportarCsv(): void {
  const secciones: string[] = []
  const r = reporte.value
  if (r) {
    secciones.push(
      generarCsv(
        ['Método', 'Estado', 'Costo total (COP/semana)', 'Tiempo (ms)', 'Gap %'],
        [
          ['Exacto', r.exacto.estado, r.exacto.objetivo, r.exacto.duracion_ms, null],
          ['Algoritmo genético', r.genetico.estado, r.genetico.objetivo, r.genetico.duracion_ms, r.comparacion.gap_pct],
        ],
        { bom: false },
      ),
    )
    if (r.sensibilidad) {
      secciones.push(
        generarCsv(
          ['Escenario', 'Costo exacto (COP)', 'Costo AG (COP)', 'Gap %', 'Tiempo exacto (ms)', 'Tiempo AG (ms)', 'Cambió la base'],
          r.sensibilidad.escenarios.map((e) => [e.nombre, e.costo_exacto, e.costo_ag, e.gap_pct, e.tiempo_exacto_ms, e.tiempo_ag_ms, e.base_cambio]),
          { bom: false },
        ),
      )
    }
  }
  const esc = escalabilidad.value
  if (esc) {
    secciones.push(
      generarCsv(
        ['Empresas', 'Plantas', 'Rutas', 'Costo exacto (COP)', 'Costo AG (COP)', 'Tiempo exacto (ms)', 'Tiempo AG (ms)', 'Gap %'],
        esc.tamanos.map((f) => [f.empresas, f.plantas, f.rutas, f.exacto.objetivo, f.genetico.objetivo, f.exacto.duracion_ms, f.genetico.duracion_ms, f.gap_pct]),
        { bom: false },
      ),
    )
  }
  descargarArchivo(`\uFEFF${secciones.join('\r\n')}`, nombreArchivoCsv('reporte'))
}
</script>

<template>
  <section class="vista">
    <p class="solo-imprimir">OptiAgro-Llanos · Reporte comparativo · {{ new Date().toLocaleDateString('es-CO') }}</p>
    <UiPageHeader titulo="Reporte comparativo" descripcion="Aquí puedes comparar el método exacto (el que siempre encuentra el menor costo) con el algoritmo genético (una búsqueda aproximada) y ver qué tan cerca queda y cuánto tarda.">
      <template #acciones>
        <div class="fila-botones no-imprimir">
          <UiButton variante="secundario" :disabled="!hayDatos" @click="exportarCsv">Exportar CSV</UiButton>
          <UiButton variante="secundario" :disabled="!hayDatos" @click="imprimir">Imprimir</UiButton>
        </div>
      </template>
    </UiPageHeader>

    <UiCard class="no-imprimir" variante="elevada" relleno="lg">
      <form class="vista__seccion" @submit.prevent="generarReporte">
        <h2>Generar el reporte</h2>
        <p class="nota">Se calcula la mejor distribución con ambos métodos usando tu red actual.</p>
        <div class="fila-botones">
          <UiButton type="submit" tamano="lg" :loading="cargandoReporte" :disabled="cargandoEsc">Generar reporte comparativo</UiButton>
        </div>
        <p v-if="cargandoReporte" class="nota" role="status">Calculando con ambos métodos; puede tardar un poco…</p>
        <details class="avanzadas">
          <summary>Opciones avanzadas</summary>
          <p class="nota">Ajustes del algoritmo genético. Los valores por defecto funcionan bien.</p>
          <ParametrosAG v-model="params" prefijo="rep" />
          <UiCheckbox v-model="conSensibilidad">Incluir también los casos de «¿Qué pasa si…?»</UiCheckbox>
          <EditorVariaciones v-if="conSensibilidad" v-model="filas" />
        </details>
      </form>
    </UiCard>

    <UiAlert v-if="errorReporte" tono="error" titulo="No se pudo generar el reporte">{{ errorReporte }}</UiAlert>
    <ReporteTablas v-if="reporte" :datos="reporte" />

    <UiCard class="no-imprimir">
      <div class="vista__seccion">
        <h2>Prueba con redes más grandes</h2>
        <p class="nota">Compara los dos métodos en redes de ejemplo cada vez más grandes (10×4, 20×6, 40×10 y 80×16 empresas × plantas) para ver cómo escalan. No usa ni cambia tu red.</p>
        <div class="fila-botones">
          <UiButton variante="secundario" :loading="cargandoEsc" :disabled="cargandoReporte" @click="ejecutarEscalabilidad">Ejecutar prueba</UiButton>
        </div>
        <p v-if="cargandoEsc" class="nota" role="status">Resolviendo redes de distintos tamaños; puede tardar…</p>
      </div>
    </UiCard>
    <UiAlert v-if="errorEsc" tono="error" titulo="No se pudo ejecutar la prueba">{{ errorEsc }}</UiAlert>
    <EscalabilidadTabla v-if="escalabilidad" :datos="escalabilidad" />
  </section>
</template>
