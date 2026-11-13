<script setup lang="ts">
/** Barras horizontales simples (CSS) para comparar dos o más valores; el valor siempre va también en texto. */
import { computed } from 'vue'

export interface BarraItem {
  etiqueta: string
  valor: number
  texto: string
}

const props = defineProps<{ titulo: string; items: BarraItem[] }>()
const max = computed(() => Math.max(...props.items.map((i) => i.valor), 1e-9))
</script>

<template>
  <figure class="barras">
    <figcaption>{{ titulo }}</figcaption>
    <ul>
      <li v-for="(i, k) in items" :key="i.etiqueta" class="barras__fila">
        <span class="barras__etiqueta">{{ i.etiqueta }}</span>
        <span class="barras__pista" aria-hidden="true"><span class="barras__relleno" :class="{ 'barras__relleno--2': k > 0 }" :style="{ width: `${Math.max((i.valor / max) * 100, 1)}%` }"></span></span>
        <span class="barras__texto">{{ i.texto }}</span>
      </li>
    </ul>
  </figure>
</template>

<style scoped>
.barras figcaption {
  margin-bottom: var(--espacio-2);
  font-size: var(--texto-sm);
  font-weight: var(--peso-fuerte);
  color: var(--color-texto-2);
}

.barras ul {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
}

.barras__fila {
  display: grid;
  grid-template-columns: 8.5rem 1fr auto;
  align-items: center;
  gap: var(--espacio-3);
  font-size: var(--texto-sm);
}

.barras__pista {
  height: 1rem;
  border-radius: var(--radio-pleno);
  background: var(--color-superficie-2);
  border: 1px solid var(--color-borde);
  overflow: hidden;
}

.barras__relleno {
  display: block;
  height: 100%;
  border-radius: var(--radio-pleno);
  background: var(--color-primario);
}

.barras__relleno--2 {
  background: var(--color-activo-barra);
}

.barras__texto {
  min-width: 6.5rem;
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-weight: var(--peso-medio);
}

@media (max-width: 40rem) {
  .barras__fila {
    grid-template-columns: 1fr auto;
  }

  .barras__pista {
    grid-column: 1 / -1;
    order: 3;
  }
}
</style>
