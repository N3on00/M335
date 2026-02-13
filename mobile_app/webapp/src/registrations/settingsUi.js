import { registerAction, registerComponent } from '../core/registry'
import SettingsHero from '../components/settings/SettingsHero.vue'
import SettingsForm from '../components/settings/SettingsForm.vue'
import {
  copyTextToClipboard,
  controllerLastError,
  reloadDashboardData,
  runBooleanAction,
  runTask,
  toggleTheme,
} from './uiShared'

registerAction('settings.load', async ({ app }) => {
  await app.controller('users').refreshProfile()
  await reloadDashboardData(app)
})

registerComponent({
  screen: 'settings',
  slot: 'header',
  id: 'settings.hero',
  order: 10,
  component: SettingsHero,
  buildProps: ({ app, router }) => ({
    onBackHome: () => router.push('/home'),
    onOpenSocial: () => router.push('/social'),
    onOpenSupport: () => router.push('/support'),
    onOpenProfile: () => router.push(`/profile/${app.state.session.user?.id || ''}`),
  }),
})

registerComponent({
  screen: 'settings',
  slot: 'main',
  id: 'settings.form',
  order: 10,
  component: SettingsForm,
  buildProps: ({ app }) => ({
    user: app.state.session.user,
    theme: app.state.ui.theme,
    busy: app.state.loading.settingsSave,
    onCopyUserId: () => {
      return copyTextToClipboard(app, {
        text: app.state.session.user?.id,
        successTitle: 'Copied',
        successMessage: 'Your user id was copied.',
      })
    },
    onToggleTheme: async () => {
      const next = toggleTheme(app)
      await runTask(app, {
        task: async () => next,
        successTitle: 'Theme updated',
        successMessage: () => `Switched to ${next} mode.`,
      })
    },
    onSave: async (payload) => {
      await runBooleanAction(app, {
        action: () => app.controller('users').updateProfile(payload),
        loadingKey: 'settingsSave',
        errorTitle: 'Settings save failed',
        errorMessage: 'Could not update your profile settings.',
        errorDetails: () => controllerLastError(app, 'users'),
        onSuccess: async () => {
          await reloadDashboardData(app)
        },
        successTitle: 'Settings saved',
        successMessage: 'Your profile has been updated.',
      })
    },
  }),
})
