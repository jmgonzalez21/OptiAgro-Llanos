<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import InsigniaDistancia from '@/components/InsigniaDistancia.vue'
import RecalcularDistancias from '@/components/RecalcularDistancias.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiEmptyState from '@/components/ui/UiEmptyState.vue'
import UiPageHeader from '@/components/ui/UiPageHeader.vue'
import UiSegmented from '@/components/ui/UiSegmented.vue'
import UiUsageBar from '@/components/ui/UiUsageBar.vue'
import UiSpinner from '@/components/ui/UiSpinner.vue'
import { formatearMoneda, formatearNumero, leerNumero } from '@/components/ui/formato'
import { listarTodo, solicitar, textoDeError, TIMEOUT_CALCULO_MS } from '@/api/util'
import { coincide, equilibrio, llena, planPorCeldas, sumar } from '@/composables/tablaTransporte'
import { useAuthStore } from '@/stores/auth'
import { useRedStore } from '@/stores/red'
import { useResultadosStore } from '@/stores/resultados'
import type { EjecucionResultado, MatrizCostos } from '@/types/fase2'

const auth = useAuthStore()
const red = useRedStore()
const resultados = useResultadosStore()

interface NodoApi {
  id: number
  codigo: string
  oferta?: number
  capacidad?: number
}
interface RutaApi {
  id: number
  empresa: string
  planta: string
  distancia_km: number | null
  distancia_fuente?: string
}

const empresasApi = ref<NodoApi[]>([])
const plantasApi = ref<NodoApi[]>([])
const rutasApi = ref<RutaApi[]>([])
const vista = ref<'costos' | 'asignacion'>('costos')
const calculando = ref(false)
const errorPlan = ref('')
/** Texto escrito en oferta (por código de empresa) y capacidad (por código de planta). */
const editOferta = ref<Record<string, string>>({})
const editCap = ref<Record<string, string>>({})

const matriz = ref<MatrizCostos | null>(null)
const cargando = ref(true)
const guardando = ref(false)
const error = ref('')
const exito = ref('')
/** Texto escrito por celda `${i}|${j}` (solo las que la persona tocó). */
const editados = ref<Record<string, string>>({})

const clave = (i: number, j: number): string => `${i}|${j}`
const original = (i: number, j: number): number | null => matriz.value?.costos[i]?.[j] ?? null

/** Lectura de una celda: valor numérico (null = vacía) o error de formato. */
function leer(i: number, j: number): { valor: number | null; invalida: boolean; editada: boolean } {
  const texto = editados.value[clave(i, j)]
  if (texto === undefined) return { valor: original(i, j), invalida: false, editada: false }
  const r = leerNumero(texto)
  if (!r.ok || (r.valor !== null && r.valor < 0)) return { valor: null, invalida: true, editada: true }
  return { valor: r.valor, invalida: false, editada: r.valor !== original(i, j) }
}

const cambios = computed(() => {
  const m = matriz.value
  const lista: Array<{ i: number; j: number; valor: number | null }> = []
  if (!m) return lista
  m.empresas.forEach((_, i) =>
    m.plantas.forEach((_, j) => {
      const c = leer(i, j)
      if (!c.invalida && c.editada) lista.push({ i, j, valor: c.valor })
    }),
  )
  return lista
})
/* ---- Oferta (columna) y capacidad (fila) ---- */
const ofertaGuardada = (codigo: string): number => empresasApi.value.find((e) => e.codigo === codigo)?.oferta ?? 0
const capacidadGuardada = (codigo: string): number => plantasApi.value.find((p) => p.codigo === codigo)?.capacidad ?? 0

function leerNodo(textos: Record<string, string>, codigo: string, guardado: number): { valor: number; invalida: boolean; editada: boolean } {
  const t = textos[codigo]
  if (t === undefined) return { valor: guardado, invalida: false, editada: false }
  const r = leerNumero(t)
  if (!r.ok || r.valor === null || r.valor < 0) return { valor: guardado, invalida: true, editada: true }
  return { valor: r.valor, invalida: false, editada: r.valor !== guardado }
}
const leerOferta = (codigo: string) => leerNodo(editOferta.value, codigo, ofertaGuardada(codigo))
const leerCap = (codigo: string) => leerNodo(editCap.value, codigo, capacidadGuardada(codigo))

