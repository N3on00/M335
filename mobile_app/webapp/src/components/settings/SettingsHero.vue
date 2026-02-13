<script setup>
import ActionButton from '../common/ActionButton.vue'

defineProps({
  onBackHome: { type: Function, required: true },
  onOpenSocial: { type: Function, required: true },
  onOpenSupport: { type: Function, required: true },
  onOpenProfile: { type: Function, required: true },
})
</script>

<template>
  <section class="card border-0 shadow-sm hero-card" data-aos="fade-down">
    <div class="card-body d-grid gap-3 p-4">
      <div>
        <p class="eyebrow">Settings</p>
        <h1 class="h3 mb-1">Customize your profile and account</h1>
        <p class="text-secondary mb-0">Edit biography, social links, avatar, and privacy controls.</p>
      </div>
      <div class="thumb-actions">
        <ActionButton label="Home" icon="bi-house" class-name="btn btn-outline-secondary" @click="onBackHome" />
        <ActionButton label="Social" icon="bi-people" class-name="btn btn-outline-secondary" @click="onOpenSocial" />
        <ActionButton label="Support" icon="bi-life-preserver" class-name="btn btn-outline-secondary" @click="onOpenSupport" />
        <ActionButton label="My Profile" icon="bi-person" class-name="btn btn-outline-secondary" @click="onOpenProfile" />
      </div>
    </div>
  </section>
</template>
