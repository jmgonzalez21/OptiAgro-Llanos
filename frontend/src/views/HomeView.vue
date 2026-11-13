<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { RouterLink, useRoute } from 'vue-router'
import MapaRed from '@/components/mapa/MapaRed.vue'
import LeyendaMapa from '@/components/mapa/LeyendaMapa.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiChip from '@/components/ui/UiChip.vue'
import UiEmptyState from '@/components/ui/UiEmptyState.vue'
import UiIcon from '@/components/ui/UiIcon.vue'
import UiIconButton from '@/components/ui/UiIconButton.vue'
import UiMarcador from '@/components/ui/UiMarcador.vue'
import UiSkeleton from '@/components/ui/UiSkeleton.vue'
import UiSpinner from '@/components/ui/UiSpinner.vue'
import {
  ETIQUETA_CANTIDAD,
  ETIQUETA_TIPO,
  formatearToneladas,
  prepararEstaciones,
} from '@/composables/useEstaciones'
import { useFullscreen } from '@/composables/useFullscreen'
import { useAuthStore } from '@/stores/auth'
import { useRedStore } from '@/stores/red'
import { solicitar, textoDeError } from '@/api/util'
import { formatearMoneda, formatearNumero } from '@/components/ui/formato'
import type { EjecucionLista } from '@/types/fase2'
import type { Pagina } from '@/types/api'

const red = useRedStore()
const route = useRoute()
const foco = computed(() => (typeof route.query.foco === 'string' ? route.query.foco : undefined))
const auth = useAuthStore()

const cargandoDemo = ref(false)
const mensajeDemo = ref('')
const errorDemo = ref('')

/** Carga los datos ficticios de demostración solo si aún no existen (administrador). */
async function cargarDemo(): Promise<void> {
  cargandoDemo.value = true
  mensajeDemo.value = ''
  errorDemo.value = ''
  try {
    const { cargado } = await solicitar<{ cargado: boolean }>('/demo/estado/')
    if (cargado) {
      mensajeDemo.value = 'Los datos de demostración ya están cargados; es posible que estén desactivados en Red logística.'
    } else {
      await solicitar('/demo/cargar/', { metodo: 'POST' })
      mensajeDemo.value = 'Datos de demostración (ficticios) cargados.'
    }
    await red.cargar()
  } catch (e) {
    errorDemo.value = textoDeError(e)
  } finally {
    cargandoDemo.value = false
  }
}
const { empresas, plantas, estado, error } = storeToRefs(red)

const panel = ref<HTMLElement | null>(null)
const mapa = ref<InstanceType<typeof MapaRed> | null>(null)
const { activo: pantallaCompleta, soportado: hayPantallaCompleta, alternar: alternarPantallaCompleta } = useFullscreen(panel)

const mostrarEmpresas = ref(true)
const mostrarPlantas = ref(true)

const estaciones = computed(() => prepararEstaciones(empresas.value, plantas.value))

const visibles = computed(() =>
  estaciones.value.ubicadas.filter((e) => (e.tipo === 'empresa' ? mostrarEmpresas.value : mostrarPlantas.value)),
)
const cuentaEmpresas = computed(() => estaciones.value.ubicadas.filter((e) => e.tipo === 'empresa').length)
const cuentaPlantas = computed(() => estaciones.value.ubicadas.filter((e) => e.tipo === 'planta').length)

const cargando = computed(() => estado.value === 'cargando')
const hayError = computed(() => estado.value === 'error')
const sinDatos = computed(() => estado.value === 'listo' && empresas.value.length + plantas.value.length === 0)
const sinFiltros = computed(() => !mostrarEmpresas.value && !mostrarPlantas.value)

function mostrarTodas(): void {
  mostrarEmpresas.value = true
  mostrarPlantas.value = true
}

function reintentar(): void {
  void red.cargar()
}

const totalOferta = computed(() => empresas.value.reduce((s, e) => s + e.oferta, 0))
const totalCapacidad = computed(() => plantas.value.reduce((s, p) => s + p.capacidad, 0))
const ultimo = ref<EjecucionLista | null>(null)

