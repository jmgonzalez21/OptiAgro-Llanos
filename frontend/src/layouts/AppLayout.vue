<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import MenuPerfil from '@/components/MenuPerfil.vue'
import UiIcon from '@/components/ui/UiIcon.vue'
import UiIconButton from '@/components/ui/UiIconButton.vue'
import UiLogo from '@/components/ui/UiLogo.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import type { NombreIcono } from '@/components/ui/icons'
import { useAuthStore } from '@/stores/auth'
import { useRedStore } from '@/stores/red'

const auth = useAuthStore()
const red = useRedStore()
const router = useRouter()
const route = useRoute()

interface SeccionMenu {
  nombre: string
  icono: NombreIcono
  ruta: string
  soloAdmin?: boolean
}

const SECCIONES: SeccionMenu[] = [
  { nombre: 'Red logística', icono: 'red', ruta: 'red' },
  { nombre: 'Matriz de costos', icono: 'ordenar', ruta: 'matriz-costos' },
  { nombre: 'Optimización', icono: 'optimizacion', ruta: 'optimizacion' },
  { nombre: '¿Qué pasa si…?', icono: 'sensibilidad', ruta: 'sensibilidad' },
  { nombre: 'Reporte comparativo', icono: 'reportes', ruta: 'reporte' },
  { nombre: 'Historial', icono: 'lista', ruta: 'historial' },
  { nombre: 'Usuarios', icono: 'candado', ruta: 'usuarios', soloAdmin: true },
  { nombre: 'Mi perfil', icono: 'usuario', ruta: 'perfil' },
]

const secciones = computed(() => SECCIONES.filter((x) => !x.soloAdmin || auth.esAdministrador))

const CLAVE_LATERAL = 'optiagro.lateral-colapsado'
const CONSULTA_COMPACTO = '(max-width: 1023.98px)'
const CONSULTA_ANCHO = '(min-width: 1280px)'

const principal = ref<HTMLElement | null>(null)
const lateral = ref<HTMLElement | null>(null)
const botonMenu = ref<InstanceType<typeof UiIconButton> | null>(null)

/** < 1024 px: el panel lateral pasa a ser un drawer. */
const esCompacto = ref(false)
const anchoGrande = ref(true)
const drawerAbierto = ref(false)

function leerPreferencia(): boolean | null {
  try {
    const valor = localStorage.getItem(CLAVE_LATERAL)
    return valor === null ? null : valor === '1'
  } catch {
    return null
  }
}

function guardarPreferencia(valor: boolean): void {
  try {
    localStorage.setItem(CLAVE_LATERAL, valor ? '1' : '0')
  } catch {
    /* almacenamiento no disponible: la preferencia solo dura la sesión de la página */
  }
}

const preferenciaColapsado = ref<boolean | null>(leerPreferencia())
/** Por defecto: expandido en >= 1280 px y colapsado entre 1024 y 1279 px; la preferencia manda. */
const colapsado = computed(() => !esCompacto.value && (preferenciaColapsado.value ?? !anchoGrande.value))

const titulo = computed(() => route.meta.titulo ?? 'Inicio')
const contexto = computed(() => (route.name === 'inicio' ? 'Red logística del Meta' : ''))

function alternarColapso(): void {
  preferenciaColapsado.value = !colapsado.value
  guardarPreferencia(preferenciaColapsado.value)
}

/* ---- Drawer (móvil/tableta) ---- */
function elementosEnfocables(): HTMLElement[] {
  const raiz = lateral.value
  if (!raiz) return []
  return Array.from(raiz.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), [tabindex="0"]'))
}

function bloquearScroll(bloquear: boolean): void {
  document.body.style.overflow = bloquear ? 'hidden' : ''
}

async function abrirDrawer(): Promise<void> {
  drawerAbierto.value = true
  bloquearScroll(true)
  await nextTick()
  elementosEnfocables()[0]?.focus()
}

function cerrarDrawer(devolverFoco = true): void {
  if (!drawerAbierto.value) return
  drawerAbierto.value = false
  bloquearScroll(false)
  if (devolverFoco) void nextTick(() => (botonMenu.value?.$el as HTMLElement | undefined)?.focus())
}