const cambiosOferta = computed(() => (matriz.value?.empresas ?? []).filter((e) => { const l = leerOferta(e.codigo); return l.editada && !l.invalida }))
const cambiosCap = computed(() => (matriz.value?.plantas ?? []).filter((p) => { const l = leerCap(p.codigo); return l.editada && !l.invalida }))

const hayInvalidas = computed(() => {
  const m = matriz.value
  return (
    !!m &&
    (m.empresas.some((_, i) => m.plantas.some((_, j) => leer(i, j).invalida)) ||
      m.empresas.some((e) => leerOferta(e.codigo).invalida) ||
      m.plantas.some((p) => leerCap(p.codigo).invalida))
  )
})
const totalCambios = computed(() => cambios.value.length + cambiosOferta.value.length + cambiosCap.value.length)
const hayCambios = computed(() => totalCambios.value > 0)

/** Totales en vivo (solo estaciones activas, con las ediciones aplicadas). */
const totalOferta = computed(() => sumar((matriz.value?.empresas ?? []).filter((e) => e.activa).map((e) => leerOferta(e.codigo).valor)))
const totalCapacidad = computed(() => sumar((matriz.value?.plantas ?? []).filter((p) => p.activa).map((p) => leerCap(p.codigo).valor)))
const balance = computed(() => equilibrio(totalOferta.value, totalCapacidad.value))

function escribirNodo(tipo: 'oferta' | 'cap', codigo: string, texto: string): void {
  if (tipo === 'oferta') editOferta.value = { ...editOferta.value, [codigo]: texto }
  else editCap.value = { ...editCap.value, [codigo]: texto }
}
function salirNodo(tipo: 'oferta' | 'cap', codigo: string): void {
  const l = tipo === 'oferta' ? leerOferta(codigo) : leerCap(codigo)
  if (!l.invalida) escribirNodo(tipo, codigo, formatearNumero(l.valor, { maxDecimales: 2 }))
}
function textoNodo(tipo: 'oferta' | 'cap', codigo: string): string {
  const t = (tipo === 'oferta' ? editOferta.value : editCap.value)[codigo]
  if (t !== undefined) return t
  return formatearNumero(tipo === 'oferta' ? ofertaGuardada(codigo) : capacidadGuardada(codigo), { maxDecimales: 2 })
}

/* ---- Plan de toneladas asignadas ---- */
const plan = computed(() => {
  const m = matriz.value
  const r = resultados.ultimoExacto
  if (!m || !r || !r.factible) return null
  return planPorCeldas(m.empresas.map((e) => e.codigo), m.plantas.map((p) => p.codigo), r.asignaciones)
})

async function calcularPlan(): Promise<void> {
  calculando.value = true
  errorPlan.value = ''
  try {
    const r = await solicitar<EjecucionResultado>('/optimizacion/exacto/', { metodo: 'POST', cuerpo: { modo_oferta: 'exact', guardar: false }, timeoutMs: TIMEOUT_CALCULO_MS })
    resultados.guardarExacto(r.resultado)
    if (!r.resultado.factible) errorPlan.value = 'Con los datos guardados no hay una distribución posible: revisa que la capacidad alcance para toda la oferta.'
  } catch (e) {
    errorPlan.value = textoDeError(e) || 'No se pudo calcular la asignación.'
  } finally {
    calculando.value = false
  }
}
watch(vista, (v) => {
  if (v === 'asignacion' && !resultados.ultimoExacto && !calculando.value) void calcularPlan()
})

/* ---- Distancias ---- */
function rutaDe(i: number, j: number): RutaApi | undefined {
  const m = matriz.value
  const e = m?.empresas[i]?.codigo
  const p = m?.plantas[j]?.codigo
  return rutasApi.value.find((r) => r.empresa === e && r.planta === p)
}

