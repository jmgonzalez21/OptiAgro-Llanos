/**
 * Municipios del Meta con las coordenadas APROXIMADAS de su cabecera municipal.
 * Dato local: no se consulta ningún servicio externo. El usuario puede afinar el pin en el mapa.
 */
export interface MunicipioMeta {
  nombre: string
  latitud: number
  longitud: number
}

export const MUNICIPIOS_META: readonly MunicipioMeta[] = [
  { nombre: 'Acacías', latitud: 3.987, longitud: -73.758 },
  { nombre: 'Barranca de Upía', latitud: 4.572, longitud: -72.965 },
  { nombre: 'Cabuyaro', latitud: 4.287, longitud: -72.793 },
  { nombre: 'Castilla la Nueva', latitud: 3.829, longitud: -73.685 },
  { nombre: 'Cubarral', latitud: 3.792, longitud: -73.843 },
  { nombre: 'Cumaral', latitud: 4.27, longitud: -73.486 },
  { nombre: 'El Calvario', latitud: 4.351, longitud: -73.713 },
  { nombre: 'El Castillo', latitud: 3.564, longitud: -73.793 },
  { nombre: 'El Dorado', latitud: 3.74, longitud: -73.834 },
  { nombre: 'Fuente de Oro', latitud: 3.464, longitud: -73.619 },
  { nombre: 'Granada', latitud: 3.545, longitud: -73.708 },
  { nombre: 'Guamal', latitud: 3.879, longitud: -73.769 },
  { nombre: 'La Macarena', latitud: 2.178, longitud: -73.785 },
  { nombre: 'Lejanías', latitud: 3.526, longitud: -74.024 },
  { nombre: 'Mapiripán', latitud: 2.897, longitud: -72.134 },
  { nombre: 'Mesetas', latitud: 3.384, longitud: -74.045 },
  { nombre: 'Puerto Concordia', latitud: 2.624, longitud: -72.758 },
  { nombre: 'Puerto Gaitán', latitud: 4.314, longitud: -72.082 },
  { nombre: 'Puerto Lleras', latitud: 3.268, longitud: -73.373 },
  { nombre: 'Puerto López', latitud: 4.09, longitud: -72.957 },
  { nombre: 'Puerto Rico', latitud: 2.938, longitud: -73.208 },
  { nombre: 'Restrepo', latitud: 4.259, longitud: -73.56 },
  { nombre: 'San Carlos de Guaroa', latitud: 3.711, longitud: -73.242 },
  { nombre: 'San Juan de Arama', latitud: 3.338, longitud: -73.887 },
  { nombre: 'San Juanito', latitud: 4.456, longitud: -73.676 },
  { nombre: 'San Martín', latitud: 3.696, longitud: -73.699 },
  { nombre: 'Uribe', latitud: 3.239, longitud: -74.351 },
  { nombre: 'Villavicencio', latitud: 4.142, longitud: -73.627 },
  { nombre: 'Vista Hermosa', latitud: 3.124, longitud: -73.752 },
]

function normalizar(texto: string): string {
  return texto
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .trim()
    .toLowerCase()
}

/** Busca un municipio por nombre sin distinguir tildes ni mayúsculas. */
export function buscarMunicipio(nombre: string): MunicipioMeta | undefined {
  const n = normalizar(nombre)
  return n ? MUNICIPIOS_META.find((m) => normalizar(m.nombre) === n) : undefined
}
