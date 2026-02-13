import { normalizeUser } from '../models/userMapper'
import { ApiStateService } from './baseService'

function addIfDefined(out, key, value) {
  if (value === undefined) return
  out[key] = value
}

function dedupeUsers(items) {
  if (!Array.isArray(items)) return []

  const out = []
  const seen = new Set()
  for (const item of items) {
    const user = normalizeUser(item)
    const id = String(user.id || '').trim()
    if (!id || seen.has(id)) continue
    seen.add(id)
    out.push(user)
  }
  return out
}

function byDisplayName(a, b) {
  const left = String(a?.display_name || a?.username || '').toLowerCase()
  const right = String(b?.display_name || b?.username || '').toLowerCase()
  return left.localeCompare(right)
}

function textIncludesUser(user, query) {
  const q = String(query || '').trim().toLowerCase()
  if (!q) return true

  const haystack = [
    user?.display_name,
    user?.username,
    user?.email,
    user?.id,
  ]
    .map((value) => String(value || '').toLowerCase())
    .join(' ')

  return haystack.includes(q)
}

export class UsersService extends ApiStateService {
  constructor(api, state) {
    super(api, state, { serviceName: 'users' })
  }

  async me() {
    if (!this.token()) {
      this.captureError('Authentication required', 'Authentication required')
      return null
    }

    try {
      const data = await this.api.get('/social/me', { token: this.token() })
      this.clearError()
      return normalizeUser(data)
    } catch (error) {
      this.captureError(error, 'Could not load user profile')
      return null
    }
  }

  async profile(userId) {
    if (!this.token()) {
      this.captureError('Authentication required', 'Authentication required')
      return null
    }

    const id = String(userId || '').trim()
    if (!id) {
      this.captureError('User id is required', 'User id is required')
      return null
    }

    try {
      const data = await this.api.get(`/social/users/${id}/profile`, { token: this.token() })
      this.clearError()
      return normalizeUser(data)
    } catch (error) {
      this.captureError(error, 'Could not load user profile')
      return null
    }
  }

  async searchByUsername(query, limit = 20) {
    if (!this.token()) {
      this.captureError('Authentication required', 'Authentication required')
      return []
    }

    const q = String(query || '').trim()
    if (!q) {
      this.clearError()
      return []
    }

    const safeLimit = Math.min(50, Math.max(1, Number(limit) || 20))
    const path = `/social/users/search?q=${encodeURIComponent(q)}&limit=${safeLimit}`

    try {
      const data = await this.api.get(path, { token: this.token() })
      this.clearError()
      return Array.isArray(data) ? data.map((item) => normalizeUser(item)) : []
    } catch (error) {
      this.captureError(error, 'Could not search users')
      return []
    }
  }

  async friendDirectory() {
    if (!this.token()) {
      this.captureError('Authentication required', 'Authentication required')
      return []
    }

    const userId = String(this.state?.session?.user?.id || '').trim()
    if (!userId) {
      this.captureError('User profile not loaded', 'User profile not loaded')
      return []
    }

    try {
      const [followers, following] = await Promise.all([
        this.api.get(`/social/followers/${userId}`, { token: this.token() }),
        this.api.get(`/social/following/${userId}`, { token: this.token() }),
      ])

      const meId = userId
      const merged = dedupeUsers([...(followers || []), ...(following || [])])
        .filter((user) => String(user.id || '') !== meId)
        .sort(byDisplayName)

      this.clearError()
      return merged
    } catch (error) {
      this.captureError(error, 'Could not load friend list')
      return []
    }
  }

  async searchFriends(query, limit = 20) {
    const safeLimit = Math.min(100, Math.max(1, Number(limit) || 20))
    const friends = await this.friendDirectory()
    return friends
      .filter((user) => textIncludesUser(user, query))
      .slice(0, safeLimit)
  }

  async updateMe(input) {
    if (!this.token()) {
      this.captureError('Authentication required', 'Authentication required')
      return null
    }

    const src = input && typeof input === 'object' ? input : {}
    const payload = {}

    addIfDefined(payload, 'username', src.username)
    addIfDefined(payload, 'email', src.email)
    addIfDefined(payload, 'display_name', src.displayName)
    addIfDefined(payload, 'bio', src.bio)
    addIfDefined(payload, 'avatar_image', src.avatarImage)
    addIfDefined(payload, 'social_accounts', src.socialAccounts)
    addIfDefined(payload, 'follow_requires_approval', src.followRequiresApproval)
    addIfDefined(payload, 'current_password', src.currentPassword)
    addIfDefined(payload, 'new_password', src.newPassword)

    try {
      const data = await this.api.put('/social/me', payload, { token: this.token() })
      this.clearError()
      return normalizeUser(data)
    } catch (error) {
      this.captureError(error, 'Could not save user profile')
      return null
    }
  }
}