/** Costo total por tonelada (transporte + operación + precio) con las ediciones aplicadas. */
function efectivo(i: number, j: number): number | null {
  const m = matriz.value
  const total = m?.costos_totales[i]?.[j]
  const base = original(i, j)
  const c = leer(i, j)
  if (c.valor === null || total === null || total === undefined || base === null) return c.valor
  return total - base + c.valor
}

/** Para cada empresa (fila), la columna con el menor costo total. */
const masBarata = computed(() => {
  const m = matriz.value
  return (m?.empresas ?? []).map((_, i) => {
    let mejor = -1
    let menor = Infinity
    ;(m?.plantas ?? []).forEach((_p, j) => {
      const v = efectivo(i, j)
      if (v !== null && v < menor) {
        menor = v
        mejor = j
      }
    })
    return mejor
  })
})

function detalle(i: number, j: number): string {
  const m = matriz.value
  const e = m?.empresas[i]
  const p = m?.plantas[j]
  const ruta = m?.rutas.find((r) => r.empresa === e?.codigo && r.planta === p?.codigo)
  if (leer(i, j).editada) return 'Valor editado, aún sin guardar.'
  if (!ruta || ruta.costo_unitario === null) return 'No hay ruta definida entre estas dos estaciones.'
  if (ruta.distancia_km !== null && ruta.tarifa_km_ton !== null) {
    return `${formatearNumero(ruta.distancia_km, { maxDecimales: 1 })} km × ${formatearMoneda(ruta.tarifa_km_ton)} por tonelada y km = ${formatearMoneda(ruta.costo_unitario)} por tonelada`
  }
  return `Costo fijo de ${formatearMoneda(ruta.costo_unitario)} por tonelada (sin distancia ni tarifa)`
}

function valorMostrado(i: number, j: number): string {
  const t = editados.value[clave(i, j)]
  if (t !== undefined) return t
  const v = original(i, j)
  return v === null ? '' : formatearNumero(v, { maxDecimales: 2 })
}
function escribir(i: number, j: number, texto: string): void {
  editados.value = { ...editados.value, [clave(i, j)]: texto }
}
/** Al salir de la celda, un valor válido se muestra con separador de miles. */
function alSalir(i: number, j: number): void {
  const c = leer(i, j)
  if (c.invalida) return
  editados.value = { ...editados.value, [clave(i, j)]: c.valor === null ? '' : formatearNumero(c.valor, { maxDecimales: 2 }) }
}

async function cargar(silencioso = false): Promise<void> {
  if (!silencioso) {
    cargando.value = true
    error.value = ''
  }
  try {
    const [m, e, p, r] = await Promise.all([
      solicitar<MatrizCostos>('/red/matriz-costos/'),
      listarTodo<NodoApi>('/empresas/'),
      listarTodo<NodoApi>('/plantas/'),
      listarTodo<RutaApi>('/rutas/'),
    ])
    matriz.value = m
    empresasApi.value = e
    plantasApi.value = p
    rutasApi.value = r
    editados.value = {}
    editOferta.value = {}
    editCap.value = {}
  } catch (e) {
    error.value = textoDeError(e)
  } finally {
    if (!silencioso) cargando.value = false
  }
}
onMounted(() => void cargar())

