<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import SlotScreenLayout from '../components/layouts/SlotScreenLayout.vue'
import { useApp } from '../core/injection'

const router = useRouter()
const app = useApp()
const screenCtx = { router }

onMounted(async () => {
  try {
    await app.ui.runAction('settings.load')
  } catch (error) {
    app.service('notify').push({
      level: 'error',
      title: 'Settings load failed',
      message: 'Could not initialize settings page.',
      details: String(error?.message || error),
    })
  }
})
</script>

<template>
  <SlotScreenLayout
    screen="settings"
    :screen-ctx="screenCtx"
    :slots="['header', 'main']"
    screen-class="container-xxl py-3 py-md-4"
  />
</template>
