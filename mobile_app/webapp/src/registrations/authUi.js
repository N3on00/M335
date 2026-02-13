import { registerAction, registerComponent } from '../core/registry'
import AuthHero from '../components/auth/AuthHero.vue'
import AuthForms from '../components/auth/AuthForms.vue'
import AuthSupport from '../components/auth/AuthSupport.vue'
import { toUserErrorMessage } from '../services/apiErrors'
import { controllerLastError, notifyInfo, reloadCoreData, runBooleanAction } from './uiShared'

registerAction('auth.help', ({ app }) => {
  notifyInfo(
    app,
    'Support',
    'If sign-in fails, contact support with details.',
    `Support: ${app.state.config.supportEmail}\nBackend: ${app.state.config.apiBaseUrl}`,
  )
})

registerComponent({
  screen: 'auth',
  slot: 'header',
  id: 'auth.hero',
  order: 10,
  component: AuthHero,
  buildProps: () => ({
    title: 'Welcome to SpotOnSight',
    subtitle: 'Professional map sharing experience with secure accounts.',
  }),
})

registerComponent({
  screen: 'auth',
  slot: 'main',
  id: 'auth.forms',
  order: 10,
  component: AuthForms,
  buildProps: ({ app, router }) => {
    const authError = () => controllerLastError(app, 'auth')

    function authErrorMessage(fallback) {
      return toUserErrorMessage(authError(), fallback)
    }

    const authErrorDetails = () => authErrorMessage('')

    async function submitAuth({
      action,
      errorTitle,
      errorMessage,
      successTitle,
      successMessage,
    }) {
      await runBooleanAction(app, {
        action,
        errorTitle,
        errorMessage,
        errorDetails: authErrorDetails,
        successTitle,
        successMessage,
        onSuccess: async () => {
          await reloadCoreData(app)
          router.push('/home')
        },
      })
    }

    return {
      onLogin: async ({ usernameOrEmail, password }) => {
        await submitAuth({
          action: () => app.controller('auth').login(usernameOrEmail, password),
          errorTitle: 'Login failed',
          errorMessage: () => authErrorMessage('Please check credentials and backend availability.'),
          successTitle: 'Welcome',
          successMessage: 'You are signed in.',
        })
      },
      onRegister: async ({ username, email, displayName, password }) => {
        await submitAuth({
          action: () => app.controller('auth').register({ username, email, displayName, password }),
          errorTitle: 'Registration failed',
          errorMessage: () => authErrorMessage('Could not create account.'),
          successTitle: 'Account ready',
          successMessage: 'Registration completed.',
        })
      },
    }
  },
})

registerComponent({
  screen: 'auth',
  slot: 'footer',
  id: 'auth.support',
  order: 10,
  component: AuthSupport,
  buildProps: ({ app }) => ({
    supportEmail: app.state.config.supportEmail,
    onHelp: () => app.ui.runAction('auth.help'),
  }),
})
