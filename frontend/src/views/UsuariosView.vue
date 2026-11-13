<script setup lang="ts">
import { onMounted, ref } from 'vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiEmptyState from '@/components/ui/UiEmptyState.vue'
import UiField from '@/components/ui/UiField.vue'
import UiModal from '@/components/ui/UiModal.vue'
import UiPageHeader from '@/components/ui/UiPageHeader.vue'
import UiPasswordField from '@/components/ui/UiPasswordField.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiSpinner from '@/components/ui/UiSpinner.vue'
import { leerErrores, listarTodo, solicitar, textoDeError } from '@/api/util'
import { ETIQUETAS_ROL, useAuthStore } from '@/stores/auth'
import type { Rol } from '@/types/api'
import type { UsuarioGestion } from '@/types/fase2'

const auth = useAuthStore()
const usuarios = ref<UsuarioGestion[]>([])
const cargando = ref(true)
const error = ref('')
const mensaje = ref('')
const ocupado = ref<number | null>(null)

async function cargar(): Promise<void> {
  cargando.value = true
  error.value = ''
  try {
    usuarios.value = await listarTodo<UsuarioGestion>('/usuarios/')
  } catch (e) {
    error.value = textoDeError(e)
  } finally {
    cargando.value = false
  }
}
onMounted(cargar)

const fecha = (iso: string | null): string => (iso ? new Date(iso).toLocaleString('es-CO') : 'Nunca')
const ROLES = [
  { valor: 'analista', etiqueta: 'Analista' },
  { valor: 'administrador', etiqueta: 'Administrador' },
]

/* ---- Crear / editar ---- */
const abierto = ref(false)
const editando = ref<UsuarioGestion | null>(null)
const form = ref({ username: '', password: '', first_name: '', last_name: '', email: '', rol: 'analista' as Rol, activo: true })
const erroresCampo = ref<Record<string, string>>({})
const errorForm = ref('')
const guardando = ref(false)

function abrir(u: UsuarioGestion | null): void {
  editando.value = u
  erroresCampo.value = {}
  errorForm.value = ''
  form.value = u
    ? { username: u.username, password: '', first_name: u.first_name, last_name: u.last_name, email: u.email, rol: u.rol, activo: u.activo }
    : { username: '', password: '', first_name: '', last_name: '', email: '', rol: 'analista', activo: true }
  abierto.value = true
}

async function guardar(): Promise<void> {
  guardando.value = true
  erroresCampo.value = {}
  errorForm.value = ''
  const f = form.value
  try {
    if (editando.value) {
      await solicitar(`/usuarios/${editando.value.id}/`, {
        metodo: 'PATCH',
        cuerpo: { first_name: f.first_name, last_name: f.last_name, email: f.email, rol: f.rol },
      })
    } else {
      await solicitar('/usuarios/', { metodo: 'POST', cuerpo: { ...f, username: f.username.trim() } })
    }
    abierto.value = false
    mensaje.value = editando.value ? 'Usuario actualizado.' : 'Usuario creado.'
    await cargar()
  } catch (e) {
    const err = leerErrores(e)
    erroresCampo.value = err.campos
    const conocidos = ['username', 'password', 'first_name', 'last_name', 'email', 'rol']
    const extra = Object.entries(err.campos).filter(([k]) => !conocidos.includes(k)).map(([k, v]) => `${k}: ${v}`)
    errorForm.value = [err.general, ...extra].filter(Boolean).join(' · ')
  } finally {
    guardando.value = false
  }
}

/* ---- Acciones de fila ---- */
async function alternarActivo(u: UsuarioGestion): Promise<void> {
  ocupado.value = u.id
  mensaje.value = ''
  error.value = ''
  try {
    await solicitar(`/usuarios/${u.id}/${u.activo ? 'desactivar' : 'activar'}/`, { metodo: 'POST' })
    mensaje.value = u.activo ? `Usuario ${u.username} desactivado.` : `Usuario ${u.username} activado.`
    await cargar()
  } catch (e) {
    error.value = textoDeError(e)
  } finally {
    ocupado.value = null
  }
}

const temporal = ref<{ usuario: string; clave: string | null; detalle: string } | null>(null)

async function restablecer(u: UsuarioGestion): Promise<void> {
  if (!window.confirm(`¿Restablecer la contraseña de ${u.username}? Se cerrarán sus sesiones abiertas.`)) return
  ocupado.value = u.id
  mensaje.value = ''
  error.value = ''
  try {
    const r = await solicitar<{ detail: string; contrasena_temporal: string | null }>(`/usuarios/${u.id}/restablecer-contrasena/`, {
      metodo: 'POST',
      cuerpo: {},
    })
    temporal.value = { usuario: u.username, clave: r.contrasena_temporal, detalle: r.detail }
  } catch (e) {
    error.value = textoDeError(e)
  } finally {
    ocupado.value = null
  }
}
</script>

