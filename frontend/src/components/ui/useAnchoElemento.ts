import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue'

/** Ancho en píxeles de un elemento (ResizeObserver). `inicial` se usa hasta medir (y en jsdom). */
export function useAnchoElemento(el: Ref<HTMLElement | null>, inicial = 560): Ref<number> {
  const ancho = ref(inicial)
  let observador: ResizeObserver | null = null

  onMounted(() => {
    const nodo = el.value
    if (!nodo) return
    const medir = (): void => {
      const w = nodo.clientWidth
      if (w > 0) ancho.value = w
    }
    medir()
    if (typeof ResizeObserver !== 'undefined') {
      observador = new ResizeObserver(medir)
      observador.observe(nodo)
    }
  })

  onBeforeUnmount(() => {
    observador?.disconnect()
    observador = null
  })

  return ancho
}
