import { AppContext } from '../core/context'
import { UIController } from '../core/uiController'
import { createAppState } from '../state/appState'
import { ApiClient } from '../services/apiClient'
import { AuthService } from '../services/authService'
import { SpotsService } from '../services/spotsService'
import { SocialService } from '../services/socialService'
import { UsersService } from '../services/usersService'
import { LocationSearchService } from '../services/locationSearchService'
import { SupportService } from '../services/supportService'
import { NotificationService } from '../services/notificationService'
import { ActivityWatchService } from '../services/activityWatchService'
import { AuthController } from '../controllers/authController'
import { SpotsController } from '../controllers/spotsController'
import { SocialController } from '../controllers/socialController'
import { UsersController } from '../controllers/usersController'
import { SupportController } from '../controllers/supportController'
import { registerUi } from './uiRegistrations'

export function buildAppContext() {
  const state = createAppState()

  const serviceFactories = {
    apiClient: (ctx) => new ApiClient(ctx.state.config.apiBaseUrl),
    authService: (ctx) => new AuthService(ctx.service('apiClient'), ctx.state),
    spotsService: (ctx) => new SpotsService(ctx.service('apiClient'), ctx.state),
    socialService: (ctx) => new SocialService(ctx.service('apiClient'), ctx.state),
    usersService: (ctx) => new UsersService(ctx.service('apiClient'), ctx.state),
    locationSearch: () => new LocationSearchService(),
    supportService: (ctx) => new SupportService(ctx.service('apiClient'), ctx.state),
    notify: (ctx) => new NotificationService(ctx.state),
    activityWatch: (ctx) => new ActivityWatchService(ctx),
  }

  const controllerFactories = {
    auth: (ctx) => new AuthController(ctx),
    spots: (ctx) => new SpotsController(ctx),
    social: (ctx) => new SocialController(ctx),
    users: (ctx) => new UsersController(ctx),
    support: (ctx) => new SupportController(ctx),
  }

  const ctx = new AppContext({ state, serviceFactories, controllerFactories })
  ctx.ui = new UIController(ctx)
  registerUi()
  return ctx
}
