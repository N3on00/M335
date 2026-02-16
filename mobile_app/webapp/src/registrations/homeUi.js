import { registerAction, registerComponent } from '../core/registry'
import HomeHero from '../components/home/HomeHero.vue'
import HomeMapWidget from '../components/home/HomeMapWidget.vue'
import HomeDiscover from '../components/home/HomeDiscover.vue'
import {
  controllerLastError,
  mergeUniqueDetails,
  notify,
  reloadDashboardData,
  runTask,
} from './uiShared'

function _homeSyncErrorDetails(app) {
  return mergeUniqueDetails(
    controllerLastError(app, 'spots'),
    controllerLastError(app, 'social'),
  )
}

async function _reloadHomeDashboardStrict(app) {
  await reloadDashboardData(app)
  const details = _homeSyncErrorDetails(app)
  if (details) {
    throw new Error(details)
  }
}

function _openMap(router, { lat = null, lon = null, spotId = '' } = {}) {
  const query = {}
  if (Number.isFinite(lat) && Number.isFinite(lon)) {
    query.lat = String(lat)
    query.lon = String(lon)
  }

  const sid = String(spotId || '').trim()
  if (sid) {
    query.spotId = sid
  }

  router.push({
    name: 'map',
    query,
  })
}

function _goToSpot(app, router, spot) {
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

  _openMap(router, { lat, lon, spotId })
}

registerAction('home.refresh', async ({ app }) => {
  await _reloadHomeDashboardStrict(app)
})

registerComponent({
  screen: 'home',
  slot: 'header',
  id: 'home.hero',
  order: 10,
  component: HomeHero,
  buildProps: ({ app }) => ({
    username: app.state.session.user?.display_name || app.state.session.user?.username || '',
  }),
})

registerComponent({
  screen: 'home',
  slot: 'main',
  id: 'home.map-widget',
  order: 8,
  component: HomeMapWidget,
  buildProps: ({ app, router }) => ({
    spots: app.state.spots,
    onOpenMap: (focus = null) => {
      const src = focus && typeof focus === 'object' ? focus : {}
      const lat = Number(src.lat)
      const lon = Number(src.lon)
      _openMap(router, {
        lat: Number.isFinite(lat) ? lat : null,
        lon: Number.isFinite(lon) ? lon : null,
      })
    },
    onOpenSpot: (spot) => _goToSpot(app, router, spot),
  }),
})

registerComponent({
  screen: 'home',
  slot: 'main',
  id: 'home.discover',
  order: 10,
  component: HomeDiscover,
  buildProps: ({ app, router }) => ({
    spots: app.state.spots,
    favorites: app.state.favorites,
    refreshBusy: app.state.loading.homeRefresh,
    onOpenProfile: (userId) => {
      const nextId = typeof userId === 'string' && userId.trim()
        ? userId.trim()
        : String(app.state.session.user?.id || '')
      router.push(`/profile/${nextId}`)
    },
    onRefresh: async () => {
      await runTask(app, {
        loadingKey: 'homeRefresh',
        task: () => _reloadHomeDashboardStrict(app),
        errorTitle: 'Sync failed',
        errorMessage: 'Could not sync spots and social data.',
        errorDetails: (error) => String(error?.message || error || ''),
        successTitle: 'Synced',
        successMessage: 'Spots and social data updated.',
      })
    },
    onGoToSpot: (spot) => _goToSpot(app, router, spot),
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
    onNotify: (payload) => notify(app, payload),
  }),
})
