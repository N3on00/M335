<script setup>
import ActionButton from '../common/ActionButton.vue'

defineProps({
  onBack: { type: Function, required: true },
  onOpenSocial: { type: Function, required: true },
  onOpenSupport: { type: Function, required: true },
  onOpenSettings: { type: Function, required: true },
})
</script>

<template>
  <section class="card border-0 shadow-sm hero-card" data-aos="fade-down">
    <div class="card-body d-grid gap-3 p-4">
      <div>
        <p class="eyebrow">Profile</p>
        <h1 class="h3 mb-1">User profile overview</h1>
        <p class="text-secondary mb-0">See biography, social accounts, created spots, and favorites.</p>
      </div>
      <div class="thumb-actions">
        <ActionButton label="Back" icon="bi-arrow-left" class-name="btn btn-outline-secondary" @click="onBack" />
        <ActionButton label="Social" icon="bi-people" class-name="btn btn-outline-primary" @click="onOpenSocial" />
        <ActionButton label="Support" icon="bi-life-preserver" class-name="btn btn-outline-primary" @click="onOpenSupport" />
        <ActionButton label="Settings" icon="bi-gear" class-name="btn btn-primary" @click="onOpenSettings" />
      </div>
    </div>
  </section>
</template>
