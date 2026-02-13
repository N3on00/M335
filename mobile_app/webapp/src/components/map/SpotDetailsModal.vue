<script setup>
import { computed, ref, watch } from 'vue'
import { toImageSource } from '../../models/imageMapper'
import UserProfileCard from '../common/UserProfileCard.vue'
import ActionButton from '../common/ActionButton.vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  spot: { type: Object, default: null },
  isFavorite: { type: Boolean, default: false },
  favoriteBusy: { type: Boolean, default: false },
  canFavorite: { type: Boolean, default: true },
  canEdit: { type: Boolean, default: true },
  canDelete: { type: Boolean, default: true },
  canShare: { type: Boolean, default: true },
  onClose: { type: Function, required: true },
  onEdit: { type: Function, default: null },
  onDelete: { type: Function, default: null },
  onToggleFavorite: { type: Function, required: true },
  onShare: { type: Function, default: null },
  onGoToSpot: { type: Function, default: null },
  onNotify: { type: Function, required: true },
  onLoadUserProfile: { type: Function, default: null },
  onOpenOwnerProfile: { type: Function, default: null },
})

const imageIndex = ref(0)
const shareText = ref('')
const ownerBusy = ref(false)
const ownerProfile = ref(null)
let ownerLoadRun = 0

watch(
  () => props.spot,
  () => {
    imageIndex.value = 0
    shareText.value = ''
  },
)

watch(
  () => [props.open, props.spot?.id, props.spot?.owner_id, props.onLoadUserProfile],
  () => {
    void refreshOwnerProfile()
  },
  { immediate: true },
)

const images = computed(() => (Array.isArray(props.spot?.images) ? props.spot.images : []))

const currentImage = computed(() => {
  if (!images.value.length) return ''
  return toImageSource(images.value[imageIndex.value])
})

const ownerAvatar = computed(() => {
  const raw = String(ownerProfile.value?.avatar_image || '').trim()
  if (!raw) return ''
  return toImageSource(raw)
})

const ownerTitle = computed(() => {
  if (ownerBusy.value) {
    return 'Loading creator...'
  }

  const name = String(ownerProfile.value?.display_name || ownerProfile.value?.username || '').trim()
  if (name) {
    return name
  }

  return 'Unknown creator'
})

const ownerSubtitle = computed(() => {
  const username = String(ownerProfile.value?.username || '').trim()
  if (username) {
    return `@${username}`
  }
  return ''
})

const ownerDetails = computed(() => {
  if (ownerBusy.value) {
    return ['Fetching creator profile']
  }

  const out = []
  const bio = String(ownerProfile.value?.bio || '').trim()
  if (bio) {
    out.push(bio.length > 90 ? `${bio.slice(0, 87)}...` : bio)
  }

  const createdAt = String(ownerProfile.value?.created_at || '').trim()
  if (createdAt) {
    out.push(`Joined ${createdAt.slice(0, 10)}`)
  }

  const ownerId = String(props.spot?.owner_id || '').trim()
  if (!out.length && ownerId) {
    out.push(`ID: ${ownerId}`)
  }

  return out
})

const ownerProfileLinkVisible = computed(() => {
  if (typeof props.onOpenOwnerProfile !== 'function') return false
  return Boolean(String(ownerProfile.value?.id || props.spot?.owner_id || '').trim())
})

function prevImage() {
  if (!images.value.length) return
  imageIndex.value = (imageIndex.value - 1 + images.value.length) % images.value.length
}

function nextImage() {
  if (!images.value.length) return
  imageIndex.value = (imageIndex.value + 1) % images.value.length
}

function onImageError() {
  props.onNotify({
    level: 'warning',
    title: 'Invalid Image',
    message: 'This spot image cannot be displayed.',
  })
}

async function submitShare() {
  if (!props.canShare || typeof props.onShare !== 'function') return
  const ok = await props.onShare(shareText.value)
  if (ok) {
    shareText.value = ''
  }
}

async function refreshOwnerProfile() {
  ownerProfile.value = null
  ownerBusy.value = false

  const ownerId = String(props.spot?.owner_id || '').trim()
  if (!props.open || !ownerId || typeof props.onLoadUserProfile !== 'function') {
    return
  }

  const runId = ++ownerLoadRun
  ownerBusy.value = true

  try {
    const profile = await props.onLoadUserProfile(ownerId)
    if (runId !== ownerLoadRun) return
    ownerProfile.value = profile && typeof profile === 'object' ? profile : null
  } finally {
    if (runId === ownerLoadRun) {
      ownerBusy.value = false
    }
  }
}

