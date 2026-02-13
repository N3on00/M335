<script setup>
import { computed } from 'vue'
import { useApp } from '../../core/injection'
import ActionButton from './ActionButton.vue'

const app = useApp()

const notifications = computed(() => app.state.notifications)

function titleOf(n) {
  const t = String(n?.title || '').trim()
  return t || 'Notification'
}

function messageOf(n) {
  const m = String(n?.message || '').trim()
  if (m) return m
  const d = String(n?.details || '').trim()
  if (d) return d.split('\n')[0]
  return 'No details provided.'
}

function close(id) {
  app.service('notify').remove(id)
}

async function copyDetails(details) {
  if (!details) return
  try {
    await navigator.clipboard.writeText(details)
    app.service('notify').push({
      level: 'success',
      title: 'Copied',
      message: 'Details copied to clipboard.',
    })
  } catch {
    app.service('notify').push({
      level: 'warning',
      title: 'Clipboard Error',
      message: 'Could not copy details from browser.',
    })
  }
}
</script>

<template>
  <TransitionGroup name="notify-slide" tag="div" class="notify-stack">
    <article
      class="alert shadow-sm border-0 mb-0 notify-alert"
      :class="`notify-alert--${n.level || 'info'}`"
      v-for="n in notifications"
      :key="n.id"
    >
      <header class="d-flex align-items-center justify-content-between gap-2 mb-1">
        <h4 class="h6 mb-0">{{ titleOf(n) }}</h4>
        <ActionButton class-name="btn btn-sm btn-light border" icon="bi-x-lg" :icon-only="true" aria-label="Close notification" @click="close(n.id)" />
      </header>
      <p class="mb-2 small">{{ messageOf(n) }}</p>
      <div class="d-flex flex-wrap gap-2">
        <ActionButton
          v-if="n.details"
          class-name="btn btn-sm btn-light border"
          icon="bi-clipboard"
          label="Copy details"
          @click="copyDetails(n.details)"
        />
        <ActionButton class-name="btn btn-sm btn-outline-secondary" label="Close" @click="close(n.id)" />
      </div>
    </article>
  </TransitionGroup>
</template>
