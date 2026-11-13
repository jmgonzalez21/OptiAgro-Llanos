<script setup lang="ts">
/** Resultado de una distribución (exacta o genética) en lenguaje de negocio: resumen, uso de plantas, envíos y mapa. */
import { computed, onMounted, ref } from 'vue'
import InsigniaDistancia from '@/components/InsigniaDistancia.vue'
import ConvergenciaSvg from './ConvergenciaSvg.vue'
import UsoPlantas, { type UsoPlanta } from './UsoPlantas.vue'
import MapaFlujos, { type Flujo } from '@/components/mapa/MapaFlujos.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiIcon from '@/components/ui/UiIcon.vue'
import { formatearDuracion, formatearMoneda, formatearNumero } from '@/components/ui/formato'
import { listarTodo } from '@/api/util'
import { serieNumerica } from '@/composables/grafico'
import { coordenadasValidas } from '@/composables/useEstaciones'
import { useRedStore } from '@/stores/red'
import type { ResultadoOptimizacion } from '@/types/fase2'

const props = defineProps<{ resultado: ResultadoOptimizacion }>()
const red = useRedStore()

const esGenetico = computed(() => props.resultado.metodo === 'genetico')
const desglose = computed(() => (props.resultado.metricas.desglose_costos ?? null) as Record<string, number> | null)
const mejor = computed(() => serieNumerica(props.resultado.metricas.convergencia))
const promedio = computed(() => serieNumerica(props.resultado.metricas.convergencia_promedio))
const verif = computed(() => props.resultado.verificacion)

const empresaPorCodigo = computed(() => new Map(red.empresas.map((e) => [e.codigo ?? '', e])))
const plantaPorCodigo = computed(() => new Map(red.plantas.map((p) => [p.codigo ?? '', p])))
const nombreEmpresa = (c: string): string => empresaPorCodigo.value.get(c)?.nombre ?? c
const nombrePlanta = (c: string): string => plantaPorCodigo.value.get(c)?.nombre ?? c

/* Distancias por carretera de las rutas de la red (por código de empresa y planta). */
interface RutaDist {
  id: number
  empresa: string
  planta: string
  distancia_km: number | null
  distancia_fuente?: string
}
const rutas = ref<Map<string, RutaDist>>(new Map())
onMounted(async () => {
  try {
    const lista = await listarTodo<RutaDist>('/rutas/')
    rutas.value = new Map(lista.map((r) => [`${r.empresa}|${r.planta}`, r]))
  } catch {
    // Sin distancias: la tabla y el mapa siguen funcionando.
  }
})
const rutaDe = (a: { empresa_id: string; planta_id: string }): RutaDist | undefined => rutas.value.get(`${a.empresa_id}|${a.planta_id}`)

const envios = computed(() => props.resultado.asignaciones.filter((a) => a.cantidad > 1e-6))
const toneladas = computed(() => envios.value.reduce((s, a) => s + a.cantidad, 0))
const nEmpresas = computed(() => new Set(envios.value.map((a) => a.empresa_id)).size)
const nPlantas = computed(() => new Set(envios.value.map((a) => a.planta_id)).size)

const usoPlantas = computed<UsoPlanta[]>(() =>
  red.plantas.map((p) => ({
    nombre: p.nombre,
    capacidad: p.capacidad,
    usado: envios.value.filter((a) => a.planta_id === p.codigo).reduce((s, a) => s + a.cantidad, 0),
  })),
)

/** Toneladas que faltan de capacidad si la oferta total supera la capacidad total de las plantas. */
const faltante = computed(() => {
  const oferta = red.empresas.reduce((s, e) => s + e.oferta, 0)
  const capacidad = red.plantas.reduce((s, p) => s + p.capacidad, 0)
  return oferta > capacidad + 1e-6 ? oferta - capacidad : 0
})

/* ---- Tabla de envíos ordenable ---- */
type Clave = 'empresa' | 'planta' | 'cantidad' | 'costo' | 'distancia'
const orden = ref<{ clave: Clave; asc: boolean }>({ clave: 'empresa', asc: true })
const filas = computed(() =>
  envios.value.map((a) => ({
    clave: `${a.empresa_id}-${a.planta_id}`,
    empresa: nombreEmpresa(a.empresa_id),
    planta: nombrePlanta(a.planta_id),
    cantidad: a.cantidad,
    costo: a.cantidad * a.costo_unitario,
    distancia: rutaDe(a)?.distancia_km ?? -1,
    fuente: rutaDe(a)?.distancia_fuente,
  })),
)
const ordenadas = computed(() => {
  const { clave, asc } = orden.value
  const dir = asc ? 1 : -1
  return [...filas.value].sort((x, y) => {
    const v = typeof x[clave] === 'number' ? (x[clave] as number) - (y[clave] as number) : String(x[clave]).localeCompare(String(y[clave]), 'es')
    return v !== 0 ? v * dir : x.empresa.localeCompare(y.empresa, 'es') || x.planta.localeCompare(y.planta, 'es')
  })
})
const mostrarEmpresa = (i: number): boolean => orden.value.clave !== 'empresa' || i === 0 || ordenadas.value[i - 1]?.empresa !== ordenadas.value[i]?.empresa
function ordenarPor(clave: Clave): void {
  orden.value = orden.value.clave === clave ? { clave, asc: !orden.value.asc } : { clave, asc: clave === 'empresa' || clave === 'planta' }
}
const ariaOrden = (clave: Clave): 'ascending' | 'descending' | 'none' => (orden.value.clave !== clave ? 'none' : orden.value.asc ? 'ascending' : 'descending')

