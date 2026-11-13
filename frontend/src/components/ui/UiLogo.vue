<script setup lang="ts">
/** Logotipo OptiAgro-Llanos: isotipo (hoja sobre baldosa verde) + nombre. */
import UiIcon from './UiIcon.vue'

withDefaults(
  defineProps<{
    /** Solo el isotipo (sidebar colapsado). El nombre sigue disponible para lectores de pantalla. */
    soloIsotipo?: boolean
    tamano?: number
  }>(),
  { soloIsotipo: false, tamano: 40 },
)
</script>

<template>
  <span class="ui-logo">
    <span class="ui-logo__isotipo" :style="{ width: `${tamano}px`, height: `${tamano}px` }" aria-hidden="true">
      <UiIcon nombre="hoja" :tamano="Math.round(tamano * 0.58)" :grosor="1.9" />
    </span>
    <span class="ui-logo__nombre" :class="{ 'sr-only': soloIsotipo }">OptiAgro<span class="ui-logo__sufijo">-Llanos</span></span>
  </span>
</template>

<style scoped>
.ui-logo {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
}

.ui-logo__isotipo {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 30%;
  background: linear-gradient(145deg, #55ab78 0%, #1f6b43 62%, #124a2d 100%);
  color: #ffffff;
  box-shadow:
    0 6px 14px -5px rgb(18 74 45 / 0.55),
    inset 0 1px 0 rgb(255 255 255 / 0.28);
}

.ui-logo__nombre {
  font-size: 1.1875rem;
  font-weight: var(--peso-fuerte);
  letter-spacing: -0.02em;
  color: var(--color-texto);
  white-space: nowrap;
}

.ui-logo__sufijo {
  color: var(--color-primario);
}
</style>
