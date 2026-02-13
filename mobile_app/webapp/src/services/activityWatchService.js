import { normalizeFilterSubscription, subscriptionMatchesSpot } from '../models/spotSubscriptions'

const POLL_MS = 22000

function userIdOf(entry) {
  return String(entry?.id || entry?.follower?.id || '').trim()
}

function requestIdOf(entry) {
  const followerId = String(entry?.follower?.id || '').trim()
  const created = String(entry?.created_at || '').trim()
  return `${followerId}|${created}`
}

function spotIdOf(spot) {
  return String(spot?.id || '').trim()
}

export class ActivityWatchService {
  constructor(ctx) {
    this.ctx = ctx
    this._timer = null
    this._busy = false
    this._seeded = false
    this._followerIds = new Set()
    this._requestIds = new Set()
    this._subMatches = new Map()
  }

  start() {
    if (this._timer) return
    this._seeded = false
    this._timer = setInterval(() => {
      void this.tick({ notify: true })
    }, POLL_MS)
    void this.tick({ notify: false })
  }

  stop() {
    if (this._timer) {
      clearInterval(this._timer)
      this._timer = null
    }
    this._busy = false
    this._seeded = false
    this._followerIds.clear()
    this._requestIds.clear()
    this._subMatches.clear()
  }

  async tick({ notify = true } = {}) {
    if (this._busy) return

    const app = this.ctx
    if (!app.ui?.isAuthenticated()) return

    const meId = String(app.state.session.user?.id || '').trim()
    if (!meId) return

    this._busy = true
    try {
      const social = app.controller('social')
      const spotsCtrl = app.controller('spots')
      const notifyService = app.service('notify')

      const [followers, incomingRequests] = await Promise.all([
        social.followersOf(meId),
        social.incomingRequests(),
      ])

      const followerList = Array.isArray(followers) ? followers : []
      const requestList = Array.isArray(incomingRequests) ? incomingRequests : []

      app.state.social.followers = followerList
      app.state.social.followersCount = followerList.length
      app.state.social.incomingRequests = requestList

      const nextFollowerIds = new Set(followerList.map((entry) => userIdOf(entry)).filter(Boolean))
      const nextRequestIds = new Set(requestList.map((entry) => requestIdOf(entry)).filter(Boolean))

      if (notify && this._seeded) {
        for (const follower of followerList) {
          const fid = userIdOf(follower)
          if (!fid || this._followerIds.has(fid)) continue

          const who = String(follower.display_name || follower.username || 'A user')
          notifyService.push({
            level: 'info',
            title: 'New follower',
            message: `${who} started following you.`,
          })
        }

        for (const request of requestList) {
          const rid = requestIdOf(request)
          if (!rid || this._requestIds.has(rid)) continue

          const who = String(request?.follower?.display_name || request?.follower?.username || 'A user')
          notifyService.push({
            level: 'info',
            title: 'Follow request',
            message: `${who} requested to follow you.`,
          })
        }
      }

      this._followerIds = nextFollowerIds
      this._requestIds = nextRequestIds

      const rawSubs = Array.isArray(app.state.map?.filterSubscriptions)
        ? app.state.map.filterSubscriptions
        : []
      const subscriptions = rawSubs
        .map((entry) => normalizeFilterSubscription(entry))
        .filter(Boolean)

      if (subscriptions.length) {
        await spotsCtrl.reload()
        const allSpots = Array.isArray(app.state.spots) ? app.state.spots : []
        const favoritesSet = new Set((app.state.favorites || []).map((id) => String(id)))

        const activeIds = new Set()
        for (const sub of subscriptions) {
          activeIds.add(sub.id)
          const currentMatchIds = new Set(
            allSpots
              .filter((spot) => subscriptionMatchesSpot(sub, spot, favoritesSet))
              .map((spot) => spotIdOf(spot))
              .filter(Boolean),
          )

          if (notify && this._seeded) {
            const prev = this._subMatches.get(sub.id) || new Set()
            let newCount = 0
            for (const sid of currentMatchIds) {
              if (!prev.has(sid)) newCount += 1
            }
            if (newCount > 0) {
              notifyService.push({
                level: 'success',
                title: 'Subscription update',
                message: `${newCount} new spot(s) matched: ${sub.label}`,
              })
            }
          }

          this._subMatches.set(sub.id, currentMatchIds)
        }

        for (const subId of [...this._subMatches.keys()]) {
          if (!activeIds.has(subId)) {
            this._subMatches.delete(subId)
          }
        }
      } else {
        this._subMatches.clear()
      }

      this._seeded = true
    } catch {
      // Keep silent to avoid noisy polling errors when backend is offline.
    } finally {
      this._busy = false
    }
  }
}
