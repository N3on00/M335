<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SlotScreenLayout from '../components/layouts/SlotScreenLayout.vue'
import { useApp } from '../core/injection'

const router = useRouter()
const route = useRoute()
const app = useApp()

const screenCtx = computed(() => ({
  router,
  route,
  userId: String(route.params.userId || ''),
}))

onMounted(async () => {
  try {
    await app.ui.runAction('profile.refresh', { userId: String(route.params.userId || '') })
  } catch (error) {
    app.service('notify').push({
      level: 'error',
      title: 'Profile load failed',
      message: 'Could not initialize profile page.',
      details: String(error?.message || error),
    })
  }
})

watch(
  () => route.params.userId,
  async (nextId) => {
    try {
      await app.ui.runAction('profile.refresh', { userId: String(nextId || '') })
    } catch (error) {
      app.service('notify').push({
        level: 'error',
        title: 'Profile refresh failed',
        message: 'Could not refresh this profile.',
        details: String(error?.message || error),
      })
    }
  },
)
</script>

<template>
  <SlotScreenLayout
    screen="profile"
    :screen-ctx="screenCtx"
    :slots="['header', 'main']"
    screen-class="container-xxl py-3 py-md-4"
  />
</template>
