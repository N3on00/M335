<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

import LeafletSpotMap from './LeafletSpotMap.vue'
import SpotEditorModal from './SpotEditorModal.vue'
import SpotDetailsModal from './SpotDetailsModal.vue'
import SpotSearchWidget from './SpotSearchWidget.vue'
import LocationSearchWidget from './LocationSearchWidget.vue'
import SpotMiniCard from '../common/SpotMiniCard.vue'
import ActionButton from '../common/ActionButton.vue'
import { createFilterSubscription, normalizeFilterSubscription } from '../../models/spotSubscriptions'

const SPOT_PAGE_SIZE = 10

const props = defineProps({
  state: { type: Object, required: true },
  focusRequest: { type: Object, default: () => ({ lat: null, lon: null, spotId: '' }) },
  onInit: { type: Function, required: true },
  onReload: { type: Function, required: true },
  onSaveSpot: { type: Function, required: true },
  onDeleteSpot: { type: Function, required: true },
  onToggleFavorite: { type: Function, required: true },
  onShareSpot: { type: Function, required: true },
  onSearchUsers: { type: Function, required: true },
  onLoadFriendUsers: { type: Function, required: true },
  onLoadUserProfile: { type: Function, required: true },
  onSearchLocations: { type: Function, required: true },
  onOpenProfile: { type: Function, required: true },
  onNotify: { type: Function, required: true },
})

function defaultSpotFilters() {
  return {
    text: '',
    tagsText: '',
    ownerText: '',
    visibility: 'all',
    onlyFavorites: false,
    radiusKm: 0,
  }
}

function normalizeVisibility(value) {
  const next = String(value || '').trim().toLowerCase()
  if (next === 'public' || next === 'following' || next === 'invite_only' || next === 'personal') {
    return next
  }
  return 'all'
}

function sanitizeSpotFilters(source) {
  const src = source && typeof source === 'object' ? source : {}
  return {
    text: String(src.text || '').trim(),
    tagsText: String(src.tagsText || '').trim(),
    ownerText: String(src.ownerText || '').trim(),
    visibility: normalizeVisibility(src.visibility || 'all'),
    onlyFavorites: Boolean(src.onlyFavorites),
    radiusKm: Math.max(0, Number(src.radiusKm) || 0),
  }
}

const detailsOpen = ref(false)
const editorOpen = ref(false)
const editorMode = ref('create')
const pickMode = ref(false)
const selectedSpot = ref(null)

const locationQuery = ref('')
const locationSearchBusy = ref(false)
const locationSearchError = ref('')
const locationResults = ref([])
const activeLocation = ref(null)
const visibleSpotCount = ref(SPOT_PAGE_SIZE)
const lastFocusSignature = ref('')

const ownerProfiles = reactive({})
const ownerLoading = reactive({})

const editorDraft = reactive({
  id: '',
  title: '',
  description: '',
  tags: [],
  lat: 47.3769,
  lon: 8.5417,
  images: [],
  visibility: 'public',
  invite_user_ids: [],
})

const spotFilters = reactive(defaultSpotFilters())

const favoritesSet = computed(() => new Set((props.state.favorites || []).map((id) => String(id))))
const filterSubscriptions = computed(() => {
  const source = Array.isArray(props.state.map?.filterSubscriptions)
    ? props.state.map.filterSubscriptions
    : []
  return source
    .map((entry) => normalizeFilterSubscription(entry))
    .filter(Boolean)
})

const selectedSpotIsOwner = computed(() => {
  const meId = String(props.state.session?.user?.id || '').trim()
  const ownerId = String(selectedSpot.value?.owner_id || '').trim()
  return Boolean(meId && ownerId && meId === ownerId)
})

const hasActiveSpotFilters = computed(() => {
  return Boolean(
    spotFilters.text
    || spotFilters.tagsText
    || spotFilters.ownerText
    || spotFilters.visibility !== 'all'
    || spotFilters.onlyFavorites
    || Number(spotFilters.radiusKm || 0) > 0,
  )
})

