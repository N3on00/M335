import { normalizeSpot, toSpotPayload } from '../models/spotMapper'
import { API_ENDPOINTS } from '../api/registry'
import { ApiStateService } from './baseService'

function asText(value) {
  return String(value || '').trim()
}

function uniqueIds(items) {
  const out = []
  const seen = new Set()
  for (const item of Array.isArray(items) ? items : []) {
    const id = asText(item)
    if (!id || seen.has(id)) continue
    seen.add(id)
    out.push(id)
  }
  return out
}

export class SpotsService extends ApiStateService {
  constructor(api, state) {
    super(api, state, { serviceName: 'spots' })
  }

  async list() {
    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_SPOTS_LIST)
      this.state.spots = Array.isArray(data) ? data.map((x) => normalizeSpot(x)) : []
      this.clearError()
      return this.state.spots
    } catch (error) {
      this.captureError(error, 'Could not load spots')
      this.state.spots = []
      return []
    }
  }

  async create(dto) {
    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_SPOTS_CREATE, {
        body: toSpotPayload(dto),
      })
      this.clearError()
      return data?.id || null
    } catch (error) {
      this.captureError(error, 'Could not create spot')
      return null
    }
  }

  async update(id, dto) {
    try {
      await this.api.request(API_ENDPOINTS.SOCIAL_SPOTS_UPDATE, {
        params: { spotId: id },
        body: toSpotPayload(dto),
      })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not update spot')
      return false
    }
  }

  async delete(id) {
    try {
      await this.api.request(API_ENDPOINTS.SOCIAL_SPOTS_DELETE, {
        params: { spotId: id },
      })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not delete spot')
      return false
    }
  }

  async byUser(userId) {
    try {
      const data = await this.api.request(API_ENDPOINTS.SOCIAL_USERS_SPOTS, {
        params: { userId },
      })
      this.clearError()
      return Array.isArray(data) ? data.map((x) => normalizeSpot(x)) : []
    } catch (error) {
      this.captureError(error, 'Could not load user spots')
      return []
    }
  }

  async favoritesOfUser(userId) {
    try {
      const refs = await this.api.request(API_ENDPOINTS.SOCIAL_USERS_FAVORITES, {
        params: { userId },
      })
      const favoriteIds = uniqueIds(
        Array.isArray(refs)
          ? refs.map((entry) => asText(entry?.spot_id))
          : [],
      )
      if (!favoriteIds.length) {
        this.clearError()
        return []
      }

      const visible = await this.api.request(API_ENDPOINTS.SOCIAL_SPOTS_LIST)
      const idSet = new Set(favoriteIds)
      const mapped = Array.isArray(visible) ? visible.map((x) => normalizeSpot(x)) : []
      this.clearError()
      return mapped.filter((spot) => idSet.has(asText(spot?.id)))
    } catch (error) {
      this.captureError(error, 'Could not load favorite spots')
      return []
    }
  }
}
