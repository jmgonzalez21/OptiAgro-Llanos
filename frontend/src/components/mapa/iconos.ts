import L from 'leaflet'
import type { TipoEstacion } from '@/composables/useEstaciones'
import { svgMarcador, TAMANO_MARCADOR } from '@/components/ui/marcadores'

/**
 * Marcadores distinguibles por FORMA e ícono además de color:
 * - Agroempresa: círculo con hoja.
 * - Planta: cuadrado redondeado, algo más grande, con fábrica/chimenea.
 * La geometría vive en `components/ui/marcadores.ts` (compartida con la leyenda);
 * los colores salen de las variables CSS --color-marcador-*.
 */
export function iconoMarcador(tipo: TipoEstacion): L.DivIcon {
  const px = TAMANO_MARCADOR[tipo]
  return L.divIcon({
    className: `marcador marcador--${tipo}`,
    html: `<span class="marcador__cuerpo">${svgMarcador(tipo, px)}</span>`,
    iconSize: [px, px],
    iconAnchor: [px / 2, px / 2],
    popupAnchor: [0, -px / 2 + 2],
  })
}
