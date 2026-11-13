<script setup lang="ts">
import { computed, ref } from 'vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiIcon from '@/components/ui/UiIcon.vue'
import UiPageHeader from '@/components/ui/UiPageHeader.vue'
import UiTabs from '@/components/ui/UiTabs.vue'
import { useAuthStore } from '@/stores/auth'
import PanelEstaciones from './red/PanelEstaciones.vue'
import TablaRutas from './red/TablaRutas.vue'

const auth = useAuthStore()
const pestana = ref('empresas')
const PESTANAS = [
  { id: 'empresas', etiqueta: 'Empresas' },
  { id: 'plantas', etiqueta: 'Plantas' },
  { id: 'rutas', etiqueta: 'Rutas' },
]
const BOTON: Record<string, string> = { empresas: 'Agregar empresa', plantas: 'Agregar planta', rutas: 'Agregar ruta' }
const etiquetaBoton = computed(() => BOTON[pestana.value] ?? 'Agregar')

// Solo hay un panel montado a la vez: la referencia apunta al de la pestaña activa.
const panel = ref<{ abrir: (fila: null) => void } | null>(null)
</script>

<template>
  <section class="vista">
    <UiPageHeader
      titulo="Red logística"
      descripcion="Aquí puedes ver y ampliar la red: agrega empresas que generan residuos y plantas que los reciben, ubícalas en el mapa y revisa las rutas que las conectan."
    >
      <template v-if="auth.esAdministrador" #acciones>
        <UiButton tamano="lg" @click="panel?.abrir(null)">
          <template #icono><UiIcon nombre="mas" :tamano="18" /></template>
          {{ etiquetaBoton }}
        </UiButton>
      </template>
    </UiPageHeader>
    <UiAlert v-if="!auth.esAdministrador" tono="info">Tu rol es de solo lectura: solo un administrador puede modificar la red.</UiAlert>
    <UiTabs v-model="pestana" :pestanas="PESTANAS" etiqueta="Tipo de elemento de la red">
      <template #panel-empresas><PanelEstaciones ref="panel" tipo="empresa" :es-admin="auth.esAdministrador" /></template>
      <template #panel-plantas><PanelEstaciones ref="panel" tipo="planta" :es-admin="auth.esAdministrador" /></template>
      <template #panel-rutas><TablaRutas ref="panel" :es-admin="auth.esAdministrador" /></template>
    </UiTabs>
  </section>
</template>
