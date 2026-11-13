/** Tipos de gestión y análisis (docs/api/openapi.yaml). Escritos a mano: solo el subconjunto que usa la UI. */
import type { Rol } from './api'

export type Metodo = 'exacto' | 'genetico' | 'sensibilidad' | 'reporte' | 'escalabilidad'

export interface UsuarioGestion {
  id: number
  username: string
  first_name: string
  last_name: string
  nombre_completo: string
  email: string
  rol: Rol
  activo: boolean
  ultimo_acceso: string | null
  fecha_creacion: string
}

export interface NodoMatriz {
  codigo: string
  nombre: string
  activa: boolean
  precio_tonelada?: number
  costo_operacion_ton?: number
}

export interface CeldaMatriz {
  empresa: string
  planta: string
  costo_unitario: number | null
  distancia_km: number | null
  tarifa_km_ton: number | null
  limite: number | null
  activa: boolean
}

export interface MatrizCostos {
  empresas: NodoMatriz[]
  plantas: NodoMatriz[]
  costos: Array<Array<number | null>>
  costos_totales: Array<Array<number | null>>
  rutas: CeldaMatriz[]
}

export interface ConfigAG {
  poblacion: number
  generaciones: number
  cruce: number
  mutacion: number
  semilla: number
  elitismo: number
  seleccion: 'torneo' | 'ruleta'
  tipo_cruce: 'un_punto' | 'dos_puntos'
  tamano_torneo: number
  inicializacion: 'aleatoria' | 'heuristica'
}

export interface Asignacion {
  empresa_id: string
  planta_id: string
  cantidad: number
  costo_unitario: number
  costo_transporte?: number
  costo_operacion?: number
  precio_tonelada?: number
}

export interface ResultadoOptimizacion {
  metodo: string
  estado: string
  factible: boolean
  objetivo: number | null
  asignaciones: Asignacion[]
  duracion_ms: number
  mensajes: string[]
  duales: Record<string, number>
  verificacion: { valida?: boolean; errores?: string[]; violacion_maxima?: number } & Record<string, unknown>
  metricas: Record<string, unknown>
}

export interface EjecucionResultado {
  ejecucion_id: number | null
  resultado: ResultadoOptimizacion
}

export interface ResumenSolucion {
  estado: string
  factible: boolean
  objetivo: number | null
  duracion_ms: number
  mensajes: string[]
}

export interface AnalisisPlanta {
  planta: string
  nombre: string
  tipo_demanda: string
  capacidad: number
  flujo: number
  utilizacion_pct: number | null
  precio_sombra: number | null
  cuello_de_botella: boolean
}

export interface RangoRhs {
  id: string
  valor_actual: number
  precio_sombra: number
  activa: boolean
  minimo: number | null
  maximo: number | null
  objetivo_en_minimo: number | null
  objetivo_en_maximo: number | null
}

export interface RangoCosto {
  ruta: string
  costo_actual: number
  flujo: number
  en_base: boolean
  costo_reducido: number
  minimo: number | null
  maximo: number | null
  objetivo_en_minimo: number | null
  objetivo_en_maximo: number | null
}

export interface EscenarioSensibilidad {
  nombre: string
  tipo: string
  ids: string[]
  porcentaje: number
  variacion_objetivo: number | null
  variacion_objetivo_pct: number | null
  gap_pct: number | null
  base_cambio: boolean | null
  dentro_de_rango: boolean | null
  asignaciones_cambiadas: number
  costo_exacto: number | null
  costo_ag: number | null
  tiempo_exacto_ms: number
  tiempo_ag_ms: number | null
  estado_exacto: string
  estado_ag: string | null
}

export interface SensibilidadResultado {
  base: { exacto: ResumenSolucion; genetico: ResumenSolucion | null; gap_pct: number | null }
  precios_sombra: { empresas: Record<string, number>; plantas: Record<string, number> }
  rangos: {
    disponible: boolean
    metodo: string | null
    oferta: RangoRhs[]
    capacidad: RangoRhs[]
    costos: RangoCosto[]
  }
  plantas: AnalisisPlanta[]
  escenarios: EscenarioSensibilidad[]
  resumen: {
    escenarios: number
    gap_pct_promedio: number | null
    gap_pct_maximo: number | null
    escenarios_con_cambio_de_base: number
    escenarios_con_cambio_de_asignacion: number
  }
  duracion_total_ms: number
  nota: string
}

export interface Variacion {
  tipo: 'oferta' | 'capacidad' | 'costo' | 'combustible'
  ids: string[]
  porcentajes: number[]
}

export interface SolucionReporte extends ResumenSolucion {
  asignaciones: Asignacion[]
  convergencia?: number[]
  convergencia_promedio?: number[]
}

export interface ReporteResultado {
  modelo: { empresas: number; plantas: number; rutas: number; oferta_total: number; capacidad_total: number }
  exacto: SolucionReporte
  genetico: SolucionReporte
  configuracion_ag: ConfigAG
  comparacion: {
    diferencia_costo: number | null
    gap_pct: number | null
    ratio_tiempo: number | null
    ag_alcanza_optimo: boolean
  }
  plantas: AnalisisPlanta[]
  sensibilidad: SensibilidadResultado | null
}

export interface FilaEscalabilidad {
  empresas: number
  plantas: number
  rutas: number
  oferta_total: number
  capacidad_total: number
  exacto: ResumenSolucion
  genetico: ResumenSolucion
  gap_pct: number | null
  ratio_tiempo: number | null
}

export interface EscalabilidadResultado {
  ficticio: boolean
  tamanos: FilaEscalabilidad[]
  duracion_total_ms: number
  nota: string
}

export interface EjecucionLista {
  id: number
  metodo: Metodo
  estado: string
  objetivo: number | null
  duracion_ms: number
  usuario: string
  escenario: number | null
  incluye_ficticios: boolean
  creada_en: string
}

export interface EjecucionDetalle extends EjecucionLista {
  configuracion: unknown
  parametros: unknown
  resultado: unknown
}
