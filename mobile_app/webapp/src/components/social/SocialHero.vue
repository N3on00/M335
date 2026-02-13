<script setup>
import ActionButton from '../common/ActionButton.vue'

defineProps({
  onBackHome: { type: Function, required: true },
  onOpenSettings: { type: Function, required: true },
  onOpenSupport: { type: Function, required: true },
  onOpenMyProfile: { type: Function, required: true },
})
</script>

<template>
  <section class="card border-0 shadow-sm hero-card" data-aos="fade-down">
    <div class="card-body d-grid gap-3 p-4">
      <div>
        <p class="eyebrow">Social Hub</p>
        <h1 class="h3 mb-1">Find friends and manage your network</h1>
        <p class="text-secondary mb-0">Search by username, approve requests, and control followers.</p>
      </div>
      <div class="thumb-actions">
        <ActionButton label="Home" icon="bi-house" class-name="btn btn-outline-secondary" @click="onBackHome" />
        <ActionButton label="My Profile" icon="bi-person" class-name="btn btn-outline-secondary" @click="onOpenMyProfile" />
        <ActionButton label="Settings" icon="bi-gear" class-name="btn btn-outline-secondary" @click="onOpenSettings" />
        <ActionButton label="Support" icon="bi-life-preserver" class-name="btn btn-outline-secondary" @click="onOpenSupport" />
      </div>
    </div>
  </section>
</template>