function teclaLateral(e: KeyboardEvent): void {
  if (!esCompacto.value || !drawerAbierto.value) return
  if (e.key === 'Escape') {
    e.preventDefault()
    cerrarDrawer()
    return
  }
  if (e.key !== 'Tab') return
  // Foco atrapado dentro del drawer.
  const lista = elementosEnfocables()
  const primero = lista[0]
  const ultimo = lista[lista.length - 1]
  if (!primero || !ultimo) return
  if (e.shiftKey && document.activeElement === primero) {
    e.preventDefault()
    ultimo.focus()
  } else if (!e.shiftKey && document.activeElement === ultimo) {
    e.preventDefault()
    primero.focus()
  }
}

// Gestión del foco: al cambiar de vista, el foco pasa al contenido principal y el drawer se cierra.
watch(
  () => route.fullPath,
  async (_nueva, anterior) => {
    if (anterior === undefined) return
    cerrarDrawer(false)
    await nextTick()
    principal.value?.focus()
  },
)

let consultaCompacto: MediaQueryList | null = null
let consultaAncho: MediaQueryList | null = null

function sincronizarAncho(): void {
  esCompacto.value = consultaCompacto?.matches ?? false
  anchoGrande.value = consultaAncho?.matches ?? true
  if (!esCompacto.value && drawerAbierto.value) cerrarDrawer(false)
}

onMounted(() => {
  if (red.estado === 'inactivo') void red.cargar()
  if (typeof window.matchMedia !== 'function') return
  consultaCompacto = window.matchMedia(CONSULTA_COMPACTO)
  consultaAncho = window.matchMedia(CONSULTA_ANCHO)
  consultaCompacto.addEventListener('change', sincronizarAncho)
  consultaAncho.addEventListener('change', sincronizarAncho)
  sincronizarAncho()
})

onBeforeUnmount(() => {
  consultaCompacto?.removeEventListener('change', sincronizarAncho)
  consultaAncho?.removeEventListener('change', sincronizarAncho)
  bloquearScroll(false)
})

async function cerrarSesion(): Promise<void> {
  auth.logout()
  red.reiniciar()
  await router.replace({ name: 'login' })
}
</script>

<template>
  <div class="app-layout" :class="{ 'app-layout--colapsado': colapsado }">
    <a class="app-layout__saltar" href="#contenido-principal" @click.prevent="principal?.focus()">
      Saltar al contenido principal
    </a>

    <div v-if="esCompacto" class="app-layout__velo" :class="{ 'app-layout__velo--visible': drawerAbierto }" aria-hidden="true" @click="cerrarDrawer()"></div>

    <aside
      id="panel-lateral"
      ref="lateral"
      class="lateral"
      :class="{ 'lateral--colapsado': colapsado, 'lateral--drawer': esCompacto, 'lateral--abierto': drawerAbierto }"
      :role="esCompacto ? 'dialog' : undefined"
      :aria-modal="esCompacto && drawerAbierto ? 'true' : undefined"
      :aria-label="esCompacto ? 'Menú principal' : undefined"
      :inert="esCompacto && !drawerAbierto ? true : undefined"
      @keydown="teclaLateral"
    >
      <div class="lateral__cabecera">
        <UiLogo :solo-isotipo="colapsado" :tamano="40" />
        <UiIconButton v-if="esCompacto" etiqueta="Cerrar menú" icono="cerrar" class="lateral__cerrar" @click="cerrarDrawer()" />
      </div>

      <nav class="lateral__nav" aria-label="Navegación principal">
        <ul class="nav-lista">
          <li>
            <RouterLink
              :to="{ name: 'inicio' }"
              class="nav-item"
              active-class="nav-item--activo"
              exact-active-class="nav-item--activo"
              :data-tip="colapsado ? 'Inicio' : undefined"
            >
              <UiIcon nombre="inicio" :tamano="21" class="nav-item__icono" />
              <span class="nav-item__texto" :class="{ 'sr-only': colapsado }">Inicio</span>
            </RouterLink>
          </li>
          <li v-for="seccion in secciones" :key="seccion.ruta">
            <RouterLink
              :to="{ name: seccion.ruta }"
              class="nav-item"
              active-class="nav-item--activo"
              :data-tip="colapsado ? seccion.nombre : undefined"
            >
              <UiIcon :nombre="seccion.icono" :tamano="21" class="nav-item__icono" />
              <span class="nav-item__texto" :class="{ 'sr-only': colapsado }">{{ seccion.nombre }}</span>
            </RouterLink>
          </li>
        </ul>
      </nav>

      <div class="lateral__pie">
        <button
          v-if="!esCompacto"
          type="button"
          class="lateral__colapsar"
          :aria-expanded="!colapsado"
          aria-controls="panel-lateral"
          :data-tip="colapsado ? 'Expandir menú' : undefined"
          @click="alternarColapso"
        >
          <UiIcon :nombre="colapsado ? 'expandir-menu' : 'contraer-menu'" :tamano="20" />
          <span :class="{ 'sr-only': colapsado }">{{ colapsado ? 'Expandir menú' : 'Contraer menú' }}</span>
        </button>
        <p v-if="!colapsado" class="lateral__version">
          <span>EcoResiduos del Llano S.A.S.</span>
          <span>v0.1<template v-if="red.hayFicticios"> · Datos de demostración</template></span>
        </p>
      </div>
    </aside>

    <div class="app-layout__columna">
      <header class="barra" role="banner">
        <UiIconButton
          v-if="esCompacto"
          ref="botonMenu"
          etiqueta="Abrir menú"
          icono="menu"
          aria-controls="panel-lateral"
          :aria-expanded="drawerAbierto"
          aria-haspopup="dialog"
          @click="abrirDrawer"
        />
        <div class="barra__titulos">
          <p class="barra__titulo">{{ titulo }}</p>
          <p v-if="contexto" class="barra__contexto">{{ contexto }}</p>
        </div>
        <UiBadge v-if="red.hayFicticios" tono="ambar" punto class="barra__demo">Datos de demostración</UiBadge>
        <MenuPerfil :nombre="auth.nombre" :rol="auth.etiquetaRol" @cerrar-sesion="cerrarSesion" />
      </header>

      <main id="contenido-principal" ref="principal" class="app-layout__contenido" tabindex="-1">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--color-fondo-degradado), var(--color-fondo);
}

