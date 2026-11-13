<script setup lang="ts">
/**
 * Mapa Leaflet (CARTO Positron) con las estaciones activas.
 * Recibe SOLO estaciones con coordenadas y sincroniza los marcadores:
 * crea los nuevos, actualiza los modificados y elimina los que ya no vienen.
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import '@/styles/mapa.css'
import {
  ETIQUETA_CANTIDAD,
  ETIQUETA_TIPO,
  formatearToneladas,
  type EstacionUbicada,
} from '@/composables/useEstaciones'
import { ICONOS } from '@/components/ui/icons'
import { iconoMarcador } from './iconos'
import { CENTRO_META, ZOOM_META, crearMapaBase } from './base'

const props = defineProps<{ estaciones: EstacionUbicada[]; /** Clave de la estación a resaltar (p. ej. empresa-12). */ foco?: string }>()


const contenedor = ref<HTMLDivElement | null>(null)
/** Cantidad de marcadores dibujados (expuesta como data-attribute para pruebas). */
const dibujados = ref(0)

let mapa: L.Map | null = null
let capa: L.LayerGroup | null = null
let observador: ResizeObserver | null = null
let encuadreInicialHecho = false
const marcadores = new Map<string, { marcador: L.Marker; firma: string }>()

const NS_SVG = 'http://www.w3.org/2000/svg'

function iconoSvg(rutas: readonly string[]): SVGElement {
  const svg = document.createElementNS(NS_SVG, 'svg')
  svg.setAttribute('viewBox', '0 0 24 24')
  svg.setAttribute('width', '22')
  svg.setAttribute('height', '22')
  svg.setAttribute('aria-hidden', 'true')
  svg.setAttribute('focusable', 'false')
  for (const d of rutas) {
    const ruta = document.createElementNS(NS_SVG, 'path')
    ruta.setAttribute('d', d)
    svg.appendChild(ruta)
  }
  return svg
}

function construirPopup(e: EstacionUbicada): HTMLElement {
  const raiz = document.createElement('div')
  raiz.className = 'popup-estacion'

  const cabecera = document.createElement('div')
  cabecera.className = 'popup-estacion__cabecera'

  const icono = document.createElement('span')
  icono.className = `popup-estacion__icono popup-estacion__icono--${e.tipo}`
  icono.appendChild(iconoSvg(e.tipo === 'empresa' ? ICONOS.hoja : ICONOS.fabrica))
  cabecera.appendChild(icono)

  const textos = document.createElement('div')
  const titulo = document.createElement('h3')
  titulo.className = 'popup-estacion__titulo'
  titulo.textContent = e.nombre
  const chip = document.createElement('span')
  chip.className = 'popup-estacion__chip'
  chip.textContent = ETIQUETA_TIPO[e.tipo]
  textos.append(titulo, chip)
  cabecera.appendChild(textos)
  raiz.appendChild(cabecera)

  const lista = document.createElement('dl')
  lista.className = 'popup-estacion__datos'
  const filas: Array<[string, string]> = [
    ['Municipio', e.municipio || 'Sin dato'],
    [ETIQUETA_CANTIDAD[e.tipo], formatearToneladas(e.cantidad)],
  ]
  for (const [etiqueta, valor] of filas) {
    const dt = document.createElement('dt')
    dt.textContent = etiqueta
    const dd = document.createElement('dd')
    dd.textContent = valor
    lista.append(dt, dd)
  }
  raiz.appendChild(lista)

  if (e.ficticio) {
    const nota = document.createElement('p')
    nota.className = 'popup-estacion__nota'
    nota.textContent = 'Dato de demostración (ficticio).'
    raiz.appendChild(nota)
  }
  return raiz
}

function firmaDe(e: EstacionUbicada): string {
  return JSON.stringify([e.latitud, e.longitud, e.nombre, e.municipio, e.cantidad, e.ficticio, e.tipo])
}

function crearMarcador(e: EstacionUbicada): L.Marker {
  const etiqueta = `${ETIQUETA_TIPO[e.tipo]}: ${e.nombre}`
  return L.marker([e.latitud, e.longitud], {
    icon: iconoMarcador(e.tipo),
    title: etiqueta,
    alt: etiqueta,
    keyboard: true,
  }).bindPopup(() => construirPopup(e), {
    maxWidth: 320,
    // Deja libres las tarjetas flotantes (filtros arriba, controles a la derecha) al desplazar la vista.
    autoPanPaddingTopLeft: [24, 150],
    autoPanPaddingBottomRight: [72, 24],
  })
}

