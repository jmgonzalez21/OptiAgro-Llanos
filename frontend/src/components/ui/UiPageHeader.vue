<script setup lang="ts">
/**
 * Cabecera de pantalla: título, descripción, metadatos (insignias, conteos) y acciones.
 * Slots: `migas` (encima del título, solo en /historial/:id), `meta` (insignias bajo el título),
 * `ayuda` (arriba a la derecha, siempre en el mismo lugar: enlace "¿Cómo funciona?", WCAG 3.2.6), `acciones`.
 * `nivel` = 1 (por defecto). Si el shell ya muestra el título como h1 en la barra superior, usa `nivel="2"`.
 */
withDefaults(defineProps<{ titulo: string; descripcion?: string; nivel?: 1 | 2 }>(), { descripcion: '', nivel: 1 })
</script>

<template>
  <header class="ui-cabecera">
    <div v-if="$slots.migas" class="ui-cabecera__migas"><slot name="migas" /></div>
    <div class="ui-cabecera__fila">
      <div class="ui-cabecera__textos">
        <component :is="`h${nivel}`" class="ui-cabecera__titulo">{{ titulo }}</component>
        <p v-if="descripcion" class="ui-cabecera__descripcion">{{ descripcion }}</p>
        <div v-if="$slots.meta" class="ui-cabecera__meta"><slot name="meta" /></div>
      </div>
      <div v-if="$slots.ayuda || $slots.acciones" class="ui-cabecera__lateral">
        <div v-if="$slots.ayuda" class="ui-cabecera__ayuda"><slot name="ayuda" /></div>
        <div v-if="$slots.acciones" class="ui-cabecera__acciones"><slot name="acciones" /></div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.ui-cabecera {
  display: flex;
  flex-direction: column;
  gap: var(--espacio-2);
  margin-bottom: var(--espacio-4);
}

.ui-cabecera__fila {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--espacio-3) var(--espacio-5);
}

.ui-cabecera__textos {
  display: flex;
  flex: 1 1 18rem;
  flex-direction: column;
  gap: var(--espacio-1);
  min-width: 0;
}

.ui-cabecera__titulo {
  font-size: var(--texto-xl);
}

@media (min-width: 48rem) {
  .ui-cabecera__titulo {
    font-size: var(--texto-2xl);
  }
}

.ui-cabecera__descripcion {
  max-width: 46rem;
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
}

.ui-cabecera__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--espacio-2);
  margin-top: var(--espacio-1);
  font-size: var(--texto-sm);
  color: var(--color-texto-2);
}

.ui-cabecera__lateral {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: var(--espacio-2);
}

.ui-cabecera__ayuda {
  font-size: var(--texto-sm);
}

.ui-cabecera__acciones {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--espacio-2);
}

@media (max-width: 40rem) {
  .ui-cabecera__lateral {
    align-items: stretch;
    width: 100%;
  }

  .ui-cabecera__acciones {
    justify-content: flex-start;
  }
}
</style>
