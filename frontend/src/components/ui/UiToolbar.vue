<script setup lang="ts">
/**
 * Barra de herramientas / filtros (`role="toolbar"` con nombre). Contenedor flexible que envuelve en pantallas
 * pequeñas. Slots: default (controles a la izquierda), `fin` (acciones a la derecha, p. ej. "Nueva empresa").
 * Nota: `role="toolbar"` no exige navegación con flechas si los controles son de formulario (búsqueda, selects);
 * para agrupar solo controles de formulario usa `rol="group"`.
 */
withDefaults(defineProps<{ etiqueta: string; rol?: 'toolbar' | 'group' | 'search' }>(), { rol: 'group' })
</script>

<template>
  <div class="ui-toolbar" :role="rol" :aria-label="etiqueta">
    <div class="ui-toolbar__grupo"><slot /></div>
    <div v-if="$slots.fin" class="ui-toolbar__fin"><slot name="fin" /></div>
  </div>
</template>

<style scoped>
.ui-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--espacio-3) var(--espacio-4);
  padding: var(--espacio-3) 0;
}

.ui-toolbar__grupo,
.ui-toolbar__fin {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--espacio-3);
  min-width: 0;
}

.ui-toolbar__fin {
  margin-left: auto;
}
</style>
