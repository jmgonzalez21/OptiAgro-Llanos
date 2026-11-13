<script setup lang="ts">
/**
 * Empresas o plantas de la red: listado limpio, alta guiada (municipio + pin en el mapa + rutas automáticas),
 * edición, activación y eliminación con el impacto explicado.
 */
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import MiniMapaUbicacion from '@/components/mapa/MiniMapaUbicacion.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCheckbox from '@/components/ui/UiCheckbox.vue'
import UiConfirmDialog from '@/components/ui/UiConfirmDialog.vue'
import UiEmptyState from '@/components/ui/UiEmptyState.vue'
import UiField from '@/components/ui/UiField.vue'
import UiIcon from '@/components/ui/UiIcon.vue'
import UiModal from '@/components/ui/UiModal.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiSpinner from '@/components/ui/UiSpinner.vue'
import { formatearMoneda, formatearNumero } from '@/components/ui/formato'
import { leerErrores, listarTodo, solicitar } from '@/api/util'
import { coordenadasValidas } from '@/composables/useEstaciones'
import { proponerRutas, siguienteCodigo, tarifaSugerida } from '@/composables/geo'
import { buscarMunicipio, MUNICIPIOS_META } from '@/data/municipiosMeta'
import { useRedStore } from '@/stores/red'
import { TIPOS_DEMANDA } from './configRed'

interface Fila {
  id: number
  codigo: string
  nombre: string
  municipio: string
  latitud: number | null
  longitud: number | null
  activa: boolean
  ficticio?: boolean
  oferta?: number
  precio_tonelada?: number
  capacidad?: number
  tipo_demanda?: string
  costo_operacion_ton?: number
}
interface RutaFila {
  empresa: string
  planta: string
  tarifa_km_ton: number | null
}

const props = defineProps<{ tipo: 'empresa' | 'planta'; esAdmin: boolean }>()
const red = useRedStore()
const router = useRouter()

const esEmpresa = computed(() => props.tipo === 'empresa')
const T = computed(() =>
  esEmpresa.value
    ? {
        ruta: 'empresas',
        singular: 'empresa',
        plural: 'empresas',
        prefijo: 'E',
        agregar: 'Agregar empresa',
        agregada: 'Empresa agregada',
        campoCantidad: 'oferta',
        etiquetaCantidad: 'Residuos que genera',
        columnaCantidad: 'Genera',
        contrarias: 'plantas',
        rutasHacia: 'las plantas',
        vacioTitulo: 'Aún no hay empresas',
        vacioTexto: 'Agrega la primera empresa generadora de residuos para empezar a armar la red.',
      }
    : {
        ruta: 'plantas',
        singular: 'planta',
        plural: 'plantas',
        prefijo: 'P',
        agregar: 'Agregar planta',
        agregada: 'Planta agregada',
        campoCantidad: 'capacidad',
        etiquetaCantidad: 'Capacidad de recepción',
        columnaCantidad: 'Recibe hasta',
        contrarias: 'empresas',
        rutasHacia: 'las empresas',
        vacioTitulo: 'Aún no hay plantas',
        vacioTexto: 'Agrega la primera planta de procesamiento para recibir los residuos.',
      },
)

const filas = ref<Fila[]>([])
const contrarias = ref<Fila[]>([])
const rutas = ref<RutaFila[]>([])
const cargando = ref(true)
const error = ref('')
const busqueda = ref('')
const filtro = ref<'todas' | 'activas' | 'inactivas'>('todas')

const filtradas = computed(() => {
  const q = busqueda.value.trim().toLowerCase()
  return filas.value.filter((f) => {
    if (filtro.value === 'activas' && !f.activa) return false
    if (filtro.value === 'inactivas' && f.activa) return false
    return !q || `${f.nombre} ${f.codigo} ${f.municipio}`.toLowerCase().includes(q)
  })
})

async function cargar(): Promise<void> {
  cargando.value = true
  error.value = ''
  try {
    const [propias, otras, todasRutas] = await Promise.all([
      listarTodo<Fila>(`/${T.value.ruta}/`),
      listarTodo<Fila>(`/${T.value.contrarias}/`),
      listarTodo<RutaFila>('/rutas/'),
    ])
    filas.value = propias
    contrarias.value = otras
    rutas.value = todasRutas
  } catch (e) {
    error.value = leerErrores(e).general || 'No se pudo cargar la información.'
  } finally {
    cargando.value = false
  }
}
onMounted(cargar)