/* ---- Mapa de flujos ---- */
const flujos = computed<Flujo[]>(() => {
  const lista: Flujo[] = []
  for (const a of envios.value) {
    const e = empresaPorCodigo.value.get(a.empresa_id)
    const p = plantaPorCodigo.value.get(a.planta_id)
    if (e && p && coordenadasValidas(e.latitud, e.longitud) && coordenadasValidas(p.latitud, p.longitud)) {
      lista.push({
        desde: { nombre: e.nombre, latitud: e.latitud as number, longitud: e.longitud as number },
        hasta: { nombre: p.nombre, latitud: p.latitud as number, longitud: p.longitud as number },
        toneladas: a.cantidad,
        costo: a.cantidad * a.costo_unitario,
        rutaId: rutaDe(a)?.id,
        distanciaKm: rutaDe(a)?.distancia_km ?? null,
      })
    }
  }
  return lista
})
const enviosSinMapa = computed(() => envios.value.length - flujos.value.length)
</script>

<template>
  <section class="resultado" :aria-label="esGenetico ? 'Resultado del algoritmo genético' : 'Resultado del cálculo'">
    <UiAlert v-if="!resultado.factible" tono="aviso" titulo="No hay una distribución posible con los datos actuales">
      <template v-if="faltante > 0">
        Las plantas no alcanzan a recibir toda la oferta: faltan {{ formatearNumero(faltante, { maxDecimales: 1 }) }} toneladas de capacidad.
        Aumenta la capacidad de una planta o reduce la oferta.
      </template>
      <template v-else>
        Con la red actual no se puede mover toda la oferta cumpliendo las condiciones. Revisa que cada empresa tenga al menos una ruta activa
        hacia una planta con capacidad disponible.
      </template>
      <details v-if="resultado.mensajes.length" class="avanzadas avanzadas--simple">
        <summary>Detalle para soporte técnico</summary>
        <p class="nota">{{ resultado.mensajes.join(' ') }}</p>
      </details>
    </UiAlert>

    <template v-else>
      <UiCard class="resumen-resultado" variante="elevada">
        <div class="resumen-resultado__cabecera">
          <UiBadge tono="verde" punto>{{ esGenetico ? 'Distribución aproximada' : 'La mejor distribución posible' }}</UiBadge>
          <span class="nota">Calculada en {{ formatearDuracion(resultado.duracion_ms) }}</span>
        </div>
        <p class="resumen-resultado__costo">
          Costo total semanal: <strong>{{ formatearMoneda(resultado.objetivo) }} COP</strong>
        </p>
        <p v-if="desglose" class="resumen-resultado__detalle">
          Transporte {{ formatearMoneda(desglose.transporte) }} y operación {{ formatearMoneda(desglose.operacion) }}<template v-if="desglose.precio"> y compra de residuos {{ formatearMoneda(desglose.precio) }}</template>.
        </p>
        <p class="resumen-resultado__detalle">
          Se mueven <strong>{{ formatearNumero(toneladas, { maxDecimales: 1 }) }} toneladas</strong> por semana desde
          <strong>{{ nEmpresas }} {{ nEmpresas === 1 ? 'empresa' : 'empresas' }}</strong> hacia <strong>{{ nPlantas }} {{ nPlantas === 1 ? 'planta' : 'plantas' }}</strong>.
        </p>
        <p v-if="esGenetico" class="nota">Este método busca una buena solución probando muchas combinaciones; puede quedar un poco por encima del mínimo posible.</p>

        <div class="verificacion">
          <template v-if="verif.valida === true">
            <UiBadge tono="verde"><UiIcon nombre="check" :tamano="13" :grosor="2.4" /> El plan cumple todas las condiciones</UiBadge>
            <details class="avanzadas avanzadas--simple">
              <summary>Ver qué se comprobó</summary>
              <ul class="lista-simple">
                <li>Cada empresa envía toda su oferta.</li>
                <li>Ninguna planta recibe más de su capacidad.</li>
                <li>Se respetan los límites de envío de cada ruta.</li>
              </ul>
            </details>
          </template>
          <UiAlert v-else-if="verif.valida === false" tono="error" titulo="El plan no cumple todas las condiciones">
            <ul class="lista-simple">
              <li v-for="(e, i) in verif.errores ?? []" :key="i">{{ e }}</li>
            </ul>
          </UiAlert>
        </div>
      </UiCard>

      <UiCard>
        <h2>Uso de cada planta</h2>
        <p class="nota">Toneladas por semana que recibe cada planta frente a lo que puede recibir.</p>
        <UsoPlantas :plantas="usoPlantas" />
      </UiCard>

      <UiCard>
        <h2>Qué empresa envía cuánto a qué planta</h2>
        <p class="nota">Pulsa un título de columna para ordenar.</p>
        <div class="tabla-scroll">
          <table class="tabla">
            <caption class="sr-only">Envíos por semana</caption>
            <thead>
              <tr>
                <th v-for="c in ([['empresa', 'Empresa'], ['planta', 'Planta'], ['cantidad', 'Toneladas por semana'], ['distancia', 'Distancia (km)'], ['costo', 'Costo por semana']] as const)" :key="c[0]" scope="col" :class="{ num: c[0] === 'cantidad' || c[0] === 'costo' || c[0] === 'distancia' }" :aria-sort="ariaOrden(c[0])">
                  <button type="button" class="orden" @click="ordenarPor(c[0])">
                    {{ c[1] }}<span aria-hidden="true">{{ orden.clave === c[0] ? (orden.asc ? ' ▲' : ' ▼') : '' }}</span>
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(f, i) in ordenadas" :key="f.clave" :class="{ 'grupo-nuevo': mostrarEmpresa(i) && i > 0 }">
                <th scope="row" class="celda-empresa">{{ mostrarEmpresa(i) ? f.empresa : '' }}<span v-if="!mostrarEmpresa(i)" class="sr-only">{{ f.empresa }}</span></th>
                <td>{{ f.planta }}</td>
                <td class="num">{{ formatearNumero(f.cantidad, { maxDecimales: 1 }) }} t</td>
                <td class="num"><InsigniaDistancia :km="f.distancia < 0 ? null : f.distancia" :fuente="f.fuente" /></td>
                <td class="num">{{ formatearMoneda(f.costo) }}</td>
              </tr>
              <tr v-if="!ordenadas.length"><td colspan="5">No hay envíos.</td></tr>
            </tbody>
          </table>
        </div>
      </UiCard>

      <UiCard>
        <h2>Mapa de envíos</h2>
        <p class="nota">Cada línea une una empresa con una planta; cuanto más gruesa, más toneladas. Pasa el cursor para ver el detalle. Las líneas siguen las carreteras (OpenStreetMap); pueden diferir de la ruta que tome un transportista.</p>
        <MapaFlujos v-if="flujos.length" :flujos="flujos" />
        <UiAlert v-else tono="info">Las estaciones de este plan no tienen ubicación en el mapa. Ubícalas desde Red logística.</UiAlert>
        <p v-if="flujos.length && enviosSinMapa > 0" class="nota">{{ enviosSinMapa }} {{ enviosSinMapa === 1 ? 'envío no se muestra' : 'envíos no se muestran' }} porque falta ubicar alguna estación.</p>
      </UiCard>

      <details v-if="mejor.length > 1" class="avanzadas">
        <summary>Cómo evolucionó el cálculo</summary>
        <p class="nota">Cada punto es una ronda de búsqueda; la línea baja a medida que el método encuentra distribuciones más baratas.</p>
        <ConvergenciaSvg :mejor="mejor" :promedio="promedio" />
      </details>
    </template>
  </section>
</template>

<style scoped>
.resultado {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-4);
}

.resultado h2 {
  font-size: var(--texto-lg);
}

.resultado :deep(.ui-tarjeta) > * + * {
  margin-top: var(--espacio-3);
}

.resumen-resultado__cabecera {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--espacio-3);
}

.resumen-resultado__costo {
  font-size: var(--texto-xl);
  letter-spacing: -0.02em;
}

.resumen-resultado__costo strong {
  color: var(--color-primario);
}

.resumen-resultado__detalle {
  font-size: var(--texto-base);
  color: var(--color-texto-2);
}

.resumen-resultado__detalle strong {
  color: var(--color-texto);
}

.verificacion {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--espacio-2);
}

.lista-simple {
  padding-left: 1.1rem;
  list-style: disc;
  font-size: var(--texto-sm);
}

.orden {
  all: unset;
  cursor: pointer;
  font: inherit;
  white-space: nowrap;
}

.orden:focus-visible {
  outline: 2px solid var(--color-foco);
  outline-offset: 2px;
}

.celda-empresa {
  font-weight: var(--peso-fuerte);
  text-align: left;
}

.tabla tr.grupo-nuevo > * {
  border-top: 2px solid var(--color-borde-fuerte);
}
</style>