async function cargarUltimo(): Promise<void> {
  try {
    const r = await solicitar<Pagina<EjecucionLista>>('/ejecuciones/', { consulta: { page_size: 10 } })
    ultimo.value = r.results.find((x) => (x.metodo === 'exacto' || x.metodo === 'genetico') && x.objetivo !== null) ?? null
  } catch {
    ultimo.value = null
  }
}

// Siempre se recargan las estaciones al entrar: así no queda una caché vieja (altas, bajas y desactivaciones).
onMounted(() => {
  void red.cargar()
  void cargarUltimo()
})
</script>

<template>
  <section class="inicio" aria-labelledby="titulo-inicio">
    <header class="inicio__cabecera">
      <h1 id="titulo-inicio" class="inicio__titulo">Mapa de la red logística</h1>
      <p class="inicio__descripcion">
        Aquí ves de un vistazo las empresas que generan residuos y las plantas que los reciben, y puedes pasar a calcular la mejor distribución.
      </p>
    </header>

    <div class="resumen" role="list" aria-label="Resumen de la red">
      <UiCard role="listitem" relleno="sm" class="resumen__item">
        <span class="resumen__etiqueta">Empresas activas</span>
        <span class="resumen__valor">{{ formatearNumero(empresas.length) }}</span>
      </UiCard>
      <UiCard role="listitem" relleno="sm" class="resumen__item">
        <span class="resumen__etiqueta">Plantas activas</span>
        <span class="resumen__valor">{{ formatearNumero(plantas.length) }}</span>
      </UiCard>
      <UiCard role="listitem" relleno="sm" class="resumen__item">
        <span class="resumen__etiqueta">Residuos que se generan</span>
        <span class="resumen__valor">{{ formatearNumero(totalOferta, { maxDecimales: 1 }) }} <small>t/semana</small></span>
      </UiCard>
      <UiCard role="listitem" relleno="sm" class="resumen__item">
        <span class="resumen__etiqueta">Capacidad de las plantas</span>
        <span class="resumen__valor">{{ formatearNumero(totalCapacidad, { maxDecimales: 1 }) }} <small>t/semana</small></span>
      </UiCard>
      <UiCard role="listitem" relleno="sm" class="resumen__item">
        <span class="resumen__etiqueta">Último costo calculado</span>
        <span v-if="ultimo && ultimo.objetivo !== null" class="resumen__valor">{{ formatearMoneda(ultimo.objetivo) }} <small>COP/semana</small></span>
        <span v-else class="resumen__vacio">Aún no has calculado</span>
      </UiCard>
    </div>

    <div class="accesos">
      <RouterLink :to="{ name: 'optimizacion' }" class="acceso acceso--principal">Calcular la mejor distribución</RouterLink>
      <RouterLink :to="{ name: 'sensibilidad' }" class="acceso">¿Qué pasa si…?</RouterLink>
      <RouterLink v-if="auth.esAdministrador" :to="{ name: 'red' }" class="acceso">Agregar empresa</RouterLink>
    </div>

    <div ref="panel" class="panel-mapa" :class="{ 'panel-mapa--completo': pantallaCompleta }">
      <div class="panel-mapa__mapa">
        <MapaRed ref="mapa" :estaciones="visibles" :foco="foco" />
      </div>

      <UiCard variante="vidrio" relleno="sm" class="panel-mapa__filtros">
        <div class="panel-mapa__chips" role="group" aria-label="Mostrar en el mapa">
          <UiChip v-model="mostrarEmpresas">
            <template #simbolo><UiMarcador tipo="empresa" :tamano="22" /></template>
            Agroempresas <span class="panel-mapa__cuenta">({{ cuentaEmpresas }})</span>
          </UiChip>
          <UiChip v-model="mostrarPlantas">
            <template #simbolo><UiMarcador tipo="planta" :tamano="24" /></template>
            Plantas <span class="panel-mapa__cuenta">({{ cuentaPlantas }})</span>
          </UiChip>
        </div>
        <div class="panel-mapa__fila">
          <p class="panel-mapa__contador" role="status" aria-live="polite" aria-atomic="true">
            <template v-if="estado === 'listo'">
              Mostrando <strong>{{ visibles.length }}</strong> de {{ estaciones.ubicadas.length }} estaciones con ubicación
            </template>
            <UiSkeleton v-else-if="cargando" ancho="11rem" alto="0.9rem" />
          </p>
          <UiButton variante="fantasma" tamano="sm" :loading="cargando" @click="reintentar">
            <template #icono><UiIcon nombre="actualizar" :tamano="15" /></template>
            <span class="panel-mapa__actualizar">Actualizar</span>
          </UiButton>
        </div>
      </UiCard>

      <div class="panel-mapa__controles">
        <div class="grupo-vidrio">
          <UiIconButton etiqueta="Acercar" icono="mas" @click="mapa?.acercar()" />
          <UiIconButton etiqueta="Alejar" icono="menos" @click="mapa?.alejar()" />
        </div>
        <div class="grupo-vidrio">
          <UiIconButton
            etiqueta="Ver todas las estaciones"
            icono="encuadrar"
            :disabled="visibles.length === 0"
            @click="mapa?.reencuadrar()"
          />
          <UiIconButton
            v-if="hayPantallaCompleta"
            :etiqueta="pantallaCompleta ? 'Salir de pantalla completa' : 'Pantalla completa'"
            :icono="pantallaCompleta ? 'pantalla-salir' : 'pantalla'"
            :pulsado="pantallaCompleta"
            @click="alternarPantallaCompleta"
          />
        </div>
      </div>

      <UiCard variante="vidrio" relleno="sm" class="panel-mapa__leyenda">
        <LeyendaMapa :empresas="cuentaEmpresas" :plantas="cuentaPlantas" />
      </UiCard>

      <div class="panel-mapa__estado">
        <UiCard v-if="hayError" variante="elevada" relleno="lg" class="estado estado--error" role="alert">
          <UiEmptyState icono="alerta" tono="error" titulo="No se pudieron cargar las estaciones." :descripcion="error ?? ''">
            <UiButton variante="primario" @click="reintentar">
              <template #icono><UiIcon nombre="actualizar" :tamano="16" /></template>
              Reintentar
            </UiButton>
          </UiEmptyState>
        </UiCard>
        <UiCard v-else-if="cargando" variante="elevada" relleno="md" class="estado estado--cargando" role="status">
          <UiSpinner :tamano="22" />
          <span>Cargando el mapa de la red…</span>
        </UiCard>
        <UiCard v-else-if="sinDatos" variante="elevada" relleno="lg" class="estado estado--vacio" role="status">
          <UiEmptyState
            icono="mapa"
            titulo="No hay estaciones activas"
            :descripcion="auth.esAdministrador ? 'Crea empresas y plantas en Red logística o carga los datos de demostración.' : 'Pide a un administrador que cargue la red logística.'"
          >
            <template v-if="auth.esAdministrador">
              <UiButton :loading="cargandoDemo" @click="cargarDemo">Cargar datos de demostración</UiButton>
              <RouterLink :to="{ name: 'red' }">Ir a Red logística</RouterLink>
            </template>
            <p v-if="mensajeDemo" class="nota" role="status">{{ mensajeDemo }}</p>
            <p v-if="errorDemo" class="nota" role="alert">{{ errorDemo }}</p>
          </UiEmptyState>
        </UiCard>
        <UiCard v-else-if="sinFiltros" variante="elevada" relleno="lg" class="estado estado--vacio" role="status">
          <UiEmptyState icono="mapa" titulo="Ningún tipo seleccionado" descripcion="Selecciona al menos un tipo de estación para verlo en el mapa.">
            <UiButton variante="secundario" @click="mostrarTodas">Mostrar todas</UiButton>
          </UiEmptyState>
        </UiCard>
      </div>
    </div>

    <UiCard v-if="estaciones.sinUbicacion.length > 0" como="section" class="sin-ubicacion" aria-labelledby="titulo-sin-ubicacion">
      <h2 id="titulo-sin-ubicacion" class="sin-ubicacion__titulo">
        <UiIcon nombre="pin-tachado" :tamano="20" />
        Estaciones sin coordenadas ({{ estaciones.sinUbicacion.length }})
      </h2>
      <p class="sin-ubicacion__ayuda">Estas estaciones están activas pero no se pueden ubicar en el mapa.</p>
      <ul class="sin-ubicacion__lista">
        <li v-for="e in estaciones.sinUbicacion" :key="e.clave" class="sin-ubicacion__item">
          <UiMarcador :tipo="e.tipo" :tamano="26" />
          <span>
            <strong>{{ e.nombre }}</strong>
            — {{ ETIQUETA_TIPO[e.tipo] }}<template v-if="e.municipio">, {{ e.municipio }}</template>
            ({{ ETIQUETA_CANTIDAD[e.tipo].toLowerCase() }}: {{ formatearToneladas(e.cantidad) }})
          </span>
        </li>
      </ul>
    </UiCard>
  </section>