const cantidadDe = (f: Fila): number => (esEmpresa.value ? (f.oferta ?? 0) : (f.capacidad ?? 0))
const numRutas = (f: Fila): number => rutas.value.filter((r) => r[props.tipo] === f.codigo).length
const ubicada = (f: Fila): boolean => coordenadasValidas(f.latitud, f.longitud)
const etiquetaDemanda = (v?: string): string => ({ exact: 'Debe recibir exactamente esa cantidad', minimum: 'Debe recibir al menos esa cantidad' })[v ?? ''] ?? ''

/* ---- Mensaje tras guardar ---- */
interface Resultado {
  titulo: string
  id: number
  ubicada: boolean
  activa: boolean
  rutasCreadas: number | null
  rutasFallidas: number
  rutasEstimadas: number
  sinUbicacion: number
  motivoFallo: string
}
const resultado = ref<Resultado | null>(null)
const mensaje = ref('')

function verEnMapa(id: number): void {
  void router.push({ name: 'inicio', query: { foco: `${props.tipo}-${id}` } })
}

/* ---- Formulario ---- */
const abierto = ref(false)
const editando = ref<Fila | null>(null)
const guardando = ref(false)
const f = reactive({
  nombre: '',
  municipio: '',
  latitud: '',
  longitud: '',
  cantidad: '',
  precio: '',
  tipoDemanda: 'capacity_max',
  costoOperacion: '',
  activa: true,
})
const crearRutas = ref(true)
const tarifa = ref('')
const errores = ref<Record<string, string>>({})
const errorForm = ref('')

// Los campos numéricos de Vue entregan number en tiempo de ejecución: se normaliza a texto.
const aNumero = (t: string | number): number | null => {
  const s = String(t ?? '').trim().replace(',', '.')
  if (s === '') return null
  const n = Number(s)
  return Number.isFinite(n) ? n : null
}
const latNum = computed(() => aNumero(f.latitud))
const lonNum = computed(() => aNumero(f.longitud))
const hayUbicacion = computed(() => coordenadasValidas(latNum.value, lonNum.value))

const opcionesMunicipio = computed(() => {
  const base = MUNICIPIOS_META.map((m) => ({ valor: m.nombre, etiqueta: m.nombre }))
  if (f.municipio && !buscarMunicipio(f.municipio)) base.unshift({ valor: f.municipio, etiqueta: f.municipio })
  return base
})

function alElegirMunicipio(): void {
  const m = buscarMunicipio(f.municipio)
  if (m) {
    f.latitud = String(m.latitud)
    f.longitud = String(m.longitud)
  }
}
watch(() => f.municipio, alElegirMunicipio)

/** Propuesta de rutas automáticas según la ubicación actual del pin. */
const propuesta = computed(() => {
  if (editando.value || !hayUbicacion.value) return { rutas: [], sinUbicacion: 0 }
  const t = aNumero(tarifa.value) ?? 0
  return proponerRutas(props.tipo, { codigo: '#', latitud: latNum.value as number, longitud: lonNum.value as number }, contrarias.value.filter((c) => c.activa), t)
})

function abrir(fila: Fila | null): void {
  editando.value = fila
  errores.value = {}
  errorForm.value = ''
  resultado.value = null
  mensaje.value = ''
  f.nombre = fila?.nombre ?? ''
  f.latitud = fila?.latitud != null ? String(fila.latitud) : ''
  f.longitud = fila?.longitud != null ? String(fila.longitud) : ''
  f.municipio = fila?.municipio ?? ''
  f.cantidad = fila ? String(cantidadDe(fila)) : ''
  f.precio = fila?.precio_tonelada != null ? String(fila.precio_tonelada) : ''
  f.tipoDemanda = fila?.tipo_demanda ?? 'capacity_max'
  f.costoOperacion = fila?.costo_operacion_ton != null ? String(fila.costo_operacion_ton) : ''
  f.activa = fila ? fila.activa : true
  crearRutas.value = true
  tarifa.value = String(tarifaSugerida(rutas.value.map((r) => r.tarifa_km_ton)))
  abierto.value = true
  // Al editar una estación sin pin pero con municipio conocido, se propone el pin del municipio.
  if (fila && !coordenadasValidas(fila.latitud, fila.longitud)) alElegirMunicipio()
}

