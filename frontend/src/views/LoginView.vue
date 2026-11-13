<script setup lang="ts">
import { computed, nextTick, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { mensajeDeError } from '@/api/errores'
import { USAR_MOCK } from '@/config'
import { redireccionSegura } from '@/router/guards'
import { useAuthStore } from '@/stores/auth'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiField from '@/components/ui/UiField.vue'
import UiIcon from '@/components/ui/UiIcon.vue'
import UiLogo from '@/components/ui/UiLogo.vue'
import UiPasswordField from '@/components/ui/UiPasswordField.vue'
import UiPatronAgro from '@/components/ui/UiPatronAgro.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const formulario = reactive({ username: '', password: '' })
const tocado = reactive({ username: false, password: false })
const intentado = ref(false)
const ayudaContrasena = ref(false)
const errorGeneral = ref('')

const campoUsuario = ref<InstanceType<typeof UiField> | null>(null)
const campoContrasena = ref<InstanceType<typeof UiPasswordField> | null>(null)
const alertaError = ref<InstanceType<typeof UiAlert> | null>(null)

const sesionExpirada = computed(() => route.query.motivo === 'expirada')

const errores = computed(() => ({
  username: formulario.username.trim() ? '' : 'Escribe tu nombre de usuario.',
  password: formulario.password ? '' : 'Escribe tu contraseña.',
}))

function mostrarError(campo: 'username' | 'password'): string {
  return tocado[campo] || intentado.value ? errores.value[campo] : ''
}

const errorUsuario = computed(() => mostrarError('username'))
const errorContrasena = computed(() => mostrarError('password'))

async function enviar(): Promise<void> {
  if (auth.cargando) return
  intentado.value = true
  errorGeneral.value = ''

  if (errores.value.username) {
    campoUsuario.value?.focus()
    return
  }
  if (errores.value.password) {
    campoContrasena.value?.focus()
    return
  }

  try {
    await auth.login({ username: formulario.username, password: formulario.password })
    await router.replace(redireccionSegura(route.query.redirect))
  } catch (e) {
    errorGeneral.value = mensajeDeError(e)
    formulario.password = ''
    tocado.password = false
    intentado.value = false
    await nextTick()
    alertaError.value?.focus()
  }
}
</script>

<template>
  <div class="login">
    <div class="login__marca">
      <div class="login__marca-contenido">
        <UiLogo :tamano="44" />

        <div class="login__mensaje">
          <p class="login__titular">Menos residuos, <span>mejores rutas.</span></p>
          <p class="login__bajada">
            Planifica el transporte de residuos agropecuarios del Meta con costos mínimos y decisiones respaldadas por datos.
          </p>
          <ul class="login__valores">
            <li>
              <span class="login__valor-icono"><UiIcon nombre="red" :tamano="18" /></span>
              Red logística clara: de la finca a la planta.
            </li>
            <li>
              <span class="login__valor-icono"><UiIcon nombre="escenarios" :tamano="18" /></span>
              Escenarios que muestran el costo antes de decidir.
            </li>
            <li>
              <span class="login__valor-icono"><UiIcon nombre="grafica" :tamano="18" /></span>
              Resultados comparables y listos para reportar.
            </li>
          </ul>
        </div>

        <p class="login__marca-pie">EcoResiduos del Llano S.A.S. · Meta, Colombia</p>
      </div>
      <div class="login__patron"><UiPatronAgro /></div>
    </div>

    <main class="login__panel" aria-labelledby="titulo-login">
      <div class="login__tarjeta">
        <UiBadge v-if="USAR_MOCK" tono="ambar" punto class="login__demo">Datos de demostración</UiBadge>

        <h1 id="titulo-login" class="login__titulo">Bienvenido</h1>
        <p class="login__subtitulo">Ingresa con tu cuenta para continuar.</p>

        <UiAlert v-if="sesionExpirada && !errorGeneral" tono="info" class="login__aviso">
          Tu sesión expiró. Inicia sesión de nuevo para continuar.
        </UiAlert>

        <form class="login__formulario" novalidate :aria-busy="auth.cargando" @submit.prevent="enviar">
          <UiAlert v-if="errorGeneral" ref="alertaError" tono="error">{{ errorGeneral }}</UiAlert>

          <UiField
            id="login-usuario"
            ref="campoUsuario"
            v-model="formulario.username"
            label="Usuario"
            icono="usuario"
            type="text"
            name="username"
            autocomplete="username"
            autocapitalize="none"
            spellcheck="false"
            required
            :error="errorUsuario"
            :disabled="auth.cargando"
            @blur="tocado.username = true"
          />

          <UiPasswordField
            id="login-contrasena"
            ref="campoContrasena"
            v-model="formulario.password"
            label="Contraseña"
            name="password"
            autocomplete="current-password"
            required
            :error="errorContrasena"
            :disabled="auth.cargando"
            @blur="tocado.password = true"
          />

          <UiButton type="submit" tamano="lg" bloque :loading="auth.cargando">
            {{ auth.cargando ? 'Ingresando…' : 'Iniciar sesión' }}
          </UiButton>
        </form>

        <div class="login__ayuda">
          <p>
            ¿Olvidaste tu contraseña?
            <button type="button" class="login__enlace" :aria-expanded="ayudaContrasena" aria-controls="login-ayuda-nota" @click="ayudaContrasena = !ayudaContrasena">
              Contacta al administrador.
            </button>
          </p>
          <p v-show="ayudaContrasena" id="login-ayuda-nota" class="login__nota">
            Pide al administrador del sistema que restablezca tu contraseña.
          </p>
        </div>

        <p v-if="USAR_MOCK" class="login__nota-demo">
          Modo demostración (sin servidor): ingresa cualquier usuario y contraseña no vacíos.
          El usuario «admin» entra como administrador; los demás, como analistas.
        </p>
      </div>

      <p class="login__pie">© 2026 OptiAgro-Llanos · Universidad de los Llanos</p>
    </main>
  </div>
</template>

<style scoped>
.login {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: auto 1fr;
  min-height: 100vh;
  background: var(--color-superficie);
}

/* ---- Panel de marca ---- */
.login__marca {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  background:
    radial-gradient(60rem 36rem at 85% -10%, var(--color-brillo), transparent 60%),
    linear-gradient(160deg, var(--color-acento) 0%, var(--color-acento-suave) 48%, var(--color-fondo) 100%);
  border-bottom: 1px solid var(--color-borde);
}

.login__marca-contenido {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: var(--espacio-5);
  padding: var(--espacio-4) var(--espacio-5);
}

.login__mensaje {
  display: none;
}

.login__marca-pie {
  display: none;
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  color: var(--color-activo-texto);
}

.login__patron {
  display: none;
}

.login__titular {
  font-size: var(--texto-xl);
  font-weight: var(--peso-fuerte);
  line-height: 1.12;
  letter-spacing: -0.03em;
  color: var(--color-texto);
}

.login__titular span {
  color: var(--color-primario);
}

.login__bajada {
  max-width: 30rem;
  margin-top: var(--espacio-3);
  color: var(--color-texto-2);
}

.login__valores {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-3);
  margin-top: var(--espacio-5);
  font-weight: var(--peso-medio);
  color: var(--color-texto);
}

