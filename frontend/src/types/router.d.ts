import 'vue-router'
import type { Rol } from '@/types/api'

declare module 'vue-router' {
  interface RouteMeta {
    /** La ruta exige sesión iniciada. */
    requiereAuth?: boolean
    /** Solo para visitantes: con sesión redirige al inicio (p. ej. /login). */
    soloInvitado?: boolean
    /** Si se define, el rol del usuario debe estar incluido. */
    roles?: Rol[]
    /** Título de la página (document.title). */
    titulo?: string
  }
}
