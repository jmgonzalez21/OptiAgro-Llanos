<script setup lang="ts">
/**
 * Mini mapa para ubicar una estación: clic en el mapa o arrastrar el pin para afinar la posición.
 * Recibe y emite coordenadas con `v-model:latitud` y `v-model:longitud` (null = sin ubicar).
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import '@/styles/mapa.css'
import type { TipoEstacion } from '@/composables/useEstaciones'
import { iconoMarcador } from './iconos'
import { crearMapaBase } from './base'

const props = defineProps<{ tipo: TipoEstacion; latitud: number | null; longitud: number | null }>()
const emit = defineEmits<{ 'update:latitud': [number]; 'update:longitud': [number] }>()

const contenedor = ref<HTMLDivElement | null>(null)
let mapa: L.Map | null = null
let pin: L.Marker | null = null
let observador: ResizeObserver | null = null

const redondear = (n: number): number => Math.round(n * 1e5) / 1e5

function colocar(lat: number, lon: number, mover: boolean): void {
  if (!mapa) return
  if (!pin) {
    pin = L.marker([lat, lon], { icon: iconoMarcador(props.tipo), draggable: true, keyboard: true, title: 'Ubicación de la estación' }).addTo(mapa)
    pin.on('dragend', () => {
      const p = pin?.getLatLng()
      if (p) emitir(p.lat, p.lng)
    })
  } else {
    pin.setLatLng([lat, lon])
  }
  if (mover) mapa.setView([lat, lon], Math.max(mapa.getZoom(), 10))
}

function emitir(lat: number, lon: number): void {
  emit('update:latitud', redondear(lat))
  emit('update:longitud', redondear(lon))
}

function sincronizar(mover: boolean): void {
  if (typeof props.latitud === 'number' && typeof props.longitud === 'number' && Number.isFinite(props.latitud) && Number.isFinite(props.longitud)) {
    colocar(props.latitud, props.longitud, mover)
  } else if (pin && mapa) {
    mapa.removeLayer(pin)
    pin = null
  }
}

onMounted(() => {
  if (!contenedor.value) return
  mapa = crearMapaBase(contenedor.value, { scrollWheelZoom: false })
  mapa.on('click', (ev: L.LeafletMouseEvent) => {
    colocar(ev.latlng.lat, ev.latlng.lng, false)
    emitir(ev.latlng.lat, ev.latlng.lng)
  })
  if (typeof ResizeObserver !== 'undefined') {
    observador = new ResizeObserver(() => mapa?.invalidateSize())
    observador.observe(contenedor.value)
  }
  sincronizar(true)
})

onBeforeUnmount(() => {
  observador?.disconnect()
  mapa?.remove()
  mapa = null
  pin = null
})

// Si las coordenadas cambian desde fuera (municipio o campos de texto), el pin las sigue; el mapa se centra.
watch(
  () => [props.latitud, props.longitud],
  () => {
    const actual = pin?.getLatLng()
    if (actual && props.latitud !== null && props.longitud !== null && Math.abs(actual.lat - props.latitud) < 1e-4 && Math.abs(actual.lng - props.longitud) < 1e-4) return
    sincronizar(true)
  },
)
</script>

<template>
  <div class="mini-mapa">
    <div ref="contenedor" class="mini-mapa__mapa" role="application" aria-label="Mapa para ubicar la estación. Haz clic o arrastra el pin para ajustar la posición."></div>
    <p class="mini-mapa__ayuda">Haz clic en el mapa o arrastra el pin para ajustar la ubicación exacta.</p>
  </div>
</template>

<style scoped>
.mini-mapa {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-1);
}

.mini-mapa__mapa {
  width: 100%;
  height: 16rem;
  border: 1px solid var(--color-borde-fuerte);
  border-radius: var(--radio-md);
  overflow: hidden;
  isolation: isolate;
}

.mini-mapa__ayuda {
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
}
</style>
