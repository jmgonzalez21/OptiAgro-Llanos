<script setup lang="ts">
/**
 * Notificación individual. Éxito/info/aviso: `role="status"`, se cierra sola (`duracion` ms), el temporizador
 * se pausa con hover y con foco dentro (WCAG 2.2.1/1.4.13) y siempre hay botón de cierre.
 * Error: `role="alert"` y no se cierra sola. Normalmente se usa a través de `useToast()` + `<UiToastRegion />`.
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import UiIcon from './UiIcon.vue'
import type { NombreIcono } from './icons'
import type { Toast } from './toast'

const props = defineProps<{ toast: Toast }>()
const emit = defineEmits<{ cerrar: [id: number] }>()

const ICONOS: Record<Toast['tono'], NombreIcono> = { exito: 'exito', info: 'info', aviso: 'aviso', error: 'alerta' }

let restante = props.toast.duracion
let inicio = 0
let temporizador: ReturnType<typeof setTimeout> | null = null
const pausado = ref(false)

function arrancar(): void {
  if (props.toast.duracion <= 0 || temporizador !== null) return
  inicio = Date.now()
  temporizador = setTimeout(() => emit('cerrar', props.toast.id), restante)
}

function pausar(): void {
  pausado.value = true
  if (temporizador === null) return
  clearTimeout(temporizador)
  temporizador = null
  restante = Math.max(1200, restante - (Date.now() - inicio))
}

function reanudar(ev?: FocusEvent): void {
  // Con foco dentro (p. ej. en el botón de cierre) no se reanuda hasta que salga.
  if (ev && (ev.currentTarget as HTMLElement).contains(ev.relatedTarget as Node | null)) return
  pausado.value = false
  arrancar()
}

function activarAccion(): void {
  props.toast.accion?.alActivar()
  emit('cerrar', props.toast.id)
}

onMounted(arrancar)
onBeforeUnmount(() => {
  if (temporizador !== null) clearTimeout(temporizador)
})
</script>

<template>
  <div
    class="ui-toast"
    :class="[`ui-toast--${toast.tono}`, { 'ui-toast--pausado': pausado }]"
    :role="toast.tono === 'error' ? 'alert' : 'status'"
    @mouseenter="pausar"
    @mouseleave="reanudar()"
    @focusin="pausar"
    @focusout="reanudar($event)"
  >
    <UiIcon :nombre="ICONOS[toast.tono]" :tamano="20" class="ui-toast__icono" />
    <div class="ui-toast__cuerpo">
      <p v-if="toast.titulo" class="ui-toast__titulo">{{ toast.titulo }}</p>
      <p class="ui-toast__mensaje">{{ toast.mensaje }}</p>
      <button v-if="toast.accion" type="button" class="ui-toast__accion" @click="activarAccion">{{ toast.accion.etiqueta }}</button>
    </div>
    <button type="button" class="ui-toast__cerrar" aria-label="Cerrar notificación" @click="emit('cerrar', toast.id)">
      <UiIcon nombre="cerrar" :tamano="18" />
    </button>
  </div>
</template>

<style scoped>
.ui-toast {
  display: flex;
  align-items: flex-start;
  gap: var(--espacio-3);
  width: min(26rem, calc(100vw - 2rem));
  padding: 0.8rem 0.5rem 0.8rem var(--espacio-4);
  border: 1px solid var(--borde);
  border-radius: var(--radio-md);
  background: var(--fondo);
  color: var(--texto);
  box-shadow: var(--sombra-md);
  font-size: var(--texto-sm);
  pointer-events: auto;
}

.ui-toast--exito {
  --fondo: var(--color-exito-fondo);
  --borde: var(--color-exito-borde);
  --texto: var(--color-exito);
}

.ui-toast--info {
  --fondo: var(--color-info-fondo);
  --borde: var(--color-info-borde);
  --texto: var(--color-info);
}

.ui-toast--aviso {
  --fondo: var(--color-aviso-fondo);
  --borde: var(--color-aviso-borde);
  --texto: var(--color-aviso);
}

.ui-toast--error {
  --fondo: var(--color-error-fondo);
  --borde: var(--color-error-borde);
  --texto: var(--color-error);
}

.ui-toast__icono {
  margin-top: 0.1rem;
}

.ui-toast__cuerpo {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.15rem;
  min-width: 0;
}

.ui-toast__titulo {
  font-weight: var(--peso-fuerte);
}

.ui-toast__mensaje {
  font-weight: var(--peso-medio);
}

.ui-toast__accion {
  margin-top: var(--espacio-1);
  padding: 0.2rem 0;
  border: 0;
  background: none;
  color: inherit;
  font-weight: var(--peso-fuerte);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.ui-toast__cerrar {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  border: 0;
  border-radius: var(--radio-sm);
  background: transparent;
  color: inherit;
}

.ui-toast__cerrar:hover {
  background: color-mix(in srgb, currentColor 12%, transparent);
}
</style>