.app-layout__saltar {
  position: absolute;
  left: -999px;
  top: 0.5rem;
  z-index: var(--z-saltar);
  padding: 0.6rem 1rem;
  border-radius: var(--radio-md);
  background: var(--color-primario);
  color: var(--color-sobre-primario);
  font-weight: var(--peso-fuerte);
  text-decoration: none;
}

.app-layout__saltar:focus {
  left: 0.75rem;
}

.app-layout__columna {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.app-layout__contenido {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  padding: var(--espacio-4);
}

.app-layout__contenido:focus {
  outline: none;
}

/* ---- Panel lateral ---- */
.lateral {
  position: sticky;
  top: 0;
  z-index: var(--z-barra);
  display: flex;
  flex: 0 0 var(--ancho-lateral);
  flex-direction: column;
  width: var(--ancho-lateral);
  height: 100vh;
  height: 100dvh;
  padding: var(--espacio-4) var(--espacio-3);
  border-right: 1px solid var(--color-borde);
  background: var(--color-superficie);
  transition:
    width var(--trans-lenta),
    flex-basis var(--trans-lenta);
}

.lateral--colapsado {
  flex-basis: var(--ancho-lateral-colapsado);
  width: var(--ancho-lateral-colapsado);
  padding-inline: 0.75rem;
}

.lateral__cabecera {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 3.5rem;
  padding: 0 0.4rem;
  margin-bottom: var(--espacio-4);
}

.lateral--colapsado .lateral__cabecera {
  justify-content: center;
  padding: 0;
}

.lateral__nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.lateral--colapsado .lateral__nav {
  overflow: visible;
}

.nav-lista {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--espacio-3);
  min-height: 2.85rem;
  padding: 0 var(--espacio-3);
  border-radius: var(--radio-md);
  color: var(--color-texto-2);
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  text-decoration: none;
  transition:
    background var(--trans),
    color var(--trans);
}

.nav-item:hover:not(.nav-item--deshabilitado) {
  background: var(--color-superficie-2);
  color: var(--color-texto);
}

.nav-item--activo {
  background: var(--color-activo-fondo);
  color: var(--color-activo-texto);
  font-weight: var(--peso-fuerte);
}

.nav-item--activo::before {
  content: '';
  position: absolute;
  left: 0;
  top: 22%;
  bottom: 22%;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--color-activo-barra);
}

.nav-item--deshabilitado {
  cursor: not-allowed;
  color: var(--color-texto-suave);
}

.nav-item--deshabilitado:focus-visible {
  background: var(--color-superficie-2);
}

.nav-item__texto {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
}

.nav-item__texto--doble {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}

.nav-item__sub {
  font-size: var(--texto-xs);
  font-weight: var(--peso-medio);
  color: var(--color-texto-suave);
}