</template>

<style scoped>
.inicio {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--espacio-4);
  min-height: 0;
}

.inicio__cabecera {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.inicio__titulo {
  font-size: var(--texto-xl);
  letter-spacing: -0.025em;
}

.inicio__descripcion {
  max-width: 46rem;
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
}

.resumen {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(10.5rem, 1fr));
  gap: var(--espacio-3);
}

.resumen__item {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.resumen__etiqueta {
  font-size: var(--texto-xs);
  color: var(--color-texto-suave);
}

.resumen__valor {
  font-size: var(--texto-xl);
  font-weight: var(--peso-fuerte);
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

.resumen__valor small {
  font-size: var(--texto-xs);
  font-weight: var(--peso-medio);
  color: var(--color-texto-suave);
  letter-spacing: 0;
}

.resumen__vacio {
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
  padding-top: 0.2rem;
}

.accesos {
  display: flex;
  flex-wrap: wrap;
  gap: var(--espacio-2);
}

.acceso {
  display: inline-flex;
  align-items: center;
  min-height: var(--alto-tactil);
  padding: 0 var(--espacio-4);
  border: 1px solid var(--color-borde-control);
  border-radius: var(--radio-md);
  background: var(--color-superficie);
  color: var(--color-texto);
  font-weight: var(--peso-fuerte);
  text-decoration: none;
  transition: background var(--trans-rapida) var(--ease);
}

.acceso:hover {
  background: var(--color-superficie-2);
}

.acceso--principal {
  border-color: transparent;
  background: var(--color-primario);
  color: var(--color-sobre-primario);
}

.acceso--principal:hover {
  background: var(--color-primario-hover);
}

/* ---- Mapa en contenedor redondeado con tarjetas flotantes de vidrio ---- */
.panel-mapa {
  position: relative;
  flex: 1;
  min-height: max(30rem, 62dvh);
  overflow: hidden;
  isolation: isolate;
  border: 1px solid var(--color-borde);
  border-radius: var(--radio-xl);
  background: var(--color-superficie-2);
  box-shadow: var(--sombra-lg);
}

.panel-mapa--completo {
  min-height: 0;
  height: 100%;
  border: 0;
  border-radius: 0;
}

.panel-mapa__mapa {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.panel-mapa__filtros {
  position: absolute;
  top: var(--espacio-3);
  left: var(--espacio-3);
  right: var(--espacio-3);
  z-index: var(--z-mapa-controles);
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
  max-width: 26rem;
}

.panel-mapa__chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--espacio-2);
}

.panel-mapa__chips :deep(.ui-chip) {
  min-height: 2.25rem;
  gap: 0.35rem;
  padding: 0 0.6rem 0 0.4rem;
  font-size: 0.8125rem;
}

/* En móvil los conteos se leen en la leyenda; el chip queda compacto */
.panel-mapa__cuenta {
  display: none;
}

/* En móvil "Actualizar" queda como botón de ícono (el texto sigue disponible para lectores de pantalla) */
.panel-mapa__actualizar {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

.panel-mapa__fila {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--espacio-2);
  padding: 0 0.25rem;
}

.panel-mapa__contador {
  flex: 1 1 0;
  min-width: 0;
  min-height: 1.4rem;
  font-size: var(--texto-xs);
  font-weight: var(--peso-medio);
  color: var(--color-texto-2);
}

.panel-mapa__contador strong {
  color: var(--color-texto);
  font-weight: var(--peso-fuerte);
}

.panel-mapa__controles {
  position: absolute;
  right: var(--espacio-3);
  bottom: 2.6rem;
  z-index: var(--z-mapa-controles);
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
}

.grupo-vidrio {
  display: flex;
  flex-direction: column;
  padding: 2px;
  border: 1px solid var(--color-vidrio-borde);
  border-radius: var(--radio-md);
  background: var(--color-vidrio);
  backdrop-filter: blur(14px) saturate(1.4);
  -webkit-backdrop-filter: blur(14px) saturate(1.4);
  box-shadow:
    0 10px 24px -10px var(--color-vidrio-sombra),
    var(--sombra-xs);
}

.grupo-vidrio :deep(.ui-icono-boton) {
  width: 2.75rem;
  height: 2.75rem;
}

.grupo-vidrio :deep(.ui-icono-boton:not(:first-child)) {
  border-top: 1px solid var(--color-borde);
  border-top-left-radius: 0;
  border-top-right-radius: 0;
}

.grupo-vidrio :deep(.ui-icono-boton:not(:last-child)) {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.panel-mapa__leyenda {
  position: absolute;
  left: var(--espacio-3);
  bottom: 2.6rem;
  z-index: var(--z-mapa-controles);
  min-width: 14rem;
}

.panel-mapa__estado {
  position: absolute;
  inset: 0;
  z-index: calc(var(--z-mapa-controles) + 1);
  display: grid;
  place-items: center;
  padding: var(--espacio-4);
  pointer-events: none;
}

.estado {
  max-width: 28rem;
  pointer-events: auto;
  animation: ui-aparecer var(--trans-lenta) both;
}

.estado--cargando {
  display: flex;
  align-items: center;
  gap: var(--espacio-3);
  color: var(--color-texto-2);
  font-weight: var(--peso-medio);
}

.estado--cargando :deep(.ui-spinner) {
  color: var(--color-primario);
}

/* ---- Estaciones sin coordenadas ---- */
.sin-ubicacion__titulo {
  display: flex;
  align-items: center;
  gap: var(--espacio-2);
  font-size: var(--texto-base);
  color: var(--color-aviso);
}

.sin-ubicacion__ayuda {
  margin: var(--espacio-1) 0 var(--espacio-3);
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
}

.sin-ubicacion__lista {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
}

.sin-ubicacion__item {
  display: flex;
  align-items: center;
  gap: var(--espacio-3);
  font-size: var(--texto-sm);
}

@media (min-width: 48rem) {
  .inicio__titulo {
    font-size: var(--texto-2xl);
  }

  .panel-mapa__filtros {
    right: auto;
    width: 26rem;
  }

  .panel-mapa__chips :deep(.ui-chip) {
    min-height: 2.5rem;
    gap: 0.5rem;
    padding: 0 0.85rem 0 0.6rem;
    font-size: var(--texto-sm);
  }

  .panel-mapa__cuenta {
    display: inline;
  }

  .panel-mapa__actualizar {
    position: static;
    width: auto;
    height: auto;
    overflow: visible;
    clip-path: none;
  }

  .panel-mapa__controles {
    top: var(--espacio-3);
    bottom: auto;
  }

  .panel-mapa__leyenda {
    bottom: var(--espacio-3);
  }
}
</style>
