import { registerAction, registerComponent } from '../core/registry'
import MapHeader from '../components/map/MapHeader.vue'
import MapWorkspace from '../components/map/MapWorkspace.vue'

function notify(app, payload) {
  app.service('notify').push(payload)
}

async function reloadMapData(app) {
  await app.controller('spots').reload()
  await app.controller('social').reloadFavorites()
}

function parseFocusRequest(route) {
  const query = route && typeof route === 'object' ? route.query : null
  const lat = Number(query?.lat)
  const lon = Number(query?.lon)
  const spotId = String(query?.spotId || '').trim()
  return {
    lat: Number.isFinite(lat) ? lat : null,
    lon: Number.isFinite(lon) ? lon : null,
    spotId,
  }
}

registerAction('map.reload', async ({ app }) => {
  await reloadMapData(app)
})

registerComponent({
  screen: 'map',
  slot: 'header',
  id: 'map.header',
  order: 10,
  component: MapHeader,
  buildProps: ({ app, router }) => ({
    onBack: () => router.push('/home'),
    onOpenSupport: () => router.push('/support'),
    onReload: async () => {
      await reloadMapData(app)
      notify(app, { level: 'success', title: 'Map refreshed', message: 'Spots loaded from backend.' })
    },
    reloadBusy: app.state.loading.mapReload,
  }),
})

registerComponent({
  screen: 'map',
  slot: 'main',
  id: 'map.workspace',
  order: 10,
  component: MapWorkspace,
  buildProps: ({ app, router, route }) => ({
    state: app.state,
    focusRequest: parseFocusRequest(route),
    onNotify: (payload) => notify(app, payload),
    onInit: async () => {
      await reloadMapData(app)
    },
    onReload: async () => {
      await reloadMapData(app)
    },
    onSaveSpot: async (spot) => {
      const ok = await app.controller('spots').saveSpot(spot)
      if (!ok) {
        notify(app, {
          level: 'error',
          title: 'Save failed',
          message: 'Spot could not be persisted.',
          details: app.controller('spots').lastError(),
        })
        return false
      }
      notify(app, { level: 'success', title: 'Saved', message: 'Spot saved successfully.' })
      return true
    },
    onDeleteSpot: async (spotId) => {
      const ok = await app.controller('spots').deleteSpot(spotId)
      if (!ok) {
        notify(app, {
          level: 'error',
          title: 'Delete failed',
          message: 'Spot could not be deleted.',
          details: app.controller('spots').lastError(),
        })
        return false
      }
      notify(app, { level: 'info', title: 'Deleted', message: 'Spot removed.' })
      return true
    },
    onToggleFavorite: async (spotId, isFavorite) => {
      const ok = await app.controller('social').toggleFavorite(spotId, isFavorite)
      if (!ok) {
        notify(app, {
          level: 'error',
          title: 'Favorite failed',
          message: 'Could not update favorite state.',
          details: app.controller('social').lastError(),
        })
        return false
      }
      notify(app, {
        level: 'success',
        title: isFavorite ? 'Removed favorite' : 'Added favorite',
        message: 'Favorite status updated.',
      })
      return true
    },
    onShareSpot: async (spotId, message) => {
      const ok = await app.controller('social').share(spotId, message)
      if (!ok) {
        notify(app, {
          level: 'error',
          title: 'Share failed',
          message: 'Could not share spot.',
          details: app.controller('social').lastError(),
        })
        return false
      }
      notify(app, { level: 'success', title: 'Shared', message: 'Spot was shared.' })
      return true
    },
    onSearchUsers: async (query, limit = 20) => {
      return app.controller('users').searchUsers(query, limit)
    },
    onLoadFriendUsers: async () => {
      return app.controller('users').friendDirectory()
    },
    onLoadUserProfile: async (userId) => {
      return app.controller('users').profile(userId)
    },
    onSearchLocations: async (query, limit = 6) => {
      return app.service('locationSearch').searchPlaces(query, limit)
    },
    onOpenProfile: (userId) => {
      if (!userId) return
      router.push(`/profile/${userId}`)
    },
  }),
})
