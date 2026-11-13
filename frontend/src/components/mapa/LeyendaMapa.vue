<script setup lang="ts">
/** Leyenda del mapa: mismos símbolos (forma + ícono + color) que los marcadores, con conteo opcional. */
import UiMarcador from '@/components/ui/UiMarcador.vue'

withDefaults(defineProps<{ empresas?: number | null; plantas?: number | null }>(), { empresas: null, plantas: null })
</script>

<template>
  <ul class="leyenda-mapa" aria-label="Leyenda del mapa">
    <li class="leyenda-mapa__item">
      <UiMarcador tipo="empresa" :tamano="26" class="leyenda-mapa__simbolo" />
      <span class="leyenda-mapa__texto">Agroempresa (oferta)</span>
      <span v-if="empresas !== null" class="leyenda-mapa__cuenta">{{ empresas }}</span>
    </li>
    <li class="leyenda-mapa__item">
      <UiMarcador tipo="planta" :tamano="30" class="leyenda-mapa__simbolo" />
      <span class="leyenda-mapa__texto">Planta (capacidad)</span>
      <span v-if="plantas !== null" class="leyenda-mapa__cuenta">{{ plantas }}</span>
    </li>
  </ul>
</template>

<style scoped>
.leyenda-mapa {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.leyenda-mapa__item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  color: var(--color-texto);
}

.leyenda-mapa__simbolo {
  display: inline-flex;
  flex-shrink: 0;
  justify-content: center;
  width: 1.9rem;
}

.leyenda-mapa__texto {
  flex: 1;
}

.leyenda-mapa__cuenta {
  min-width: 1.6rem;
  padding: 0 0.45rem;
  border-radius: var(--radio-pleno);
  background: var(--color-activo-fondo);
  color: var(--color-activo-texto);
  font-size: var(--texto-xs);
  font-weight: var(--peso-fuerte);
  text-align: center;
  line-height: 1.5rem;
}
</style>
