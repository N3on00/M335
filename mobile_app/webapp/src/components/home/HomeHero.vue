<script setup>
import ActionButton from '../common/ActionButton.vue'

defineProps({
  username: { type: String, default: '' },
  onOpenSupport: { type: Function, required: true },
  onLogout: { type: Function, required: true },
})
</script>

<template>
  <section class="card border-0 shadow-sm hero-card" data-aos="fade-down">
    <div class="card-body d-flex flex-column flex-lg-row justify-content-between align-items-lg-center gap-3 p-4 p-lg-5">
      <div>
        <p class="eyebrow">SpotOnSight</p>
        <h1 class="display-6 fw-bold mb-2">Welcome back{{ username ? `, ${username}` : '' }}</h1>
        <p class="lead text-secondary mb-0">Discover, save, and share unique places with your network.</p>
      </div>
      <div class="d-flex flex-wrap gap-2">
        <ActionButton label="Support" icon="bi-life-preserver" class-name="btn btn-outline-primary" @click="onOpenSupport" />
        <ActionButton label="Logout" icon="bi-box-arrow-right" class-name="btn btn-outline-secondary" @click="onLogout" />
      </div>
    </div>
  </section>
</template>
