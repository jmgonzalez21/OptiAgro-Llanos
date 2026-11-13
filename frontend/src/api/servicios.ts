/**
 * Servicios de la API: una función por endpoint del contrato (docs/api/openapi.yaml).
 * Funcionan igual contra el backend real y contra la capa mock, porque el mock
 * se enchufa un nivel más abajo (como `fetch`), ver `./mock`.
 *
 * Aquí también se normalizan rarezas del contrato: respuestas paginadas,
 * decimales como texto (DRF DecimalField) y coordenadas ausentes.
 */
import { crearClienteHttp, type ClienteHttp, type OpcionesSolicitud, type SesionHttp } from './http'
import type {
  Credenciales,
  Empresa,
  FiltroEstaciones,
  LoginRespuesta,
  Pagina,
  Planta,
  RefrescoRespuesta,
  Usuario,
} from '@/types/api'

export interface ApiService {
  /** Conecta el cliente HTTP con el store de sesión (tokens). */
  configurarSesion(sesion: SesionHttp): void
  /** POST /auth/login/ */
  login(credenciales: Credenciales): Promise<LoginRespuesta>
  /** POST /auth/refresh/ */
  refrescar(refresh: string): Promise<RefrescoRespuesta>
  /** POST /auth/logout/ (revoca el refresh; no lanza si falla). */
  logout(refresh: string): Promise<void>
  /** GET /auth/me/ */
  obtenerUsuario(): Promise<Usuario>
  /** Petición genérica autenticada a cualquier endpoint de la API. */
  solicitar<T>(ruta: string, opciones?: OpcionesSolicitud): Promise<T>
  /** GET /empresas/?activa=true (todas las páginas) */
  listarEmpresas(filtro?: FiltroEstaciones): Promise<Empresa[]>
  /** GET /plantas/?activa=true (todas las páginas) */
  listarPlantas(filtro?: FiltroEstaciones): Promise<Planta[]>
}

const TAMANO_PAGINA = 200
const MAX_PAGINAS = 50

/** Convierte número o texto numérico a number; vacío o inválido -> null. */
export function aNumeroONull(valor: unknown): number | null {
  if (valor === null || valor === undefined || valor === '') return null
  const n = typeof valor === 'number' ? valor : Number(valor)
  return Number.isFinite(n) ? n : null
}

type Crudo = Record<string, unknown>

function normalizarBase(r: Crudo) {
  return {
    id: Number(r.id),
    codigo: typeof r.codigo === 'string' ? r.codigo : undefined,
    nombre: String(r.nombre ?? ''),
    municipio: String(r.municipio ?? ''),
    latitud: aNumeroONull(r.latitud),
    longitud: aNumeroONull(r.longitud),
    activa: r.activa !== false,
    ficticio: typeof r.ficticio === 'boolean' ? r.ficticio : undefined,
  }
}

export function normalizarEmpresa(r: Crudo): Empresa {
  return {
    ...normalizarBase(r),
    oferta: aNumeroONull(r.oferta) ?? 0,
    precio_tonelada: aNumeroONull(r.precio_tonelada) ?? undefined,
  }
}

export function normalizarPlanta(r: Crudo): Planta {
  return {
    ...normalizarBase(r),
    capacidad: aNumeroONull(r.capacidad) ?? 0,
    tipo_demanda: r.tipo_demanda as Planta['tipo_demanda'],
    costo_operacion_ton: aNumeroONull(r.costo_operacion_ton) ?? undefined,
  }
}

/** Nombre para mostrar: acepta `nombre_completo` o `first_name` + `last_name`. */
export function nombreDeUsuario(u: Pick<Usuario, 'username' | 'nombre_completo' | 'first_name' | 'last_name'>): string {
  const completo = u.nombre_completo?.trim()
  if (completo) return completo
  const partes = `${u.first_name ?? ''} ${u.last_name ?? ''}`.trim()
  return partes || u.username
}

export function crearApi(cliente: ClienteHttp): ApiService {
  async function listarTodas<T>(
    ruta: string,
    filtro: FiltroEstaciones | undefined,
    normalizar: (r: Crudo) => T,
  ): Promise<T[]> {
    const resultado: T[] = []
    for (let pagina = 1; pagina <= MAX_PAGINAS; pagina++) {
      const datos = await cliente.solicitar<Pagina<Crudo> | Crudo[]>(ruta, {
        consulta: { activa: filtro?.activa, page: pagina, page_size: TAMANO_PAGINA },
      })
      // Tolera una respuesta sin paginar (lista simple).
      if (Array.isArray(datos)) return datos.map(normalizar)
      resultado.push(...datos.results.map(normalizar))
      if (!datos.next) break
    }
    return resultado
  }

  return {
    configurarSesion: (sesion) => cliente.configurarSesion(sesion),
    login: (credenciales) =>
      cliente.solicitar<LoginRespuesta>('/auth/login/', { metodo: 'POST', cuerpo: credenciales, autenticar: false }),
    refrescar: (refresh) => cliente.refrescarConToken(refresh),
    logout: async (refresh) => {
      try {
        await cliente.solicitar('/auth/logout/', { metodo: 'POST', cuerpo: { refresh }, autenticar: false })
      } catch {
        /* la sesión local se cierra igual */
      }
    },
    obtenerUsuario: () => cliente.solicitar<Usuario>('/auth/me/'),
    solicitar: (ruta, opciones) => cliente.solicitar(ruta, opciones),
    listarEmpresas: (filtro) => listarTodas('/empresas/', filtro, normalizarEmpresa),
    listarPlantas: (filtro) => listarTodas('/plantas/', filtro, normalizarPlanta),
  }
}

export { crearClienteHttp }
