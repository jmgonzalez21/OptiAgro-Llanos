/** Configuración de la aplicación derivada de variables de entorno de Vite. */

/** Por defecto se usa la API real; `VITE_USE_MOCK=true` activa la capa mock. */
export const USAR_MOCK: boolean = (import.meta.env.VITE_USE_MOCK ?? 'false').trim().toLowerCase() !== 'false'

export const API_BASE: string = (import.meta.env.VITE_API_BASE ?? '/api/v1').replace(/\/+$/, '')

/** Clave de sessionStorage donde se guarda SOLO el refresh token. */
export const CLAVE_REFRESH = 'optiagro.refresh'
