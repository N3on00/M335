import { createRouter, createWebHistory } from 'vue-router'

import AuthView from '../views/AuthView.vue'
import HomeView from '../views/HomeView.vue'
import MapView from '../views/MapView.vue'
import SocialView from '../views/SocialView.vue'
import SettingsView from '../views/SettingsView.vue'
import ProfileView from '../views/ProfileView.vue'
import SupportView from '../views/SupportView.vue'

export function createAppRouter(appCtx) {
  const router = createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', redirect: '/home' },
      { path: '/auth', name: 'auth', component: AuthView, meta: { guestOnly: true } },
      { path: '/home', name: 'home', component: HomeView, meta: { requiresAuth: true } },
      { path: '/map', name: 'map', component: MapView, meta: { requiresAuth: true } },
      { path: '/social', name: 'social', component: SocialView, meta: { requiresAuth: true } },
      { path: '/settings', name: 'settings', component: SettingsView, meta: { requiresAuth: true } },
      { path: '/profile/:userId?', name: 'profile', component: ProfileView, meta: { requiresAuth: true } },
      { path: '/support', name: 'support', component: SupportView, meta: { requiresAuth: true } },
    ],
  })

  router.beforeEach(async (to) => {
    const isAuth = appCtx.ui.isAuthenticated()

    if (to.meta.requiresAuth && !isAuth) {
      return { name: 'auth' }
    }
    if (to.meta.guestOnly && isAuth) {
      return { name: 'home' }
    }
    return true
  })

  return router
}
