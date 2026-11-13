/**
 * Estaciones de la red logística: agroempresas (oferta) y plantas (capacidad).
 * Solo se exponen las ACTIVAS: si una estación deja de venir como activa
 * (o llega con activa=false) desaparece de los getters y, por tanto, del mapa.
 */
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { obtenerApi } from '@/api'
import { mensajeDeError } from '@/api/errores'
import type { Empresa, Planta } from '@/types/api'

export type EstadoCarga = 'inactivo' | 'cargando' | 'listo' | 'error'

export const useRedStore = defineStore('red', () => {
  const empresasCrudas = ref<Empresa[]>([])
  const plantasCrudas = ref<Planta[]>([])
  const estado = ref<EstadoCarga>('inactivo')
  const error = ref<string | null>(null)

  const empresas = computed(() => empresasCrudas.value.filter((e) => e.activa))
  const plantas = computed(() => plantasCrudas.value.filter((p) => p.activa))
  /** Hay datos de demostración ficticios en la red activa. */
  const hayFicticios = computed(() => [...empresas.value, ...plantas.value].some((e) => e.ficticio === true))
  const total = computed(() => empresas.value.length + plantas.value.length)

  /** Carga (o recarga) las estaciones activas. Reemplaza lo anterior por completo. */
  async function cargar(): Promise<void> {
    const api = obtenerApi()
    estado.value = 'cargando'
    error.value = null
    try {
      const [listaEmpresas, listaPlantas] = await Promise.all([
        api.listarEmpresas({ activa: true }),
        api.listarPlantas({ activa: true }),
      ])
      empresasCrudas.value = listaEmpresas
      plantasCrudas.value = listaPlantas
      estado.value = 'listo'
    } catch (e) {
      error.value = mensajeDeError(e)
      estado.value = 'error'
    }
  }

  function reiniciar(): void {
    empresasCrudas.value = []
    plantasCrudas.value = []
    estado.value = 'inactivo'
    error.value = null
  }

  return { empresas, plantas, total, hayFicticios, estado, error, cargar, reiniciar }
})
