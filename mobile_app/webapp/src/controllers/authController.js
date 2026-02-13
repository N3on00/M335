import { persistSession } from '../state/appState'
import { BaseController } from './baseController'

export class AuthController extends BaseController {
  constructor(ctx) {
    super(ctx, 'authService')
  }

  async login(usernameOrEmail, password) {
    const ok = await this.service().login(usernameOrEmail, password)
    if (ok) {
      persistSession(this.ctx.state)
    }
    return ok
  }

  async register(input) {
    const ok = await this.service().register(input)
    if (ok) {
      persistSession(this.ctx.state)
    }
    return ok
  }

  logout() {
    this.service().logout()
    this.ctx.state.favorites = []
    persistSession(this.ctx.state)
  }

  isAuthenticated() {
    return Boolean(this.ctx.state.session.token)
  }
}