const activeLocationLabel = computed(() => String(activeLocation.value?.label || ''))

const filteredSpots = computed(() => {
  const allSpots = Array.isArray(props.state.spots) ? props.state.spots : []
  const text = String(spotFilters.text || '').toLowerCase()
  const ownerText = String(spotFilters.ownerText || '').toLowerCase()
  const visibility = String(spotFilters.visibility || 'all')
  const requiredTags = tokenize(spotFilters.tagsText)
  const radiusKm = Number(spotFilters.radiusKm || 0)
  const center = radiusCenter()

  return allSpots.filter((spot) => {
    if (!spot || typeof spot !== 'object') return false

    if (spotFilters.onlyFavorites && !isFavorite(spot)) {
      return false
    }

    if (visibility !== 'all' && String(spot.visibility || 'public') !== visibility) {
      return false
    }

    if (text) {
      const haystack = [
        spot?.title,
        spot?.description,
        ...(Array.isArray(spot?.tags) ? spot.tags : []),
      ]
        .map((value) => String(value || '').toLowerCase())
        .join(' ')
      if (!haystack.includes(text)) {
        return false
      }
    }

    if (requiredTags.length) {
      const tags = (Array.isArray(spot?.tags) ? spot.tags : []).map((tag) => String(tag || '').toLowerCase())
      const hasAll = requiredTags.every((requested) => tags.some((tag) => tag.includes(requested)))
      if (!hasAll) {
        return false
      }
    }

    if (ownerText && !ownerSearchText(spot).includes(ownerText)) {
      return false
    }

    if (radiusKm > 0 && center) {
      const distance = distanceKm(
        Number(spot?.lat || 0),
        Number(spot?.lon || 0),
        center[0],
        center[1],
      )
      if (!Number.isFinite(distance) || distance > radiusKm) {
        return false
      }
    }

    return true
  })
})

const listedSpots = computed(() => filteredSpots.value.slice(0, visibleSpotCount.value))

const remainingSpotCount = computed(() => {
  return Math.max(0, filteredSpots.value.length - listedSpots.value.length)
})

const canLoadMoreSpots = computed(() => remainingSpotCount.value > 0)

const ownerIdsSignature = computed(() => {
  const ids = [...new Set(
    (Array.isArray(props.state.spots) ? props.state.spots : [])
      .map((spot) => String(spot?.owner_id || '').trim())
      .filter(Boolean),
  )]
    .sort()
  return ids.join('|')
})

watch(
  () => ownerIdsSignature.value,
  () => {
    void warmOwnerProfiles(props.state.spots)
  },
  { immediate: true },
)

watch(
  () => props.state.spots,
  () => {
    if (!selectedSpot.value?.id) return
    const next = (props.state.spots || []).find((spot) => String(spot?.id || '') === String(selectedSpot.value?.id || ''))
    if (next) {
      selectedSpot.value = next
    }
  },
  { deep: true },
)

watch(
  () => props.focusRequest,
  (next) => {
    applyFocusRequest(next)
  },
  { deep: true, immediate: true },
)

function tokenize(text) {
  return String(text || '')
    .toLowerCase()
    .split(/[\s,]+/)
    .map((entry) => entry.trim())
    .filter(Boolean)
}

function ownerSearchText(spot) {
  const ownerId = String(spot?.owner_id || '').trim()
  const profile = ownerId ? ownerProfiles[ownerId] : null
  return [ownerId, profile?.username, profile?.display_name, profile?.email]
    .map((entry) => String(entry || '').toLowerCase())
    .join(' ')
}