function sincronizar(): void {
  if (!mapa || !capa) return
  const vigentes = new Set<string>()

  for (const e of props.estaciones) {
    vigentes.add(e.clave)
    const firma = firmaDe(e)
    const previo = marcadores.get(e.clave)
    if (previo?.firma === firma) continue
    if (previo) capa.removeLayer(previo.marcador)
    const marcador = crearMarcador(e)
    capa.addLayer(marcador)
    marcadores.set(e.clave, { marcador, firma })
  }

  for (const [clave, { marcador }] of marcadores) {
    if (!vigentes.has(clave)) {
      capa.removeLayer(marcador)
      marcadores.delete(clave)
    }
  }
  dibujados.value = marcadores.size

  // Solo se encuadra automáticamente la primera vez que hay datos (salvo que haya una estación en foco).
  if (!encuadreInicialHecho && props.estaciones.length > 0) {
    if (!props.foco || !marcadores.has(props.foco)) reencuadrar()
    encuadreInicialHecho = true
  }
  aplicarFoco()
}

let focoAplicado = ''

/** Centra la estación pedida, abre su ficha y la resalta con un pulso. */
function aplicarFoco(): void {
  const clave = props.foco
  if (!mapa || !clave || focoAplicado === clave) return
  const m = marcadores.get(clave)
  if (!m) return
  focoAplicado = clave
  mapa.setView(m.marcador.getLatLng(), Math.max(mapa.getZoom(), 12))
  m.marcador.openPopup()
  const el = m.marcador.getElement()
  el?.classList.add('marcador--foco')
  window.setTimeout(() => el?.classList.remove('marcador--foco'), 6000)
}

/** Ajusta la vista para mostrar todas las estaciones visibles (o el Meta si no hay). */
function reencuadrar(): void {
  if (!mapa) return
  if (props.estaciones.length === 0) {
    mapa.setView(CENTRO_META, ZOOM_META)
    return
  }
  const limites = L.latLngBounds(props.estaciones.map((e) => [e.latitud, e.longitud] as L.LatLngTuple))
  mapa.fitBounds(limites, { padding: [48, 48], maxZoom: 11 })
}

function acercar(): void {
  mapa?.zoomIn()
}

function alejar(): void {
  mapa?.zoomOut()
}

function invalidarTamano(): void {
  mapa?.invalidateSize()
}

onMounted(() => {
  if (!contenedor.value) return
  // Sin control de zoom de Leaflet: la vista de Inicio dibuja los suyos (acercar/alejar se exponen abajo).
  mapa = crearMapaBase(contenedor.value, { zoomControl: false })
  mapa.on('popupopen', (ev) => {
    const cerrar = ev.popup.getElement()?.querySelector('.leaflet-popup-close-button')
    cerrar?.setAttribute('aria-label', 'Cerrar ficha')
    cerrar?.setAttribute('title', 'Cerrar ficha')
  })
  capa = L.layerGroup().addTo(mapa)

  if (typeof ResizeObserver !== 'undefined') {
    observador = new ResizeObserver(() => invalidarTamano())
    observador.observe(contenedor.value)
  }
  sincronizar()
})

onBeforeUnmount(() => {
  observador?.disconnect()
  observador = null
  marcadores.clear()
  mapa?.remove()
  mapa = null
  capa = null
})

watch(() => props.estaciones, sincronizar, { deep: true })
watch(() => props.foco, () => aplicarFoco())

defineExpose({ reencuadrar, invalidarTamano, acercar, alejar })
</script>

<template>
  <div
    ref="contenedor"
    class="mapa-red"
    role="region"
    aria-label="Mapa de la red logística. Usa las flechas para desplazarte y más o menos para acercar."
    :data-marcadores="dibujados"
  ></div>
</template>

<style>
/* Dimensionado: Leaflet necesita altura. El aspecto (marcadores, popup, atribución) está en styles/mapa.css
   y styles/marcadores.css. Sin `scoped`: los marcadores y popups los crea Leaflet fuera de este componente. */
.mapa-red {
  width: 100%;
  height: 100%;
  min-height: 24rem;
}
</style>
