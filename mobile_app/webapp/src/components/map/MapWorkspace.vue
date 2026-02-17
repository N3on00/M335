<script setup>
import { computed, nextTick, reactive, ref, watch } from 'vue'

import LeafletSpotMap from './LeafletSpotMap.vue'
import SpotEditorModal from './SpotEditorModal.vue'
import SpotDetailsModal from './SpotDetailsModal.vue'
import SpotSearchWidget from './SpotSearchWidget.vue'
import LocationSearchWidget from './LocationSearchWidget.vue'
import SpotMiniCard from '../common/SpotMiniCard.vue'
import ActionButton from '../common/ActionButton.vue'
import {
  createFilterSubscription,
  createSubscriptionSnapshot,
  normalizeFilterSubscription,
} from '../../models/spotSubscriptions'
import { buildSpotSharePayload } from '../../models/spotSharePayload'
import { resolveGoToSpot } from '../../models/mapSpotNavigation'
import { useOwnerProfiles } from '../../composables/useOwnerProfiles'

const SPOT_PAGE_SIZE = 10

const props = defineProps({
  state: { type: Object, required: true },
  focusRequest: { type: Object, default: () => ({ lat: null, lon: null, spotId: '' }) },
  behavior: { type: Object, required: true },
})

const { ownerLabel, ownerSearchText, warmOwnerProfiles } = useOwnerProfiles(
  (ownerId) => props.behavior.loadUserProfile(ownerId),
)

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

function normalizeSubscriptionForUser(entry, fallbackOwnerUserId = '') {
  const normalized = normalizeFilterSubscription(entry)
  if (!normalized) return null

  const ownerUserId = String(normalized.ownerUserId || '').trim() || String(fallbackOwnerUserId || '').trim()
  return {
    ...normalized,
    ownerUserId,
  }
}