async function guardar(): Promise<void> {
  const m = matriz.value
  if (!m || !hayCambios.value || hayInvalidas.value) return
  error.value = ''
  exito.value = ''
  // Celda vacía = quitar la ruta (se desactiva); con valor = costo unitario directo y ruta activa.
  const rutas = cambios.value.map((c) => {
    const empresa = m.empresas[c.i]?.codigo
    const planta = m.plantas[c.j]?.codigo
    return c.valor === null ? { empresa, planta, activa: false } : { empresa, planta, costo_unitario: c.valor, activa: true }
  })
  guardando.value = true
  try {
    if (rutas.length) await solicitar<MatrizCostos>('/red/matriz-costos/', { metodo: 'PUT', cuerpo: { rutas } })
    for (const e of cambiosOferta.value) {
      const id = empresasApi.value.find((x) => x.codigo === e.codigo)?.id
      if (id !== undefined) await solicitar(`/empresas/${id}/`, { metodo: 'PATCH', cuerpo: { oferta: leerOferta(e.codigo).valor } })
    }
    for (const p of cambiosCap.value) {
      const id = plantasApi.value.find((x) => x.codigo === p.codigo)?.id
      if (id !== undefined) await solicitar(`/plantas/${id}/`, { metodo: 'PATCH', cuerpo: { capacidad: leerCap(p.codigo).valor } })
    }
    const n = totalCambios.value
    resultados.guardarExacto(null)
    await cargar(true)
    exito.value = `Cambios guardados (${n}). Los próximos cálculos ya los usan.`
    void red.cargar()
  } catch (e) {
    const msg = textoDeError(e) || 'No se pudo guardar. Revisa los datos e inténtalo de nuevo.'
    await cargar(true)
    error.value = msg
  } finally {
    guardando.value = false
  }
}

function descartar(): void {
  editados.value = {}
  editOferta.value = {}
  editCap.value = {}
  error.value = ''
}

onBeforeRouteLeave(() => !hayCambios.value || window.confirm('Tienes cambios sin guardar en la matriz. ¿Salir de todos modos?'))
</script>

