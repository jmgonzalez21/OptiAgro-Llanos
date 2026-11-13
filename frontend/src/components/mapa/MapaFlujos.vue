<script setup lang="ts">
/** Mapa de flujos: una línea por envío empresa → planta, con grosor proporcional a las toneladas. */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import '@/styles/mapa.css'
import { formatearMoneda, formatearNumero } from '@/components/ui/formato'
import { solicitar } from '@/api/util'
import { iconoMarcador } from './iconos'
import { crearMapaBase } from './base'
import { useFullscreen } from '@/composables/useFullscreen'

export interface PuntoFlujo {
  nombre: string
  latitud: number
  longitud: number
}
export interface Flujo {
  desde: PuntoFlujo
  hasta: PuntoFlujo
  toneladas: number
  costo: number
  /** Ruta de la red (para pedir su trayecto por carretera). */
  rutaId?: number
  distanciaKm?: number | null
}

interface TrayectoApi {
  ruta_id: number
  fuente: string
  distancia_km: number | null
  trayecto: { coordinates?: number[][] } | null
}

const MAX_TRAYECTOS = 30

const props = defineProps<{ flujos: Flujo[] }>()

/** Trayecto por carretera de cada ruta (lat, lon); lo que no esté aquí se dibuja en línea recta. */
const trayectos = ref<Map<number, L.LatLngTuple[]>>(new Map())
const hayRespaldo = ref(false)
let peticion = 0

const contenedor = ref<HTMLDivElement | null>(null)
let mapa: L.Map | null = null
let capa: L.LayerGroup | null = null
let observador: ResizeObserver | null = null

const color = (): string => getComputedStyle(document.documentElement).getPropertyValue('--color-activo-barra').trim() || '#2f8f55'

function dibujar(): void {
  if (!mapa || !capa) return
  capa.clearLayers()
  if (props.flujos.length === 0) return
  const max = Math.max(...props.flujos.map((f) => f.toneladas), 1)
  const puntos: L.LatLngTuple[] = []
  const vistos = new Set<string>()
  const c = color()
  for (const f of props.flujos) {
    const a: L.LatLngTuple = [f.desde.latitud, f.desde.longitud]
    const b: L.LatLngTuple = [f.hasta.latitud, f.hasta.longitud]
    puntos.push(a, b)
    const camino = f.rutaId !== undefined ? trayectos.value.get(f.rutaId) : undefined
    if (camino) puntos.push(...camino)
    L.polyline(camino ?? [a, b], { color: c, weight: 2 + (f.toneladas / max) * 10, opacity: 0.6, lineCap: 'round' })
      .bindTooltip(`<strong>${esc(f.desde.nombre)} → ${esc(f.hasta.nombre)}</strong><br>${formatearNumero(f.toneladas, { maxDecimales: 1 })} t/semana · ${formatearMoneda(f.costo)} por semana${f.distanciaKm != null ? `<br>${formatearNumero(f.distanciaKm, { maxDecimales: 1 })} km${camino ? ' por carretera' : ''}` : ''}`, { sticky: true, className: 'flujo-tooltip' })
      .addTo(capa)
    for (const [tipo, p] of [['empresa', f.desde], ['planta', f.hasta]] as const) {
      const clave = `${tipo}-${p.nombre}`
      if (vistos.has(clave)) continue
      vistos.add(clave)
      L.marker([p.latitud, p.longitud], { icon: iconoMarcador(tipo), title: p.nombre, alt: p.nombre, keyboard: false }).bindTooltip(esc(p.nombre), { direction: 'top', offset: [0, -14] }).addTo(capa)
    }
  }
  mapa.fitBounds(L.latLngBounds(puntos), { padding: [40, 40], maxZoom: 11 })
}

function esc(t: string): string {
  return t.replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[m] as string)
}

