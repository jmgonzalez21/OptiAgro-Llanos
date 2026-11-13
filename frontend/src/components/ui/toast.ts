/**
 * Notificaciones (toasts). Estado a nivel de módulo: no requiere Pinia ni provide/inject.
 * Montar `<UiToastRegion />` una sola vez (App.vue / AppLayout) y llamar `useToast()` donde haga falta.
 *
 * Regla UX (§4.5): los éxitos/avisos se cierran a los 6 s (se pausan con hover/foco);
 * los errores NO desaparecen solos: quedan hasta que la persona los cierre.
 */
import { readonly, shallowRef } from 'vue'

export type TonoToast = 'exito' | 'info' | 'aviso' | 'error'

export interface AccionToast {
  etiqueta: string
  /** Se ejecuta al activarla; el toast se cierra después. */
  alActivar: () => void
}

export interface Toast {
  id: number
  tono: TonoToast
  titulo?: string
  mensaje: string
  /** ms hasta cerrarse; 0 = permanente. Los errores siempre son permanentes. */
  duracion: number
  accion?: AccionToast
}

export interface OpcionesToast {
  titulo?: string
  duracion?: number
  accion?: AccionToast
}

export const DURACION_TOAST = 6000

const lista = shallowRef<Toast[]>([])
let contador = 0

function notificar(tono: TonoToast, mensaje: string, opciones: OpcionesToast = {}): number {
  const id = ++contador
  const duracion = tono === 'error' ? 0 : (opciones.duracion ?? DURACION_TOAST)
  lista.value = [...lista.value, { id, tono, mensaje, titulo: opciones.titulo, duracion, accion: opciones.accion }].slice(-5)
  return id
}

function cerrar(id: number): void {
  lista.value = lista.value.filter((t) => t.id !== id)
}

function limpiar(): void {
  lista.value = []
}

export function useToast() {
  return {
    toasts: readonly(lista),
    notificar,
    exito: (mensaje: string, o?: OpcionesToast) => notificar('exito', mensaje, o),
    info: (mensaje: string, o?: OpcionesToast) => notificar('info', mensaje, o),
    aviso: (mensaje: string, o?: OpcionesToast) => notificar('aviso', mensaje, o),
    error: (mensaje: string, o?: OpcionesToast) => notificar('error', mensaje, o),
    cerrar,
    limpiar,
  }
}
