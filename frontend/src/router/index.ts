import { createRouter, type RouterHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { evaluarAcceso } from './guards'
import { rutasApp } from './routes'

const NOMBRE_APP = 'OptiAgro-Llanos'

/** Crea el router con los guards instalados (Pinia debe estar activo). */
export function crearRouter(historial: RouterHistory, rutas: RouteRecordRaw[] = rutasApp) {
  const router = createRouter({ history: historial, routes: rutas })

  router.beforeEach((to) => evaluarAcceso(to, useAuthStore()))

  router.afterEach((to) => {
    const titulo = to.meta.titulo
    document.title = titulo ? `${titulo} · ${NOMBRE_APP}` : NOMBRE_APP
  })

  return router
}
