/**
 * DATOS DE DEMOSTRACIÓN — solo para la capa mock.
 *
 * - Las 4 plantas usan nombres y coordenadas de sedes reales, pero sus
 *   capacidades son valores de relleno (no son cifras reales).
 * - Las 10 agroempresas son FICTICIAS: los nombres, las ofertas y las
 *   coordenadas son inventados (plausibles dentro del Meta) y no
 *   corresponden a ninguna empresa real. Llevan `ficticio: true`.
 * Los datos reales viven únicamente en la base de datos del backend.
 */
import type { Empresa, Planta } from '@/types/api'

export const PLANTAS_MOCK: Planta[] = [
  { id: 1, codigo: 'P1', nombre: 'Planta Villavicencio', municipio: 'Villavicencio', latitud: 4.142, longitud: -73.6266, capacidad: 120, tipo_demanda: 'capacity_max', activa: true, ficticio: false },
  { id: 2, codigo: 'P2', nombre: 'Planta Restrepo', municipio: 'Restrepo', latitud: 4.259, longitud: -73.568, capacidad: 90, tipo_demanda: 'capacity_max', activa: true, ficticio: false },
  { id: 3, codigo: 'P3', nombre: 'Planta Granada', municipio: 'Granada', latitud: 3.545, longitud: -73.708, capacidad: 80, tipo_demanda: 'capacity_max', activa: true, ficticio: false },
  { id: 4, codigo: 'P4', nombre: 'Planta Puerto Gaitán', municipio: 'Puerto Gaitán', latitud: 4.314, longitud: -72.082, capacidad: 100, tipo_demanda: 'capacity_max', activa: true, ficticio: false },
]

/** EMPRESAS FICTICIAS (demostración). */
export const EMPRESAS_MOCK: Empresa[] = [
  { id: 1, codigo: 'E1', nombre: 'Agroempresa Ficticia 01 (palma)', municipio: 'Acacías', latitud: 3.987, longitud: -73.758, oferta: 45, activa: true, ficticio: true },
  { id: 2, codigo: 'E2', nombre: 'Agroempresa Ficticia 02 (arroz)', municipio: 'Cumaral', latitud: 4.27, longitud: -73.485, oferta: 38, activa: true, ficticio: true },
  { id: 3, codigo: 'E3', nombre: 'Agroempresa Ficticia 03 (ganadería)', municipio: 'Puerto López', latitud: 4.09, longitud: -72.956, oferta: 60, activa: true, ficticio: true },
  { id: 4, codigo: 'E4', nombre: 'Agroempresa Ficticia 04 (porcícola)', municipio: 'San Martín', latitud: 3.698, longitud: -73.696, oferta: 27, activa: true, ficticio: true },
  { id: 5, codigo: 'E5', nombre: 'Agroempresa Ficticia 05 (avícola)', municipio: 'Guamal', latitud: 3.879, longitud: -73.768, oferta: 33, activa: true, ficticio: true },
  { id: 6, codigo: 'E6', nombre: 'Agroempresa Ficticia 06 (maíz)', municipio: 'Barranca de Upía', latitud: 4.57, longitud: -72.964, oferta: 52, activa: true, ficticio: true },
  { id: 7, codigo: 'E7', nombre: 'Agroempresa Ficticia 07 (soya)', municipio: 'Cabuyaro', latitud: 4.29, longitud: -72.793, oferta: 41, activa: true, ficticio: true },
  { id: 8, codigo: 'E8', nombre: 'Agroempresa Ficticia 08 (frutales)', municipio: 'Castilla la Nueva', latitud: 3.83, longitud: -73.68, oferta: 24, activa: true, ficticio: true },
  { id: 9, codigo: 'E9', nombre: 'Agroempresa Ficticia 09 (piscícola)', municipio: 'San Carlos de Guaroa', latitud: 3.711, longitud: -73.242, oferta: 30, activa: true, ficticio: true },
  { id: 10, codigo: 'E10', nombre: 'Agroempresa Ficticia 10 (cacao)', municipio: 'Villavicencio', latitud: 4.19, longitud: -73.6, oferta: 36, activa: true, ficticio: true },
]
