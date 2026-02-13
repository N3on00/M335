<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApp } from '../../core/injection'
import ActionButton from '../common/ActionButton.vue'

const app = useApp()
const route = useRoute()
const router = useRouter()
const extraOpen = ref(false)

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

const primaryEntries = computed(() => navEntries.value.slice(0, 3))
const extraEntries = computed(() => navEntries.value.slice(3))

const hasActiveExtra = computed(() => {
  const current = String(route.name || '')
  return extraEntries.value.some((entry) => String(entry.key) === current)
})

const show = computed(() => {
  if (!app.ui.isAuthenticated()) return false
  return route.name !== 'auth'
})

function open(entry) {
  if (!entry?.to) return
  extraOpen.value = false
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

function toggleExtraLinks() {
  extraOpen.value = !extraOpen.value
}

function openHome() {
  extraOpen.value = false
  router.push({ name: 'home' })
}
</script>

<template>
  <nav class="app-top-nav card border-0 shadow-sm" v-if="show" data-aos="fade-down">
    <div class="app-top-nav__inner">
      <button class="app-top-nav__brand app-top-nav__brand-button" type="button" aria-label="Go to home" @click="openHome">
        <span class="brand rounded-4"><i class="bi bi-compass-fill"></i></span>
        <div>
          <strong>SpotOnSight</strong>
          <div class="small text-secondary">Navigation</div>
        </div>
      </button>

      <div class="app-top-nav__center">
        <div class="app-top-nav__links app-top-nav__links--primary">
          <ActionButton
            v-for="entry in primaryEntries"
            :key="`app-nav-${entry.key}`"
            :class-name="isActive(entry) ? 'btn btn-primary app-top-nav__link app-top-nav__link--active' : 'btn btn-outline-secondary app-top-nav__link'"
            :icon="entry.icon"
            :label="entry.label"
            @click="open(entry)"
          />

          <ActionButton
            v-if="extraEntries.length"
            :class-name="(extraOpen || hasActiveExtra)
              ? 'btn btn-primary app-top-nav__link app-top-nav__link--active'
              : 'btn btn-outline-secondary app-top-nav__link'"
            :icon="extraOpen ? 'bi-chevron-up' : 'bi-chevron-down'"
            label="More"
            @click="toggleExtraLinks"
          />
        </div>

        <Transition name="app-nav-expand">
          <div class="app-top-nav__links app-top-nav__links--extra" v-if="extraOpen && extraEntries.length">
            <ActionButton
              v-for="entry in extraEntries"
              :key="`app-nav-extra-${entry.key}`"
              :class-name="isActive(entry) ? 'btn btn-primary app-top-nav__link app-top-nav__link--active' : 'btn btn-outline-secondary app-top-nav__link'"
              :icon="entry.icon"
              :label="entry.label"
              @click="open(entry)"
            />
          </div>
        </Transition>
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
