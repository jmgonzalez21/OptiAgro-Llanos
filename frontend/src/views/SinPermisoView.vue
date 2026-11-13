<script setup lang="ts">
import { RouterLink } from 'vue-router'
import UiCard from '@/components/ui/UiCard.vue'
import UiIcon from '@/components/ui/UiIcon.vue'
</script>

<template>
  <section class="vista-simple" aria-labelledby="titulo-sin-permiso">
    <UiCard variante="elevada" relleno="lg" class="vista-simple__tarjeta">
      <span class="vista-simple__icono"><UiIcon nombre="candado" :tamano="26" /></span>
      <h1 id="titulo-sin-permiso">Acceso denegado</h1>
      <p>No tienes permiso para ver esta sección con tu rol actual.</p>
      <RouterLink :to="{ name: 'inicio' }" class="vista-simple__enlace">Volver al inicio</RouterLink>
    </UiCard>
  </section>
</template>

<style scoped>
.vista-simple {
  display: grid;
  flex: 1;
  place-items: center;
}

.vista-simple__tarjeta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--espacio-3);
  max-width: 26rem;
  text-align: center;
}

.vista-simple__icono {
  display: grid;
  place-items: center;
  width: 3.5rem;
  height: 3.5rem;
  border-radius: 50%;
  background: var(--color-activo-fondo);
  color: var(--color-activo-texto);
}

.vista-simple p {
  color: var(--color-texto-2);
}

.vista-simple__enlace {
  display: inline-flex;
  align-items: center;
  min-height: var(--alto-tactil);
  padding: 0 var(--espacio-5);
  border: 1px solid var(--color-borde-fuerte);
  border-radius: var(--radio-md);
  background: var(--color-superficie);
  color: var(--color-activo-texto);
  font-size: var(--texto-sm);
  font-weight: var(--peso-fuerte);
  text-decoration: none;
  transition: background var(--trans);
}

.vista-simple__enlace:hover {
  background: var(--color-acento-suave);
}
</style>
