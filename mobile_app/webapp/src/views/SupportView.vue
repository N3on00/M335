<script setup>
import { useRouter } from 'vue-router'
import SlotScreenLayout from '../components/layouts/SlotScreenLayout.vue'

const router = useRouter()
const screenCtx = { router }
</script>

<template>
  <SlotScreenLayout
    screen="support"
    :screen-ctx="screenCtx"
    :slots="['header', 'main']"
    screen-class="container-xxl py-3 py-md-4"
  />
</template>