/** Pide los trayectos reales de los envíos con toneladas (máx. 30, los más grandes primero). */
async function cargarTrayectos(): Promise<void> {
  const mi = ++peticion
  const candidatos = props.flujos
    .filter((f) => f.rutaId !== undefined && f.toneladas > 0)
    .sort((x, y) => y.toneladas - x.toneladas)
    .slice(0, MAX_TRAYECTOS)
  const faltantes = props.flujos.length - candidatos.length
  if (candidatos.length === 0) {
    trayectos.value = new Map()
    hayRespaldo.value = props.flujos.length > 0
    dibujar()
    return
  }
  const mapaNuevo = new Map<number, L.LatLngTuple[]>()
  try {
    const ids = candidatos.map((f) => f.rutaId).join(',')
    const r = await solicitar<{ trayectos: TrayectoApi[] }>('/rutas/trayectos/', { consulta: { ids } })
    for (const t of r.trayectos) {
      const coords = t.trayecto?.coordinates
      if (t.fuente === 'carretera' && coords && coords.length > 1) mapaNuevo.set(t.ruta_id, coords.map(([lon, lat]) => [lat as number, lon as number] as L.LatLngTuple))
    }
  } catch {
    // Sin trayectos: se mantiene la línea recta de respaldo.
  }
  if (mi !== peticion) return
  trayectos.value = mapaNuevo
  hayRespaldo.value = mapaNuevo.size < props.flujos.length || faltantes > 0
  dibujar()
}

const envoltura = ref<HTMLElement | null>(null)
const pantallaCompleta = useFullscreen(envoltura)

onMounted(() => {
  if (!contenedor.value) return
  // Rueda del mouse activa y con pasos finos (0,5) para acercar/alejar sin usar los botones +/−.
  mapa = crearMapaBase(contenedor.value, { scrollWheelZoom: true, zoomSnap: 0.5, zoomDelta: 0.5, wheelPxPerZoomLevel: 90 })
  capa = L.layerGroup().addTo(mapa)
  if (typeof ResizeObserver !== 'undefined') {
    observador = new ResizeObserver(() => mapa?.invalidateSize())
    observador.observe(contenedor.value)
  }
  dibujar()
  void cargarTrayectos()
})
onBeforeUnmount(() => {
  observador?.disconnect()
  mapa?.remove()
  mapa = null
  capa = null
})
watch(() => props.flujos, () => { dibujar(); void cargarTrayectos() }, { deep: true })
</script>

<template>
  <div ref="envoltura" class="mapa-flujos-envoltura">
    <div ref="contenedor" class="mapa-flujos" role="img" aria-label="Mapa con los envíos de cada empresa a cada planta; las líneas más gruesas llevan más toneladas."></div>
    <button v-if="pantallaCompleta.soportado.value" type="button" class="mapa-flujos__completa" :aria-pressed="pantallaCompleta.activo.value" @click="pantallaCompleta.alternar()">
      {{ pantallaCompleta.activo.value ? 'Salir de pantalla completa' : 'Pantalla completa' }}
    </button>
    <p class="mapa-flujos__ayuda">Usa la rueda del mouse para acercar o alejar, y arrastra para moverte.</p>
  </div>
  <p v-if="hayRespaldo" class="nota">Algunos envíos se muestran en línea recta porque no se pudo obtener su trayecto por carretera.</p>
</template>

<style scoped>
.mapa-flujos-envoltura {
  position: relative;
  background: var(--color-fondo);
}

.mapa-flujos {
  width: 100%;
  /* Grande: ocupa ~3/4 de la altura de la ventana (entre 30 y 52 rem). */
  height: clamp(30rem, 75vh, 52rem);
  border: 1px solid var(--color-borde-fuerte);
  border-radius: var(--radio-md);
  overflow: hidden;
  isolation: isolate;
}

.mapa-flujos-envoltura:fullscreen .mapa-flujos {
  height: 100vh;
  border: 0;
  border-radius: 0;
}

.mapa-flujos__completa {
  position: absolute;
  top: var(--espacio-3);
  right: var(--espacio-3);
  z-index: 1100;
  padding: 0.4rem 0.8rem;
  border: 1px solid var(--color-borde-control);
  border-radius: var(--radio-md);
  background: var(--color-superficie);
  color: var(--color-texto);
  font: inherit;
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  cursor: pointer;
  box-shadow: var(--sombra-sm, 0 1px 4px rgb(0 0 0 / 0.15));
}

.mapa-flujos__completa:hover {
  background: var(--color-superficie-hover);
}

.mapa-flujos__ayuda {
  position: absolute;
  left: var(--espacio-3);
  bottom: var(--espacio-5, 1.5rem);
  z-index: 1100;
  margin: 0;
  padding: 0.25rem 0.6rem;
  border-radius: var(--radio-md);
  background: rgb(255 255 255 / 0.85);
  color: var(--color-texto-2);
  font-size: var(--texto-xs);
  pointer-events: none;
}
</style>
