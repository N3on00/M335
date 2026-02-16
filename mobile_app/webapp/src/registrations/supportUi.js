import { registerComponent } from '../core/registry'
import SupportHero from '../components/support/SupportHero.vue'
import SupportForm from '../components/support/SupportForm.vue'
import { controllerLastError, runBooleanAction } from './uiShared'

registerComponent({
  screen: 'support',
  slot: 'header',
  id: 'support.hero',
  order: 10,
  component: SupportHero,
})

registerComponent({
  screen: 'support',
  slot: 'main',
  id: 'support.form',
  order: 10,
  component: SupportForm,
  buildProps: ({ app, router }) => ({
    user: app.state.session.user,
    currentPath: router.currentRoute.value.fullPath,
    busy: app.state.loading.supportSubmit,
    onSubmit: async (payload) => {
      return runBooleanAction(app, {
        action: () => app.controller('support').submitTicket(payload),
        loadingKey: 'supportSubmit',
        errorTitle: 'Support request failed',
        errorMessage: 'Could not submit your support request.',
        errorDetails: () => controllerLastError(app, 'support'),
        successTitle: 'Request sent',
        successMessage: (ticket) => {
          const id = String(ticket?.id || '').trim()
          if (!id) return 'Support request submitted successfully.'
          return `Support ticket ${id} submitted.`
        },
      })
    },
  }),
})