.lateral--colapsado .nav-item {
  justify-content: center;
  padding: 0;
}

/* Tooltip del panel colapsado (el nombre accesible ya está en el texto .sr-only) */
.lateral--colapsado [data-tip]::after {
  content: attr(data-tip) / '';
  position: absolute;
  left: calc(100% + 0.75rem);
  top: 50%;
  z-index: 10;
  padding: 0.35rem 0.7rem;
  border-radius: var(--radio-sm);
  background: var(--color-texto);
  color: var(--color-texto-inverso);
  font-size: var(--texto-xs);
  font-weight: var(--peso-medio);
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transform: translate(-4px, -50%);
  transition:
    opacity var(--trans-rapida),
    transform var(--trans-rapida);
}

.lateral--colapsado [data-tip]:hover::after,
.lateral--colapsado [data-tip]:focus-visible::after {
  opacity: 1;
  transform: translate(0, -50%);
}

.lateral__pie {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-3);
  margin-top: var(--espacio-3);
  padding-top: var(--espacio-3);
  border-top: 1px solid var(--color-borde);
}

.lateral__colapsar {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--espacio-3);
  min-height: 2.5rem;
  padding: 0 var(--espacio-3);
  border: 0;
  border-radius: var(--radio-md);
  background: transparent;
  color: var(--color-texto-2);
  font-size: var(--texto-sm);
  font-weight: var(--peso-medio);
  transition: background var(--trans);
}

.lateral__colapsar:hover {
  background: var(--color-superficie-2);
  color: var(--color-texto);
}

.lateral--colapsado .lateral__colapsar {
  justify-content: center;
  padding: 0;
}

.lateral__version {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0 var(--espacio-3);
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
}

.lateral__version span:first-child {
  font-weight: var(--peso-fuerte);
  color: var(--color-texto-2);
}

/* ---- Drawer (< 1024 px) ---- */
.lateral--drawer {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: var(--z-drawer);
  flex: none;
  width: min(85vw, 20rem);
  padding: var(--espacio-4) var(--espacio-3);
  border-right: 0;
  border-radius: 0 var(--radio-xl) var(--radio-xl) 0;
  box-shadow: var(--sombra-lg);
  visibility: hidden;
  transform: translateX(-100%);
  transition:
    transform var(--trans-lenta),
    visibility 0s linear var(--trans-lenta);
}

.lateral--drawer.lateral--abierto {
  visibility: visible;
  transform: translateX(0);
  transition:
    transform var(--trans-lenta),
    visibility 0s;
}

.app-layout__velo {
  position: fixed;
  inset: 0;
  z-index: var(--z-drawer-velo);
  background: var(--color-velo);
  backdrop-filter: blur(2px);
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--trans-lenta);
}

.app-layout__velo--visible {
  opacity: 1;
  pointer-events: auto;
}

/* ---- Barra superior translúcida ---- */
.barra {
  position: sticky;
  top: 0;
  z-index: var(--z-barra);
  display: flex;
  align-items: center;
  gap: var(--espacio-2);
  min-height: var(--alto-barra);
  padding: 0.5rem var(--espacio-3);
  border-bottom: 1px solid var(--color-borde);
  background: color-mix(in srgb, var(--color-superficie) 78%, transparent);
  backdrop-filter: blur(14px) saturate(1.5);
  -webkit-backdrop-filter: blur(14px) saturate(1.5);
}

.barra__demo {
  margin-left: auto;
}

.barra__titulos {
  display: flex;
  flex: 1 0 auto;
  flex-direction: column;
  min-width: 0;
  line-height: 1.2;
}

.barra__titulo {
  white-space: nowrap;
  font-size: var(--texto-lg);
  font-weight: var(--peso-fuerte);
  letter-spacing: -0.01em;
  color: var(--color-texto);
}

.barra__contexto {
  display: none;
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
  white-space: nowrap;
}

@media (min-width: 40rem) {
  .barra {
    gap: var(--espacio-3);
    padding-inline: var(--espacio-4);
  }

  .barra__contexto {
    display: block;
  }
}

@media (min-width: 48rem) {
  .barra {
    padding-inline: var(--espacio-5);
  }

  .app-layout__contenido {
    padding: var(--espacio-5);
  }
}

@media (min-width: 80rem) {
  .app-layout__contenido {
    padding: var(--espacio-5) var(--espacio-6) var(--espacio-6);
  }
}
</style>
