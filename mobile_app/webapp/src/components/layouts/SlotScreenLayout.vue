<script setup>
import SlotHost from '../core/SlotHost.vue'

defineProps({
  screen: { type: String, required: true },
  slots: { type: Array, default: () => ['header', 'main', 'footer'] },
  screenCtx: { type: Object, default: () => ({}) },
  screenClass: { type: String, default: '' },
})
</script>

<template>
  <main :class="['screen', screenClass]">
    <SlotHost
      v-for="slot in slots"
      :key="`${screen}-${slot}`"
      :screen="screen"
      :slot="slot"
      :screen-ctx="screenCtx"
    />
  </main>
</template>