function validar(): boolean {
  const e: Record<string, string> = {}
  if (!f.nombre.trim()) e.nombre = `Escribe el nombre de la ${T.value.singular}.`
  const c = aNumero(f.cantidad)
  if (c === null) e.cantidad = esEmpresa.value ? 'Indica cuántas toneladas por semana genera la empresa.' : 'Indica cuántas toneladas por semana puede recibir la planta.'
  else if (c < 0) e.cantidad = 'La cantidad no puede ser negativa.'
  if (String(f.latitud).trim() !== '' && (latNum.value === null || Math.abs(latNum.value) > 90)) e.latitud = 'La latitud debe estar entre −90 y 90.'
  if (String(f.longitud).trim() !== '' && (lonNum.value === null || Math.abs(lonNum.value) > 180)) e.longitud = 'La longitud debe estar entre −180 y 180.'
  if (String(f.latitud).trim() === '' !== (String(f.longitud).trim() === '')) e.latitud = e.latitud || 'Indica latitud y longitud juntas, o deja ambas vacías.'
  if (!editando.value && crearRutas.value && hayUbicacion.value) {
    const t = aNumero(tarifa.value)
    if (t === null || t <= 0) e.tarifa = 'Escribe una tarifa mayor que 0.'
  }
  errores.value = e
  errorForm.value = Object.keys(e).length ? 'Revisa los campos marcados.' : ''
  return Object.keys(e).length === 0
}

const traducir = (msg: string): string =>
  msg
    .replace(/This field is required\.?/i, 'Este campo es obligatorio.')
    .replace(/A valid number is required\.?/i, 'Escribe un número válido.')
    .replace(/Ensure this value is greater than or equal to (\S+)\.?/i, 'Debe ser $1 o mayor.')
    .replace(/Ensure this value is less than or equal to (\S+)\.?/i, 'Debe ser $1 o menor.')
    .replace(/already exists\.?/i, 'ya existe.')

async function guardar(): Promise<void> {
  if (!validar()) return
  guardando.value = true
  errorForm.value = ''
  const cuerpo: Record<string, unknown> = {
    nombre: f.nombre.trim(),
    municipio: f.municipio,
    latitud: hayUbicacion.value ? latNum.value : null,
    longitud: hayUbicacion.value ? lonNum.value : null,
    [T.value.campoCantidad]: aNumero(f.cantidad) ?? 0,
    activa: f.activa,
  }
  if (esEmpresa.value) cuerpo.precio_tonelada = aNumero(f.precio) ?? 0
  else {
    cuerpo.tipo_demanda = f.tipoDemanda
    cuerpo.costo_operacion_ton = aNumero(f.costoOperacion) ?? 0
  }
  try {
    if (editando.value) {
      const id = editando.value.id
      await solicitar(`/${T.value.ruta}/${id}/`, { metodo: 'PATCH', cuerpo })
      abierto.value = false
      resultado.value = { titulo: 'Cambios guardados', id, ubicada: hayUbicacion.value, activa: f.activa, rutasCreadas: null, rutasFallidas: 0, rutasEstimadas: 0, sinUbicacion: 0, motivoFallo: '' }
    } else {
      const codigo = siguienteCodigo(T.value.prefijo, filas.value.map((x) => x.codigo))
      const creada = await solicitar<Fila>(`/${T.value.ruta}/`, { metodo: 'POST', cuerpo: { ...cuerpo, codigo } })
      let creadas: number | null = null
      let fallidas = 0
      let estimadas = 0
      let motivo = ''
      let sin = 0
      if (crearRutas.value && hayUbicacion.value) {
        const p = proponerRutas(props.tipo, { codigo: creada.codigo ?? codigo, latitud: latNum.value as number, longitud: lonNum.value as number }, contrarias.value.filter((c) => c.activa), aNumero(tarifa.value) ?? 0)
        sin = p.sinUbicacion
        // Solo se envía empresa, planta y tarifa: el backend calcula la distancia por carretera.
        const res = await Promise.allSettled(p.rutas.map((r) => solicitar<{ aviso?: string | null }>('/rutas/', { metodo: 'POST', cuerpo: { ...r, activa: true } })))
        creadas = 0
        for (const x of res) {
          if (x.status === 'fulfilled') {
            creadas++
            if (x.value?.aviso) estimadas++
          } else {
            fallidas++
            if (!motivo) motivo = textoRutaFallida(x.reason)
          }
        }
      }
      abierto.value = false
      resultado.value = { titulo: hayUbicacion.value && f.activa ? `${T.value.agregada} y ubicada en el mapa` : `${T.value.agregada}`, id: creada.id, ubicada: hayUbicacion.value, activa: f.activa, rutasCreadas: creadas, rutasFallidas: fallidas, rutasEstimadas: estimadas, sinUbicacion: sin, motivoFallo: motivo }
    }
    await Promise.all([cargar(), red.cargar()])
  } catch (e) {
    const err = leerErrores(e)
    const campos: Record<string, string> = {}
    const mapa: Record<string, string> = { oferta: 'cantidad', capacidad: 'cantidad', precio_tonelada: 'precio', costo_operacion_ton: 'costoOperacion', tipo_demanda: 'tipoDemanda' }
    const otros: string[] = []
    for (const [k, v] of Object.entries(err.campos)) {
      const destino = mapa[k] ?? k
      if (['nombre', 'cantidad', 'latitud', 'longitud', 'precio', 'costoOperacion'].includes(destino)) campos[destino] = traducir(v)
      else otros.push(k === 'codigo' ? 'No se pudo asignar el código automático; inténtalo de nuevo.' : traducir(`${k}: ${v}`))
    }
    errores.value = campos
    errorForm.value = [traducir(err.general), ...otros].filter(Boolean).join(' ') || 'Revisa los campos marcados.'
  } finally {
    guardando.value = false
  }
}

