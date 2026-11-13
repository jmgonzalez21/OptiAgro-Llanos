<script setup lang="ts">
/** Rutas entre empresas y plantas: listado, alta manual, edición, activación y eliminación (administrador). */
import { computed, onMounted, reactive, ref } from 'vue'
import InsigniaDistancia from '@/components/InsigniaDistancia.vue'
import RecalcularDistancias from '@/components/RecalcularDistancias.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiConfirmDialog from '@/components/ui/UiConfirmDialog.vue'
import UiEmptyState from '@/components/ui/UiEmptyState.vue'
import UiField from '@/components/ui/UiField.vue'
import UiModal from '@/components/ui/UiModal.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiSpinner from '@/components/ui/UiSpinner.vue'
import { formatearMoneda, formatearNumero } from '@/components/ui/formato'
import { leerErrores, listarTodo, solicitar } from '@/api/util'
import { useRedStore } from '@/stores/red'

interface Ruta {
  id: number
  empresa: string
  planta: string
  distancia_km: number | null
  distancia_fuente?: 'carretera' | 'estimada' | 'manual'
  tarifa_km_ton: number | null
  costo_unitario: number | null
  limite: number | null
  activa: boolean
}
interface Nodo {
  codigo: string
  nombre: string
}

const props = defineProps<{ esAdmin: boolean }>()
const red = useRedStore()

const filas = ref<Ruta[]>([])
const empresas = ref<Nodo[]>([])
const plantas = ref<Nodo[]>([])
const cargando = ref(true)
const error = ref('')
const mensaje = ref('')
const busqueda = ref('')
const filtro = ref<'todas' | 'activas' | 'inactivas'>('todas')

const nombreDe = (lista: Nodo[], codigo: string): string => lista.find((n) => n.codigo === codigo)?.nombre ?? codigo

const filtradas = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  return filas.value.filter((r) => {
    if (filtro.value === 'activas' && !r.activa) return false
    if (filtro.value === 'inactivas' && r.activa) return false
    return !q || `${r.empresa} ${r.planta} ${nombreDe(empresas.value, r.empresa)} ${nombreDe(plantas.value, r.planta)}`.toLowerCase().includes(q)
  })
})

async function cargar(): Promise<void> {
  cargando.value = true
  error.value = ''
  try {
    const [r, e, p] = await Promise.all([listarTodo<Ruta>('/rutas/'), listarTodo<Nodo>('/empresas/'), listarTodo<Nodo>('/plantas/')])
    filas.value = r
    empresas.value = e
    plantas.value = p
  } catch (e) {
    error.value = leerErrores(e).general || 'No se pudieron cargar las rutas.'
  } finally {
    cargando.value = false
  }
}
onMounted(cargar)

/* ---- Formulario ---- */
const abierto = ref(false)
const editando = ref<Ruta | null>(null)
const guardando = ref(false)
const f = reactive({ empresa: '', planta: '', distancia: '', tarifa: '', costo: '', limite: '', activa: true })
const errores = ref<Record<string, string>>({})
const errorForm = ref('')

// Los campos numéricos de Vue entregan number en tiempo de ejecución: se normaliza a texto.
const aNumero = (t: string | number): number | null => {
  const s = String(t ?? '').trim().replace(',', '.')
  if (s === '') return null
  const n = Number(s)
  return Number.isFinite(n) ? n : null
}
const texto = (v: number | null): string => (v === null || v === undefined ? '' : String(v))

function abrir(r: Ruta | null): void {
  editando.value = r
  errores.value = {}
  errorForm.value = ''
  mensaje.value = ''
  f.empresa = r?.empresa ?? ''
  f.planta = r?.planta ?? ''
  f.distancia = texto(r?.distancia_km ?? null)
  f.tarifa = texto(r?.tarifa_km_ton ?? null)
  f.costo = texto(r?.costo_unitario ?? null)
  f.limite = texto(r?.limite ?? null)
  f.activa = r ? r.activa : true
  abierto.value = true
}

const costoEstimado = computed(() => {
  const d = aNumero(f.distancia)
  const t = aNumero(f.tarifa)
  return d !== null && t !== null ? d * t : null
})

