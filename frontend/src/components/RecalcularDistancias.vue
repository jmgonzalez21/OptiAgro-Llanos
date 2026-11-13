<script setup lang="ts">
/** Botón (solo administrador) que recalcula las distancias por carretera; por defecto solo las estimadas. */
import { ref } from 'vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCheckbox from '@/components/ui/UiCheckbox.vue'
import { solicitar, textoDeError, TIMEOUT_CALCULO_MS } from '@/api/util'

interface Respuesta {
  actualizadas: number
  estimadas: number
  errores: number
  aviso?: string | null
}

const emit = defineEmits<{ hecho: [] }>()

const incluirManuales = ref(false)
const trabajando = ref(false)
const resumen = ref('')
const aviso = ref('')
const error = ref('')

async function recalcular(): Promise<void> {
  trabajando.value = true
  resumen.value = ''
  aviso.value = ''
  error.value = ''
  try {
    const r = await solicitar<Respuesta>('/rutas/recalcular-distancias/', {
      metodo: 'POST',
      cuerpo: incluirManuales.value ? { incluir_manuales: true } : { solo_estimadas: true },
      timeoutMs: TIMEOUT_CALCULO_MS,
    })
    resumen.value = `Se actualizaron ${r.actualizadas} ${r.actualizadas === 1 ? 'distancia' : 'distancias'} (${r.estimadas} estimadas, ${r.errores} con error).`
    aviso.value = r.aviso ?? ''
    emit('hecho')
  } catch (e) {
    error.value = textoDeError(e) || 'No se pudieron recalcular las distancias.'
  } finally {
    trabajando.value = false
  }
}
</script>

<template>
  <div class="recalcular">
    <div class="recalcular__fila">
      <UiButton variante="secundario" :loading="trabajando" @click="recalcular">Recalcular distancias por carretera</UiButton>
      <UiCheckbox v-model="incluirManuales" :disabled="trabajando">Incluir también las ingresadas a mano</UiCheckbox>
    </div>
    <p v-if="incluirManuales" class="nota">Atención: las distancias ingresadas a mano se sobrescribirán con las de carretera.</p>
    <p v-else class="nota">Por defecto solo se actualizan las distancias estimadas.</p>
    <UiAlert v-if="resumen" tono="exito">{{ resumen }} <template v-if="aviso">{{ aviso }}</template></UiAlert>
    <UiAlert v-if="error" tono="error">{{ error }}</UiAlert>
  </div>
</template>

<style scoped>
.recalcular {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
}

.recalcular__fila {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--espacio-3);
}
</style>
