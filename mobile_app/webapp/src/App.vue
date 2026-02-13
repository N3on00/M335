<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterView } from 'vue-router'
import NotificationStack from './components/common/NotificationStack.vue'
import SosLoader from './components/common/SosLoader.vue'
import AppTopNav from './components/layouts/AppTopNav.vue'
import { useApp } from './core/injection'

const app = useApp()
const bootLoading = ref(true)
const activityWatch = app.service('activityWatch')

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

onMounted(async () => {
  const startedAt = Date.now()

  try {
    if (app.ui.isAuthenticated()) {
      await Promise.all([
        app.controller('users').refreshProfile(),
        app.controller('spots').reload(),
        app.controller('social').reloadFavorites(),
      ])
    }
  } catch (error) {
    app.service('notify').push({
      level: 'error',
      title: 'Initial load failed',
      message: 'Some data could not be loaded on startup.',
      details: String(error?.message || error),
    })
  } finally {
    const elapsed = Date.now() - startedAt
    const minimumVisibleMs = 450
    if (elapsed < minimumVisibleMs) {
      await wait(minimumVisibleMs - elapsed)
    }
    bootLoading.value = false
  }
})

watch(
  () => app.state.session.token,
  (token) => {
    if (String(token || '').trim()) {
      activityWatch.start()
      return
    }
    activityWatch.stop()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  activityWatch.stop()
})
</script>

<template>
  <div class="app-shell position-relative">
    <div class="orb orb--one" />
    <div class="orb orb--two" />

    <AppTopNav />

    <RouterView v-slot="{ Component, route }">
      <Transition name="route-fade" mode="out-in">
        <component :is="Component" :key="route.fullPath" />
      </Transition>
    </RouterView>

    <Transition name="app-loader-fade">
      <div class="app-loader-screen" v-if="bootLoading">
        <div class="app-loader-panel card border-0 shadow-sm">
          <SosLoader size="lg" label="Loading web app..." />
          <p class="text-secondary small mb-0">Please wait a moment.</p>
        </div>
      </div>
    </Transition>

    <NotificationStack />
  </div>
</template>
