<script setup>
import { computed, reactive, ref, watch } from 'vue'
import ActionButton from '../common/ActionButton.vue'
import SpotDetailsModal from '../map/SpotDetailsModal.vue'
import SpotMiniCard from '../common/SpotMiniCard.vue'

const props = defineProps({
  spots: { type: Array, default: () => [] },
  favorites: { type: Array, default: () => [] },
  onOpenMap: { type: Function, required: true },
  onOpenSocial: { type: Function, required: true },
  onOpenSupport: { type: Function, required: true },
  onOpenSettings: { type: Function, required: true },
  onOpenProfile: { type: Function, required: true },
  onRefresh: { type: Function, required: true },
  onToggleFavorite: { type: Function, required: true },
  onLoadUserProfile: { type: Function, required: true },
  onNotify: { type: Function, required: true },
  refreshBusy: { type: Boolean, default: false },
})

const favoritesSet = computed(() => new Set((props.favorites || []).map((x) => String(x))))
const detailsOpen = ref(false)
const selectedSpot = ref(null)
const ownerProfiles = reactive({})
const ownerLoading = reactive({})

const listedSpots = computed(() => {
  return [...props.spots]
    .filter((spot) => spot && typeof spot === 'object')
    .sort((a, b) => String(a.title || '').localeCompare(String(b.title || '')))
})

watch(
  () => props.spots,
  (spots) => {
    void warmOwnerProfiles(spots)
  },
  { immediate: true, deep: true },
)

function isFavorite(spot) {
  const id = String(spot?.id || '')
  if (!id) return false
  return favoritesSet.value.has(id)
}

function ownerProfileOf(spot) {
  const ownerId = String(spot?.owner_id || '').trim()
  if (!ownerId) return null
  return ownerProfiles[ownerId] || null
}

function ownerLabel(spot) {
  const ownerId = String(spot?.owner_id || '').trim()
  if (!ownerId) return 'unknown creator'

  if (ownerLoading[ownerId]) {
    return 'loading creator...'
  }

  const profile = ownerProfileOf(spot)
  const username = String(profile?.username || '').trim()
  if (username) {
    return `@${username}`
  }

  const displayName = String(profile?.display_name || '').trim()
  if (displayName) {
    return displayName
  }

  return `id: ${ownerId}`
}

async function warmOwnerProfiles(spots) {
  const ownerIds = [...new Set(
    (Array.isArray(spots) ? spots : [])
      .map((spot) => String(spot?.owner_id || '').trim())
      .filter(Boolean),
  )]

  await Promise.all(
    ownerIds.map(async (ownerId) => {
      if (ownerLoading[ownerId]) return
      if (ownerId in ownerProfiles) return

      ownerLoading[ownerId] = true
      try {
        const profile = await props.onLoadUserProfile(ownerId)
        ownerProfiles[ownerId] = profile && typeof profile === 'object' ? profile : null
      } finally {
        ownerLoading[ownerId] = false
      }
    }),
  )
}

function openSpotDetails(spot) {
  selectedSpot.value = spot
  detailsOpen.value = true
}

function closeSpotDetails() {
  detailsOpen.value = false
}

async function toggleFavoriteForSpot(spot) {
  const spotId = String(spot?.id || '').trim()
  if (!spotId) return
  await props.onToggleFavorite(spotId, isFavorite(spot))
}

function openOwnerProfile(userId) {
  const ownerId = String(userId || '').trim()
  if (!ownerId) return
  props.onOpenProfile(ownerId)
}
</script>

<template>
  <section class="card border-0 shadow-sm" data-aos="fade-up" data-aos-delay="60">
    <div class="card-body d-grid gap-3 p-4">
      <header class="discover-header">
        <div>
          <h3 class="h4 mb-1">Discover Spots</h3>
          <p class="text-secondary mb-0">Browse all spots in a compact list without opening the map.</p>
        </div>
      </header>

      <div class="thumb-actions">
        <ActionButton
          label="Open map editor"
          icon="bi-map"
          class-name="btn btn-primary"
          @click="onOpenMap"
        />
        <ActionButton
          label="Socials"
          icon="bi-people"
          class-name="btn btn-outline-primary"
          @click="onOpenSocial"
        />
        <ActionButton
          label="Support"
          icon="bi-life-preserver"
          class-name="btn btn-outline-primary"
          @click="onOpenSupport"
        />
        <ActionButton
          label="My profile"
          icon="bi-person"
          class-name="btn btn-outline-primary"
          @click="onOpenProfile"
        />
        <ActionButton
          label="Settings"
          icon="bi-gear"
          class-name="btn btn-outline-primary"
          @click="onOpenSettings"
        />
        <ActionButton
          label="Refresh spots"
          icon="bi-arrow-repeat"
          :busy="refreshBusy"
          busy-label="Refreshing..."
          class-name="btn btn-outline-primary"
          @click="onRefresh"
        />
      </div>

      <div class="spot-feed" v-if="listedSpots.length">
        <SpotMiniCard
          v-for="spot in listedSpots"
          :key="spot.id || `${spot.title}-${spot.lat}-${spot.lon}`"
          :spot="spot"
          :owner-label="ownerLabel(spot)"
          :is-favorite="isFavorite(spot)"
          :interactive="true"
          @open="openSpotDetails"
        >
          <template #top-actions>
            <div class="spot-card-mini__quick-actions">
              <ActionButton
                :class-name="isFavorite(spot) ? 'btn btn-sm btn-warning' : 'btn btn-sm btn-outline-warning'"
                :icon="isFavorite(spot) ? 'bi-heart-fill' : 'bi-heart'"
                :icon-only="true"
                :aria-label="isFavorite(spot) ? 'Unlike spot' : 'Like spot'"
                @click.stop="toggleFavoriteForSpot(spot)"
              />
              <ActionButton
                class-name="btn btn-sm btn-outline-secondary"
                label="Details"
                @click.stop="openSpotDetails(spot)"
              />
            </div>
          </template>
        </SpotMiniCard>
      </div>

      <div class="text-secondary" v-else>
        No spots yet. Open the map editor to create your first spot.
      </div>

      <SpotDetailsModal
        :open="detailsOpen"
        :spot="selectedSpot"
        :is-favorite="isFavorite(selectedSpot)"
        :can-edit="false"
        :can-delete="false"
        :can-share="false"
        :on-close="closeSpotDetails"
        :on-toggle-favorite="() => toggleFavoriteForSpot(selectedSpot)"
        :on-notify="onNotify"
        :on-load-user-profile="onLoadUserProfile"
        :on-open-owner-profile="openOwnerProfile"
      />
    </div>
  </section>
</template>
