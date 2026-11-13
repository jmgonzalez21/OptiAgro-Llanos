<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import ParametrosAG from '@/components/analisis/ParametrosAG.vue'
import ResultadoPanel from '@/components/analisis/ResultadoPanel.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCheckbox from '@/components/ui/UiCheckbox.vue'
import UiPageHeader from '@/components/ui/UiPageHeader.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import { aPayloadAG, paramsAGPorDefecto } from '@/composables/paramsAG'
import { leerErrores, solicitar, TIMEOUT_CALCULO_MS } from '@/api/util'
import { useRedStore } from '@/stores/red'
import { useResultadosStore } from '@/stores/resultados'
import type { EjecucionResultado } from '@/types/fase2'

const red = useRedStore()
const resultados = useResultadosStore()
const params = ref(paramsAGPorDefecto())
const metodo = ref<'exacto' | 'genetico'>('exacto')
const modoOferta = ref<'exact' | 'maximum'>('exact')
const guardar = ref(true)

const ejecutando = ref(false)
const resultado = ref<EjecucionResultado | null>(null)
const errorGeneral = ref('')
const erroresCampo = ref<Record<string, string>>({})

// La red se recarga al entrar: así los nombres y capacidades del resultado están al día.
onMounted(() => void red.cargar())

async function calcular(): Promise<void> {
  ejecutando.value = true
  errorGeneral.value = ''
  erroresCampo.value = {}
  const cuerpo = metodo.value === 'exacto' ? { modo_oferta: modoOferta.value, guardar: guardar.value } : { ...aPayloadAG(params.value), guardar: guardar.value }
  try {
    resultado.value = await solicitar<EjecucionResultado>(`/optimizacion/${metodo.value}/`, { metodo: 'POST', cuerpo, timeoutMs: TIMEOUT_CALCULO_MS })
    if (metodo.value === 'exacto' && modoOferta.value === 'exact') resultados.guardarExacto(resultado.value.resultado)
  } catch (e) {
    resultado.value = null
    const err = leerErrores(e)
    erroresCampo.value = err.campos
    errorGeneral.value = err.general || (Object.keys(err.campos).length ? 'Revisa los valores de «Opciones avanzadas».' : 'No se pudo calcular. Inténtalo de nuevo.')
  } finally {
    ejecutando.value = false
  }
}
</script>

<template>
  <section class="vista">
    <UiPageHeader
      titulo="Optimización"
      descripcion="Aquí puedes calcular cuántas toneladas debe enviar cada empresa a cada planta para que el costo semanal sea el más bajo posible."
    />

    <UiAlert v-if="red.estado === 'listo' && (red.empresas.length === 0 || red.plantas.length === 0)" tono="aviso" titulo="Falta información en la red">
      Para calcular necesitas al menos una empresa y una planta activas. Agrégalas en <RouterLink :to="{ name: 'red' }">Red logística</RouterLink>.
    </UiAlert>

    <UiCard variante="elevada" relleno="lg">
      <form class="calcular" @submit.prevent="calcular">
        <div>
          <h2>Calcular la mejor distribución</h2>
          <p class="nota">Se usan las empresas, plantas y costos actuales de tu red.</p>
        </div>
        <UiButton type="submit" tamano="lg" :loading="ejecutando">Calcular la mejor distribución</UiButton>
        <p v-if="ejecutando" class="nota" role="status">Calculando… {{ metodo === 'genetico' ? 'este método puede tardar unos segundos.' : 'solo tomará un momento.' }}</p>

        <details class="avanzadas">
          <summary>Opciones avanzadas</summary>
          <UiSelect
            id="metodo"
            v-model="metodo"
            label="Método de cálculo"
            hint="El exacto garantiza el menor costo. El algoritmo genético prueba muchas combinaciones y da una solución aproximada; sirve para compararlo con el exacto."
            :opciones="[
              { valor: 'exacto', etiqueta: 'Exacto (recomendado)' },
              { valor: 'genetico', etiqueta: 'Algoritmo genético (aproximado)' },
            ]"
          />
          <UiSelect
            v-if="metodo === 'exacto'"
            id="modo-oferta"
            v-model="modoOferta"
            label="Residuos de cada empresa"
            :opciones="[
              { valor: 'exact', etiqueta: 'Se retira todo lo que genera cada empresa' },
              { valor: 'maximum', etiqueta: 'Se puede dejar parte sin retirar' },
            ]"
          />
          <template v-else>
            <p class="nota">Estos valores ya vienen listos para un buen resultado; cámbialos solo si quieres experimentar.</p>
            <ParametrosAG v-model="params" :errores="erroresCampo" />
            <div><UiButton variante="fantasma" tamano="sm" @click="params = paramsAGPorDefecto()">Volver a los valores recomendados</UiButton></div>
          </template>
          <UiCheckbox v-model="guardar">Guardar este cálculo en el historial</UiCheckbox>
        </details>
      </form>
    </UiCard>

    <UiAlert v-if="errorGeneral" tono="error" titulo="No se pudo calcular">{{ errorGeneral }}</UiAlert>

    <ResultadoPanel v-if="resultado" :resultado="resultado.resultado" />
    <p v-if="resultado?.ejecucion_id" class="nota">Este cálculo quedó guardado en el <RouterLink :to="{ name: 'historial' }">historial</RouterLink> (n.º {{ resultado.ejecucion_id }}).</p>
  </section>
</template>

<style scoped>
.calcular {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--espacio-3);
}

.calcular details {
  align-self: stretch;
}

.calcular details > :deep(*) {
  max-width: 100%;
}
</style>
