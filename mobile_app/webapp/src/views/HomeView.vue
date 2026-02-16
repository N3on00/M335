<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SlotScreenLayout from '../components/layouts/SlotScreenLayout.vue'
import { useApp } from '../core/injection'

const router = useRouter()
const screenCtx = { router }
const app = useApp()

onMounted(async () => {
  try {
    await app.ui.runAction('home.refresh')
  } catch (e) {
    if (!app.ui.isAuthenticated()) {
      return
    }
    app.service('notify').push({
      level: 'error',
      title: 'Dashboard load failed',
      message: 'Could not initialize home screen.',
      details: String(e?.message || e),
    })
  }
})
</script>

<template>
  <SlotScreenLayout
    screen="home"
    :screen-ctx="screenCtx"
    :slots="['header', 'main']"
    screen-class="container-xxl py-3 py-md-4"
  />
</template>
