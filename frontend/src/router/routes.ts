import type { RouteRecordRaw } from 'vue-router'

export const rutasApp: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { soloInvitado: true, titulo: 'Iniciar sesión' },
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiereAuth: true },
    children: [
      {
        path: '',
        name: 'inicio',
        component: () => import('@/views/HomeView.vue'),
        meta: { titulo: 'Inicio' },
      },
      {
        path: 'red',
        name: 'red',
        component: () => import('@/views/RedView.vue'),
        meta: { titulo: 'Red logística' },
      },
      {
        path: 'matriz',
        name: 'matriz-costos',
        component: () => import('@/views/MatrizView.vue'),
        meta: { titulo: 'Matriz de costos' },
      },
      {
        path: 'optimizacion',
        name: 'optimizacion',
        component: () => import('@/views/OptimizacionView.vue'),
        meta: { titulo: 'Optimización' },
      },
      {
        path: 'sensibilidad',
        name: 'sensibilidad',
        component: () => import('@/views/SensibilidadView.vue'),
        meta: { titulo: '¿Qué pasa si…?' },
      },
      {
        path: 'reporte',
        name: 'reporte',
        component: () => import('@/views/ReporteView.vue'),
        meta: { titulo: 'Reporte comparativo' },
      },
      {
        path: 'historial',
        name: 'historial',
        component: () => import('@/views/HistorialView.vue'),
        meta: { titulo: 'Historial de ejecuciones' },
      },
      {
        path: 'usuarios',
        name: 'usuarios',
        component: () => import('@/views/UsuariosView.vue'),
        meta: { titulo: 'Usuarios', roles: ['administrador'] },
      },
      {
        path: 'perfil',
        name: 'perfil',
        component: () => import('@/views/PerfilView.vue'),
        meta: { titulo: 'Mi perfil' },
      },
      {
        path: 'sin-permiso',
        name: 'sin-permiso',
        component: () => import('@/views/SinPermisoView.vue'),
        meta: { titulo: 'Acceso denegado' },
      },
    ],
  },
  { path: '/:resto(.*)*', redirect: { name: 'inicio' } },
]