<template>
  <section class="vista">
    <UiPageHeader
      titulo="Matriz de costos"
      descripcion="Aquí puedes ver y corregir cuánto cuesta llevar una tonelada de cada empresa a cada planta (en pesos colombianos). El valor más bajo de cada empresa está resaltado."
    />

    <UiAlert v-if="!auth.esAdministrador" tono="info">Tu rol es de solo lectura: solo un administrador puede editar los costos.</UiAlert>
    <UiAlert v-if="exito" tono="exito">{{ exito }}</UiAlert>
    <UiAlert v-if="error" tono="error" titulo="No se pudo completar la acción">{{ error }}</UiAlert>

    <p v-if="cargando" class="nota" role="status"><UiSpinner :tamano="16" /> Cargando los costos…</p>
    <UiEmptyState v-else-if="!matriz || matriz.empresas.length === 0 || matriz.plantas.length === 0" icono="red" titulo="Aún no hay costos que mostrar" descripcion="Agrega al menos una empresa y una planta en «Red logística»; sus costos aparecerán aquí." />
    <template v-else>
      <div class="barra-guardado" :class="{ 'barra-guardado--activa': hayCambios }" role="status" aria-live="polite">
        <span v-if="hayInvalidas" class="barra-guardado__texto barra-guardado__texto--error">Hay valores que no son un número válido (marcados en rojo). Corrígelos para poder guardar.</span>
        <span v-else-if="hayCambios" class="barra-guardado__texto"><strong>{{ totalCambios }}</strong> {{ totalCambios === 1 ? 'cambio sin guardar' : 'cambios sin guardar' }}</span>
        <span v-else class="nota">{{ auth.esAdministrador ? 'Escribe sobre un costo, una oferta o una capacidad para cambiarlo. Dejar un costo vacío quita esa ruta.' : 'Solo lectura.' }}</span>
        <div v-if="auth.esAdministrador" class="fila-botones">
          <UiButton variante="fantasma" :disabled="!hayCambios || guardando" @click="descartar">Descartar cambios</UiButton>
          <UiButton :disabled="!hayCambios || hayInvalidas" :loading="guardando" @click="guardar">Guardar cambios</UiButton>
        </div>
      </div>

      <div class="fila-botones">
        <UiSegmented v-model="vista" etiqueta="Qué mostrar en la tabla" :opciones="[{ valor: 'costos', etiqueta: 'Costos' }, { valor: 'asignacion', etiqueta: 'Toneladas asignadas' }]" />
        <UiButton v-if="vista === 'asignacion'" variante="secundario" :loading="calculando" @click="calcularPlan">Calcular y ver asignación</UiButton>
      </div>
      <p class="nota">Cada celda es el costo por tonelada; la última columna y fila muestran cuánto ofrece cada empresa y cuánto puede recibir cada planta.</p>
      <UiAlert v-if="errorPlan" tono="aviso">{{ errorPlan }}</UiAlert>
      <UiAlert v-if="vista === 'asignacion' && !plan && !calculando && !errorPlan" tono="info">Pulsa «Calcular y ver asignación» para ver cuántas toneladas debe enviar cada empresa a cada planta.</UiAlert>
      <UiAlert v-if="vista === 'asignacion' && plan && hayCambios" tono="aviso">Esta asignación se calculó con los datos guardados; guarda tus cambios y vuelve a calcular para actualizarla.</UiAlert>

      <div class="tabla-scroll">
        <table class="tabla tabla--entrada tabla--matriz" :style="{ minWidth: `calc(18.5rem + ${matriz.plantas.length} * 6.5rem)` }">
          <caption class="sr-only">{{ vista === 'costos' ? 'Costo en pesos por tonelada, de cada empresa a cada planta, con la oferta de cada empresa y la capacidad de cada planta' : 'Toneladas por semana que cada empresa envía a cada planta' }}</caption>
          <thead>
            <tr>
              <th scope="col">Empresa ↓ &nbsp; Planta →</th>
              <th v-for="p in matriz.plantas" :key="p.codigo" scope="col" class="num">{{ p.nombre }}<small>{{ p.codigo }} · {{ vista === 'costos' ? 'COP/t' : 't/semana' }}</small></th>
              <th scope="col" class="num col-total">{{ vista === 'costos' ? 'Oferta (t/semana)' : 'Total enviado (t/semana)' }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(e, i) in matriz.empresas" :key="e.codigo" :class="{ 'fila-inactiva': !e.activa }">
              <th scope="row">{{ e.nombre }}<small>{{ e.codigo }}</small></th>
              <template v-if="vista === 'costos'">
                <td v-for="(p, j) in matriz.plantas" :key="p.codigo" class="num" :class="{ 'celda-barata': masBarata[i] === j }" :title="detalle(i, j)">
                  <label class="sr-only" :for="`c-${i}-${j}`">Costo por tonelada de {{ e.nombre }} a {{ p.nombre }}, en pesos</label>
                  <input
                    :id="`c-${i}-${j}`"
                    type="text"
                    inputmode="decimal"
                    autocomplete="off"
                    :value="valorMostrado(i, j)"
                    :disabled="!auth.esAdministrador || guardando"
                    :aria-invalid="leer(i, j).invalida || undefined"
                    :class="{ 'celda-cambiada': leer(i, j).editada && !leer(i, j).invalida, 'celda-invalida': leer(i, j).invalida }"
                    @input="escribir(i, j, ($event.target as HTMLInputElement).value)"
                    @blur="alSalir(i, j)"
                    @focus="($event.target as HTMLInputElement).select()"
                  />
                  <span v-if="masBarata[i] === j" class="celda__marca">Más barata</span>
                  <span v-else-if="efectivo(i, j) !== null && efectivo(i, j) !== leer(i, j).valor" class="celda__sub">Total {{ formatearMoneda(efectivo(i, j)) }}</span>
                  <span v-if="rutaDe(i, j)?.distancia_km != null" class="celda__sub"><InsigniaDistancia :km="rutaDe(i, j)?.distancia_km" :fuente="rutaDe(i, j)?.distancia_fuente" /></span>
                </td>
                <td class="num col-total">
                  <label class="sr-only" :for="`o-${i}`">Oferta semanal de {{ e.nombre }}, en toneladas</label>
                  <input
                    :id="`o-${i}`"
                    type="text"
                    inputmode="decimal"
                    autocomplete="off"
                    :value="textoNodo('oferta', e.codigo)"
                    :disabled="!auth.esAdministrador || guardando"
                    :aria-invalid="leerOferta(e.codigo).invalida || undefined"
                    :class="{ 'celda-cambiada': leerOferta(e.codigo).editada && !leerOferta(e.codigo).invalida, 'celda-invalida': leerOferta(e.codigo).invalida }"
                    @input="escribirNodo('oferta', e.codigo, ($event.target as HTMLInputElement).value)"
                    @blur="salirNodo('oferta', e.codigo)"
                    @focus="($event.target as HTMLInputElement).select()"
                  />
                </td>
              </template>
              <template v-else>
                <td v-for="(p, j) in matriz.plantas" :key="p.codigo" class="num" :class="{ 'celda-cero': !plan || (plan.toneladas[i]?.[j] ?? 0) < 1e-6 }">
                  <template v-if="plan">{{ (plan.toneladas[i]?.[j] ?? 0) < 1e-6 ? '0' : formatearNumero(plan.toneladas[i]?.[j] ?? 0, { maxDecimales: 1 }) }}</template>
                  <template v-else>—</template>
                </td>
                <td class="num col-total">
                  <template v-if="plan">
                    {{ formatearNumero(plan.porEmpresa[i] ?? 0, { maxDecimales: 1 }) }} t
                    <span v-if="coincide(plan.porEmpresa[i] ?? 0, ofertaGuardada(e.codigo))" class="ok" title="Se retira toda la oferta de la empresa"><span aria-hidden="true">✔</span><span class="sr-only">Cumple su oferta</span></span>
                    <span v-else class="celda__sub">de {{ formatearNumero(ofertaGuardada(e.codigo), { maxDecimales: 1 }) }} t</span>
                  </template>
                  <template v-else>—</template>
                </td>
              </template>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <th scope="row">{{ vista === 'costos' ? 'Capacidad (t/semana)' : 'Total recibido (t/semana)' }}</th>
              <template v-if="vista === 'costos'">
                <td v-for="p in matriz.plantas" :key="p.codigo" class="num" :class="{ 'fila-inactiva': !p.activa }">
                  <label class="sr-only" :for="`k-${p.codigo}`">Capacidad semanal de {{ p.nombre }}, en toneladas</label>
                  <input
                    :id="`k-${p.codigo}`"
                    type="text"
                    inputmode="decimal"
                    autocomplete="off"
                    :value="textoNodo('cap', p.codigo)"
                    :disabled="!auth.esAdministrador || guardando"
                    :aria-invalid="leerCap(p.codigo).invalida || undefined"
                    :class="{ 'celda-cambiada': leerCap(p.codigo).editada && !leerCap(p.codigo).invalida, 'celda-invalida': leerCap(p.codigo).invalida }"
                    @input="escribirNodo('cap', p.codigo, ($event.target as HTMLInputElement).value)"
                    @blur="salirNodo('cap', p.codigo)"
                    @focus="($event.target as HTMLInputElement).select()"
                  />
                </td>
                <td class="num col-total esquina">
                  <span class="esquina__linea">Oferta total: <strong>{{ formatearNumero(totalOferta, { maxDecimales: 1 }) }} t</strong></span>
                  <span class="esquina__linea">Capacidad total: <strong>{{ formatearNumero(totalCapacidad, { maxDecimales: 1 }) }} t</strong></span>
                </td>
              </template>
              <template v-else>
                <td v-for="(p, j) in matriz.plantas" :key="p.codigo" class="num">
                  <template v-if="plan">
                    {{ formatearNumero(plan.porPlanta[j] ?? 0, { maxDecimales: 1 }) }} t
                    <UiUsageBar :etiqueta="`Uso de ${p.nombre}`" :valor="plan.porPlanta[j] ?? 0" :maximo="capacidadGuardada(p.codigo)" :critico="llena(plan.porPlanta[j] ?? 0, capacidadGuardada(p.codigo))" texto-critico="Planta llena" />
                  </template>
                  <template v-else>—</template>
                </td>
                <td class="num col-total esquina">
                  <template v-if="plan"><span class="esquina__linea">Costo total semanal</span><strong>{{ formatearMoneda(plan.costoTotal) }}</strong></template>
                  <template v-else>—</template>
                </td>
              </template>
            </tr>
          </tfoot>
        </table>
      </div>

      <UiAlert v-if="balance.alcanza" tono="exito">La red alcanza: sobran {{ formatearNumero(balance.diferencia, { maxDecimales: 1 }) }} t de capacidad.</UiAlert>
      <UiAlert v-else tono="error">La red NO alcanza: faltan {{ formatearNumero(balance.diferencia, { maxDecimales: 1 }) }} t de capacidad para recibir toda la oferta.</UiAlert>

      <p v-if="vista === 'costos'" class="nota">
        Pasa el cursor sobre un costo para ver cómo se calcula (distancia × tarifa). «Total» incluye también la operación de la planta y el precio de los residuos.
        Las celdas con fondo ámbar tienen cambios sin guardar. Los totales incluyen solo empresas y plantas activas.
      </p>
      <p class="nota">Las distancias se calculan sobre las carreteras de OpenStreetMap (ruta por carretera más corta/rápida); pueden diferir de la ruta que tome un transportista.</p>
      <RecalcularDistancias v-if="auth.esAdministrador" @hecho="cargar(true)" />
    </template>
  </section>
</template>

<style scoped>
.barra-guardado {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-3);
  padding: var(--espacio-2) var(--espacio-4);
  border: 1px solid var(--color-borde);
  border-radius: var(--radio-md);
  background: var(--color-superficie);
}

