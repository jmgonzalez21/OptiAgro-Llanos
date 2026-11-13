import { beforeEach, describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, type Router } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import { crearRouter } from '@/router'
import { useAuthStore } from '@/stores/auth'
import { limpiarAlmacenamiento, prepararApiMock } from '@/test/helpers'

const Vacia = { template: '<div />' }

async function montar(consulta = '/login') {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router: Router = crearRouter(createMemoryHistory(), [
    { path: '/login', name: 'login', component: LoginView, meta: { soloInvitado: true } },
    { path: '/', name: 'inicio', component: Vacia, meta: { requiereAuth: true } },
    { path: '/escenarios', name: 'escenarios', component: Vacia, meta: { requiereAuth: true } },
  ])
  await router.push(consulta)
  await router.isReady()
  const envoltorio = mount(LoginView, { global: { plugins: [pinia, router] }, attachTo: document.body })
  return { envoltorio, router, auth: useAuthStore() }
}

describe('LoginView', () => {
  let mock: ReturnType<typeof prepararApiMock>['mock']

  beforeEach(() => {
    document.body.innerHTML = ''
    limpiarAlmacenamiento()
    ;({ mock } = prepararApiMock())
  })

  it('asocia etiquetas a los campos', async () => {
    const { envoltorio } = await montar()
    expect(envoltorio.find('label[for="login-usuario"]').text()).toBe('Usuario')
    expect(envoltorio.find('input#login-usuario').exists()).toBe(true)
    expect(envoltorio.find('label[for="login-contrasena"]').text()).toBe('Contraseña')
  })

  it('muestra errores en línea y no llama a la API con campos vacíos', async () => {
    const { envoltorio } = await montar()
    await envoltorio.find('form').trigger('submit')

    expect(envoltorio.find('#login-usuario-error').text()).toContain('nombre de usuario')
    expect(envoltorio.find('input#login-usuario').attributes('aria-invalid')).toBe('true')
    expect(envoltorio.find('input#login-usuario').attributes('aria-describedby')).toBe('login-usuario-error')
    expect(mock.estado.registro).toHaveLength(0)
    // El foco pasa al primer campo inválido.
    expect(document.activeElement).toBe(envoltorio.find('input#login-usuario').element)
  })

  it('valida al salir del campo (blur)', async () => {
    const { envoltorio } = await montar()
    await envoltorio.find('input#login-contrasena').trigger('blur')
    expect(envoltorio.find('#login-contrasena-error').exists()).toBe(true)
    expect(envoltorio.find('#login-usuario-error').exists()).toBe(false)
  })

  it('alterna mostrar/ocultar contraseña', async () => {
    const { envoltorio } = await montar()
    const campo = envoltorio.find('input#login-contrasena')
    const boton = envoltorio.find('button.campo__alternar')
    expect(campo.attributes('type')).toBe('password')
    expect(boton.attributes('aria-pressed')).toBe('false')
    await boton.trigger('click')
    expect(campo.attributes('type')).toBe('text')
    expect(boton.attributes('aria-pressed')).toBe('true')
    expect(boton.text()).toBe('Ocultar contraseña')
  })

  it('credenciales inválidas: muestra el error en un role=alert y enfoca el mensaje', async () => {
    mock.estado.rechazarLogin = true
    const { envoltorio, auth } = await montar()
    await envoltorio.find('input#login-usuario').setValue('ana')
    await envoltorio.find('input#login-contrasena').setValue('mala')
    await envoltorio.find('form').trigger('submit')
    await flushPromises()

    const alerta = envoltorio.find('[role="alert"]')
    expect(alerta.exists()).toBe(true)
    expect(alerta.text()).toBe('Usuario o contraseña incorrectos.')
    expect(auth.autenticado).toBe(false)
    expect(document.activeElement).toBe(alerta.element)
    // La contraseña se limpia tras un intento fallido.
    expect((envoltorio.find('input#login-contrasena').element as HTMLInputElement).value).toBe('')
  })

  it('red caída: muestra un mensaje de conexión', async () => {
    mock.estado.caido = true
    const { envoltorio } = await montar()
    await envoltorio.find('input#login-usuario').setValue('ana')
    await envoltorio.find('input#login-contrasena').setValue('x')
    await envoltorio.find('form').trigger('submit')
    await flushPromises()

    expect(envoltorio.find('[role="alert"]').text()).toContain('No hay conexión con el servidor')
  })

  it('deshabilita el botón y marca aria-busy mientras carga', async () => {
    const { envoltorio } = await montar()
    await envoltorio.find('input#login-usuario').setValue('ana')
    await envoltorio.find('input#login-contrasena').setValue('x')
    const envio = envoltorio.find('form').trigger('submit')
    await Promise.resolve()
    const boton = envoltorio.find('button[type="submit"]')
    expect(boton.attributes('disabled')).toBeDefined()
    expect(boton.attributes('aria-busy')).toBe('true')
    await envio
    await flushPromises()
  })

  it('login correcto navega al inicio', async () => {
    const { envoltorio, router, auth } = await montar()
    await envoltorio.find('input#login-usuario').setValue('admin')
    await envoltorio.find('input#login-contrasena').setValue('x')
    await envoltorio.find('form').trigger('submit')
    await flushPromises()

    expect(auth.autenticado).toBe(true)
    expect(router.currentRoute.value.name).toBe('inicio')
  })

  it('respeta ?redirect= tras iniciar sesión y avisa si la sesión expiró', async () => {
    const { envoltorio, router } = await montar('/login?motivo=expirada&redirect=/escenarios')
    expect(envoltorio.find('[role="status"]').text()).toContain('sesión expiró')
    await envoltorio.find('input#login-usuario').setValue('ana')
    await envoltorio.find('input#login-contrasena').setValue('x')
    await envoltorio.find('form').trigger('submit')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/escenarios')
  })
})
