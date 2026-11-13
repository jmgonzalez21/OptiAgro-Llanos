<script setup lang="ts">
/** Etiqueta compacta de estado/rol. Tonos: neutro, verde, ambar, info, error. */
withDefaults(
  defineProps<{
    tono?: 'neutro' | 'verde' | 'ambar' | 'info' | 'error'
    punto?: boolean
  }>(),
  { tono: 'neutro', punto: false },
)
</script>

<template>
  <span class="ui-insignia" :class="`ui-insignia--${tono}`">
    <span v-if="punto" class="ui-insignia__punto" aria-hidden="true"></span>
    <slot />
  </span>
</template>

<style scoped>
.ui-insignia {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.15rem 0.65rem;
  border: 1px solid var(--borde);
  border-radius: var(--radio-pleno);
  background: var(--fondo);
  color: var(--texto);
  font-size: var(--texto-xs);
  font-weight: var(--peso-fuerte);
  line-height: 1.4;
  white-space: nowrap;
}

.ui-insignia__punto {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 50%;
  background: currentColor;
}

.ui-insignia--neutro {
  --fondo: var(--color-superficie-2);
  --borde: var(--color-borde);
  --texto: var(--color-texto-2);
}

.ui-insignia--verde {
  --fondo: var(--color-activo-fondo);
  --borde: var(--color-exito-borde);
  --texto: var(--color-activo-texto);
}

.ui-insignia--ambar {
  --fondo: var(--color-aviso-fondo);
  --borde: var(--color-aviso-borde);
  --texto: var(--color-aviso);
}

.ui-insignia--info {
  --fondo: var(--color-info-fondo);
  --borde: var(--color-info-borde);
  --texto: var(--color-info);
}

.ui-insignia--error {
  --fondo: var(--color-error-fondo);
  --borde: var(--color-error-borde);
  --texto: var(--color-error);
}
</style>
