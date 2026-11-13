<script setup lang="ts">
/** Resultado de «¿Qué pasa si…?»: escenarios en frases con semáforo, cuellos de botella y margen de seguridad. */
import { computed } from 'vue'
import MargenBarra from './MargenBarra.vue'
import UsoPlantas from './UsoPlantas.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiCard from '@/components/ui/UiCard.vue'
import { formatearMoneda, formatearNumero, formatearPorcentaje } from '@/components/ui/formato'
import { ETIQUETA_SEMAFORO, esFactible, frase, semaforo, textoMargen, textoPlan, condicion, type Nombres } from '@/composables/escenarios'
import { useRedStore } from '@/stores/red'
import type { SensibilidadResultado } from '@/types/fase2'

const props = defineProps<{ datos: SensibilidadResultado }>()
const red = useRedStore()

const nombres = computed<Nombres>(() => ({
  empresas: new Map(red.empresas.map((e) => [e.codigo ?? '', e.nombre])),
  plantas: new Map([...red.plantas.map((p) => [p.codigo ?? '', p.nombre] as const), ...props.datos.plantas.map((p) => [p.planta, p.nombre] as const)]),
}))

const costoBase = computed(() => props.datos.base.exacto.objetivo)
const hayAg = computed(() => props.datos.escenarios.some((e) => e.gap_pct !== null))

const cuellos = computed(() =>
  props.datos.plantas
    .filter((p) => p.cuello_de_botella)
    .map((p) => ({ nombre: p.nombre, ahorro: Math.abs(p.precio_sombra ?? 0) }))
    .sort((a, b) => b.ahorro - a.ahorro),
)
const usoPlantas = computed(() => props.datos.plantas.map((p) => ({ nombre: p.nombre, usado: p.flujo, capacidad: p.capacidad })))

const margenPlantas = computed(() => (props.datos.rangos.disponible ? props.datos.rangos.capacidad : []))
const margenEmpresas = computed(() => (props.datos.rangos.disponible ? props.datos.rangos.oferta : []))
</script>

