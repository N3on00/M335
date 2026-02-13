<script setup>
import ActionButton from '../common/ActionButton.vue'

defineProps({
  onBackHome: { type: Function, required: true },
  onOpenSocial: { type: Function, required: true },
  onOpenSettings: { type: Function, required: true },
})
</script>

<template>
  <section class="card border-0 shadow-sm hero-card" data-aos="fade-down">
    <div class="card-body d-grid gap-3 p-4">
      <div>
        <p class="eyebrow">Support</p>
        <h1 class="h3 mb-1">Report bugs, complaints, or feature requests</h1>
        <p class="text-secondary mb-0">Send your feedback directly to the backend support queue.</p>
      </div>

      <div class="thumb-actions">
        <ActionButton label="Home" icon="bi-house" class-name="btn btn-outline-secondary" @click="onBackHome" />
        <ActionButton label="Social" icon="bi-people" class-name="btn btn-outline-secondary" @click="onOpenSocial" />
        <ActionButton label="Settings" icon="bi-gear" class-name="btn btn-outline-secondary" @click="onOpenSettings" />
      </div>
    </div>
  </section>
</template>
