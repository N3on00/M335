<script setup>
import { useRouter } from 'vue-router'
import SlotScreenLayout from '../components/layouts/SlotScreenLayout.vue'

const router = useRouter()
const screenCtx = { router }
</script>

<template>
  <SlotScreenLayout
    screen="auth"
    :screen-ctx="screenCtx"
    :slots="['header', 'main', 'footer']"
    screen-class="screen--auth container-xxl py-3 py-md-4"
  />
</template>
