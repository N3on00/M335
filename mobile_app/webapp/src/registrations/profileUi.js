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

  const [profile, createdSpots, favoriteSpots] = await Promise.all([
    app.controller('users').profile(userId),
    app.controller('spots').byUser(userId),
    app.controller('spots').favoritesOfUser(userId),
  ])

  app.state.profile.current = profile
  app.state.profile.createdSpots = Array.isArray(createdSpots) ? createdSpots : []
  app.state.profile.favoriteSpots = Array.isArray(favoriteSpots) ? favoriteSpots : []
  app.state.profile.viewedUserId = userId
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