function ownedSubscriptions(entries, ownerUserId) {
  const owner = String(ownerUserId || '').trim()
  if (!owner) return []

  return (Array.isArray(entries) ? entries : [])
    .map((entry) => normalizeSubscriptionForUser(entry, owner))
    .filter(Boolean)
    .filter((entry) => String(entry.ownerUserId || '').trim() === owner)
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
const mapViewportAnchor = ref(null)
const visibleSpotCount = ref(SPOT_PAGE_SIZE)
const spotResultsExpanded = ref(true)
const lastFocusSignature = ref('')

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

const currentUserId = computed(() => String(props.state.session?.user?.id || '').trim())
const favoritesSet = computed(() => new Set((props.state.favorites || []).map((id) => String(id))))
const filterSubscriptions = computed(() => {
  const ownerUserId = currentUserId.value
  if (!ownerUserId) return []

  return ownedSubscriptions(props.state.map?.filterSubscriptions, ownerUserId)
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
  const ownerUserId = currentUserId.value
  if (!ownerUserId) {
    props.behavior.notify({
      level: 'warning',
      title: 'Sign in required',
      message: 'Please sign in again before creating filter subscriptions.',
    })
    return
  }

  const baselineSnapshot = createSubscriptionSnapshot(filteredSpots.value)

  const sub = createFilterSubscription({
    filters: spotFilters,
    center: currentSubscriptionCenter(),
    label: '',
    snapshot: baselineSnapshot,
    ownerUserId,
  })

  const out = ownedSubscriptions(props.state.map?.filterSubscriptions, ownerUserId)

  const signature = JSON.stringify({ filters: sub.filters, center: sub.center })
  const alreadyExists = out
    .some((entry) => JSON.stringify({ filters: entry.filters, center: entry.center }) === signature)
  if (alreadyExists) {
    props.behavior.notify({
      level: 'info',
      title: 'Already subscribed',
      message: 'This filter is already in your subscriptions.',
    })
    return
  }

  out.push(sub)
  props.state.map.filterSubscriptions = out

  props.behavior.notify({
    level: 'success',
    title: 'Filter subscribed',
    message: `Saved current result (${Object.keys(baselineSnapshot).length} spots) for: ${sub.label}`,
    details: 'You will only get alerts for newly matching spots or changed matching spots.',
  })
}

function removeFilterSubscription(subId) {
  const ownerUserId = currentUserId.value
  const next = ownedSubscriptions(props.state.map?.filterSubscriptions, ownerUserId)
    .filter((entry) => {
      const isSameOwner = String(entry.ownerUserId || '').trim() === ownerUserId
      const isTarget = String(entry.id || '') === String(subId || '')
      return !(isSameOwner && isTarget)
    })

  props.state.map.filterSubscriptions = next

  props.behavior.notify({
    level: 'info',
    title: 'Subscription removed',
    message: 'This map filter subscription was deleted.',
  })
}

function applyFilterSubscription(subscription) {
  const sub = normalizeSubscriptionForUser(subscription, currentUserId.value)
  if (!sub) return
  if (String(sub.ownerUserId || '').trim() !== currentUserId.value) return

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

  props.behavior.notify({
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
  detailsOpen.value = false
  const target = resolveGoToSpot(spot, props.state.map.zoom, 14)
  if (!target) {
    selectedSpot.value = spot
    return
  }

  props.state.map.center = target.center
  props.state.map.zoom = target.zoom

  selectedSpot.value = spot
  void nextTick(() => {
    scrollMapIntoView()
  })
}

function scrollMapIntoView() {
  const host = mapViewportAnchor.value
  if (!host || typeof host.scrollIntoView !== 'function') {
    return
  }

  const reduceMotion = typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  host.scrollIntoView({
    behavior: reduceMotion ? 'auto' : 'smooth',
    block: 'start',
    inline: 'nearest',
  })
}

function onViewportChange(center, zoom) {
  props.state.map.center = center
  props.state.map.zoom = zoom
}

async function saveSpot(spot) {
  const ok = await props.behavior.saveSpot(spot)
  if (!ok) return
  editorOpen.value = false
}

async function deleteSpot() {
  if (!selectedSpot.value?.id) return
  const ok = await props.behavior.deleteSpot(selectedSpot.value.id)
  if (!ok) return
  detailsOpen.value = false
}

async function toggleFavorite() {
  if (!selectedSpot.value?.id) return
  await props.behavior.toggleFavorite(selectedSpot.value.id, isFavorite(selectedSpot.value))
}

async function toggleFavoriteForSpot(spot) {
  if (!spot?.id) return
  await props.behavior.toggleFavorite(String(spot.id), isFavorite(spot))
}

async function shareSpot(message) {
  const spot = selectedSpot.value
  const spotId = String(spot?.id || '').trim()
  if (!spotId) return false

  const sharePayload = buildSpotSharePayload(
    spot,
    message,
    typeof window !== 'undefined' ? window.location.origin : '',
  )

  const backendShared = await props.behavior.shareSpot(spotId, String(message || ''))
  const externalShareResult = await shareExternally(sharePayload)

  if (externalShareResult === 'copied') {
    props.behavior.notify({
      level: 'info',
      title: 'Link copied',
      message: 'Spot link copied to clipboard.',
    })
  }

  if (!backendShared && (externalShareResult === 'shared' || externalShareResult === 'copied')) {
    props.behavior.notify({
      level: 'warning',
      title: 'Shared locally only',
      message: 'Spot was shared from this device, but backend share logging failed.',
    })
    return true
  }

  return backendShared
}

async function shareExternally(payload) {
  if (typeof navigator === 'undefined') return ''

  if (typeof navigator.share === 'function') {
    try {
      await navigator.share(payload)
      return 'shared'
    } catch (error) {
      if (String(error?.name || '') === 'AbortError') {
        return 'cancelled'
      }
    }
  }

  const shareUrl = String(payload?.url || '').trim()
  if (shareUrl && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
    try {
      await navigator.clipboard.writeText(shareUrl)
      return 'copied'
    } catch {
      return ''
    }
  }

  return ''
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
  props.behavior.notify({
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
  props.behavior.openProfile(nextId)
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
    const out = await props.behavior.searchLocations(query, 7)
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

  props.behavior.notify({
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

async function onReload() {
  await props.behavior.reload()
}

function onSearchUsers(query, limit = 20) {
  return props.behavior.searchUsers(query, limit)
}

function onLoadFriendUsers() {
  return props.behavior.loadFriendUsers()
}

function onLoadUserProfile(userId) {
  return props.behavior.loadUserProfile(userId)
}

function onNotify(payload) {
  props.behavior.notify(payload)
}
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
      :initial-expanded="false"
      @update:filters="updateSpotFilters"
      @reset="resetSpotFilters"
      @subscribe="subscribeCurrentFilters"
      @apply-subscription="applyFilterSubscription"
      @remove-subscription="removeFilterSubscription"
    />

    <section class="card border-0 shadow-sm map-widget-card" data-aos="fade-up" data-aos-delay="65">
      <div class="card-body d-grid gap-2 p-3">
        <header class="d-flex flex-wrap align-items-start justify-content-between gap-2">
          <div>
            <h3 class="h6 mb-1">Spot search results</h3>
            <p class="small text-secondary mb-0">Results are grouped directly under the spot search card.</p>
          </div>

          <ActionButton
            class-name="btn btn-sm btn-outline-secondary"
            :icon="spotResultsExpanded ? 'bi-chevron-up' : 'bi-chevron-down'"
            :label="spotResultsExpanded ? 'Collapse results' : `Expand results (${filteredSpots.length})`"
            :disabled="!filteredSpots.length"
            @click="spotResultsExpanded = !spotResultsExpanded"
          />
        </header>

        <div class="small text-secondary" v-if="!filteredSpots.length">
          No spots match your current filters.
        </div>

        <template v-else-if="spotResultsExpanded">
          <div class="small text-secondary">Tap a card to open full details.</div>

          <div class="spot-feed map-spot-feed">
            <SpotMiniCard
              v-for="spot in listedSpots"
              :key="`map-list-${spot.id}`"
              :spot="spot"
              :owner-label="ownerLabel(spot)"
              :distance-label="spotDistanceLabel(spot)"
              :interactive="true"
              @open="openSpotFromList"
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
        </template>

        <div class="small text-secondary" v-else>
          {{ filteredSpots.length }} result(s) hidden. Expand to view.
        </div>
      </div>
    </section>

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

    <div ref="mapViewportAnchor">
      <LeafletSpotMap
        :spots="filteredSpots"
        :center="state.map.center"
        :zoom="state.map.zoom"
        :on-map-tap="onMapTap"
        :on-marker-select="onMarkerSelect"
        :on-viewport-change="onViewportChange"
      />
    </div>

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
