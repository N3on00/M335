<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import { firstImageSource } from '../../models/imageMapper'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
})

const props = defineProps({
  spots: { type: Array, default: () => [] },
  center: { type: Array, default: () => [47.3769, 8.5417] },
  zoom: { type: Number, default: 12 },
  onMapTap: { type: Function, required: true },
  onMarkerSelect: { type: Function, required: true },
  onViewportChange: { type: Function, required: true },
})

const host = ref(null)
let map = null
let markersLayer = null
let wheelAt = 0
let pointer = null
const previewIconCache = new Map()

function escapeHtmlAttr(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function previewMarkerIcon(imageSrc) {
  const key = String(imageSrc || '').trim()
  if (!key) return null

  if (previewIconCache.has(key)) {
    return previewIconCache.get(key)
  }

  const safeSrc = escapeHtmlAttr(key)
  const icon = L.divIcon({
    className: 'spot-preview-marker',
    html: `<div class="spot-preview-marker__card"><img class="spot-preview-marker__backdrop" src="${safeSrc}" alt="" loading="lazy" /><img class="spot-preview-marker__image" src="${safeSrc}" alt="spot preview" loading="lazy" /></div><div class="spot-preview-marker__tip"></div>`,
    iconSize: [62, 76],
    iconAnchor: [31, 72],
  })

  previewIconCache.set(key, icon)
  return icon
}

function syncMarkers() {
  if (!markersLayer) return
  markersLayer.clearLayers()

  for (const spot of props.spots) {
    if (!spot || typeof spot !== 'object') continue
    const lat = Number(spot.lat)
    const lon = Number(spot.lon)
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue

    const preview = firstImageSource(spot.images)
    const icon = preview ? previewMarkerIcon(preview) : null
    const marker = icon
      ? L.marker([lat, lon], { icon })
      : L.marker([lat, lon])

    marker.on('click', () => props.onMarkerSelect(spot))
    marker.addTo(markersLayer)
  }
}

function shouldIgnoreTap(ev) {
  if (Date.now() - wheelAt < 350) {
    return true
  }
  if (!pointer) {
    return false
  }
  const dt = Date.now() - pointer.t
  const dx = Math.abs((ev.originalEvent?.clientX || 0) - pointer.x)
  const dy = Math.abs((ev.originalEvent?.clientY || 0) - pointer.y)
  const moved = Math.sqrt(dx * dx + dy * dy)
  return dt > 450 || moved > 12 || pointer.moved
}

onMounted(() => {
  map = L.map(host.value, {
    zoomControl: true,
    scrollWheelZoom: true,
  }).setView(props.center, props.zoom)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 20,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map)

  markersLayer = L.layerGroup().addTo(map)
  syncMarkers()

  map.on('wheel', () => {
    wheelAt = Date.now()
  })

  map.on('mousedown', (ev) => {
    pointer = {
      x: ev.originalEvent?.clientX || 0,
      y: ev.originalEvent?.clientY || 0,
      t: Date.now(),
      moved: false,
    }
  })

  map.on('mousemove', (ev) => {
    if (!pointer) return
    const dx = Math.abs((ev.originalEvent?.clientX || 0) - pointer.x)
    const dy = Math.abs((ev.originalEvent?.clientY || 0) - pointer.y)
    if (Math.sqrt(dx * dx + dy * dy) > 10) {
      pointer.moved = true
    }
  })

  map.on('moveend zoomend', () => {
    const c = map.getCenter()
    props.onViewportChange([c.lat, c.lng], map.getZoom())
  })

  map.on('dragstart zoomstart', () => {
    if (pointer) {
      pointer.moved = true
    }
  })

  map.on('click', (ev) => {
    const ignore = shouldIgnoreTap(ev)
    pointer = null
    if (ignore) {
      return
    }
    props.onMapTap(ev.latlng.lat, ev.latlng.lng)
  })
})

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})

watch(
  () => props.spots,
  () => {
    syncMarkers()
  },
  { deep: true },
)

watch(
  () => [props.center[0], props.center[1], props.zoom],
  () => {
    if (!map) return
    const center = map.getCenter()
    const z = map.getZoom()
    if (
      Math.abs(center.lat - props.center[0]) > 0.000001 ||
      Math.abs(center.lng - props.center[1]) > 0.000001 ||
      z !== props.zoom
    ) {
      map.setView(props.center, props.zoom)
    }
  },
)
</script>

<template>
  <div class="leaflet-map" ref="host" data-aos="zoom-in" data-aos-delay="80" />
</template>
