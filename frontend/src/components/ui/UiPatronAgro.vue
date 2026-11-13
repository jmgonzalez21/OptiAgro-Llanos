<script setup lang="ts">
/**
 * Ilustración decorativa: curvas de nivel + red de nodos (agroempresas → plantas).
 * Monocroma (verdes del tema), sin texto, oculta a tecnologías de apoyo.
 */
const CONTORNO =
  'M0,-250 C90,-262 190,-192 232,-92 C274,8 232,132 150,202 C68,272 -62,272 -152,212 C-242,152 -272,40 -242,-62 C-212,-164 -100,-238 0,-250 Z'

const CURVAS = [1, 0.87, 0.74, 0.62, 0.5, 0.39, 0.29, 0.2].map((escala, i) => ({
  escala,
  giro: i * 7,
  opacidad: 0.55 - i * 0.045,
}))

/** Empresas (círculos) y plantas (cuadrados redondeados) en el lienzo 600x520. */
const EMPRESAS = [
  { x: 96, y: 330 },
  { x: 168, y: 232 },
  { x: 232, y: 420 },
  { x: 318, y: 262 },
  { x: 420, y: 452 },
  { x: 506, y: 330 },
  { x: 470, y: 196 },
]
const PLANTAS = [
  { x: 258, y: 330 },
  { x: 404, y: 336 },
]

/** Rutas: [empresa, planta] con una curva suave entre ambos. */
const RUTAS = [
  [0, 0],
  [1, 0],
  [2, 0],
  [3, 0],
  [3, 1],
  [4, 1],
  [5, 1],
  [6, 1],
] as const

function curva(i: number, j: number): string {
  const e = EMPRESAS[i]!
  const p = PLANTAS[j]!
  const mx = (e.x + p.x) / 2
  const my = (e.y + p.y) / 2
  const dx = p.x - e.x
  const dy = p.y - e.y
  // Control perpendicular a la línea, para que el arco sea suave y distinto en cada ruta.
  const signo = (i + j) % 2 === 0 ? 1 : -1
  const cx = mx - dy * 0.18 * signo
  const cy = my + dx * 0.18 * signo
  return `M${e.x},${e.y} Q${cx.toFixed(1)},${cy.toFixed(1)} ${p.x},${p.y}`
}
</script>

<template>
  <svg class="patron" viewBox="0 0 600 520" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
    <g class="patron__curvas" transform="translate(330 300)">
      <path
        v-for="c in CURVAS"
        :key="c.escala"
        :d="CONTORNO"
        :transform="`rotate(${c.giro}) scale(${c.escala})`"
        :style="{ opacity: c.opacidad }"
        vector-effect="non-scaling-stroke"
      />
    </g>
    <g class="patron__curvas patron__curvas--menores" transform="translate(70 90) scale(0.62)">
      <path
        v-for="c in CURVAS.slice(0, 5)"
        :key="c.escala"
        :d="CONTORNO"
        :transform="`rotate(${-c.giro}) scale(${c.escala})`"
        :style="{ opacity: c.opacidad }"
        vector-effect="non-scaling-stroke"
      />
    </g>

    <g class="patron__rutas">
      <path v-for="([i, j], k) in RUTAS" :key="k" :d="curva(i, j)" />
    </g>

    <g class="patron__empresas">
      <circle v-for="(e, k) in EMPRESAS" :key="k" :cx="e.x" :cy="e.y" r="7" />
    </g>
    <g class="patron__plantas">
      <g v-for="(p, k) in PLANTAS" :key="k">
        <circle class="patron__halo" :cx="p.x" :cy="p.y" r="26" />
        <rect :x="p.x - 12" :y="p.y - 12" width="24" height="24" rx="8" />
      </g>
    </g>
  </svg>
</template>

<style scoped>
.patron {
  display: block;
  width: 100%;
  height: 100%;
}

.patron__curvas path {
  fill: none;
  stroke: var(--color-acento-fuerte);
  stroke-width: 1.1;
}

.patron__curvas--menores path {
  stroke-width: 1;
}

.patron__rutas path {
  fill: none;
  stroke: var(--color-activo-barra);
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-dasharray: 2 7;
  opacity: 0.75;
  animation: patron-flujo 6s linear infinite;
}

.patron__empresas circle {
  fill: var(--color-superficie);
  stroke: var(--color-activo-barra);
  stroke-width: 2.5;
}

.patron__plantas rect {
  fill: var(--color-marcador-planta);
  stroke: var(--color-superficie);
  stroke-width: 3;
}

.patron__halo {
  fill: var(--color-acento-fuerte);
  opacity: 0.28;
}

@keyframes patron-flujo {
  to {
    stroke-dashoffset: -72;
  }
}
</style>