async function guardar(): Promise<void> {
  const e: Record<string, string> = {}
  if (!editando.value) {
    if (!f.empresa) e.empresa = 'Elige la empresa de origen.'
    if (!f.planta) e.planta = 'Elige la planta de destino.'
  }
  const tieneDistTarifa = aNumero(f.distancia) !== null && aNumero(f.tarifa) !== null
  const calculable = !editando.value && aNumero(f.tarifa) !== null // el backend calcula la distancia por carretera
  if (!tieneDistTarifa && !calculable && aNumero(f.costo) === null) e.distancia = 'Indica la tarifa (la distancia se calcula sola) o un costo por tonelada en «Opciones avanzadas».'
  errores.value = e
  if (Object.keys(e).length) {
    errorForm.value = 'Revisa los campos marcados.'
    return
  }
  guardando.value = true
  errorForm.value = ''
  const cuerpo: Record<string, unknown> = {
    // En un alta sin distancia no se envía el campo: el backend la calcula por carretera.
    ...(editando.value || aNumero(f.distancia) !== null ? { distancia_km: aNumero(f.distancia) } : {}),
    tarifa_km_ton: aNumero(f.tarifa),
    costo_unitario: tieneDistTarifa ? null : aNumero(f.costo),
    limite: aNumero(f.limite),
    activa: f.activa,
  }
  try {
    if (editando.value) await solicitar(`/rutas/${editando.value.id}/`, { metodo: 'PATCH', cuerpo })
    else await solicitar('/rutas/', { metodo: 'POST', cuerpo: { ...cuerpo, empresa: f.empresa, planta: f.planta } })
    abierto.value = false
    mensaje.value = editando.value ? 'Cambios guardados.' : 'Ruta agregada.'
    await Promise.all([cargar(), red.cargar()])
  } catch (err) {
    const r = leerErrores(err)
    errores.value = Object.fromEntries(Object.entries(r.campos).filter(([k]) => ['empresa', 'planta', 'distancia_km', 'tarifa_km_ton'].includes(k)).map(([k, v]) => [k === 'distancia_km' ? 'distancia' : k === 'tarifa_km_ton' ? 'tarifa' : k, v]))
    errorForm.value = r.general || Object.values(r.campos).join(' ') || 'No se pudo guardar la ruta.'
  } finally {
    guardando.value = false
  }
}

/* ---- Acciones ---- */
const ocupada = ref<number | null>(null)
const aEliminar = ref<Ruta | null>(null)

async function alternar(r: Ruta): Promise<void> {
  ocupada.value = r.id
  error.value = ''
  try {
    await solicitar(`/rutas/${r.id}/`, { metodo: 'PATCH', cuerpo: { activa: !r.activa } })
    mensaje.value = r.activa ? 'Ruta desactivada: ya no se usa en los cálculos.' : 'Ruta activada.'
    await Promise.all([cargar(), red.cargar()])
  } catch (e) {
    error.value = leerErrores(e).general || 'No se pudo cambiar el estado.'
  } finally {
    ocupada.value = null
  }
}

async function eliminar(): Promise<void> {
  const r = aEliminar.value
  if (!r) return
  ocupada.value = r.id
  try {
    await solicitar(`/rutas/${r.id}/`, { metodo: 'DELETE' })
    mensaje.value = 'Ruta eliminada.'
    aEliminar.value = null
    await Promise.all([cargar(), red.cargar()])
  } catch (e) {
    aEliminar.value = null
    error.value = leerErrores(e).general || 'No se pudo eliminar la ruta.'
  } finally {
    ocupada.value = null
  }
}

const recargarTodo = (): Promise<unknown> => Promise.all([cargar(), red.cargar()])

defineExpose({ abrir })
</script>

