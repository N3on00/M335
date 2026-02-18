export function asText(value) {
  return String(value || '').trim()
}

export function sanitizeText(value) {
  return asText(value)
}

export function tokenize(text) {
  return String(text || '')
    .toLowerCase()
    .split(/[\s,]+/)
    .map((part) => part.trim())
    .filter(Boolean)
}

export function parseCoordinate(value) {
  if (value === null || value === undefined) return null
  if (typeof value === 'string' && value.trim() === '') return null
  const out = Number(value)
  return Number.isFinite(out) ? out : null
}

export function sanitizeNumber(value, defaultValue = 0) {
  const out = Number(value)
  return Number.isFinite(out) ? out : defaultValue
}

export function sanitizeBoolean(value) {
  return Boolean(value)
}

export function sanitizeArray(value) {
  return Array.isArray(value) ? value : []
}

export function sanitizeObject(value) {
  return value && typeof value === 'object' ? value : {}
}

export function sanitizeId(value) {
  return asText(value)
}

export function normalizeVisibility(value) {
  const out = String(value || '').trim().toLowerCase()
  if (out === 'public' || out === 'following' || out === 'invite_only' || out === 'personal') {
    return out
  }
  return 'all'
}
