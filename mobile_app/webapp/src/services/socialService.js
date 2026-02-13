import { extractSpotId } from '../models/spotMapper'
import { normalizeUser } from '../models/userMapper'
import { ApiStateService } from './baseService'

export class SocialService extends ApiStateService {
  constructor(api, state) {
    super(api, state, { serviceName: 'social' })
  }

  async loadFavorites() {
    if (!this.token()) {
      this.state.favorites = []
      this.clearError()
      return []
    }
    try {
      const data = await this.api.get('/social/favorites', { token: this.token() })
      this.state.favorites = Array.isArray(data)
        ? data.map((x) => extractSpotId(x)).filter(Boolean)
        : []
      this.clearError()
      return this.state.favorites
    } catch (error) {
      this.captureError(error, 'Could not load favorites')
      this.state.favorites = []
      return []
    }
  }

  async favoriteSpot(spotId) {
    try {
      await this.api.post(`/social/favorites/${spotId}`, {}, { token: this.token() })
      if (!this.state.favorites.includes(spotId)) {
        this.state.favorites.push(spotId)
      }
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not update favorite')
      return false
    }
  }

  async unfavoriteSpot(spotId) {
    try {
      await this.api.delete(`/social/favorites/${spotId}`, { token: this.token() })
      this.state.favorites = this.state.favorites.filter((id) => id !== spotId)
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not update favorite')
      return false
    }
  }

  async shareSpot(spotId, message) {
    try {
      await this.api.post(`/social/share/${spotId}`, { message: message || '' }, { token: this.token() })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not share spot')
      return false
    }
  }

  async followUser(userId) {
    try {
      const data = await this.api.post(`/social/follow/${userId}`, {}, { token: this.token() })
      const status = String(data?.status || 'following').toLowerCase()
      this.clearError()
      if (status === 'pending') {
        return 'pending'
      }
      return 'following'
    } catch (error) {
      this.captureError(error, 'Could not follow user')
      return ''
    }
  }

  async unfollowUser(userId) {
    try {
      await this.api.delete(`/social/follow/${userId}`, { token: this.token() })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not unfollow user')
      return false
    }
  }

  async removeFollower(userId) {
    try {
      await this.api.delete(`/social/followers/${userId}`, { token: this.token() })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not remove follower')
      return false
    }
  }

  async incomingFollowRequests() {
    try {
      const data = await this.api.get('/social/follow/requests', { token: this.token() })
      this.clearError()
      if (!Array.isArray(data)) return []
      return data.map((entry) => ({
        ...entry,
        follower: normalizeUser(entry?.follower),
      }))
    } catch (error) {
      this.captureError(error, 'Could not load follow requests')
      return []
    }
  }

  async approveFollowRequest(userId) {
    try {
      await this.api.post(`/social/follow/requests/${userId}/approve`, {}, { token: this.token() })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not approve follow request')
      return false
    }
  }

  async rejectFollowRequest(userId) {
    try {
      await this.api.post(`/social/follow/requests/${userId}/reject`, {}, { token: this.token() })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not reject follow request')
      return false
    }
  }

  async blockUser(userId) {
    try {
      await this.api.post(`/social/block/${userId}`, {}, { token: this.token() })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not block user')
      return false
    }
  }

  async unblockUser(userId) {
    try {
      await this.api.delete(`/social/block/${userId}`, { token: this.token() })
      this.clearError()
      return true
    } catch (error) {
      this.captureError(error, 'Could not unblock user')
      return false
    }
  }

  async blockedUsers() {
    try {
      const data = await this.api.get('/social/blocked', { token: this.token() })
      this.clearError()
      return Array.isArray(data) ? data.map((item) => normalizeUser(item)) : []
    } catch (error) {
      this.captureError(error, 'Could not load blocked users')
      return []
    }
  }

  async followersOf(userId) {
    try {
      const data = await this.api.get(`/social/followers/${userId}`, { token: this.token() })
      this.clearError()
      return Array.isArray(data) ? data.map((item) => normalizeUser(item)) : []
    } catch (error) {
      this.captureError(error, 'Could not load followers')
      return []
    }
  }

  async followingOf(userId) {
    try {
      const data = await this.api.get(`/social/following/${userId}`, { token: this.token() })
      this.clearError()
      return Array.isArray(data) ? data.map((item) => normalizeUser(item)) : []
    } catch (error) {
      this.captureError(error, 'Could not load following users')
      return []
    }
  }
}