<template>
  <div class="vista__seccion sens">
    <UiCard variante="elevada">
      <p class="sens__base">
        Costo actual: <strong>{{ formatearMoneda(costoBase) }} COP por semana</strong>
      </p>
      <p class="nota">Se compara cada «¿qué pasa si…?» con este costo.</p>
    </UiCard>

    <section aria-labelledby="sens-casos">
      <h2 id="sens-casos">Qué pasaría en cada caso</h2>
      <ul class="casos">
        <li v-for="(e, i) in datos.escenarios" :key="i" class="caso" :class="`caso--${semaforo(e)}`">
          <span class="semaforo" :class="`semaforo--${semaforo(e)}`" aria-hidden="true"></span>
          <p>
            <span class="caso__etiqueta">{{ ETIQUETA_SEMAFORO[semaforo(e)] }}.</span>
            {{ frase(e, nombres) }}
          </p>
        </li>
      </ul>

      <div class="tabla-scroll sens__tabla">
        <table class="tabla">
          <caption class="sr-only">Resumen de escenarios</caption>
          <thead>
            <tr>
              <th scope="col">Si…</th>
              <th scope="col" class="num">Costo semanal</th>
              <th scope="col" class="num">Cambio</th>
              <th scope="col">¿Cambia el plan?</th>
              <th v-if="hayAg" scope="col" class="num sens__ag">Algoritmo genético</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(e, i) in datos.escenarios" :key="i">
              <td class="celda-ajustable">{{ condicion(e, nombres).replace(/^./, (c) => c.toUpperCase()) }}</td>
              <td class="num">{{ esFactible(e) ? formatearMoneda(e.costo_exacto) : 'Sin solución' }}</td>
              <td class="num">{{ formatearPorcentaje(e.variacion_objetivo_pct, { decimales: 1, conSigno: true }) }}</td>
              <td>{{ esFactible(e) ? textoPlan(e) : '—' }}</td>
              <td v-if="hayAg" class="num sens__ag">{{ e.gap_pct === null ? '—' : `${formatearPorcentaje(e.gap_pct, { decimales: 1 })} sobre el óptimo` }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="hayAg" class="nota">La última columna muestra qué tan cerca queda el algoritmo genético (un método aproximado) del costo mínimo en cada caso.</p>
    </section>

    <UiCard como="section" aria-labelledby="sens-cuellos">
      <h2 id="sens-cuellos">Cuellos de botella</h2>
      <p class="nota">Plantas que están llenas y limitan el ahorro.</p>
      <ul v-if="cuellos.length" class="lista-frases">
        <li v-for="c in cuellos" :key="c.nombre">
          <template v-if="c.ahorro > 0">Ampliar <strong>{{ c.nombre }}</strong> en 1 t ahorraría <strong>{{ formatearMoneda(c.ahorro) }}</strong> a la semana.</template>
          <template v-else><strong>{{ c.nombre }}</strong> está llena, pero ampliarla ahora no reduciría el costo.</template>
        </li>
      </ul>
      <UiAlert v-else tono="exito">Ninguna planta está llena: hay capacidad de sobra y no hay cuellos de botella.</UiAlert>
      <UsoPlantas :plantas="usoPlantas" />
      <details class="avanzadas avanzadas--simple">
        <summary>¿Qué significa esto?</summary>
        <p class="nota">Una planta llena obliga a enviar residuos a destinos más caros. Si pudiera recibir una tonelada más, ese sería el ahorro semanal. El cálculo vale para ampliaciones pequeñas, dentro del margen de seguridad.</p>
      </details>
    </UiCard>

    <UiCard como="section" aria-labelledby="sens-margen">
      <h2 id="sens-margen">Margen de seguridad</h2>
      <p class="nota">Hasta dónde pueden cambiar los valores sin que el plan de envíos tenga que cambiar.</p>
      <UiAlert v-if="!datos.rangos.disponible" tono="info">Para esta red no se pudo calcular el margen de seguridad.</UiAlert>
      <template v-else>
        <ul class="margenes">
          <li v-for="r in margenPlantas" :key="r.id">
            <p>La capacidad de <strong>{{ nombres.plantas.get(r.id) ?? r.id }}</strong> {{ textoMargen(r.minimo, r.maximo) }}. <span class="nota">Hoy: {{ formatearNumero(r.valor_actual, { maxDecimales: 1 }) }} t.</span></p>
            <MargenBarra :valor="r.valor_actual" :minimo="r.minimo" :maximo="r.maximo" />
          </li>
        </ul>
        <details v-if="margenEmpresas.length" class="avanzadas">
          <summary>Margen de la oferta de cada empresa</summary>
          <ul class="margenes">
            <li v-for="r in margenEmpresas" :key="r.id">
              <p>La oferta de <strong>{{ nombres.empresas.get(r.id) ?? r.id }}</strong> {{ textoMargen(r.minimo, r.maximo) }}. <span class="nota">Hoy: {{ formatearNumero(r.valor_actual, { maxDecimales: 1 }) }} t.</span></p>
              <MargenBarra :valor="r.valor_actual" :minimo="r.minimo" :maximo="r.maximo" />
            </li>
          </ul>
        </details>
      </template>
    </UiCard>
  </div>
</template>

<style scoped>
.sens h2 {
  font-size: var(--texto-lg);
  margin-bottom: var(--espacio-2);
}

.sens :deep(.ui-tarjeta) > * + * {
  margin-top: var(--espacio-3);
}

.sens__base {
  font-size: var(--texto-lg);
}

.casos {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
  margin-bottom: var(--espacio-3);
}

.caso {
  display: flex;
  align-items: flex-start;
  gap: var(--espacio-3);
  padding: var(--espacio-3) var(--espacio-4);
  border: 1px solid var(--color-borde);
  border-left-width: 4px;
  border-radius: var(--radio-md);
  background: var(--color-superficie);
}

.caso .semaforo {
  margin-top: 0.4rem;
}

.caso--verde {
  border-left-color: var(--color-activo-barra);
}

.caso--ambar {
  border-left-color: var(--color-aviso);
}

.caso--rojo {
  border-left-color: var(--color-error);
}

.caso__etiqueta {
  font-weight: var(--peso-fuerte);
}

.celda-ajustable {
  white-space: normal !important;
  min-width: 14rem;
}

.sens__tabla .sens__ag {
  color: var(--color-texto-suave);
  font-size: var(--texto-xs);
}

.lista-frases,
.margenes {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-3);
}

.margenes li {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
  font-size: var(--texto-sm);
}
</style>
