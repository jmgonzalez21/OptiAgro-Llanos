/**
 * Sesión del usuario.
 *
 * - Usuario, rol y tokens viven en memoria (Pinia).
 * - Para sobrevivir a un refresco de página se guarda SOLO el refresh token en
 *   sessionStorage (con try/catch: puede no estar disponible).
 * - `restaurarSesion()` canjea ese refresh token por un access nuevo.
 */
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { obtenerApi } from '@/api'
import { nombreDeUsuario } from '@/api/servicios'
import { ErrorApi, ErrorRed } from '@/api/errores'
import { CLAVE_REFRESH } from '@/config'
import type { Credenciales, Rol, Usuario } from '@/types/api'

function leerRefreshGuardado(): string | null {
  try {
    return sessionStorage.getItem(CLAVE_REFRESH)
  } catch {
    return null
  }
}

function guardarRefresh(token: string): void {
  try {
    sessionStorage.setItem(CLAVE_REFRESH, token)
  } catch {
    /* sessionStorage no disponible: la sesión simplemente no sobrevivirá al refresco. */
  }
}

function borrarRefresh(): void {
  try {
    sessionStorage.removeItem(CLAVE_REFRESH)
  } catch {
    /* sin acción */
  }
}

export const ETIQUETAS_ROL: Record<Rol, string> = {
  administrador: 'Administrador',
  analista: 'Analista',
}

export const useAuthStore = defineStore('auth', () => {
  const api = obtenerApi()

  const usuario = ref<Usuario | null>(null)
  const access = ref<string | null>(null)
  const refresh = ref<string | null>(null)
  /** true cuando la sesión terminó por vencimiento (no por cierre voluntario). */
  const sesionExpirada = ref(false)
  const cargando = ref(false)
  const inicializado = ref(false)

  const autenticado = computed(() => usuario.value !== null && access.value !== null)
  const rol = computed<Rol | null>(() => usuario.value?.rol ?? null)
  const esAdministrador = computed(() => rol.value === 'administrador')
  const nombre = computed(() => (usuario.value ? nombreDeUsuario(usuario.value) : ''))
  const etiquetaRol = computed(() => (rol.value ? ETIQUETAS_ROL[rol.value] : ''))

  function limpiar(): void {
    usuario.value = null
    access.value = null
    refresh.value = null
    borrarRefresh()
  }

  function establecerTokens(nuevoAccess: string, nuevoRefresh?: string): void {
    access.value = nuevoAccess
    if (nuevoRefresh) {
      refresh.value = nuevoRefresh
      guardarRefresh(nuevoRefresh)
    }
  }

  // Conecta el cliente HTTP (interceptor) con este store.
  api.configurarSesion({
    obtenerAccess: () => access.value,
    obtenerRefresh: () => refresh.value,
    alRenovar: (nuevoAccess, nuevoRefresh) => establecerTokens(nuevoAccess, nuevoRefresh),
    alExpirar: () => {
      limpiar()
      sesionExpirada.value = true
    },
  })

  /** Inicia sesión. Lanza un `ErrorApi` tipado si falla (credenciales, red, etc.). */
  async function login(credenciales: Credenciales): Promise<void> {
    cargando.value = true
    sesionExpirada.value = false
    try {
      const respuesta = await api.login({ username: credenciales.username.trim(), password: credenciales.password })
      establecerTokens(respuesta.access, respuesta.refresh)
      try {
        usuario.value = respuesta.usuario ?? (await api.obtenerUsuario())
      } catch (e) {
        limpiar()
        throw e
      }
    } finally {
      cargando.value = false
    }
  }

  /** Cierra la sesión: revoca el refresh en el servidor (sin esperar) y limpia el estado local. */
  function logout(): void {
    const token = refresh.value ?? leerRefreshGuardado()
    if (token) void api.logout(token)
    limpiar()
    sesionExpirada.value = false
  }

  /** PATCH /auth/me/: edita nombre, apellido y correo propios. */
  async function actualizarPerfil(datos: { first_name: string; last_name: string; email: string }): Promise<void> {
    usuario.value = await api.solicitar<Usuario>('/auth/me/', { metodo: 'PATCH', cuerpo: datos })
  }

  /** POST /auth/cambiar-contrasena/: revoca las demás sesiones y entrega tokens nuevos. */
  async function cambiarContrasena(actual: string, nueva: string): Promise<void> {
    const r = await api.solicitar<{ access: string; refresh: string }>('/auth/cambiar-contrasena/', {
      metodo: 'POST',
      cuerpo: { contrasena_actual: actual, contrasena_nueva: nueva },
    })
    establecerTokens(r.access, r.refresh)
  }

  /**
   * Intenta recuperar la sesión con el refresh token de sessionStorage.
   * Devuelve true si quedó autenticado.
   */
  async function restaurarSesion(): Promise<boolean> {
    const guardado = refresh.value ?? leerRefreshGuardado()
    if (!guardado) return false
    cargando.value = true
    try {
      const datos = await api.refrescar(guardado)
      refresh.value = guardado
      establecerTokens(datos.access, datos.refresh)
      usuario.value = await api.obtenerUsuario()
      return true
    } catch (e) {
      // Con la red caída se conserva el refresh token para poder reintentar luego.
      const recuperable = e instanceof ErrorRed || (e instanceof ErrorApi && e.codigo === 'servidor')
      if (recuperable) {
        usuario.value = null
        access.value = null
      } else {
        limpiar()
      }
      return false
    } finally {
      cargando.value = false
    }
  }

  let promesaInicial: Promise<void> | null = null
  /** Restaura la sesión una sola vez; la usan los route guards. */
  function inicializar(): Promise<void> {
    promesaInicial ??= restaurarSesion()
      .then(() => undefined)
      .finally(() => {
        inicializado.value = true
      })
    return promesaInicial
  }

  return {
    usuario,
    access,
    refresh,
    sesionExpirada,
    cargando,
    inicializado,
    autenticado,
    rol,
    esAdministrador,
    nombre,
    etiquetaRol,
    login,
    logout,
    actualizarPerfil,
    cambiarContrasena,
    restaurarSesion,
    inicializar,
  }
})