.barra-guardado--activa {
  border-color: var(--color-aviso);
  background: var(--color-aviso-fondo);
}

.barra-guardado__texto--error {
  color: var(--color-error);
  font-weight: var(--peso-medio);
}

/* La matriz debe caber en pantalla: columnas repartidas, texto que se envuelve y campos que se adaptan.
   El scroll horizontal solo aparece como último recurso (muchas plantas, ver min-width en la plantilla). */
.tabla--matriz {
  table-layout: fixed;
  width: 100%;
  font-size: var(--texto-xs);
}

.tabla--matriz th,
.tabla--matriz td {
  padding: 0.4rem 0.4rem;
  white-space: normal;
  overflow-wrap: anywhere;
}

.tabla--matriz thead th:not(:first-child):not(.col-total) {
  text-align: center;
  line-height: 1.2;
}

.tabla--matriz th:first-child {
  width: 10rem;
}

.tabla--matriz th.col-total,
.tabla--matriz td.col-total {
  width: 8.5rem;
}

.tabla--matriz td input {
  width: 100%;
  min-width: 0;
  padding: 0.3rem 0.35rem;
  font-size: var(--texto-sm);
}

.tabla--matriz th small {
  display: block;
  font-weight: var(--peso-normal);
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
}

.tabla--matriz tbody th {
  text-align: left;
  font-weight: var(--peso-fuerte);
}

