<script setup lang="ts">
/**
 * Región de notificaciones. Montar UNA vez (App.vue o AppLayout): `<UiToastRegion />`.
 * La región existe siempre (los lectores de pantalla necesitan la región viva antes del contenido).
 */
import UiToast from './UiToast.vue'
import { useToast } from './toast'

const { toasts, cerrar } = useToast()
</script>

<template>
  <Teleport to="body">
    <section class="ui-toast-region" aria-label="Notificaciones">
      <TransitionGroup name="ui-toast" tag="div" class="ui-toast-region__lista">
        <UiToast v-for="t in toasts" :key="t.id" :toast="t" @cerrar="cerrar" />
      </TransitionGroup>
    </section>
  </Teleport>
</template>

<style scoped>
.ui-toast-region {
  position: fixed;
  right: var(--espacio-4);
  bottom: var(--espacio-4);
  z-index: var(--z-toast);
  pointer-events: none;
}

.ui-toast-region__lista {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--espacio-2);
}

.ui-toast-enter-active,
.ui-toast-leave-active {
  transition:
    opacity var(--trans),
    transform var(--trans);
}

.ui-toast-enter-from,
.ui-toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 40rem) {
  .ui-toast-region {
    right: 0;
    left: 0;
    bottom: var(--espacio-3);
    display: flex;
    justify-content: center;
  }
}
</style>
