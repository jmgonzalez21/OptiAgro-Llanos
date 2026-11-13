/**
 * Comportamiento común de diálogos y paneles: foco inicial, foco atrapado (Tab/Mayús+Tab),
 * Esc, devolución del foco al disparador y bloqueo del scroll del documento.
 */
import { nextTick, onBeforeUnmount, watch, type Ref } from 'vue'

const SELECTOR_ENFOCABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
  '[contenteditable="true"]',
].join(',')

export function elementosEnfocables(raiz: HTMLElement): HTMLElement[] {
  return Array.from(raiz.querySelectorAll<HTMLElement>(SELECTOR_ENFOCABLE)).filter(
    (el) => !el.hasAttribute('inert') && el.getAttribute('aria-hidden') !== 'true' && !el.closest('[hidden]'),
  )
}

let bloqueos = 0
let overflowPrevio = ''

function bloquearScroll(): void {
  if (bloqueos === 0) {
    overflowPrevio = document.documentElement.style.overflow
    document.documentElement.style.overflow = 'hidden'
  }
  bloqueos++
}

function liberarScroll(): void {
  bloqueos = Math.max(0, bloqueos - 1)
  if (bloqueos === 0) document.documentElement.style.overflow = overflowPrevio
}

export interface OpcionesDialogo {
  /** Contenedor del diálogo (el que recibe el foco atrapado). */
  contenedor: Ref<HTMLElement | null>
  abierto: Ref<boolean>
  /** Se llama con Esc. */
  alEscape: () => void
  /** Elemento que recibe el foco al abrir (por defecto `[data-autofocus]`, luego el primero enfocable). */
  focoInicial?: () => HTMLElement | null | undefined
}

export function useDialogo(opciones: OpcionesDialogo): { alTeclado: (ev: KeyboardEvent) => void } {
  let disparador: HTMLElement | null = null
  let bloqueado = false

  function enfocarInicial(): void {
    const raiz = opciones.contenedor.value
    if (!raiz) return
    const elegido =
      opciones.focoInicial?.() ??
      raiz.querySelector<HTMLElement>('[data-autofocus]') ??
      elementosEnfocables(raiz).find((el) => !el.matches('[data-cerrar]')) ??
      raiz
    elegido.focus({ preventScroll: true })
  }

  watch(
    opciones.abierto,
    async (abierto) => {
      if (abierto) {
        disparador = document.activeElement instanceof HTMLElement ? document.activeElement : null
        if (!bloqueado) {
          bloquearScroll()
          bloqueado = true
        }
        await nextTick()
        enfocarInicial()
      } else {
        if (bloqueado) {
          liberarScroll()
          bloqueado = false
        }
        const destino = disparador
        disparador = null
        if (destino && document.contains(destino)) {
          await nextTick()
          destino.focus({ preventScroll: true })
        }
      }
    },
    { immediate: true, flush: 'post' },
  )

  onBeforeUnmount(() => {
    if (bloqueado) {
      liberarScroll()
      bloqueado = false
    }
  })

  function alTeclado(ev: KeyboardEvent): void {
    if (ev.key === 'Escape' && !ev.defaultPrevented) {
      ev.stopPropagation()
      ev.preventDefault()
      opciones.alEscape()
      return
    }
    if (ev.key !== 'Tab') return
    const raiz = opciones.contenedor.value
    if (!raiz) return
    const lista = elementosEnfocables(raiz)
    if (lista.length === 0) {
      ev.preventDefault()
      raiz.focus()
      return
    }
    const primero = lista[0]!
    const ultimo = lista[lista.length - 1]!
    const activo = document.activeElement
    if (ev.shiftKey && (activo === primero || activo === raiz)) {
      ev.preventDefault()
      ultimo.focus()
    } else if (!ev.shiftKey && activo === ultimo) {
      ev.preventDefault()
      primero.focus()
    }
  }

  return { alTeclado }
}
