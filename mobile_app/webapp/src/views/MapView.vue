<script setup>
import { useRouter } from 'vue-router'
import SlotScreenLayout from '../components/layouts/SlotScreenLayout.vue'

const router = useRouter()
const screenCtx = { router }
</script>

<template>
  <SlotScreenLayout
    screen="map"
    :screen-ctx="screenCtx"
    :slots="['header', 'main']"
    screen-class="screen--map container-fluid py-3 py-md-4 px-lg-4"
  />
</template>