.tabla--matriz td {
  vertical-align: top;
}

.celda-barata {
  background: var(--color-acento-suave);
}

.celda-barata input {
  border-color: var(--color-activo-barra);
  font-weight: var(--peso-fuerte);
}

.celda__marca,
.celda__sub {
  display: block;
  margin-top: 0.15rem;
  font-size: var(--texto-xs);
}

.celda__marca {
  font-weight: var(--peso-fuerte);
  color: var(--color-primario);
}

.celda__sub {
  color: var(--color-texto-suave);
}

.col-total {
  background: var(--color-superficie-2);
  font-weight: var(--peso-medio);
}

.tabla--matriz tfoot th,
.tabla--matriz tfoot td {
  border-top: 2px solid var(--color-borde-fuerte);
  text-align: left;
}

.tabla--matriz tfoot td.num {
  text-align: right;
}

.esquina__linea {
  display: block;
  font-size: var(--texto-xs);
  font-weight: var(--peso-normal);
}

.celda-cero {
  color: var(--color-texto-suave);
  opacity: 0.55;
}

.ok {
  margin-left: 0.25rem;
  color: var(--color-activo-texto);
  font-weight: var(--peso-fuerte);
}

.tabla--entrada input.celda-invalida {
  border-color: var(--color-error);
  background: var(--color-error-fondo);
}
</style>
