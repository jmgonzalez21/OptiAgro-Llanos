/**
 * Tipos del contrato REST (docs/api/openapi.yaml, prefijo /api/v1).
 * Se mantienen a mano porque solo se usa un subconjunto; cuando el contrato
 * crezca puede generarse con openapi-typescript.
 */

export type Rol = 'administrador' | 'analista'

export interface Usuario {
  id: number
  username: string
  email: string
  rol: Rol
  /** Forma pedida para /auth/me. */
  nombre_completo?: string
  /** Forma actual de docs/api/openapi.yaml (se acepta cualquiera de las dos). */
  first_name?: string
  last_name?: string
}

export interface Credenciales {
  username: string
  password: string
}

export interface LoginRespuesta {
  access: string
  refresh: string
  /** El OpenAPI lo incluye; si no viniera, el store consulta /auth/me. */
  usuario?: Usuario
}

export interface RefrescoRespuesta {
  access: string
  /** Solo si el backend rota los refresh tokens. */
  refresh?: string
}

export type TipoDemanda = 'capacity_max' | 'exact' | 'minimum'

interface EstacionBase {
  id: number
  codigo?: string
  nombre: string
  municipio: string
  /** null = sin coordenadas registradas. */
  latitud: number | null
  longitud: number | null
  activa: boolean
  /** Dato de demostración ficticio. */
  ficticio?: boolean
}

export interface Empresa extends EstacionBase {
  /** Oferta en t/semana. */
  oferta: number
  precio_tonelada?: number
}

export interface Planta extends EstacionBase {
  /** Capacidad en t/semana. */
  capacidad: number
  tipo_demanda?: TipoDemanda
  costo_operacion_ton?: number
}

export interface Pagina<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface FiltroEstaciones {
  activa?: boolean
}
