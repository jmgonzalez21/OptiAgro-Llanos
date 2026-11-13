import { watch } from 'vue'
import type { RouteLocationNormalized, RouteLocationRaw, Router } from 'vue-router'
import type { useAuthStore } from '@/stores/auth'

type AuthStore = ReturnType<typeof useAuthStore>

/** Solo se aceptan redirecciones internas (evita open redirect). */
export function redireccionSegura(destino: unknown): string {
  return typeof destino === 'string' && destino.startsWith('/') && !destino.startsWith('//') ? destino : '/'
}

/**
 * Decide si se permite la navegación. Devuelve `true` o el destino alternativo.
 * - Rutas privadas (`meta.requiereAuth`) sin sesión -> /login?redirect=...
 * - Rutas `meta.soloInvitado` (login) con sesión -> inicio.
 * - `meta.roles` presente y rol no incluido -> /sin-permiso.
 */
export async function evaluarAcceso(to: RouteLocationNormalized, auth: AuthStore): Promise<true | RouteLocationRaw> {
  await auth.inicializar()

  if (to.meta.soloInvitado && auth.autenticado) return { name: 'inicio' }

  if (to.meta.requiereAuth && !auth.autenticado) {
    return {
      name: 'login',
      query: to.fullPath && to.fullPath !== '/' ? { redirect: to.fullPath } : undefined,
    }
  }

  if (to.meta.roles?.length && (!auth.rol || !to.meta.roles.includes(auth.rol))) {
    return { name: 'sin-permiso' }
  }
  return true
}

/**
 * Si la sesión expira mientras se usa la app (refresh vencido), manda al login
 * conservando la ruta actual y avisando del motivo.
 */
export function vigilarSesion(router: Router, auth: AuthStore): void {
  watch(
    () => auth.sesionExpirada,
    (expirada) => {
      if (!expirada) return
      const actual = router.currentRoute.value
      if (actual.meta.requiereAuth) {
        void router.replace({
          name: 'login',
          query: { motivo: 'expirada', redirect: actual.fullPath !== '/' ? actual.fullPath : undefined },
        })
      }
    },
  )
}