<template>
  <section class="vista">
    <UiPageHeader titulo="Usuarios" descripcion="Aquí puedes crear cuentas, cambiar roles y desactivar accesos. Nadie puede desactivarse a sí mismo y siempre debe quedar un administrador activo.">
      <template #acciones><UiButton @click="abrir(null)">Nuevo usuario</UiButton></template>
    </UiPageHeader>

    <UiAlert v-if="mensaje" tono="exito">{{ mensaje }}</UiAlert>
    <UiAlert v-if="error" tono="error" titulo="No se pudo completar la acción">{{ error }}</UiAlert>

    <p v-if="cargando" class="nota" role="status"><UiSpinner :tamano="16" /> Cargando usuarios…</p>
    <UiEmptyState v-else-if="usuarios.length === 0" icono="usuario" titulo="No hay usuarios" />
    <div v-else class="tabla-scroll">
      <table class="tabla">
        <caption class="sr-only">Usuarios</caption>
        <thead>
          <tr>
            <th scope="col">Usuario</th>
            <th scope="col">Nombre</th>
            <th scope="col">Correo</th>
            <th scope="col">Rol</th>
            <th scope="col">Estado</th>
            <th scope="col">Último acceso</th>
            <th scope="col">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in usuarios" :key="u.id" :class="{ 'fila-inactiva': !u.activo }">
            <td>{{ u.username }} <UiBadge v-if="u.id === auth.usuario?.id" tono="info">Tú</UiBadge></td>
            <td>{{ u.nombre_completo || '—' }}</td>
            <td>{{ u.email || '—' }}</td>
            <td>{{ ETIQUETAS_ROL[u.rol] }}</td>
            <td><UiBadge :tono="u.activo ? 'verde' : 'neutro'">{{ u.activo ? 'Activo' : 'Inactivo' }}</UiBadge></td>
            <td>{{ fecha(u.ultimo_acceso) }}</td>
            <td>
              <div class="fila-botones">
                <UiButton variante="secundario" tamano="sm" :disabled="ocupado === u.id" @click="abrir(u)">Editar</UiButton>
                <UiButton variante="fantasma" tamano="sm" :disabled="ocupado === u.id" @click="alternarActivo(u)">{{ u.activo ? 'Desactivar' : 'Activar' }}</UiButton>
                <UiButton variante="fantasma" tamano="sm" :disabled="ocupado === u.id" @click="restablecer(u)">Restablecer contraseña</UiButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <UiModal v-model:abierto="abierto" :titulo="editando ? `Editar ${editando.username}` : 'Nuevo usuario'" :bloquear-cierre="guardando">
      <form id="form-usuario" class="vista__seccion" novalidate @submit.prevent="guardar">
        <UiAlert v-if="errorForm" tono="error">{{ errorForm }}</UiAlert>
        <UiField id="u-username" v-model="form.username" label="Nombre de usuario *" :disabled="!!editando" autocomplete="off" :error="erroresCampo.username" />
        <UiPasswordField v-if="!editando" id="u-password" v-model="form.password" label="Contraseña inicial * (mínimo 10 caracteres)" autocomplete="new-password" :error="erroresCampo.password" />
        <UiField id="u-nombre" v-model="form.first_name" label="Nombre" :error="erroresCampo.first_name" />
        <UiField id="u-apellido" v-model="form.last_name" label="Apellidos" :error="erroresCampo.last_name" />
        <UiField id="u-email" v-model="form.email" label="Correo electrónico" type="email" :error="erroresCampo.email" />
        <UiSelect id="u-rol" v-model="form.rol" label="Rol" :opciones="ROLES" :error="erroresCampo.rol" />
      </form>
      <template #pie>
        <UiButton variante="fantasma" :disabled="guardando" @click="abierto = false">Cancelar</UiButton>
        <UiButton type="submit" form="form-usuario" :loading="guardando">Guardar</UiButton>
      </template>
    </UiModal>

    <UiModal :abierto="temporal !== null" titulo="Contraseña restablecida" @update:abierto="temporal = null">
      <div v-if="temporal" class="vista__seccion">
        <p>{{ temporal.detalle }}</p>
        <template v-if="temporal.clave">
          <p>Contraseña temporal de <strong>{{ temporal.usuario }}</strong> (se muestra una sola vez; compártela por un canal seguro):</p>
          <p class="valor-clave">{{ temporal.clave }}</p>
        </template>
      </div>
      <template #pie><UiButton @click="temporal = null">Listo, ya la copié</UiButton></template>
    </UiModal>
  </section>
</template>
