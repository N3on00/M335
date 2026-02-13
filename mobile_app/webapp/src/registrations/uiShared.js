import { toUserErrorMessage } from '../services/apiErrors'

function resolve(value, ...args) {
  return typeof value === 'function' ? value(...args) : value
}

function toDetails(value) {
  if (value == null) return ''
  const text = String(value).trim()
  if (!text) return ''
  return toUserErrorMessage(text, text)
}

function resolveText(value, fallback, ...args) {
  const text = toDetails(resolve(value, ...args))
  if (text) return text
  return toDetails(fallback)
}

export function notify(app, payload) {
  app.service('notify').push(payload)
}

export function notifyInfo(app, title, message, details = '') {
  notify(app, { level: 'info', title, message, details })
}

export function notifySuccess(app, title, message, details = '') {
  notify(app, { level: 'success', title, message, details })
}

export function notifyError(app, title, message, details = '') {
  notify(app, { level: 'error', title, message, details })
}

export function toggleTheme(app) {
  const current = String(app?.state?.ui?.theme || 'light').toLowerCase()
  const next = current === 'dark' ? 'light' : 'dark'
  app.state.ui.theme = next
  return next
}

export async function copyTextToClipboard(app, {
  text,
  successTitle = 'Copied',
  successMessage = 'Copied to clipboard.',
  emptyTitle = 'Missing value',
  emptyMessage = 'There is nothing to copy.',
  errorTitle = 'Clipboard Error',
  errorMessage = 'Could not copy value from browser.',
} = {}) {
  const value = String(text || '').trim()
  if (!value) {
    notifyInfo(app, emptyTitle, emptyMessage)
    return false
  }

  try {
    await navigator.clipboard.writeText(value)
    notifySuccess(app, successTitle, successMessage)
    return true
  } catch (error) {
    notifyError(app, errorTitle, errorMessage, toDetails(error?.message || error))
    return false
  }
}

function _ensureLoadingState(app, key) {
  if (!key) return
  if (!(key in app.state.loading)) {
    app.state.loading[key] = false
  }
  if (!app.state.loadingCounts) {
    app.state.loadingCounts = {}
  }
  if (!(key in app.state.loadingCounts)) {
    app.state.loadingCounts[key] = 0
  }
}

function _beginLoading(app, key) {
  if (!key) return
  _ensureLoadingState(app, key)
  app.state.loadingCounts[key] += 1
  app.state.loading[key] = true
}

function _endLoading(app, key) {
  if (!key) return
  _ensureLoadingState(app, key)
  app.state.loadingCounts[key] = Math.max(0, (app.state.loadingCounts[key] || 0) - 1)
  app.state.loading[key] = app.state.loadingCounts[key] > 0
}

export function observeAction(app, {
  loadingKey = '',
  errorTitle = 'Action failed',
  errorMessage = 'Please try again.',
  errorDetails,
  successTitle = '',
  successMessage = '',
  successLevel = 'success',
  successWhen,
  onSuccess,
}, action) {
  return async (...args) => {
    _beginLoading(app, loadingKey)
    try {
      const result = await action(...args)
      const pass = typeof successWhen === 'function' ? !!successWhen(result) : true

      if (!pass) {
        const details = toDetails(resolve(errorDetails, result) || '')
        notifyError(
          app,
          resolveText(errorTitle, 'Action failed', result),
          resolveText(errorMessage, 'Please try again.', result),
          details,
        )
        return result
      }

      if (onSuccess) {
        await onSuccess(result)
      }

      const nextSuccessTitle = toDetails(resolve(successTitle, result))
      const nextSuccessMessage = toDetails(resolve(successMessage, result))
      if (nextSuccessTitle || nextSuccessMessage) {
        notify(app, {
          level: successLevel,
          title: nextSuccessTitle || 'Done',
          message: nextSuccessMessage || '',
        })
      }

      return result
    } catch (error) {
      const details = toDetails(resolve(errorDetails, error) || error?.message || error)
      notifyError(
        app,
        resolveText(errorTitle, 'Action failed', error),
        resolveText(errorMessage, 'Please try again.', error),
        details,
      )
      return null
    } finally {
      _endLoading(app, loadingKey)
    }
  }
}

