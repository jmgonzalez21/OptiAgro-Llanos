<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import EditorVariaciones from '@/components/analisis/EditorVariaciones.vue'
import ParametrosAG from '@/components/analisis/ParametrosAG.vue'
import SensibilidadResultados from '@/components/analisis/SensibilidadResultados.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCheckbox from '@/components/ui/UiCheckbox.vue'
import UiIcon from '@/components/ui/UiIcon.vue'
import UiPageHeader from '@/components/ui/UiPageHeader.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import { PRESETS } from '@/composables/escenarios'
import { aPayloadAG, paramsAGPorDefecto } from '@/composables/paramsAG'
import { aVariaciones, filaVariacionNueva, type FilaVariacion } from '@/composables/variaciones'
import { solicitar, textoDeError, TIMEOUT_CALCULO_MS } from '@/api/util'
import { useRedStore } from '@/stores/red'
import type { SensibilidadResultado, Variacion } from '@/types/fase2'

const red = useRedStore()
onMounted(() => void red.cargar())

const activos = ref<Set<string>>(new Set(['comb10', 'oferta-10']))
const plantaElegida = ref('')
const personalizado = ref(false)
const filas = ref<FilaVariacion[]>([filaVariacionNueva('combustible', '5 15')])
const incluirAg = ref(true)
const params = ref(paramsAGPorDefecto())
// Para que el análisis sea ágil, el AG de cada escenario usa una población y generaciones moderadas.
params.value.poblacion = '40'
params.value.generaciones = '80'

const opcionesPlanta = computed(() => red.plantas.map((p) => ({ valor: p.codigo ?? '', etiqueta: p.nombre })))
watch(opcionesPlanta, (o) => { if (!o.some((x) => x.valor === plantaElegida.value)) plantaElegida.value = o[0]?.valor ?? '' }, { immediate: true })
const plantaEfectiva = computed(() => plantaElegida.value)

function alternar(id: string): void {
  const s = new Set(activos.value)
  if (!s.delete(id)) s.add(id)
  activos.value = s
}

const variaciones = computed<Variacion[]>(() => {
  const lista = PRESETS.filter((p) => activos.value.has(p.id) && (!p.necesitaPlanta || plantaEfectiva.value)).map((p) => p.variacion(plantaEfectiva.value))
  return personalizado.value ? [...lista, ...aVariaciones(filas.value)] : lista
})
const cantidad = computed(() => variaciones.value.reduce((s, v) => s + v.porcentajes.length, 0))

const cargando = ref(false)
const error = ref('')
const resultado = ref<SensibilidadResultado | null>(null)

async function ejecutar(): Promise<void> {
  error.value = ''
  if (variaciones.value.length === 0) {
    error.value = 'Elige al menos un caso para ver qué pasaría.'
    return
  }
  cargando.value = true
  try {
    const r = await solicitar<{ resultado: SensibilidadResultado }>('/optimizacion/sensibilidad/', {
      metodo: 'POST',
      cuerpo: { variaciones: variaciones.value, incluir_ag: incluirAg.value, config_ag: aPayloadAG(params.value) },
      timeoutMs: TIMEOUT_CALCULO_MS,
    })
    resultado.value = r.resultado
  } catch (e) {
    resultado.value = null
    error.value = textoDeError(e) || 'No se pudo calcular. Inténtalo de nuevo.'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <section class="vista">
    <UiPageHeader
      titulo="¿Qué pasa si…?"
      descripcion="Aquí puedes probar cambios (el combustible sube, llegan más residuos, una planta falla…) y ver cuánto cambiaría el costo y si habría que modificar el plan. No se altera tu red."
    />

    <UiAlert v-if="red.estado === 'listo' && (red.empresas.length === 0 || red.plantas.length === 0)" tono="aviso" titulo="Falta información en la red">
      Necesitas al menos una empresa y una planta activas. Agrégalas en <RouterLink :to="{ name: 'red' }">Red logística</RouterLink>.
    </UiAlert>

    <UiCard variante="elevada" relleno="lg">
      <form class="vista__seccion" @submit.prevent="ejecutar">
        <div>
          <h2>1. Elige los casos que quieres probar</h2>
          <p class="nota">Pulsa para activar o desactivar cada caso.</p>
        </div>
        <div class="presets" role="group" aria-label="Casos a probar">
          <div v-for="p in PRESETS" :key="p.id" class="preset" :class="{ 'preset--activo': activos.has(p.id) }">
            <button type="button" class="preset__boton" :aria-pressed="activos.has(p.id)" @click="alternar(p.id)">
              <span class="preset__marca" aria-hidden="true"><UiIcon v-if="activos.has(p.id)" nombre="check" :tamano="14" :grosor="3" /></span>
              <span>
                <strong>{{ p.titulo }}</strong>
                <small>{{ p.descripcion }}</small>
              </span>
            </button>
            <UiSelect v-if="p.necesitaPlanta && activos.has(p.id)" id="preset-planta" v-model="plantaElegida" label="¿Cuál planta?" :opciones="opcionesPlanta" />
          </div>
        </div>

        <UiCheckbox v-model="personalizado">Quiero definir un caso propio</UiCheckbox>
        <EditorVariaciones v-if="personalizado" v-model="filas" />

        <details class="avanzadas">
          <summary>Opciones avanzadas</summary>
          <UiCheckbox v-model="incluirAg">Comparar también con el algoritmo genético (un método aproximado)</UiCheckbox>
          <template v-if="incluirAg"><ParametrosAG v-model="params" prefijo="sens" /></template>
        </details>

        <div class="fila-botones">
          <UiButton type="submit" tamano="lg" :loading="cargando" :disabled="cantidad === 0">Ver qué pasaría</UiButton>
          <span class="nota">{{ cantidad === 0 ? 'Elige al menos un caso.' : `${cantidad} ${cantidad === 1 ? 'caso elegido' : 'casos elegidos'}` }}</span>
        </div>
        <p v-if="cargando" class="nota" role="status">Calculando cada caso; puede tardar un poco…</p>
      </form>
    </UiCard>

    <UiAlert v-if="error" tono="error" titulo="No se pudo calcular">{{ error }}</UiAlert>
    <SensibilidadResultados v-if="resultado" :datos="resultado" />
  </section>
</template>

<style scoped>
.presets {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
  gap: var(--espacio-3);
}

.preset {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
  border: 1px solid var(--color-borde-control);
  border-radius: var(--radio-md);
  background: var(--color-superficie);
  padding: var(--espacio-3);
  transition: background var(--trans-rapida) var(--ease);
}

.preset--activo {
  border-color: var(--color-activo-barra);
  background: var(--color-acento-suave);
}

.preset__boton {
  all: unset;
  display: flex;
  align-items: flex-start;
  gap: var(--espacio-3);
  cursor: pointer;
  font-size: var(--texto-sm);
}

.preset__boton:focus-visible {
  outline: 2px solid var(--color-foco);
  outline-offset: 3px;
  border-radius: var(--radio-sm);
}

.preset__boton small {
  display: block;
  margin-top: 0.15rem;
  color: var(--color-texto-2);
  font-size: var(--texto-xs);
}

.preset__marca {
  display: grid;
  place-items: center;
  flex: none;
  width: 1.25rem;
  height: 1.25rem;
  margin-top: 0.1rem;
  border: 2px solid var(--color-borde-control);
  border-radius: 6px;
  background: var(--color-superficie);
  color: var(--color-sobre-primario);
}

.preset--activo .preset__marca {
  border-color: var(--color-primario);
  background: var(--color-primario);
}
</style>