function openOwnerProfile() {
  if (typeof props.onOpenOwnerProfile !== 'function') return
  const ownerId = String(ownerProfile.value?.id || props.spot?.owner_id || '').trim()
  if (!ownerId) return
  props.onOpenOwnerProfile(ownerId)
}

function editSpot() {
  if (typeof props.onEdit === 'function') {
    props.onEdit()
  }
}

function deleteSpot() {
  if (typeof props.onDelete === 'function') {
    props.onDelete()
  }
}

function toggleFavorite() {
  if (!props.canFavorite) return
  props.onToggleFavorite()
}

function goToSpot() {
  if (typeof props.onGoToSpot !== 'function') return
  props.onGoToSpot(props.spot)
}
</script>

<template>
  <Teleport to="body">
    <div class="modal" v-if="open && spot">
      <div class="modal__backdrop" @click="onClose" />
      <div class="modal__content card border-0 shadow-lg">
        <header class="modal__header">
          <h3 class="h4 mb-0">{{ spot.title }}</h3>
          <ActionButton
            class-name="btn btn-outline-secondary btn-sm"
            icon="bi-x-lg"
            :icon-only="true"
            aria-label="Close details"
            @click="onClose"
          />
        </header>

      <p class="text-secondary mb-0">{{ spot.description || 'No description' }}</p>
      <p class="text-secondary mb-0">
        <i class="bi bi-geo-alt me-1"></i>{{ Number(spot.lat).toFixed(6) }}, {{ Number(spot.lon).toFixed(6) }}
      </p>
      <p class="text-secondary mb-0">
        <i class="bi bi-shield-lock me-1"></i>{{ String(spot.visibility || 'public').replace('_', ' ') }}
      </p>

      <section class="spot-owner-box">
        <span class="small text-secondary">Created by</span>
        <UserProfileCard
          :title="ownerTitle"
          :subtitle="ownerSubtitle"
          :avatar="ownerAvatar"
          :details="ownerDetails"
          :compact="true"
        >
          <template #actions>
            <ActionButton
              v-if="ownerProfileLinkVisible"
              class-name="btn btn-sm btn-outline-secondary"
              icon="bi-person-badge"
              label="Profile"
              @click="openOwnerProfile"
            />
          </template>
        </UserProfileCard>
      </section>

      <div class="tag-row">
        <span v-for="t in spot.tags" :key="t" class="tag">{{ t }}</span>
      </div>

      <div class="image-viewer" v-if="images.length">
        <img :src="currentImage" alt="spot image" @error="onImageError" loading="lazy" />
        <div class="viewer-actions">
          <ActionButton class-name="btn btn-outline-secondary" label="Prev" @click="prevImage" />
          <span class="text-secondary small">{{ imageIndex + 1 }} / {{ images.length }}</span>
          <ActionButton class-name="btn btn-outline-secondary" label="Next" @click="nextImage" />
        </div>
      </div>

      <div class="share-box" v-if="canShare">
        <input class="form-control" v-model="shareText" maxlength="300" placeholder="Share message (optional)" />
        <ActionButton class-name="btn btn-outline-primary" icon="bi-send" label="Share" @click="submitShare" />
      </div>

      <footer class="modal__footer">
        <div class="d-flex flex-wrap gap-2">
          <ActionButton
            v-if="typeof onGoToSpot === 'function'"
            class-name="btn btn-outline-primary"
            icon="bi-signpost-2"
            label="Go to"
            @click="goToSpot"
          />
          <ActionButton
            class-name="btn btn-outline-warning"
            :icon="isFavorite ? 'bi-heartbreak' : 'bi-heart'"
            :label="isFavorite ? 'Unlike' : 'Like'"
            :disabled="favoriteBusy || !canFavorite"
            @click="toggleFavorite"
          />
        </div>

        <div class="d-flex flex-wrap justify-content-end gap-2">
          <ActionButton class-name="btn btn-outline-secondary" label="Edit" v-if="canEdit" @click="editSpot" />
          <ActionButton class-name="btn btn-danger" label="Delete" v-if="canDelete" @click="deleteSpot" />
        </div>
      </footer>

      </div>
    </div>
  </Teleport>
</template>
