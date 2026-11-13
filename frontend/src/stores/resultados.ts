/** Último resultado del método exacto, compartido entre Optimización y la matriz (vista «Toneladas asignadas»). */
import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { ResultadoOptimizacion } from '@/types/fase2'

export const useResultadosStore = defineStore('resultados', () => {
  const ultimoExacto = ref<ResultadoOptimizacion | null>(null)
  function guardarExacto(r: ResultadoOptimizacion | null): void {
    ultimoExacto.value = r
  }
  return { ultimoExacto, guardarExacto }
})
