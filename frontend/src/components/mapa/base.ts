import L from 'leaflet'

/** Centro aproximado del departamento del Meta. */
export const CENTRO_META: L.LatLngTuple = [3.95, -73.1]
export const ZOOM_META = 8
// OpenStreetMap estándar (sin clave). Política de uso: https://operations.osmfoundation.org/policies/tiles/
export const URL_MOSAICOS = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
export const ATRIBUCION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

/** Crea un mapa Leaflet con el mapa base OpenStreetMap, sin el prefijo de Leaflet en la atribución. */
export function crearMapaBase(el: HTMLElement, opciones: L.MapOptions = {}): L.Map {
  const mapa = L.map(el, { center: CENTRO_META, zoom: ZOOM_META, minZoom: 6, maxZoom: 17, ...opciones })
  mapa.attributionControl.setPrefix('<a href="https://leafletjs.com" target="_blank" rel="noopener">Leaflet</a>')
  L.tileLayer(URL_MOSAICOS, { attribution: ATRIBUCION, maxZoom: 19 }).addTo(mapa)
  return mapa
}
