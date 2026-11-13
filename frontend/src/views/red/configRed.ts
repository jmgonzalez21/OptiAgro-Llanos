/** Tipos de demanda de una planta, en lenguaje de negocio. */
export const TIPOS_DEMANDA = [
  { valor: 'capacity_max', etiqueta: 'Recibe hasta su capacidad (lo habitual)' },
  { valor: 'exact', etiqueta: 'Debe recibir exactamente esa cantidad' },
  { valor: 'minimum', etiqueta: 'Debe recibir al menos esa cantidad' },
]
