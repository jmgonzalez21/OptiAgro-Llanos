<script setup lang="ts">
/**
 * Panel lateral para formularios (480 px; pantalla completa por debajo de 768 px).
 * `role="dialog"` + `aria-modal`, foco atrapado, Esc, foco devuelto al disparador, pie fijo con
 * `scroll-padding-bottom` para que no tape el campo enfocado (WCAG 2.4.11).
 *
 * Igual que UiModal: `:abierto` controlado; emite `cerrar(motivo)` y `update:abierto(false)`; con
 * `bloquearCierre` solo emite `cerrar` (el padre abre el diálogo de 3 opciones si hay cambios sin guardar).
 * Slots: default (cuerpo), `pie` (Guardar / Cancelar), `cabecera` (contenido extra bajo el título, p. ej. UiStepper).
 */
import { computed, ref, toRef, useId, useSlots } from 'vue'
import UiIcon from './UiIcon.vue'
import { useDialogo } from './useDialogo'
import type { MotivoCierre } from './UiModal.vue'

const props = withDefaults(
  defineProps<{
    abierto: boolean
    titulo: string
    descripcion?: string
    /** Ancho en escritorio (CSS). Por defecto 30rem = 480 px. */
    ancho?: string
    lado?: 'derecha' | 'izquierda'
    bloquearCierre?: boolean
  }>(),
  { descripcion: '', ancho: '30rem', lado: 'derecha', bloquearCierre: false },
)

const emit = defineEmits<{
  'update:abierto': [valor: boolean]
  cerrar: [motivo: MotivoCierre]
}>()

const slots = useSlots()
const id = useId()
const idTitulo = `${id}-titulo`
const idDescripcion = `${id}-desc`
const panel = ref<HTMLElement | null>(null)

function solicitarCierre(motivo: MotivoCierre): void {
  emit('cerrar', motivo)
  if (!props.bloquearCierre) emit('update:abierto', false)
}

const { alTeclado } = useDialogo({
  contenedor: panel,
  abierto: toRef(props, 'abierto'),
  alEscape: () => solicitarCierre('esc'),
})

const tieneDescripcion = computed(() => props.descripcion !== '' || !!slots.descripcion)
</script>

<template>
  <Teleport to="body">
    <Transition :name="`ui-drawer-${lado}`">
      <div v-if="abierto" class="ui-drawer" :class="`ui-drawer--${lado}`" @keydown="alTeclado">
        <div class="ui-drawer__velo" aria-hidden="true" @click="solicitarCierre('velo')"></div>
        <section
          ref="panel"
          class="ui-drawer__panel"
          :style="{ '--ancho-drawer': ancho }"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="idTitulo"
          :aria-describedby="tieneDescripcion ? idDescripcion : undefined"
          tabindex="-1"
        >
          <header class="ui-drawer__cabecera">
            <div class="ui-drawer__encabezado">
              <h2 :id="idTitulo" class="ui-drawer__titulo">{{ titulo }}</h2>
              <button type="button" class="ui-drawer__cerrar" data-cerrar aria-label="Cerrar panel" @click="solicitarCierre('boton')">
                <UiIcon nombre="cerrar" :tamano="20" />
              </button>
            </div>
            <p v-if="tieneDescripcion" :id="idDescripcion" class="ui-drawer__descripcion"><slot name="descripcion">{{ descripcion }}</slot></p>
            <slot name="cabecera" />
          </header>
          <div class="ui-drawer__cuerpo"><slot /></div>
          <footer v-if="$slots.pie" class="ui-drawer__pie"><slot name="pie" /></footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.ui-drawer {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  display: flex;
}

.ui-drawer--derecha {
  justify-content: flex-end;
}

.ui-drawer__velo {
  position: absolute;
  inset: 0;
  background: var(--color-velo);
}

.ui-drawer__panel {
  position: relative;
  display: flex;
  flex-direction: column;
  width: min(var(--ancho-drawer), 100vw);
  height: 100%;
  background: var(--color-superficie);
  color: var(--color-texto);
  box-shadow: var(--sombra-lg);
}

.ui-drawer--derecha .ui-drawer__panel {
  border-left: 1px solid var(--color-borde);
}

.ui-drawer--izquierda .ui-drawer__panel {
  border-right: 1px solid var(--color-borde);
}

.ui-drawer__panel:focus-visible {
  outline: none;
  box-shadow: var(--sombra-lg);
}

.ui-drawer__cabecera {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
  padding: var(--espacio-4) var(--espacio-4) var(--espacio-3) var(--espacio-5);
  border-bottom: 1px solid var(--color-borde);
}

.ui-drawer__encabezado {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-3);
}

.ui-drawer__titulo {
  font-size: var(--texto-lg);
}

.ui-drawer__descripcion {
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
}

.ui-drawer__cerrar {
  display: grid;
  flex-shrink: 0;
  place-items: center;
  width: var(--alto-tactil);
  height: var(--alto-tactil);
  border: 0;
  border-radius: var(--radio-md);
  background: transparent;
  color: var(--color-texto-2);
}

.ui-drawer__cerrar:hover {
  background: var(--color-acento-suave);
  color: var(--color-activo-texto);
}

.ui-drawer__cuerpo {
  flex: 1;
  min-height: 0;
  padding: var(--espacio-4) var(--espacio-5);
  overflow-y: auto;
  /* El pie fijo no debe tapar el campo enfocado (WCAG 2.4.11). */
  scroll-padding-block: 1rem 6rem;
}

.ui-drawer__pie {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--espacio-2);
  padding: var(--espacio-3) var(--espacio-5);
  border-top: 1px solid var(--color-borde);
  background: var(--color-superficie);
}

.ui-drawer-derecha-enter-active,
.ui-drawer-derecha-leave-active,
.ui-drawer-izquierda-enter-active,
.ui-drawer-izquierda-leave-active {
  transition: opacity var(--trans);
}

.ui-drawer-derecha-enter-active .ui-drawer__panel,
.ui-drawer-derecha-leave-active .ui-drawer__panel,
.ui-drawer-izquierda-enter-active .ui-drawer__panel,
.ui-drawer-izquierda-leave-active .ui-drawer__panel {
  transition: transform var(--trans-lenta);
}

.ui-drawer-derecha-enter-from,
.ui-drawer-derecha-leave-to,
.ui-drawer-izquierda-enter-from,
.ui-drawer-izquierda-leave-to {
  opacity: 0;
}

.ui-drawer-derecha-enter-from .ui-drawer__panel,
.ui-drawer-derecha-leave-to .ui-drawer__panel {
  transform: translateX(100%);
}

.ui-drawer-izquierda-enter-from .ui-drawer__panel,
.ui-drawer-izquierda-leave-to .ui-drawer__panel {
  transform: translateX(-100%);
}

@media (max-width: 47.99rem) {
  .ui-drawer__panel {
    width: 100vw;
  }
}
</style>