/** Motivo legible de una ruta que no se pudo crear (p. ej. falta de coordenadas). */
function textoRutaFallida(razon: unknown): string {
  const t = leerErrores(razon)
  const txt = `${t.general} ${Object.values(t.campos).join(' ')}`.trim()
  if (/coordenad|ubicaci|latitud|longitud/i.test(txt)) return 'Falta la ubicación (coordenadas) de alguna estación, por eso no se pudo calcular la distancia.'
  return txt
}

/* ---- Acciones de fila ---- */
const confirmacion = ref<{ accion: 'eliminar' | 'desactivar'; fila: Fila } | null>(null)
const ocupada = ref<number | null>(null)

const impacto = computed(() => {
  const c = confirmacion.value
  if (!c) return []
  const n = numRutas(c.fila)
  const rutasTxt = `${esEmpresa.value ? 'Esta empresa' : 'Esta planta'} tiene ${n} ${n === 1 ? 'ruta' : 'rutas'}`
  if (c.accion === 'eliminar') return [`${rutasTxt}; se eliminarán junto con ella.`, 'Dejará de aparecer en el mapa y en los cálculos.', 'Esta acción no se puede deshacer.']
  return [`${rutasTxt}; se conservan pero no se usarán.`, 'Dejará de aparecer en el mapa y en los cálculos. Podrás activarla de nuevo cuando quieras.']
})

async function activar(fila: Fila): Promise<void> {
  ocupada.value = fila.id
  error.value = ''
  try {
    await solicitar(`/${T.value.ruta}/${fila.id}/`, { metodo: 'PATCH', cuerpo: { activa: true } })
    mensaje.value = `${esEmpresa.value ? 'Empresa activada' : 'Planta activada'}: ${fila.nombre} vuelve a aparecer en el mapa.`
    resultado.value = null
    await Promise.all([cargar(), red.cargar()])
  } catch (e) {
    error.value = leerErrores(e).general || 'No se pudo activar.'
  } finally {
    ocupada.value = null
  }
}

async function confirmar(): Promise<void> {
  const c = confirmacion.value
  if (!c) return
  ocupada.value = c.fila.id
  error.value = ''
  try {
    if (c.accion === 'eliminar') await solicitar(`/${T.value.ruta}/${c.fila.id}/`, { metodo: 'DELETE' })
    else await solicitar(`/${T.value.ruta}/${c.fila.id}/`, { metodo: 'PATCH', cuerpo: { activa: false } })
    mensaje.value = c.accion === 'eliminar' ? `${c.fila.nombre} se eliminó de la red.` : `${c.fila.nombre} quedó inactiva y ya no aparece en el mapa.`
    resultado.value = null
    confirmacion.value = null
    await Promise.all([cargar(), red.cargar()])
  } catch (e) {
    confirmacion.value = null
    error.value = leerErrores(e).general || 'No se pudo completar la acción.'
  } finally {
    ocupada.value = null
  }
}

