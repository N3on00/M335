function normalizeVisibility(value) {
  const out = String(value || '').trim().toLowerCase()
  if (out === 'public' || out === 'following' || out === 'invite_only' || out === 'personal') {
    return out
  }
  return 'all'
}

function sanitizeText(value) {
  return String(value || '').trim()
}

function sanitizeRadius(value) {
  return Math.max(0, Number(value) || 0)
}

function sanitizeCenter(center) {
  const src = center && typeof center === 'object' ? center : null
  if (!src) return null

  const lat = Number(src.lat)
  const lon = Number(src.lon)
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return null
  }

  return {
    lat,
    lon,
    label: sanitizeText(src.label),
  }
}

function sanitizeFilters(filters) {
  const src = filters && typeof filters === 'object' ? filters : {}
  return {
    text: sanitizeText(src.text),
    tagsText: sanitizeText(src.tagsText),
    ownerText: sanitizeText(src.ownerText),
    visibility: normalizeVisibility(src.visibility),
    onlyFavorites: Boolean(src.onlyFavorites),
    radiusKm: sanitizeRadius(src.radiusKm),
  }
}

function tokenize(text) {
  return String(text || '')
    .toLowerCase()
    .split(/[\s,]+/)
    .map((part) => part.trim())
    .filter(Boolean)
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

function defaultLabel(filters, center) {
  const parts = []
  if (center?.label) parts.push(center.label)
  if (filters.text) parts.push(`text: ${filters.text}`)
  if (filters.tagsText) parts.push(`tags: ${filters.tagsText}`)
  if (filters.ownerText) parts.push(`owner: ${filters.ownerText}`)
  if (filters.visibility !== 'all') parts.push(filters.visibility)
  if (filters.onlyFavorites) parts.push('favorites')
  if (filters.radiusKm > 0) parts.push(`${filters.radiusKm}km`)
  return parts.join(' | ') || 'All visible spots'
}

export function createFilterSubscription({ label = '', filters = {}, center = null } = {}) {
  const normalizedFilters = sanitizeFilters(filters)
  const normalizedCenter = sanitizeCenter(center)
  const normalizedLabel = sanitizeText(label) || defaultLabel(normalizedFilters, normalizedCenter)

  return {
    id: `sub-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    createdAt: new Date().toISOString(),
    label: normalizedLabel,
    filters: normalizedFilters,
    center: normalizedCenter,
  }
}

export function normalizeFilterSubscription(input) {
  if (!input || typeof input !== 'object') return null

  const id = sanitizeText(input.id)
  if (!id) return null

  const filters = sanitizeFilters(input.filters)
  const center = sanitizeCenter(input.center)
  const label = sanitizeText(input.label) || defaultLabel(filters, center)
  const createdAt = sanitizeText(input.createdAt) || new Date().toISOString()

  return {
    id,
    createdAt,
    label,
    filters,
    center,
  }
}

export function subscriptionMatchesSpot(subscription, spot, favoritesSet = new Set()) {
  if (!subscription || typeof subscription !== 'object') return false
  if (!spot || typeof spot !== 'object') return false

  const filters = sanitizeFilters(subscription.filters)
  const center = sanitizeCenter(subscription.center)

  const spotId = String(spot.id || '').trim()
  const title = String(spot.title || '')
  const description = String(spot.description || '')
  const visibility = String(spot.visibility || 'public')
  const tags = Array.isArray(spot.tags) ? spot.tags.map((x) => String(x || '').toLowerCase()) : []
  const owner = String(spot.owner_id || '').toLowerCase()

  if (filters.onlyFavorites) {
    if (!spotId || !favoritesSet.has(spotId)) return false
  }

  if (filters.visibility !== 'all' && visibility !== filters.visibility) {
    return false
  }

  if (filters.text) {
    const needle = filters.text.toLowerCase()
    const haystack = [title, description, ...tags]
      .map((x) => String(x || '').toLowerCase())
      .join(' ')
    if (!haystack.includes(needle)) {
      return false
    }
  }

  if (filters.tagsText) {
    const requested = tokenize(filters.tagsText)
    const hasAll = requested.every((entry) => tags.some((tag) => tag.includes(entry)))
    if (!hasAll) {
      return false
    }
  }

  if (filters.ownerText) {
    const ownerNeedle = filters.ownerText.toLowerCase()
    if (!owner.includes(ownerNeedle)) {
      return false
    }
  }

  if (filters.radiusKm > 0 && center) {
    const lat = Number(spot.lat)
    const lon = Number(spot.lon)
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      return false
    }
    const dist = distanceKm(lat, lon, center.lat, center.lon)
    if (!Number.isFinite(dist) || dist > filters.radiusKm) {
      return false
    }
  }

  return true
}
