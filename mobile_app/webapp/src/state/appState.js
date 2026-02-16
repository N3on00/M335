import { reactive } from 'vue'
import { normalizeUser } from '../models/userMapper'
import { normalizeFilterSubscription } from '../models/spotSubscriptions'

const SESSION_KEY = 'sos_web_session_v1'
const THEME_KEY = 'sos_web_theme_v1'
const FILTER_SUBSCRIPTIONS_KEY = 'sos_map_filter_subscriptions_v1'

function loadSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) {
      return { token: '', user: null }
    }
    const parsed = JSON.parse(raw)
    return {
      token: typeof parsed.token === 'string' ? parsed.token : '',
      user: parsed.user && typeof parsed.user === 'object' ? normalizeUser(parsed.user) : null,
    }
  } catch {
    return { token: '', user: null }
  }
}

function loadTheme() {
  try {
    const raw = String(localStorage.getItem(THEME_KEY) || '').trim().toLowerCase()
    if (raw === 'dark') return 'dark'
    return 'light'
  } catch {
    return 'light'
  }
}

function loadFilterSubscriptions() {
  try {
    const raw = localStorage.getItem(FILTER_SUBSCRIPTIONS_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
      .map((entry) => normalizeFilterSubscription(entry))
      .filter(Boolean)
  } catch {
    return []
  }
}

export function createAppState() {
  const session = loadSession()
  const theme = loadTheme()
  const filterSubscriptions = loadFilterSubscriptions()
  return reactive({
    config: {
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
      supportEmail: import.meta.env.VITE_SUPPORT_EMAIL || 'support@spotonsight.app',
    },
    session,
    spots: [],
    favorites: [],
    notifications: [],
    notificationLog: [],
    loading: {
      authLogin: false,
      authRegister: false,
      homeRefresh: false,
      socialReload: false,
      socialFollow: false,
      socialUnfollow: false,
      socialSearch: false,
      mapReload: false,
      mapSave: false,
      mapDelete: false,
      mapFavorite: false,
      mapShare: false,
      settingsLoad: false,
      settingsSave: false,
      profileLoad: false,
      supportSubmit: false,
    },
    loadingCounts: {},
    social: {
      followersCount: 0,
      followingCount: 0,
      followers: [],
      following: [],
      searchResults: [],
      incomingRequests: [],
      blockedUsers: [],
    },
    map: {
      center: [47.3769, 8.5417],
      zoom: 12,
      draftLat: null,
      draftLon: null,
      filterSubscriptions,
    },
    profile: {
      current: null,
      createdSpots: [],
      favoriteSpots: [],
      viewedUserId: '',
    },
    ui: {
      theme,
    },
  })
}

export function persistSession(state) {
  localStorage.setItem(
    SESSION_KEY,
    JSON.stringify({
      token: state.session.token,
      user: state.session.user,
    }),
  )
}

export function persistTheme(state) {
  localStorage.setItem(THEME_KEY, String(state?.ui?.theme || 'light'))
}

export function persistFilterSubscriptions(state) {
  const subs = Array.isArray(state?.map?.filterSubscriptions)
    ? state.map.filterSubscriptions
    : []
  localStorage.setItem(FILTER_SUBSCRIPTIONS_KEY, JSON.stringify(subs))
}
