<script setup lang="ts">
/**
 * Medidor de contraseña (4 segmentos + texto de nivel + requisitos con ✓/✕ en texto). Mínimo 10 caracteres.
 * Guía, no autoridad: el servidor decide. El nivel se anuncia por `aria-live="polite"` con retardo de 600 ms
 * para no saturar al lector de pantalla. Úsalo bajo `UiPasswordField`: `<UiPasswordStrength :valor="clave" :usuario="u" :correo="c" />`.
 */
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import UiIcon from './UiIcon.vue'
import { evaluarClave } from './claves'

const props = withDefaults(
  defineProps<{
    valor: string
    usuario?: string
    correo?: string
    minimo?: number
    /** Retardo (ms) antes de anunciar el nivel. */
    retardo?: number
  }>(),
  { usuario: '', correo: '', minimo: 10, retardo: 600 },
)

const evaluacion = computed(() => evaluarClave(props.valor, { usuario: props.usuario, correo: props.correo, minimo: props.minimo }))

const anuncio = ref('')
let temporizador: ReturnType<typeof setTimeout> | null = null
watch(
  () => evaluacion.value.etiqueta + evaluacion.value.requisitos.map((r) => (r.cumple ? 1 : 0)).join(''),
  () => {
    if (temporizador) clearTimeout(temporizador)
    temporizador = setTimeout(() => {
      const e = evaluacion.value
      anuncio.value = e.nivel === null ? '' : `Seguridad de la contraseña: ${e.etiqueta}.`
    }, props.retardo)
  },
)
onBeforeUnmount(() => {
  if (temporizador) clearTimeout(temporizador)
})
</script>

<template>
  <div class="ui-clave" :class="evaluacion.nivel === null ? '' : `ui-clave--nivel-${evaluacion.nivel}`">
    <div class="ui-clave__medidor" aria-hidden="true">
      <span v-for="n in 4" :key="n" class="ui-clave__segmento" :class="{ 'ui-clave__segmento--lleno': n <= evaluacion.segmentos }"></span>
    </div>
    <p class="ui-clave__nivel">
      <span class="ui-clave__etiqueta">Seguridad:</span>
      <strong>{{ evaluacion.etiqueta }}</strong>
    </p>
    <ul class="ui-clave__requisitos" aria-label="Requisitos de la contraseña">
      <li v-for="r in evaluacion.requisitos" :key="r.id" :class="r.cumple ? 'ui-clave__req--ok' : 'ui-clave__req--falta'">
        <UiIcon :nombre="r.cumple ? 'check' : 'cerrar'" :tamano="14" :grosor="2.6" />
        <span>{{ r.texto }}<span class="sr-only">: {{ r.cumple ? 'cumple' : 'no cumple' }}</span></span>
      </li>
    </ul>
    <p class="sr-only" aria-live="polite">{{ anuncio }}</p>
  </div>
</template>

<style scoped>
.ui-clave {
  --nivel: var(--color-borde-fuerte);
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
}

.ui-clave--nivel-0 {
  --nivel: var(--color-error);
}

.ui-clave--nivel-1 {
  --nivel: var(--color-aviso);
}

.ui-clave--nivel-2 {
  --nivel: var(--color-info);
}

.ui-clave--nivel-3 {
  --nivel: var(--color-primario);
}

.ui-clave__medidor {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
}

.ui-clave__segmento {
  height: 0.4rem;
  border-radius: var(--radio-pleno);
  background: var(--color-borde-fuerte);
  transition: background var(--trans);
}

.ui-clave__segmento--lleno {
  background: var(--nivel);
}

.ui-clave__nivel {
  display: flex;
  gap: 0.4rem;
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
}

.ui-clave__nivel strong {
  color: var(--nivel);
}

.ui-clave--nivel-2 .ui-clave__nivel strong,
.ui-clave--nivel-3 .ui-clave__nivel strong {
  color: var(--color-texto);
}

.ui-clave__requisitos {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  font-size: var(--texto-xs);
}

.ui-clave__requisitos li {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.ui-clave__req--ok {
  color: var(--color-exito);
}

.ui-clave__req--falta {
  color: var(--color-texto-suave);
}
</style>
