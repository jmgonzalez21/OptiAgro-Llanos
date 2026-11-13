import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createWebHistory } from 'vue-router'
import './styles/index.css'
import App from './App.vue'
import { crearRouter } from './router'
import { vigilarSesion } from './router/guards'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)

const router = crearRouter(createWebHistory())
vigilarSesion(router, useAuthStore(pinia))
app.use(router)

app.mount('#app')
