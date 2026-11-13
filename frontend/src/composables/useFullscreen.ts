import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue'

/** Pantalla completa para un elemento (API Fullscreen). `soportado` es false en iOS Safari, etc. */
export function useFullscreen(elemento: Ref<HTMLElement | null>) {
  const activo = ref(false)
  const soportado = ref(false)

  function sincronizar(): void {
    activo.value = document.fullscreenElement !== null && document.fullscreenElement === elemento.value
  }

  async function alternar(): Promise<void> {
    try {
      if (document.fullscreenElement) await document.exitFullscreen()
      else await elemento.value?.requestFullscreen()
    } catch {
      /* el navegador rechazó la solicitud: no hay nada que hacer */
    }
  }

  onMounted(() => {
    soportado.value = typeof document.fullscreenEnabled === 'boolean' && document.fullscreenEnabled
    document.addEventListener('fullscreenchange', sincronizar)
  })
  onBeforeUnmount(() => document.removeEventListener('fullscreenchange', sincronizar))

  return { activo, soportado, alternar }
}
