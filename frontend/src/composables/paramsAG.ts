/** Parámetros del algoritmo genético como texto de formulario y su conversión al cuerpo de la API. */
export interface ParamsAGForm {
  poblacion: string
  generaciones: string
  cruce: string
  mutacion: string
  semilla: string
  elitismo: string
  seleccion: 'torneo' | 'ruleta'
  tipo_cruce: 'un_punto' | 'dos_puntos'
  tamano_torneo: string
  inicializacion: 'aleatoria' | 'heuristica'
}

export function paramsAGPorDefecto(): ParamsAGForm {
  return {
    poblacion: '60',
    generaciones: '150',
    cruce: '0.8',
    mutacion: '0.12',
    semilla: '42',
    elitismo: '2',
    seleccion: 'torneo',
    tipo_cruce: 'un_punto',
    tamano_torneo: '3',
    inicializacion: 'aleatoria',
  }
}

/** Texto -> número (acepta coma decimal). Vacío o inválido se omite para que el servidor use su valor por defecto. */
export function aPayloadAG(f: ParamsAGForm): Record<string, number | string> {
  const salida: Record<string, number | string> = {
    seleccion: f.seleccion,
    tipo_cruce: f.tipo_cruce,
    inicializacion: f.inicializacion,
  }
  const numericos = ['poblacion', 'generaciones', 'cruce', 'mutacion', 'semilla', 'elitismo', 'tamano_torneo'] as const
  for (const clave of numericos) {
    const texto = f[clave].trim().replace(',', '.')
    if (texto === '') continue
    const n = Number(texto)
    if (Number.isFinite(n)) salida[clave] = n
  }
  return salida
}
