import { registerAction, registerComponent } from '../core/registry'
import ProfileHero from '../components/profile/ProfileHero.vue'
import ProfileSummary from '../components/profile/ProfileSummary.vue'
import { notify } from './uiShared'

async function loadProfileState(app, targetId) {
  const userId = String(targetId || app.state.session.user?.id || '').trim()
  if (!userId) {
    app.state.profile.current = null
    app.state.profile.createdSpots = []
    app.state.profile.favoriteSpots = []
    app.state.profile.viewedUserId = ''
    return
  }

  const meId = String(app.state.session.user?.id || '').trim()

  const [profile, createdSpots, favoriteSpots, following] = await Promise.all([
    app.controller('users').profile(userId),
    app.controller('spots').byUser(userId),
    app.controller('spots').favoritesOfUser(userId),
    meId ? app.controller('social').followingOf(meId) : Promise.resolve([]),
  ])

  app.state.profile.current = profile
  app.state.profile.createdSpots = Array.isArray(createdSpots) ? createdSpots : []
  app.state.profile.favoriteSpots = Array.isArray(favoriteSpots) ? favoriteSpots : []
  app.state.profile.viewedUserId = userId
  app.state.social.following = Array.isArray(following) ? following : []
}

registerAction('profile.refresh', async ({ app, payload }) => {
  const targetId = payload && typeof payload === 'object' ? payload.userId : ''
  await loadProfileState(app, targetId)
})

registerComponent({
  screen: 'profile',
  slot: 'header',
  id: 'profile.hero',
  order: 10,
  component: ProfileHero,
  buildProps: ({ router }) => ({
    onBack: () => router.back(),
    onOpenSocial: () => router.push('/social'),
    onOpenSupport: () => router.push('/support'),
    onOpenSettings: () => router.push('/settings'),
  }),
})

registerComponent({
  screen: 'profile',
  slot: 'main',
  id: 'profile.summary',
  order: 10,
  component: ProfileSummary,
  buildProps: ({ app, router }) => ({
    profile: app.state.profile.current,
    createdSpots: app.state.profile.createdSpots,
    favoriteSpots: app.state.profile.favoriteSpots,
    favorites: app.state.favorites,
    isOwnProfile: String(app.state.profile.viewedUserId || '') === String(app.state.session.user?.id || ''),
    isFollowingProfile: (app.state.social.following || [])
      .map((user) => String(user?.id || '').trim())
      .includes(String(app.state.profile.viewedUserId || '').trim()),
    followBusy: app.state.loading.socialFollow || app.state.loading.socialUnfollow,
    onFollowProfile: async () => {
      const targetId = String(app.state.profile.viewedUserId || '').trim()
      if (!targetId) return false

      app.state.loading.socialFollow = true
      try {
        const status = await app.controller('social').follow(targetId)
        if (!status) {
          notify(app, {
            level: 'error',
            title: 'Follow failed',
            message: 'Could not follow this profile.',
            details: app.controller('social').lastError(),
          })
          return false
        }

        notify(app, {
          level: 'success',
          title: status === 'pending' ? 'Request sent' : 'Followed',
          message: status === 'pending' ? 'Waiting for user approval.' : 'You are now following this profile.',
        })

        await loadProfileState(app, targetId)
        return true
      } finally {
        app.state.loading.socialFollow = false
      }
    },
    onUnfollowProfile: async () => {
      const targetId = String(app.state.profile.viewedUserId || '').trim()
      if (!targetId) return false

      app.state.loading.socialUnfollow = true
      try {
        const ok = await app.controller('social').unfollow(targetId)
        if (!ok) {
          notify(app, {
            level: 'error',
            title: 'Unfollow failed',
            message: 'Could not unfollow this profile.',
            details: app.controller('social').lastError(),
          })
          return false
        }

        notify(app, {
          level: 'info',
          title: 'Unfollowed',
          message: 'You no longer follow this profile.',
        })

        await loadProfileState(app, targetId)
        return true
      } finally {
        app.state.loading.socialUnfollow = false
      }
    },
    onGoToSpot: (spot) => {
      const lat = Number(spot?.lat)
      const lon = Number(spot?.lon)
      const spotId = String(spot?.id || '').trim()
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
        notify(app, {
          level: 'warning',
          title: 'Spot location missing',
          message: 'This spot has no usable coordinates.',
        })
        return
      }

      router.push({
        name: 'map',
        query: {
          lat: String(lat),
          lon: String(lon),
          spotId,
        },
      })
    },
    onToggleFavorite: async (spotId, currentlyFavorite) => {
      const ok = await app.controller('social').toggleFavorite(spotId, currentlyFavorite)
      if (!ok) {
        notify(app, {
          level: 'error',
          title: 'Like failed',
          message: 'Could not update like state.',
          details: app.controller('social').lastError(),
        })
        return false
      }

      notify(app, {
        level: 'success',
        title: currentlyFavorite ? 'Like removed' : 'Liked',
        message: currentlyFavorite ? 'Spot removed from your likes.' : 'Spot added to your likes.',
      })
      return true
    },
    onLoadUserProfile: async (userId) => {
      return app.controller('users').profile(userId)
    },
    onOpenProfile: (userId) => {
      router.push(`/profile/${userId}`)
    },
    onNotify: (payload) => notify(app, payload),
  }),
})
