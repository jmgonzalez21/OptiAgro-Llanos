<script setup lang="ts">
/** Uso de cada planta: toneladas recibidas frente a su capacidad, con aviso "Planta llena" al 100 %. */
import UiUsageBar from '@/components/ui/UiUsageBar.vue'
import { formatearNumero } from '@/components/ui/formato'

export interface UsoPlanta {
  nombre: string
  usado: number
  capacidad: number
}

defineProps<{ plantas: UsoPlanta[] }>()
const llena = (p: UsoPlanta): boolean => p.capacidad > 0 && p.usado >= p.capacidad - 1e-6
</script>

<template>
  <ul class="uso">
    <li v-for="p in plantas" :key="p.nombre" class="uso__fila">
      <div class="uso__texto">
        <strong>{{ p.nombre }}</strong>
        <span class="uso__cifras">{{ formatearNumero(p.usado, { maxDecimales: 1 }) }} de {{ formatearNumero(p.capacidad, { maxDecimales: 1 }) }} t/semana</span>
      </div>
      <UiUsageBar :etiqueta="`Uso de ${p.nombre}`" :valor="p.usado" :maximo="p.capacidad" :critico="llena(p)" texto-critico="Planta llena" />
    </li>
    <li v-if="plantas.length === 0" class="nota">No hay plantas activas.</li>
  </ul>
</template>

<style scoped>
.uso {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-3);
}

.uso__texto {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--espacio-1) var(--espacio-3);
  margin-bottom: 0.25rem;
  font-size: var(--texto-sm);
}

.uso__cifras {
  color: var(--color-texto-2);
  font-variant-numeric: tabular-nums;
}
</style>