.login__valores li {
  display: flex;
  align-items: center;
  gap: var(--espacio-3);
}

.login__valor-icono {
  display: grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  flex-shrink: 0;
  border-radius: 12px;
  background: var(--color-superficie);
  color: var(--color-primario);
  box-shadow: var(--sombra-sm);
}

/* ---- Panel del formulario ---- */
.login__panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--espacio-5);
  padding: var(--espacio-6) var(--espacio-4) var(--espacio-5);
}

.login__tarjeta {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 25rem;
  animation: ui-aparecer 480ms var(--ease) both;
}

.login__demo {
  align-self: flex-start;
  margin-bottom: var(--espacio-4);
}

.login__titulo {
  font-size: var(--texto-2xl);
  letter-spacing: -0.03em;
}

.login__subtitulo {
  margin-top: var(--espacio-1);
  color: var(--color-texto-2);
}

.login__aviso {
  margin-top: var(--espacio-4);
}

.login__formulario {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-4);
  margin-top: var(--espacio-5);
}

.login__formulario > :last-child {
  margin-top: var(--espacio-2);
}

.login__ayuda {
  margin-top: var(--espacio-5);
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
  text-align: center;
}

.login__enlace {
  padding: 0;
  border: 0;
  background: none;
  color: var(--color-enlace);
  font-weight: var(--peso-fuerte);
  text-decoration: underline;
  text-decoration-color: var(--color-acento-fuerte);
  text-underline-offset: 3px;
  transition: text-decoration-color var(--trans-rapida);
}

.login__enlace:hover {
  text-decoration-color: currentColor;
}

.login__nota {
  margin-top: var(--espacio-2);
  padding: var(--espacio-3);
  border-radius: var(--radio-md);
  background: var(--color-acento-suave);
  color: var(--color-activo-texto);
  animation: ui-aparecer var(--trans) both;
}

.login__nota-demo {
  margin-top: var(--espacio-5);
  padding-top: var(--espacio-4);
  border-top: 1px dashed var(--color-borde-fuerte);
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
  text-align: center;
}

.login__pie {
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
  text-align: center;
}

/* ---- Tableta: franja superior con logo y titular ---- */
@media (min-width: 600px) {
  .login__marca-contenido {
    padding: var(--espacio-5) var(--espacio-6);
  }

  .login__mensaje {
    display: block;
  }

  .login__bajada,
  .login__valores {
    display: none;
  }

  .login__titular {
    font-size: var(--texto-2xl);
  }
}

/* ---- Escritorio: pantalla dividida ---- */
@media (min-width: 1024px) {
  .login {
    grid-template-columns: 45fr 55fr;
    grid-template-rows: 1fr;
  }

  .login__marca {
    border-bottom: 0;
    border-right: 1px solid var(--color-borde);
  }

  .login__marca-contenido {
    justify-content: space-between;
    min-height: 100vh;
    padding: var(--espacio-7) var(--espacio-7) var(--espacio-6);
  }

  .login__bajada {
    display: block;
  }

  .login__valores {
    display: flex;
  }

  .login__titular {
    font-size: var(--texto-3xl);
  }

  .login__marca-pie {
    display: block;
  }

  .login__patron {
    position: absolute;
    right: -4%;
    bottom: -3%;
    z-index: 0;
    display: block;
    width: 94%;
    max-width: 44rem;
    aspect-ratio: 600 / 520;
    pointer-events: none;
    -webkit-mask-image: linear-gradient(to bottom, transparent 0%, #000 42%);
    mask-image: linear-gradient(to bottom, transparent 0%, #000 42%);
  }

  .login__panel {
    min-height: 100vh;
  }
}

@media (min-width: 1280px) {
  .login {
    grid-template-columns: 1fr 1fr;
  }
}

@media (min-width: 1024px) and (max-height: 700px) {
  .login__patron {
    display: none;
  }
}
</style>

