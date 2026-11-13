/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** 'true' (por defecto) usa la capa mock; 'false' usa la API real. */
  readonly VITE_USE_MOCK?: string
  /** Base de la API REST. Por defecto '/api/v1'. */
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
