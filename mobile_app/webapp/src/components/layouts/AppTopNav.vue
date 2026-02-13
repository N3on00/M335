<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApp } from '../../core/injection'
import ActionButton from '../common/ActionButton.vue'

const app = useApp()
const route = useRoute()
const router = useRouter()

const navEntries = computed(() => {
  const meId = String(app.state.session.user?.id || '').trim()
  return [
    { key: 'home', label: 'Home', icon: 'bi-house', to: { name: 'home' } },
    { key: 'map', label: 'Map', icon: 'bi-map', to: { name: 'map' } },
    { key: 'social', label: 'Social', icon: 'bi-people', to: { name: 'social' } },
    { key: 'profile', label: 'Profile', icon: 'bi-person', to: { name: 'profile', params: { userId: meId } } },
    { key: 'settings', label: 'Settings', icon: 'bi-gear', to: { name: 'settings' } },
    { key: 'support', label: 'Support', icon: 'bi-life-preserver', to: { name: 'support' } },
  ]
})

const incomingCount = computed(() => {
  const list = Array.isArray(app.state.social?.incomingRequests)
    ? app.state.social.incomingRequests
    : []
  return list.length
})

const show = computed(() => {
  if (!app.ui.isAuthenticated()) return false
  return route.name !== 'auth'
})

function open(entry) {
  if (!entry?.to) return
  router.push(entry.to)
}

function isActive(entry) {
  return String(route.name || '') === String(entry.key)
}

function logout() {
  app.controller('auth').logout()
  app.service('notify').push({
    level: 'info',
    title: 'Logged out',
    message: 'Session ended.',
  })
  router.push({ name: 'auth' })
}
</script>

<template>
  <nav class="app-top-nav card border-0 shadow-sm" v-if="show" data-aos="fade-down">
    <div class="app-top-nav__inner">
      <div class="app-top-nav__brand">
        <span class="brand rounded-4"><i class="bi bi-compass-fill"></i></span>
        <div>
          <strong>SpotOnSight</strong>
          <div class="small text-secondary">Unified navigation</div>
        </div>
      </div>

      <div class="app-top-nav__links">
        <ActionButton
          v-for="entry in navEntries"
          :key="`app-nav-${entry.key}`"
          :class-name="isActive(entry) ? 'btn btn-primary app-top-nav__link app-top-nav__link--active' : 'btn btn-outline-secondary app-top-nav__link'"
          :icon="entry.icon"
          :label="entry.label"
          @click="open(entry)"
        />
      </div>

      <div class="app-top-nav__tools">
        <span class="app-top-nav__notice" v-if="incomingCount > 0">
          <i class="bi bi-bell me-1"></i>{{ incomingCount }} request(s)
        </span>
        <ActionButton
          class-name="btn btn-outline-danger"
          icon="bi-box-arrow-right"
          label="Logout"
          @click="logout"
        />
      </div>
    </div>
  </nav>
</template>
