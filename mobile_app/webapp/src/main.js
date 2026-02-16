import { createApp } from 'vue'
import { watch } from 'vue'
import AOS from 'aos'
import { buildAppContext } from './bootstrap/appBootstrap'
import { APP_CTX_KEY } from './core/injection'
import { createAppRouter } from './router'
import { persistFilterSubscriptions, persistSession, persistTheme } from './state/appState'

import 'bootswatch/dist/flatly/bootstrap.min.css'
import 'bootstrap-icons/font/bootstrap-icons.css'
import 'aos/dist/aos.css'
import './style.css'
import 'leaflet/dist/leaflet.css'
import App from './App.vue'

const appCtx = buildAppContext()
const router = createAppRouter(appCtx)

function applyTheme(theme) {
  const next = String(theme || 'light').toLowerCase() === 'dark' ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', next)
  document.body.classList.toggle('theme-dark', next === 'dark')
}

applyTheme(appCtx.state.ui.theme)

AOS.init({
  duration: 650,
  once: true,
  easing: 'ease-out-cubic',
  offset: 18,
})

router.afterEach(() => {
  setTimeout(() => {
    AOS.refreshHard()
  }, 0)
})

watch(
  () => [appCtx.state.session.token, appCtx.state.session.user],
  () => {
    persistSession(appCtx.state)
  },
  { deep: true },
)

watch(
  () => appCtx.state.session.token,
  (token) => {
    const hasToken = Boolean(String(token || '').trim())
    if (hasToken) return

    const currentRoute = router.currentRoute.value
    if (String(currentRoute?.name || '') === 'auth') return
    if (currentRoute?.meta?.requiresAuth) {
      void router.replace({ name: 'auth' })
    }
  },
  { immediate: true },
)

watch(
  () => appCtx.state.ui.theme,
  () => {
    applyTheme(appCtx.state.ui.theme)
    persistTheme(appCtx.state)
  },
)

watch(
  () => appCtx.state.map.filterSubscriptions,
  () => {
    persistFilterSubscriptions(appCtx.state)
  },
  { deep: true },
)

const app = createApp(App)
app.provide(APP_CTX_KEY, appCtx)
app.use(router)
app.mount('#app')