export function controllerLastError(app, controllerId) {
  try {
    const ctrl = app.controller(controllerId)
    if (!ctrl || typeof ctrl.lastError !== 'function') return ''
    return toDetails(ctrl.lastError())
  } catch {
    return ''
  }
}

export async function runTask(app, {
  task,
  loadingKey = '',
  errorTitle = 'Action failed',
  errorMessage = 'Please try again.',
  errorDetails,
  successTitle = '',
  successMessage = '',
  successLevel = 'success',
  onSuccess,
}) {
  _beginLoading(app, loadingKey)
  try {
    const result = await task()
    if (onSuccess) {
      await onSuccess(result)
    }
    const nextSuccessTitle = toDetails(resolve(successTitle, result))
    const nextSuccessMessage = toDetails(resolve(successMessage, result))
    if (nextSuccessTitle || nextSuccessMessage) {
      notify(app, {
        level: successLevel,
        title: nextSuccessTitle || 'Done',
        message: nextSuccessMessage || '',
      })
    }
    return { ok: true, result }
  } catch (error) {
    const details = toDetails(resolve(errorDetails, error) || error?.message || error)
    notifyError(
      app,
      resolveText(errorTitle, 'Action failed', error),
      resolveText(errorMessage, 'Please try again.', error),
      details,
    )
    return { ok: false, error }
  } finally {
    _endLoading(app, loadingKey)
  }
}

export async function runBooleanAction(app, {
  action,
  loadingKey = '',
  errorTitle,
  errorMessage,
  errorDetails,
  successTitle = '',
  successMessage = '',
  successLevel = 'success',
  onSuccess,
}) {
  const { ok, result } = await runTask(app, {
    task: action,
    loadingKey,
    errorTitle,
    errorMessage,
    errorDetails,
  })

  if (!ok) {
    return false
  }

  if (!result) {
    const details = toDetails(resolve(errorDetails, result) || '')
    notifyError(
      app,
      resolveText(errorTitle, 'Action failed', result),
      resolveText(errorMessage, 'Please try again.', result),
      details,
    )
    return false
  }

  if (onSuccess) {
    await onSuccess(result)
  }
  const nextSuccessTitle = toDetails(resolve(successTitle, result))
  const nextSuccessMessage = toDetails(resolve(successMessage, result))
  if (nextSuccessTitle || nextSuccessMessage) {
    notify(app, {
      level: successLevel,
      title: nextSuccessTitle || 'Done',
      message: nextSuccessMessage || '',
    })
  }
  return true
}

export async function reloadCoreData(app) {
  await app.controller('spots').reload()
  await app.controller('social').reloadFavorites()
}

export async function reloadDashboardData(app) {
  await reloadCoreData(app)

  const uid = app.state.session.user?.id
  if (!uid) {
    app.state.social.followersCount = 0
    app.state.social.followingCount = 0
    app.state.social.followers = []
    app.state.social.following = []
    app.state.social.incomingRequests = []
    app.state.social.blockedUsers = []
    return
  }

  const [followers, following, incomingRequests, blockedUsers] = await Promise.all([
    app.controller('social').followersOf(uid),
    app.controller('social').followingOf(uid),
    app.controller('social').incomingRequests(),
    app.controller('social').blockedUsers(),
  ])
  app.state.social.followers = Array.isArray(followers) ? followers : []
  app.state.social.following = Array.isArray(following) ? following : []
  app.state.social.incomingRequests = Array.isArray(incomingRequests) ? incomingRequests : []
  app.state.social.blockedUsers = Array.isArray(blockedUsers) ? blockedUsers : []
  app.state.social.followersCount = app.state.social.followers.length
  app.state.social.followingCount = app.state.social.following.length
}
