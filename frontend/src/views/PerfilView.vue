<script setup lang="ts">
import { ref } from 'vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiField from '@/components/ui/UiField.vue'
import UiPageHeader from '@/components/ui/UiPageHeader.vue'
import UiPasswordField from '@/components/ui/UiPasswordField.vue'
import { leerErrores } from '@/api/util'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const perfil = ref({
  first_name: auth.usuario?.first_name ?? '',
  last_name: auth.usuario?.last_name ?? '',
  email: auth.usuario?.email ?? '',
})
const erroresPerfil = ref<Record<string, string>>({})
const errorPerfil = ref('')
const okPerfil = ref('')
const guardandoPerfil = ref(false)

async function guardarPerfil(): Promise<void> {
  guardandoPerfil.value = true
  erroresPerfil.value = {}
  errorPerfil.value = ''
  okPerfil.value = ''
  try {
    await auth.actualizarPerfil({ ...perfil.value })
    okPerfil.value = 'Datos actualizados.'
  } catch (e) {
    const err = leerErrores(e)
    erroresPerfil.value = err.campos
    errorPerfil.value = err.general
  } finally {
    guardandoPerfil.value = false
  }
}

const clave = ref({ actual: '', nueva: '', confirmar: '' })
const erroresClave = ref<Record<string, string>>({})
const errorClave = ref('')
const okClave = ref('')
const guardandoClave = ref(false)

async function cambiarClave(): Promise<void> {
  erroresClave.value = {}
  errorClave.value = ''
  okClave.value = ''
  if (clave.value.nueva.length < 10) {
    erroresClave.value = { contrasena_nueva: 'La contraseña nueva debe tener al menos 10 caracteres.' }
    return
  }
  if (clave.value.nueva !== clave.value.confirmar) {
    erroresClave.value = { confirmar: 'Las contraseñas no coinciden.' }
    return
  }
  guardandoClave.value = true
  try {
    await auth.cambiarContrasena(clave.value.actual, clave.value.nueva)
    okClave.value = 'Contraseña actualizada. Las demás sesiones abiertas se cerraron.'
    clave.value = { actual: '', nueva: '', confirmar: '' }
  } catch (e) {
    const err = leerErrores(e)
    erroresClave.value = err.campos
    errorClave.value = err.general
  } finally {
    guardandoClave.value = false
  }
}
</script>

<template>
  <section class="vista">
    <UiPageHeader titulo="Mi perfil" descripcion="Aquí puedes revisar tus datos y cambiar tu contraseña.">
      <template #meta>
        <UiBadge tono="verde">{{ auth.etiquetaRol }}</UiBadge>
        <span class="nota">Usuario: {{ auth.usuario?.username }}</span>
      </template>
    </UiPageHeader>

    <UiCard>
      <form class="vista__seccion" novalidate @submit.prevent="guardarPerfil">
        <h2>Mis datos</h2>
        <UiAlert v-if="okPerfil" tono="exito">{{ okPerfil }}</UiAlert>
        <UiAlert v-if="errorPerfil" tono="error">{{ errorPerfil }}</UiAlert>
        <div class="formulario-grid">
          <UiField id="p-nombre" v-model="perfil.first_name" label="Nombre" :error="erroresPerfil.first_name" />
          <UiField id="p-apellido" v-model="perfil.last_name" label="Apellidos" :error="erroresPerfil.last_name" />
          <UiField id="p-email" v-model="perfil.email" label="Correo electrónico" type="email" :error="erroresPerfil.email" />
        </div>
        <div><UiButton type="submit" :loading="guardandoPerfil">Guardar datos</UiButton></div>
      </form>
    </UiCard>

    <UiCard>
      <form class="vista__seccion" novalidate @submit.prevent="cambiarClave">
        <h2>Cambiar contraseña</h2>
        <UiAlert v-if="okClave" tono="exito">{{ okClave }}</UiAlert>
        <UiAlert v-if="errorClave" tono="error">{{ errorClave }}</UiAlert>
        <div class="formulario-grid">
          <UiPasswordField id="p-actual" v-model="clave.actual" label="Contraseña actual" autocomplete="current-password" :error="erroresClave.contrasena_actual" />
          <UiPasswordField id="p-nueva" v-model="clave.nueva" label="Contraseña nueva" autocomplete="new-password" hint="Mínimo 10 caracteres" :error="erroresClave.contrasena_nueva" />
          <UiPasswordField id="p-confirmar" v-model="clave.confirmar" label="Confirmar contraseña nueva" autocomplete="new-password" :error="erroresClave.confirmar" />
        </div>
        <div><UiButton type="submit" :loading="guardandoClave">Cambiar contraseña</UiButton></div>
      </form>
    </UiCard>
  </section>
</template>