defineExpose({ abrir })
</script>

<template>
  <div class="vista__seccion">
    <div class="herramientas">
      <div class="herramientas__crece">
        <UiField :id="`buscar-${T.ruta}`" v-model="busqueda" label="Buscar" type="search" placeholder="Nombre o municipio" icono="buscar" />
      </div>
      <UiSelect
        :id="`filtro-${T.ruta}`"
        v-model="filtro"
        label="Mostrar"
        :opciones="[
          { valor: 'todas', etiqueta: 'Todas' },
          { valor: 'activas', etiqueta: 'Solo activas' },
          { valor: 'inactivas', etiqueta: 'Solo inactivas' },
        ]"
      />
    </div>

    <UiAlert v-if="resultado" tono="exito" :titulo="resultado.titulo">
      <template v-if="resultado.rutasCreadas !== null">
        Se {{ resultado.rutasCreadas === 1 ? 'creó' : 'crearon' }} {{ resultado.rutasCreadas }} {{ resultado.rutasCreadas === 1 ? 'ruta' : 'rutas' }}<template v-if="resultado.rutasEstimadas">; {{ resultado.rutasEstimadas }} {{ resultado.rutasEstimadas === 1 ? 'quedó' : 'quedaron' }} con distancia estimada porque el servicio de mapas no respondió; puedes recalcularlas después en la pestaña Rutas</template>. Puedes ajustar sus costos en
        <RouterLink :to="{ name: 'matriz-costos' }">Matriz de costos</RouterLink>.
        <template v-if="resultado.rutasFallidas"> No se pudieron crear {{ resultado.rutasFallidas }}<template v-if="resultado.motivoFallo"> ({{ resultado.motivoFallo }})</template>; revísalas en la pestaña Rutas.</template>
        <template v-if="resultado.sinUbicacion"> {{ resultado.sinUbicacion }} {{ T.contrarias }} sin ubicación se omitieron: agrégales ruta a mano.</template>
      </template>
      <template v-else-if="!resultado.ubicada">Aún no tiene ubicación, así que no aparece en el mapa.</template>
      <template v-else>Los cambios ya se reflejan en el mapa y en los cálculos.</template>
      <template v-if="resultado.ubicada && resultado.activa" #acciones>
        <UiButton variante="secundario" tamano="sm" @click="verEnMapa(resultado.id)">
          <template #icono><UiIcon nombre="mapa" :tamano="15" /></template>
          Ver en el mapa
        </UiButton>
      </template>
    </UiAlert>
    <UiAlert v-if="mensaje" tono="exito">{{ mensaje }}</UiAlert>
    <UiAlert v-if="error" tono="error" titulo="No se pudo completar la acción">
      {{ error }}
      <template #acciones><UiButton variante="secundario" tamano="sm" @click="cargar">Reintentar</UiButton></template>
    </UiAlert>

    <p v-if="cargando" class="nota" role="status"><UiSpinner :tamano="16" /> Cargando {{ T.plural }}…</p>
    <UiEmptyState v-else-if="filas.length === 0 && !error" icono="red" :titulo="T.vacioTitulo" :descripcion="esAdmin ? T.vacioTexto : 'Un administrador debe agregarlas.'">
      <UiButton v-if="esAdmin" @click="abrir(null)">{{ T.agregar }}</UiButton>
    </UiEmptyState>
    <UiEmptyState v-else-if="filtradas.length === 0 && filas.length > 0" icono="buscar" titulo="Sin resultados" descripcion="Ninguna coincide con la búsqueda o el filtro. Prueba con otro nombre." />
    <div v-else-if="filas.length > 0" class="tabla-scroll">
      <table class="tabla tabla--estaciones">
        <caption class="sr-only">{{ T.plural }} de la red</caption>
        <thead>
          <tr>
            <th scope="col">Nombre</th>
            <th scope="col">Municipio</th>
            <th scope="col" class="num">{{ T.columnaCantidad }}</th>
            <th scope="col">Mapa</th>
            <th scope="col">Estado</th>
            <th v-if="esAdmin" scope="col"><span class="sr-only">Acciones</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="fila in filtradas" :key="fila.id" :class="{ 'fila-inactiva': !fila.activa }">
            <th scope="row" class="estacion__nombre">
              {{ fila.nombre }}
              <small>{{ fila.codigo }}<template v-if="fila.ficticio"> · demostración</template></small>
            </th>
            <td>{{ fila.municipio || '—' }}</td>
            <td class="num">
              {{ formatearNumero(cantidadDe(fila), { maxDecimales: 1 }) }} t/semana
              <small v-if="!esEmpresa && etiquetaDemanda(fila.tipo_demanda)" class="estacion__sub">{{ etiquetaDemanda(fila.tipo_demanda) }}</small>
              <small v-if="esEmpresa && fila.precio_tonelada" class="estacion__sub">Precio {{ formatearMoneda(fila.precio_tonelada) }}/t</small>
            </td>
            <td>
              <UiBadge v-if="ubicada(fila)" tono="info"><UiIcon nombre="pin" :tamano="12" /> Ubicada</UiBadge>
              <UiBadge v-else tono="ambar">Sin ubicar</UiBadge>
            </td>
            <td><UiBadge :tono="fila.activa ? 'verde' : 'neutro'" punto>{{ fila.activa ? 'Activa' : 'Inactiva' }}</UiBadge></td>
            <td v-if="esAdmin">
              <div class="fila-botones fila-botones--fin">
                <UiButton v-if="fila.activa && ubicada(fila)" variante="fantasma" tamano="sm" @click="verEnMapa(fila.id)">Ver en el mapa</UiButton>
                <UiButton variante="secundario" tamano="sm" :disabled="ocupada === fila.id" @click="abrir(fila)">Editar</UiButton>
                <UiButton v-if="!fila.activa" variante="fantasma" tamano="sm" :disabled="ocupada === fila.id" @click="activar(fila)">Activar</UiButton>
                <UiButton v-else variante="fantasma" tamano="sm" :disabled="ocupada === fila.id" @click="confirmacion = { accion: 'desactivar', fila }">Desactivar</UiButton>
                <UiButton variante="peligro" tamano="sm" :disabled="ocupada === fila.id" @click="confirmacion = { accion: 'eliminar', fila }">Eliminar</UiButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="!cargando && filas.length" class="nota">Mostrando {{ filtradas.length }} de {{ filas.length }} {{ T.plural }}.</p>

    <UiModal v-model:abierto="abierto" :titulo="editando ? `Editar ${T.singular}` : T.agregar" ancho="lg" :bloquear-cierre="guardando">
      <form id="form-estacion" class="vista__seccion" novalidate @submit.prevent="guardar">
        <UiAlert v-if="errorForm" tono="error">{{ errorForm }}</UiAlert>

        <UiField id="est-nombre" v-model="f.nombre" label="Nombre *" :placeholder="esEmpresa ? 'Ej.: Avícola Los Llanos' : 'Ej.: Planta de compostaje Acacías'" :error="errores.nombre" data-autofocus />

        <div class="formulario-grid">
          <UiSelect id="est-municipio" v-model="f.municipio" label="Municipio del Meta" placeholder="Elige un municipio" :opciones="opcionesMunicipio" hint="Al elegirlo, el pin se coloca solo en el mapa." />
          <UiField id="est-cantidad" v-model="f.cantidad" :label="`${T.etiquetaCantidad} *`" type="number" min="0" step="any" :error="errores.cantidad">
            <template #suffix><span class="unidad">t/semana</span></template>
          </UiField>
        </div>

        <fieldset class="bloque">
          <legend>Ubicación en el mapa</legend>
          <MiniMapaUbicacion
            :tipo="tipo"
            :latitud="latNum"
            :longitud="lonNum"
            @update:latitud="(v) => (f.latitud = String(v))"
            @update:longitud="(v) => (f.longitud = String(v))"
          />
          <div class="formulario-grid coordenadas">
            <UiField id="est-lat" v-model="f.latitud" label="Latitud" type="number" step="any" :error="errores.latitud" />
            <UiField id="est-lon" v-model="f.longitud" label="Longitud" type="number" step="any" :error="errores.longitud" />
          </div>
          <p v-if="!hayUbicacion" class="nota">Sin ubicación, la {{ T.singular }} no aparecerá en el mapa ni se podrán estimar sus rutas.</p>
        </fieldset>

        <details class="avanzadas">
          <summary>Opciones avanzadas</summary>
          <div class="formulario-grid">
            <UiField v-if="esEmpresa" id="est-precio" v-model="f.precio" label="Precio de la tonelada (COP/t)" type="number" min="0" step="any" hint="0 = la empresa entrega los residuos sin costo." />
            <template v-else>
              <UiSelect id="est-demanda" v-model="f.tipoDemanda" label="Cómo recibe los residuos" :opciones="TIPOS_DEMANDA" hint="Por defecto, la planta recibe hasta su capacidad." />
              <UiField id="est-operacion" v-model="f.costoOperacion" label="Costo de operación (COP/t)" type="number" min="0" step="any" hint="Costo de procesar cada tonelada en la planta." />
            </template>
          </div>
        </details>

        <UiCheckbox v-if="editando" v-model="f.activa"><strong>Activa</strong> — si la desmarcas, deja de aparecer en el mapa y en los cálculos.</UiCheckbox>

        <fieldset v-else class="bloque">
          <legend>Rutas hacia {{ T.rutasHacia }}</legend>
          <UiCheckbox v-model="crearRutas" :disabled="!hayUbicacion">Crear automáticamente las rutas hacia todas {{ T.rutasHacia }}</UiCheckbox>
          <template v-if="crearRutas && hayUbicacion">
            <UiField id="est-tarifa" v-model="tarifa" label="Tarifa por tonelada y kilómetro (COP)" type="number" min="0" step="any" :error="errores.tarifa" hint="Por defecto, la mediana de las tarifas actuales. La distancia se calcula por las carreteras de OpenStreetMap." />
            <p class="nota" role="status">
              Se crearán {{ propuesta.rutas.length }} {{ propuesta.rutas.length === 1 ? 'ruta' : 'rutas' }}<template v-if="propuesta.sinUbicacion">; {{ propuesta.sinUbicacion }} {{ T.contrarias }} sin ubicación quedan fuera</template>. Así podrás incluirla en los cálculos de inmediato.
            </p>
          </template>
          <p v-else-if="!hayUbicacion" class="nota">Ubica la {{ T.singular }} en el mapa para poder estimar las distancias.</p>
        </fieldset>
      </form>
      <template #pie>
        <UiButton variante="fantasma" :disabled="guardando" @click="abierto = false">Cancelar</UiButton>
        <UiButton type="submit" form="form-estacion" :loading="guardando">{{ editando ? 'Guardar cambios' : `Guardar ${T.singular}` }}</UiButton>
      </template>
    </UiModal>

    <UiConfirmDialog
      :abierto="confirmacion !== null"
      :titulo="confirmacion?.accion === 'eliminar' ? `¿Eliminar ${T.singular}?` : `¿Desactivar ${T.singular}?`"
      :descripcion="confirmacion?.fila.nombre ?? ''"
      :impacto="impacto"
      :tono="confirmacion?.accion === 'eliminar' ? 'peligro' : 'normal'"
      :texto-confirmar="confirmacion?.accion === 'eliminar' ? 'Sí, eliminar' : 'Sí, desactivar'"
      :cargando="ocupada !== null"
      @confirmar="confirmar"
      @cancelar="confirmacion = null"
      @update:abierto="(v) => { if (!v) confirmacion = null }"
    />
  </div>
</template>

<style scoped>
.estacion__nombre {
  font-weight: var(--peso-fuerte);
  text-align: left;
}

.estacion__nombre small,
.estacion__sub {
  display: block;
  font-weight: var(--peso-normal, 450);
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
}

.fila-botones--fin {
  justify-content: flex-end;
  flex-wrap: nowrap;
}

.unidad {
  padding-right: 0.75rem;
  font-size: var(--texto-sm);
  color: var(--color-texto-suave);
  white-space: nowrap;
}

.bloque {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-3);
  padding: var(--espacio-3) var(--espacio-4);
  border: 1px solid var(--color-borde);
  border-radius: var(--radio-md);
  background: var(--color-superficie);
  min-width: 0;
}

.bloque legend {
  padding: 0 var(--espacio-2);
  font-size: var(--texto-sm);
  font-weight: var(--peso-fuerte);
  color: var(--color-texto-2);
}

.coordenadas {
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
}

</style>
