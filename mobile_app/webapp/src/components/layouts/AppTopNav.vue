<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useApp } from '../../core/injection'
import { toImageSource } from '../../models/imageMapper'
import {
  ROUTE_NAMES,
  routeToAuth,
  routeToHome,
  routeToMap,
  routeToProfile,
  routeToSettings,
  routeToSocial,
  routeToSupport,
} from '../../router/routeSpec'
import ActionButton from '../common/ActionButton.vue'
import UserProfileCard from '../common/UserProfileCard.vue'

const app = useApp()
const route = useRoute()
const router = useRouter()

const notificationsOpen = ref(false)
const userMenuOpen = ref(false)
const isMobile = ref(false)
const navRoot = ref(null)
const panelRoot = ref(null)
const expandedLogEntries = ref({})

const navEntries = computed(() => {
  return [
    { key: ROUTE_NAMES.SOCIAL, label: 'Social', icon: 'bi-people', to: routeToSocial() },
    { key: ROUTE_NAMES.MAP, label: 'Map', icon: 'bi-map', to: routeToMap() },
    { key: ROUTE_NAMES.HOME, label: 'Home', icon: 'bi-house', to: routeToHome() },
  ]
})

const me = computed(() => app.state.session.user || null)

const logEntries = computed(() => {
  const source = Array.isArray(app.state.notificationLog) ? app.state.notificationLog : []
  return [...source].reverse()
})

const logCount = computed(() => logEntries.value.length)

const userTriggerClass = computed(() => {
  if (userMenuOpen.value) {
    return 'btn btn-primary app-top-nav__tool-btn app-top-nav__user-trigger-btn app-top-nav__user-trigger--active'
  }
  return 'btn btn-outline-secondary app-top-nav__tool-btn app-top-nav__user-trigger-btn'
})

const incomingCount = computed(() => {
  const list = Array.isArray(app.state.social?.incomingRequests)
    ? app.state.social.incomingRequests
    : []
  return list.length
})

const primaryEntries = computed(() => navEntries.value)

const show = computed(() => {
  if (!app.ui.isAuthenticated()) return false
  return route.name !== ROUTE_NAMES.AUTH
})

const userAvatar = computed(() => {
  const raw = String(me.value?.avatar_image || '').trim()
  if (!raw) return ''
  return toImageSource(raw)
})

const userTitle = computed(() => {
  return String(me.value?.display_name || me.value?.username || 'Your account')
})

const userNavName = computed(() => {
  const username = String(me.value?.username || '').trim()
  if (username) return `@${username}`
  return String(me.value?.display_name || 'Profile')
})

const userSubtitle = computed(() => {
  const username = String(me.value?.username || '').trim()
  if (!username) return ''
  return `@${username}`
})

const userDetails = computed(() => {
  const details = []
  const email = String(me.value?.email || '').trim()
  if (email) details.push(email)
  if (incomingCount.value > 0) {
    details.push(`${incomingCount.value} follow request(s)`)
  }
  return details
})

watch(
  () => route.fullPath,
  () => {
    notificationsOpen.value = false
    userMenuOpen.value = false
  },
)

function updateViewportMode() {
  if (typeof window === 'undefined') return
  isMobile.value = window.matchMedia('(max-width: 900px)').matches
  syncNotificationAnchor()
}

function applyMobileOverlayHeight(value = 0) {
  if (typeof document === 'undefined') return
  const px = Math.max(0, Math.ceil(Number(value) || 0))
  document.documentElement.style.setProperty('--app-mobile-nav-overlay-height', `${px}px`)
}

function syncNotificationAnchor() {
  if (typeof window === 'undefined') return

  if (!show.value || !isMobile.value || !navRoot.value) {
    applyMobileOverlayHeight(0)
    return
  }

  const navRect = navRoot.value.getBoundingClientRect()
  let top = navRect.top

  if ((notificationsOpen.value || userMenuOpen.value) && panelRoot.value) {
    const panelRect = panelRoot.value.getBoundingClientRect()
    top = Math.min(top, panelRect.top)
  }

  const overlayHeight = window.innerHeight - top
  applyMobileOverlayHeight(overlayHeight)
}

function scheduleNotificationAnchorSync() {
  nextTick(() => {
    syncNotificationAnchor()
    if (typeof window !== 'undefined') {
      window.requestAnimationFrame(() => syncNotificationAnchor())
    }
  })
}

watch(
  () => [show.value, isMobile.value, notificationsOpen.value, userMenuOpen.value, route.fullPath],
  () => {
    scheduleNotificationAnchorSync()
  },
  { immediate: true },
)

onMounted(() => {
  updateViewportMode()
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', updateViewportMode)
    scheduleNotificationAnchorSync()
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', updateViewportMode)
  }
  applyMobileOverlayHeight(0)
})

function closePanels() {
  notificationsOpen.value = false
  userMenuOpen.value = false
}

function open(entry) {
  if (!entry?.to) return
  closePanels()
  router.push(entry.to)
}

function isActive(entry) {
  return String(route.name || '') === String(entry.key)
}

function logout() {
  closePanels()
  app.controller('auth').logout()
  app.service('notify').push({
    level: 'info',
    title: 'Logged out',
    message: 'Session ended.',
  })
  router.push(routeToAuth())
}

function openHome() {
  closePanels()
  router.push(routeToHome())
}

function toggleNotifications() {
  userMenuOpen.value = false
  notificationsOpen.value = !notificationsOpen.value
}

function toggleUserMenu() {
  notificationsOpen.value = false
  userMenuOpen.value = !userMenuOpen.value
}