<template>
  <div class="vista__seccion">
    <div class="herramientas">
      <div class="herramientas__crece">
        <UiField id="buscar-rutas" v-model="busqueda" label="Buscar" type="search" placeholder="Empresa o planta" icono="buscar" />
      </div>
      <UiSelect
        id="filtro-rutas"
        v-model="filtro"
        label="Mostrar"
        :opciones="[
          { valor: 'todas', etiqueta: 'Todas' },
          { valor: 'activas', etiqueta: 'Solo activas' },
          { valor: 'inactivas', etiqueta: 'Solo inactivas' },
        ]"
      />
    </div>

    <UiAlert v-if="mensaje" tono="exito">{{ mensaje }}</UiAlert>
    <UiAlert v-if="error" tono="error" titulo="No se pudo completar la acción">
      {{ error }}
      <template #acciones><UiButton variante="secundario" tamano="sm" @click="cargar">Reintentar</UiButton></template>
    </UiAlert>

    <p v-if="cargando" class="nota" role="status"><UiSpinner :tamano="16" /> Cargando rutas…</p>
    <UiEmptyState v-else-if="filas.length === 0 && !error" icono="red" titulo="Aún no hay rutas" :descripcion="esAdmin ? 'Las rutas se crean solas al agregar una empresa o planta; también puedes agregar una a mano.' : ''">
      <UiButton v-if="esAdmin" @click="abrir(null)">Agregar ruta</UiButton>
    </UiEmptyState>
    <UiEmptyState v-else-if="filtradas.length === 0 && filas.length > 0" icono="buscar" titulo="Sin resultados" descripcion="Ninguna ruta coincide con la búsqueda o el filtro." />
    <div v-else-if="filas.length > 0" class="tabla-scroll">
      <table class="tabla">
        <caption class="sr-only">Rutas de la red</caption>
        <thead>
          <tr>
            <th scope="col">Desde (empresa)</th>
            <th scope="col">Hacia (planta)</th>
            <th scope="col" class="num">Distancia</th>
            <th scope="col" class="num">Costo por tonelada</th>
            <th scope="col" class="num">Límite</th>
            <th scope="col">Estado</th>
            <th v-if="esAdmin" scope="col"><span class="sr-only">Acciones</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in filtradas" :key="r.id" :class="{ 'fila-inactiva': !r.activa }">
            <td>{{ nombreDe(empresas, r.empresa) }} <small class="nota">{{ r.empresa }}</small></td>
            <td>{{ nombreDe(plantas, r.planta) }} <small class="nota">{{ r.planta }}</small></td>
            <td class="num"><InsigniaDistancia :km="r.distancia_km" :fuente="r.distancia_fuente" /></td>
            <td class="num">{{ r.costo_unitario === null ? '—' : formatearMoneda(r.costo_unitario) }}</td>
            <td class="num">{{ r.limite === null ? 'Sin límite' : `${formatearNumero(r.limite, { maxDecimales: 1 })} t/semana` }}</td>
            <td><UiBadge :tono="r.activa ? 'verde' : 'neutro'" punto>{{ r.activa ? 'Activa' : 'Inactiva' }}</UiBadge></td>
            <td v-if="esAdmin">
              <div class="fila-botones">
                <UiButton variante="secundario" tamano="sm" :disabled="ocupada === r.id" @click="abrir(r)">Editar</UiButton>
                <UiButton variante="fantasma" tamano="sm" :disabled="ocupada === r.id" @click="alternar(r)">{{ r.activa ? 'Desactivar' : 'Activar' }}</UiButton>
                <UiButton variante="peligro" tamano="sm" :disabled="ocupada === r.id" @click="aEliminar = r">Eliminar</UiButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="!cargando && filas.length" class="nota">Mostrando {{ filtradas.length }} de {{ filas.length }} rutas. Las distancias se calculan sobre las carreteras de OpenStreetMap (ruta por carretera más corta/rápida); pueden diferir de la ruta que tome un transportista.</p>
    <RecalcularDistancias v-if="props.esAdmin" @hecho="recargarTodo" />

    <UiModal v-model:abierto="abierto" :titulo="editando ? 'Editar ruta' : 'Agregar ruta'" ancho="lg" :bloquear-cierre="guardando">
      <form id="form-ruta" class="vista__seccion" novalidate @submit.prevent="guardar">
        <UiAlert v-if="errorForm" tono="error">{{ errorForm }}</UiAlert>
        <div class="formulario-grid">
          <UiSelect id="ruta-empresa" v-model="f.empresa" label="Empresa de origen *" placeholder="Elige una empresa" :opciones="empresas.map((n) => ({ valor: n.codigo, etiqueta: n.nombre }))" :disabled="!!editando" :error="errores.empresa" />
          <UiSelect id="ruta-planta" v-model="f.planta" label="Planta de destino *" placeholder="Elige una planta" :opciones="plantas.map((n) => ({ valor: n.codigo, etiqueta: n.nombre }))" :disabled="!!editando" :error="errores.planta" />
          <UiField id="ruta-distancia" v-model="f.distancia" label="Distancia (km)" type="number" min="0" step="any" :error="errores.distancia" />
          <UiField id="ruta-tarifa" v-model="f.tarifa" label="Tarifa (COP por tonelada y km)" type="number" min="0" step="any" :error="errores.tarifa" />
        </div>
        <p v-if="!editando" class="nota">Si dejas la distancia vacía, se calcula sola por carretera. Si la escribes, queda como «Manual».</p>
        <p v-if="costoEstimado !== null" class="nota" role="status">Costo del transporte: {{ formatearMoneda(costoEstimado) }} por tonelada ({{ f.distancia }} km × {{ f.tarifa }}).</p>
        <details class="avanzadas">
          <summary>Opciones avanzadas</summary>
          <div class="formulario-grid">
            <UiField id="ruta-costo" v-model="f.costo" label="Costo fijo por tonelada (COP/t)" type="number" min="0" step="any" hint="Solo se usa si no indicas distancia y tarifa." />
            <UiField id="ruta-limite" v-model="f.limite" label="Límite de envío (t/semana)" type="number" min="0" step="any" hint="Vacío = sin límite." />
          </div>
        </details>
        <label v-if="editando" class="etiqueta-nativa"><span>Estado</span>
          <select v-model="f.activa"><option :value="true">Activa</option><option :value="false">Inactiva (no se usa en los cálculos)</option></select>
        </label>
      </form>
      <template #pie>
        <UiButton variante="fantasma" :disabled="guardando" @click="abierto = false">Cancelar</UiButton>
        <UiButton type="submit" form="form-ruta" :loading="guardando">{{ editando ? 'Guardar cambios' : 'Guardar ruta' }}</UiButton>
      </template>
    </UiModal>

    <UiConfirmDialog
      :abierto="aEliminar !== null"
      titulo="¿Eliminar esta ruta?"
      :descripcion="aEliminar ? `${nombreDe(empresas, aEliminar.empresa)} → ${nombreDe(plantas, aEliminar.planta)}` : ''"
      :impacto="['La empresa ya no podrá enviar a esa planta por esta ruta.', 'Esta acción no se puede deshacer.']"
      tono="peligro"
      texto-confirmar="Sí, eliminar"
      :cargando="ocupada !== null"
      @confirmar="eliminar"
      @cancelar="aEliminar = null"
      @update:abierto="(v) => { if (!v) aEliminar = null }"
    />
  </div>
</template>
