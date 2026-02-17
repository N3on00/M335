function parseCoordinate(value) {
  if (value === null || value === undefined) return null
  if (typeof value === 'string' && value.trim() === '') return null

  const out = Number(value)
  return Number.isFinite(out) ? out : null
}

export function resolveGoToSpot(spot, currentZoom, minZoom = 14) {
  const lat = parseCoordinate(spot?.lat)
  const lon = parseCoordinate(spot?.lon)
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    return null
  }

  return {
    center: [lat, lon],
    zoom: Math.max(Number(minZoom) || 14, Number(currentZoom) || 12),
  }
}