function openMyProfile() {
  const userId = String(me.value?.id || '').trim()
  closePanels()
  router.push(routeToProfile(userId))
}

function openSettings() {
  closePanels()
  router.push(routeToSettings())
}

function openSupport() {
  closePanels()
  router.push(routeToSupport())
}

function clearNotificationLog() {
  app.service('notify').clearLog()
  expandedLogEntries.value = {}
}

function notificationEntryKey(entry) {
  const id = String(entry?.id || '').trim()
  if (id) return id
  const createdAt = String(entry?.createdAt || '').trim()
  const title = String(entry?.title || '').trim()
  return `${createdAt}-${title}`
}

function notificationDetails(entry) {
  return String(entry?.details || '').trim()
}

function hasNotificationDetails(entry) {
  return Boolean(notificationDetails(entry))
}

function isNotificationExpanded(entry) {
  return Boolean(expandedLogEntries.value[notificationEntryKey(entry)])
}

function toggleNotificationExpanded(entry) {
  const key = notificationEntryKey(entry)
  expandedLogEntries.value = {
    ...expandedLogEntries.value,
    [key]: !isNotificationExpanded(entry),
  }
}

function notificationMessage(entry) {
  const message = String(entry?.message || '').trim()
  if (message) return message
  const details = String(entry?.details || '').trim()
  if (!details) return 'No details provided.'
  return details.split(/\r?\n/)[0]
}

function notificationTimestamp(entry) {
  const text = String(entry?.createdAt || '').trim()
  if (!text) return ''

  const date = new Date(text)
  if (Number.isNaN(date.getTime())) return ''

  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <nav class="app-top-nav card border-0 shadow-sm" v-if="show" data-aos="fade-down" ref="navRoot">
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
        </div>
      </div>

      <div class="app-top-nav__tools">
        <ActionButton
          :class-name="notificationsOpen ? 'btn btn-primary app-top-nav__tool-btn' : 'btn btn-outline-secondary app-top-nav__tool-btn'"
          icon="bi-bell"
          :label="isMobile ? '' : `Notifications (${logCount})`"
          :icon-only="isMobile"
          aria-label="Open notification log"
          @click="toggleNotifications"
        />
        <ActionButton
          :class-name="userTriggerClass"
          aria-label="Open user menu"
          @click="toggleUserMenu"
        >
          <span class="app-top-nav__user-trigger">
            <span class="app-top-nav__user-avatar" v-if="userAvatar">
              <img :src="userAvatar" alt="profile avatar" loading="lazy" />
            </span>
            <span class="app-top-nav__user-avatar app-top-nav__user-avatar--empty" v-else>
              <i class="bi bi-person"></i>
            </span>
            <span class="app-top-nav__user-name">{{ userNavName }}</span>
          </span>
        </ActionButton>
      </div>
    </div>

    <Transition name="app-nav-expand">
      <div class="app-top-nav__panel" ref="panelRoot" v-if="notificationsOpen || userMenuOpen">
        <section class="card border-0 shadow-sm app-top-nav__panel-card" v-if="notificationsOpen">
          <div class="app-top-nav__panel-header">
            <h4 class="h6 mb-0">Notification log</h4>
            <ActionButton
              class-name="btn btn-sm btn-outline-secondary"
              label="Clear log"
              :disabled="!logEntries.length"
              @click="clearNotificationLog"
            />
          </div>

          <div class="app-top-nav__notification-list" v-if="logEntries.length">
            <article class="app-top-nav__notification-item" v-for="entry in logEntries" :key="`log-${entry.id}-${entry.createdAt}`">
              <div class="app-top-nav__notification-title-row">
                <strong>{{ entry.title || 'Notification' }}</strong>
                <span class="small text-secondary">{{ notificationTimestamp(entry) }}</span>
              </div>

              <p class="small mb-0 app-top-nav__notification-message">{{ notificationMessage(entry) }}</p>

              <div class="app-top-nav__notification-actions" v-if="hasNotificationDetails(entry)">
                <ActionButton
                  class-name="btn btn-sm btn-link p-0"
                  :icon="isNotificationExpanded(entry) ? 'bi-chevron-up' : 'bi-chevron-down'"
                  :label="isNotificationExpanded(entry) ? 'Hide details' : 'Show details'"
                  @click="toggleNotificationExpanded(entry)"
                />
              </div>

              <pre class="app-top-nav__notification-details" v-if="isNotificationExpanded(entry)">{{ notificationDetails(entry) }}</pre>
            </article>
          </div>

          <p class="small text-secondary mb-0" v-else>No notifications yet.</p>
        </section>

        <section class="card border-0 shadow-sm app-top-nav__panel-card" v-if="userMenuOpen">
          <UserProfileCard
            :title="userTitle"
            :subtitle="userSubtitle"
            :avatar="userAvatar"
            :details="userDetails"
            compact
          >
            <template #actions>
              <ActionButton class-name="btn btn-sm btn-outline-secondary" icon="bi-person" label="My profile" @click="openMyProfile" />
              <ActionButton class-name="btn btn-sm btn-outline-secondary" icon="bi-gear" label="Settings" @click="openSettings" />
              <ActionButton class-name="btn btn-sm btn-outline-secondary" icon="bi-life-preserver" label="Support" @click="openSupport" />
              <ActionButton class-name="btn btn-sm btn-outline-danger" icon="bi-box-arrow-right" label="Logout" @click="logout" />
            </template>
          </UserProfileCard>
        </section>
      </div>
    </Transition>
  </nav>
</template>
