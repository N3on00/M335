import { normalizeSpot, toSpotPayload } from '../models/spotMapper'
import { ApiStateService } from './baseService'

export class SpotsService extends ApiStateService {
  constructor(api, state) {
    super(api, state, { serviceName: 'spots' })
  }

  async list() {
    try {
      const data = await this.api.get('/social/spots', { token: this.token() })
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
      const data = await this.api.post('/social/spots', toSpotPayload(dto), { token: this.token() })
      this.clearError()
      return data?.id || null
    } catch (error) {
      this.captureError(error, 'Could not create spot')
      return null
    }
  }

  async update(id, dto) {
    try {
      await this.api.put(`/social/spots/${id}`, toSpotPayload(dto), { token: this.token() })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not update spot')
      return false
    }
  }

  async delete(id) {
    try {
      await this.api.delete(`/social/spots/${id}`, { token: this.token() })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not delete spot')
      return false
    }
  }

  async byUser(userId) {
    try {
      const data = await this.api.get(`/social/users/${userId}/spots`, { token: this.token() })
      this.clearError()
      return Array.isArray(data) ? data.map((x) => normalizeSpot(x)) : []
    } catch (error) {
      this.captureError(error, 'Could not load user spots')
      return []
    }
  }

  async favoritesOfUser(userId) {
    try {
      const data = await this.api.get(`/social/users/${userId}/favorites`, { token: this.token() })
      this.clearError()
      return Array.isArray(data) ? data.map((x) => normalizeSpot(x)) : []
    } catch (error) {
      this.captureError(error, 'Could not load favorite spots')
      return []
    }
  }
}