function ownerLabel(spot) {
  const ownerId = String(spot?.owner_id || '').trim()
  if (!ownerId) return 'unknown creator'

  if (ownerLoading[ownerId]) {
    return 'loading creator...'
  }

  const profile = ownerProfiles[ownerId]
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

function radiusCenter() {
  if (activeLocation.value) {
    return [Number(activeLocation.value.lat), Number(activeLocation.value.lon)]
  }

  const center = Array.isArray(props.state.map?.center) ? props.state.map.center : []
  if (center.length >= 2 && Number.isFinite(Number(center[0])) && Number.isFinite(Number(center[1]))) {
    return [Number(center[0]), Number(center[1])]
  }

  return null
}

function distanceKm(latA, lonA, latB, lonB) {
  const dLat = (latB - latA) * (Math.PI / 180)
  const dLon = (lonB - lonA) * (Math.PI / 180)
  const radLatA = latA * (Math.PI / 180)
  const radLatB = latB * (Math.PI / 180)
  const a = Math.sin(dLat / 2) ** 2
    + Math.cos(radLatA) * Math.cos(radLatB) * Math.sin(dLon / 2) ** 2
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return 6371 * c
}

function spotDistanceLabel(spot) {
  const center = radiusCenter()
  if (!center) return ''

  const distance = distanceKm(
    Number(spot?.lat || 0),
    Number(spot?.lon || 0),
    center[0],
    center[1],
  )
  if (!Number.isFinite(distance)) return ''

  if (distance >= 10) {
    return `${distance.toFixed(0)} km away`
  }
  return `${distance.toFixed(1)} km away`
}

function isFavorite(spot) {
  const spotId = String(spot?.id || '').trim()
  return Boolean(spotId && favoritesSet.value.has(spotId))
}

function updateSpotFilters(next) {
  Object.assign(spotFilters, sanitizeSpotFilters(next))
  visibleSpotCount.value = SPOT_PAGE_SIZE
}

function resetSpotFilters() {
  Object.assign(spotFilters, defaultSpotFilters())
  visibleSpotCount.value = SPOT_PAGE_SIZE
}

function focusSignature(input) {
  const src = input && typeof input === 'object' ? input : {}
  const lat = Number(src.lat)
  const lon = Number(src.lon)
  const spotId = String(src.spotId || '').trim()
  return [
    Number.isFinite(lat) ? lat.toFixed(6) : '',
    Number.isFinite(lon) ? lon.toFixed(6) : '',
    spotId,
  ].join('|')
}

function applyFocusRequest(input) {
  const sig = focusSignature(input)
  if (!sig || sig === '||' || lastFocusSignature.value === sig) {
    return
  }

  const src = input && typeof input === 'object' ? input : {}
  const lat = Number(src.lat)
  const lon = Number(src.lon)
  const spotId = String(src.spotId || '').trim()

  if (Number.isFinite(lat) && Number.isFinite(lon)) {
    props.state.map.center = [lat, lon]
    props.state.map.zoom = Math.max(14, Number(props.state.map.zoom || 12))
  }

  if (spotId) {
    const spot = (Array.isArray(props.state.spots) ? props.state.spots : [])
      .find((entry) => String(entry?.id || '').trim() === spotId)
    if (spot) {
      selectedSpot.value = spot
      detailsOpen.value = true
    }
  }

  lastFocusSignature.value = sig
}

function currentSubscriptionCenter() {
  if (activeLocation.value) {
    return {
      lat: Number(activeLocation.value.lat),
      lon: Number(activeLocation.value.lon),
      label: String(activeLocation.value.label || ''),
    }
  }

  const center = Array.isArray(props.state.map?.center) ? props.state.map.center : []
  if (center.length < 2) return null

  const lat = Number(center[0])
  const lon = Number(center[1])
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null

  return {
    lat,
    lon,
    label: '',
  }
}

function subscribeCurrentFilters() {
  const sub = createFilterSubscription({
    filters: spotFilters,
    center: currentSubscriptionCenter(),
    label: '',
  })

  const out = Array.isArray(props.state.map.filterSubscriptions)
    ? [...props.state.map.filterSubscriptions]
    : []

  const signature = JSON.stringify({ filters: sub.filters, center: sub.center })
  const alreadyExists = out
    .map((entry) => normalizeFilterSubscription(entry))
    .filter(Boolean)
    .some((entry) => JSON.stringify({ filters: entry.filters, center: entry.center }) === signature)
  if (alreadyExists) {
    props.onNotify({
      level: 'info',
      title: 'Already subscribed',
      message: 'This filter is already in your subscriptions.',
    })
    return
  }

  out.push(sub)
  props.state.map.filterSubscriptions = out

  props.onNotify({
    level: 'success',
    title: 'Filter subscribed',
    message: `You will be notified about updates for: ${sub.label}`,
  })
}

function removeFilterSubscription(subId) {
  const source = Array.isArray(props.state.map.filterSubscriptions)
    ? props.state.map.filterSubscriptions
    : []
  const next = source.filter((entry) => String(entry?.id || '') !== String(subId || ''))
  props.state.map.filterSubscriptions = next

  props.onNotify({
    level: 'info',
    title: 'Subscription removed',
    message: 'This map filter subscription was deleted.',
  })
}

function applyFilterSubscription(subscription) {
  const sub = normalizeFilterSubscription(subscription)
  if (!sub) return

  Object.assign(spotFilters, sanitizeSpotFilters(sub.filters))

  if (sub.center) {
    activeLocation.value = {
      id: `sub-${sub.id}`,
      label: String(sub.center.label || 'Subscribed area'),
      lat: Number(sub.center.lat),
      lon: Number(sub.center.lon),
      type: 'subscription',
    }
    props.state.map.center = [Number(sub.center.lat), Number(sub.center.lon)]
    props.state.map.zoom = Math.max(14, Number(props.state.map.zoom || 12))
  } else {
    activeLocation.value = null
  }

  visibleSpotCount.value = SPOT_PAGE_SIZE

  props.onNotify({
    level: 'info',
    title: 'Subscription applied',
    message: `Applied filter: ${sub.label}`,
  })
}

function updateLocationQuery(next) {
  locationQuery.value = String(next || '')
}

function startCreateAt(lat, lon) {
  editorMode.value = 'create'
  detailsOpen.value = false
  Object.assign(editorDraft, {
    id: '',
    title: '',
    description: '',
    tags: [],
    lat,
    lon,
    images: [],
    visibility: 'public',
    invite_user_ids: [],
  })
  editorOpen.value = true
}

function openEditorFromSpot(spot) {
  if (!spot) return

  editorMode.value = 'edit'
  Object.assign(editorDraft, {
    id: spot.id || '',
    title: spot.title || '',
    description: spot.description || '',
    tags: [...(spot.tags || [])],
    lat: Number(spot.lat || 0),
    lon: Number(spot.lon || 0),
    images: [...(spot.images || [])],
    visibility: String(spot.visibility || 'public'),
    invite_user_ids: [...(spot.invite_user_ids || [])],
  })
  editorOpen.value = true
}

function onMapTap(lat, lon) {
  if (pickMode.value && editorOpen.value) {
    editorDraft.lat = lat
    editorDraft.lon = lon
    pickMode.value = false
    return
  }

  if (pickMode.value) {
    editorDraft.lat = lat
    editorDraft.lon = lon
    pickMode.value = false
    editorOpen.value = true
    return
  }

  startCreateAt(lat, lon)
}

function onMarkerSelect(spot) {
  selectedSpot.value = spot
  detailsOpen.value = true
}

function openSpotFromList(spot) {
  selectedSpot.value = spot
  detailsOpen.value = true
}

function goToSpot(spot) {
  const lat = Number(spot?.lat)
  const lon = Number(spot?.lon)
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return

  props.state.map.center = [lat, lon]
  props.state.map.zoom = Math.max(14, Number(props.state.map.zoom || 12))

  selectedSpot.value = spot
  detailsOpen.value = true
}

function onViewportChange(center, zoom) {
  props.state.map.center = center
  props.state.map.zoom = zoom
}

async function saveSpot(spot) {
  const ok = await props.onSaveSpot(spot)
  if (!ok) return
  editorOpen.value = false
  await props.onReload()
}

async function deleteSpot() {
  if (!selectedSpot.value?.id) return
  const ok = await props.onDeleteSpot(selectedSpot.value.id)
  if (!ok) return
  detailsOpen.value = false
  await props.onReload()
}

async function toggleFavorite() {
  if (!selectedSpot.value?.id) return
  await props.onToggleFavorite(selectedSpot.value.id, isFavorite(selectedSpot.value))
}

async function toggleFavoriteForSpot(spot) {
  if (!spot?.id) return
  await props.onToggleFavorite(String(spot.id), isFavorite(spot))
}

async function shareSpot(message) {
  if (!selectedSpot.value?.id) return false
  return props.onShareSpot(selectedSpot.value.id, message)
}

function pickLocationFromEditor(draft) {
  Object.assign(editorDraft, {
    id: draft.id || '',
    title: draft.title || '',
    description: draft.description || '',
    tags: [...(draft.tags || [])],
    lat: Number(draft.lat || 0),
    lon: Number(draft.lon || 0),
    images: [...(draft.images || [])],
    visibility: String(draft.visibility || 'public'),
    invite_user_ids: [...(draft.invite_user_ids || [])],
  })

  editorOpen.value = false
  pickMode.value = true
  props.onNotify({
    level: 'info',
    title: 'Pick location',
    message: 'Click on the map to set a new location.',
  })
}

function closeEditor() {
  editorOpen.value = false
  pickMode.value = false
}

function closeDetails() {
  detailsOpen.value = false
}

function editFromDetails() {
  detailsOpen.value = false
  openEditorFromSpot(selectedSpot.value)
}

function openOwnerProfile(userId) {
  const nextId = String(userId || '').trim()
  if (!nextId) return
  props.onOpenProfile(nextId)
}

async function searchLocations() {
  const query = String(locationQuery.value || '').trim()
  if (!query || locationSearchBusy.value) {
    return
  }

  locationSearchBusy.value = true
  locationSearchError.value = ''
  locationResults.value = []

  try {
    const out = await props.onSearchLocations(query, 7)
    const results = Array.isArray(out) ? out : []
    locationResults.value = results
    if (!results.length) {
      locationSearchError.value = 'No places matched this search.'
    }
  } catch (error) {
    locationSearchError.value = String(error?.message || error || 'Location search failed')
  } finally {
    locationSearchBusy.value = false
  }
}

function selectLocation(result) {
  if (!result) return

  activeLocation.value = result
  locationResults.value = []
  props.state.map.center = [Number(result.lat), Number(result.lon)]
  props.state.map.zoom = Math.max(14, Number(props.state.map.zoom || 12))
  visibleSpotCount.value = SPOT_PAGE_SIZE

  props.onNotify({
    level: 'info',
    title: 'Location selected',
    message: `Map moved to ${result.label}.`,
  })
}

function clearLocationFilter() {
  activeLocation.value = null
  visibleSpotCount.value = SPOT_PAGE_SIZE
}

function loadMoreSpots() {
  visibleSpotCount.value += SPOT_PAGE_SIZE
}

onMounted(async () => {
  try {
    await props.onInit()
    applyFocusRequest(props.focusRequest)
  } catch (e) {
    props.onNotify({
      level: 'error',
      title: 'Map init failed',
      message: 'Could not load map data from backend.',
      details: String(e?.message || e),
    })
  }
})
</script>

<template>
  <section class="map-workspace">
    <div class="card border-0 shadow-sm" data-aos="fade-up" data-aos-delay="40">
      <div class="card-body d-flex flex-wrap align-items-center gap-2">
        <ActionButton
          class-name="btn btn-primary"
          icon="bi-plus-circle"
          label="New spot"
          @click="startCreateAt(state.map.center[0], state.map.center[1])"
        />
        <ActionButton
          class-name="btn btn-outline-primary"
          icon="bi-arrow-repeat"
          label="Reload spots"
          @click="onReload"
        />
        <span class="badge-soft" v-if="pickMode">Pick mode active: click map</span>
      </div>
    </div>

    <SpotSearchWidget
      :filters="spotFilters"
      :active-location-label="activeLocationLabel"
      :result-count="filteredSpots.length"
      :total-count="state.spots.length"
      :can-reset="hasActiveSpotFilters"
      :subscriptions="filterSubscriptions"
      @update:filters="updateSpotFilters"
      @reset="resetSpotFilters"
      @subscribe="subscribeCurrentFilters"
      @apply-subscription="applyFilterSubscription"
      @remove-subscription="removeFilterSubscription"
    />

    <LocationSearchWidget
      :query="locationQuery"
      :busy="locationSearchBusy"
      :error-text="locationSearchError"
      :results="locationResults"
      :active-location="activeLocation"
      @update:query="updateLocationQuery"
      @search="searchLocations"
      @select="selectLocation"
      @clear="clearLocationFilter"
    />

    <LeafletSpotMap
      :spots="filteredSpots"
      :center="state.map.center"
      :zoom="state.map.zoom"
      :on-map-tap="onMapTap"
      :on-marker-select="onMarkerSelect"
      :on-viewport-change="onViewportChange"
    />

    <section class="card border-0 shadow-sm" data-aos="fade-up" data-aos-delay="70" v-if="filteredSpots.length">
      <div class="card-body d-grid gap-2 p-3">
        <div class="small text-secondary">Tap a card to open full details.</div>

        <div class="spot-feed map-spot-feed">
          <SpotMiniCard
            v-for="spot in listedSpots"
            :key="`map-list-${spot.id}`"
            :spot="spot"
            :owner-label="ownerLabel(spot)"
            :distance-label="spotDistanceLabel(spot)"
            :interactive="true"
            :show-go-to="true"
            @open="openSpotFromList"
            @go-to="goToSpot"
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
                  @click.stop="openSpotFromList(spot)"
                />
              </div>
            </template>
          </SpotMiniCard>
        </div>

        <div class="map-spot-feed__load-more" v-if="canLoadMoreSpots">
          <span class="map-spot-feed__bar" aria-hidden="true"></span>
          <ActionButton
            class-name="btn btn-sm btn-outline-primary"
            :label="`Load ${Math.min(SPOT_PAGE_SIZE, remainingSpotCount)} more (${remainingSpotCount} left)`"
            @click="loadMoreSpots"
          />
        </div>
      </div>
    </section>

    <section class="card border-0 shadow-sm" data-aos="fade-up" data-aos-delay="70" v-else>
      <div class="card-body text-secondary">
        No spots match your current filters.
      </div>
    </section>

    <SpotEditorModal
      :open="editorOpen"
      :mode="editorMode"
      :draft="editorDraft"
      :on-cancel="closeEditor"
      :on-submit="saveSpot"
      :on-pick-location="pickLocationFromEditor"
      :on-search-users="onSearchUsers"
      :on-load-friend-users="onLoadFriendUsers"
      :on-load-user-profile="onLoadUserProfile"
      :on-notify="onNotify"
    />

    <SpotDetailsModal
      :open="detailsOpen"
      :spot="selectedSpot"
      :is-favorite="isFavorite(selectedSpot)"
      :favorite-busy="state.loading.mapFavorite"
      :can-edit="selectedSpotIsOwner"
      :can-delete="selectedSpotIsOwner"
      :can-share="true"
      :on-close="closeDetails"
      :on-edit="editFromDetails"
      :on-delete="deleteSpot"
      :on-toggle-favorite="toggleFavorite"
      :on-share="shareSpot"
      :on-go-to-spot="goToSpot"
      :on-notify="onNotify"
      :on-load-user-profile="onLoadUserProfile"
      :on-open-owner-profile="openOwnerProfile"
    />
  </section>
</template>
