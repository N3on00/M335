<script setup>
import { computed, reactive, watch } from 'vue'
import ActionButton from '../common/ActionButton.vue'
import { toImageSource } from '../../models/imageMapper'

const props = defineProps({
  user: { type: Object, default: null },
  theme: { type: String, default: 'light' },
  busy: { type: Boolean, default: false },
  onSave: { type: Function, required: true },
  onToggleTheme: { type: Function, required: true },
  onCopyUserId: { type: Function, required: true },
})

const form = reactive({
  username: '',
  email: '',
  displayName: '',
  bio: '',
  avatarImage: '',
  followRequiresApproval: false,
  instagram: '',
  github: '',
  website: '',
  currentPassword: '',
  newPassword: '',
  confirmNewPassword: '',
  showCurrentPassword: false,
  showNewPassword: false,
  showConfirmPassword: false,
})

const isDark = computed(() => String(props.theme || '').toLowerCase() === 'dark')

const passwordChecks = computed(() => {
  const current = String(form.currentPassword || '')
  const next = String(form.newPassword || '')
  const confirm = String(form.confirmNewPassword || '')
  const changing = next.length > 0 || confirm.length > 0 || current.length > 0

  return {
    changing,
    currentProvided: current.length > 0,
    len: next.length >= 8,
    lower: /[a-z]/.test(next),
    upper: /[A-Z]/.test(next),
    digit: /\d/.test(next),
    special: /[^A-Za-z0-9]/.test(next),
    match: next.length > 0 && confirm.length > 0 && next === confirm,
  }
})

const passwordRequirements = computed(() => [
  {
    text: 'Current password required when changing password',
    ok: passwordChecks.value.changing ? passwordChecks.value.currentProvided : false,
  },
  { text: 'Minimum 8 characters', ok: passwordChecks.value.len },
  { text: 'At least one lowercase letter', ok: passwordChecks.value.lower },
  { text: 'At least one uppercase letter', ok: passwordChecks.value.upper },
  { text: 'At least one number', ok: passwordChecks.value.digit },
  { text: 'At least one special character', ok: passwordChecks.value.special },
  { text: 'New password must match confirmation', ok: passwordChecks.value.match },
])

const canSubmitPasswordChange = computed(() => {
  if (!passwordChecks.value.changing) {
    return true
  }
  return (
    passwordChecks.value.currentProvided
    && passwordChecks.value.len
    && passwordChecks.value.lower
    && passwordChecks.value.upper
    && passwordChecks.value.digit
    && passwordChecks.value.special
    && passwordChecks.value.match
  )
})

watch(
  () => props.user,
  (user) => {
    const u = user || {}
    form.username = String(u.username || '')
    form.email = String(u.email || '')
    form.displayName = String(u.display_name || u.displayName || '')
    form.bio = String(u.bio || '')
    form.avatarImage = String(u.avatar_image || u.avatarImage || '')
    form.followRequiresApproval = Boolean(u.follow_requires_approval)

    const social = u.social_accounts && typeof u.social_accounts === 'object' ? u.social_accounts : {}
    form.instagram = String(social.instagram || '')
    form.github = String(social.github || '')
    form.website = String(social.website || '')

    form.currentPassword = ''
    form.newPassword = ''
    form.confirmNewPassword = ''
  },
  { immediate: true, deep: true },
)

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('Could not read image file'))
    reader.onload = () => {
      const out = String(reader.result || '')
      const idx = out.indexOf(',')
      resolve(idx >= 0 ? out.slice(idx + 1) : out)
    }
    reader.readAsDataURL(file)
  })
}

async function onAvatarSelect(event) {
  const file = event?.target?.files?.[0]
  if (!file) return
  try {
    form.avatarImage = await readFileAsBase64(file)
  } catch {
    form.avatarImage = ''
  }
  if (event.target) {
    event.target.value = ''
  }
}

function submit() {
  if (!canSubmitPasswordChange.value) {
    return
  }

  props.onSave({
    username: form.username,
    email: form.email,
    displayName: form.displayName,
    bio: form.bio,
    avatarImage: form.avatarImage,
    followRequiresApproval: form.followRequiresApproval,
    socialAccounts: {
      instagram: form.instagram,
      github: form.github,
      website: form.website,
    },
    currentPassword: form.currentPassword,
    newPassword: form.newPassword,
  })
}
</script>

<template>
  <section class="card border-0 shadow-sm" data-aos="fade-up" data-aos-delay="80">
    <div class="card-body d-grid gap-3 p-4">
      <div class="settings-theme-row">
        <div>
          <h3 class="h5 mb-1">Theme</h3>
          <p class="text-secondary mb-0">Switch between light and dark mode.</p>
        </div>
        <ActionButton
          :class-name="isDark ? 'btn btn-outline-warning' : 'btn btn-outline-secondary'"
          :icon="isDark ? 'bi-sun' : 'bi-moon-stars'"
          :label="isDark ? 'Light mode' : 'Dark mode'"
          @click="onToggleTheme"
        />
      </div>

      <div class="social-self-id">
        <span class="text-secondary">User id</span>
        <ActionButton class-name="btn btn-link p-0 social-self-id__button" aria-label="Copy user id" @click="onCopyUserId">
          <code>{{ user?.id || '-' }}</code>
          <i class="bi bi-clipboard ms-2"></i>
        </ActionButton>
      </div>

      <div class="row g-2">
        <div class="col-12 col-md-6">
          <label class="form-label">Username</label>
          <input class="form-control" v-model="form.username" :disabled="busy" />
        </div>
        <div class="col-12 col-md-6">
          <label class="form-label">Email</label>
          <input class="form-control" v-model="form.email" :disabled="busy" />
        </div>
      </div>

      <div class="row g-2">
        <div class="col-12 col-md-6">
          <label class="form-label">Display name</label>
          <input class="form-control" v-model="form.displayName" :disabled="busy" />
        </div>
        <div class="col-12 col-md-6 d-grid align-content-end">
          <label class="form-check mt-4">
            <input class="form-check-input" type="checkbox" v-model="form.followRequiresApproval" :disabled="busy" />
            <span class="form-check-label">Require approval for followers</span>
          </label>
        </div>
      </div>

      <div>
        <label class="form-label">Biography</label>
        <textarea class="form-control" rows="4" maxlength="1200" v-model="form.bio" :disabled="busy" />
      </div>

      <div class="row g-2">
        <div class="col-12 col-md-4">
          <label class="form-label">Instagram</label>
          <input class="form-control" v-model="form.instagram" placeholder="https://instagram.com/..." :disabled="busy" />
        </div>
        <div class="col-12 col-md-4">
          <label class="form-label">GitHub</label>
          <input class="form-control" v-model="form.github" placeholder="https://github.com/..." :disabled="busy" />
        </div>
        <div class="col-12 col-md-4">
          <label class="form-label">Website</label>
          <input class="form-control" v-model="form.website" placeholder="https://..." :disabled="busy" />
        </div>
      </div>

      <div>
        <label class="form-label">Profile picture</label>
        <input class="form-control" type="file" accept="image/png,image/jpeg,image/webp" :disabled="busy" @change="onAvatarSelect" />
        <div class="settings-avatar-preview" v-if="form.avatarImage">
          <img :src="toImageSource(form.avatarImage)" alt="avatar preview" loading="lazy" />
        </div>
      </div>

      <div class="row g-2">
        <div class="col-12 col-md-4">
          <label class="form-label">Current password</label>
          <div class="input-group">
            <input class="form-control" :type="form.showCurrentPassword ? 'text' : 'password'" v-model="form.currentPassword" :disabled="busy" />
            <ActionButton class-name="btn btn-outline-secondary" label="Show" @click="form.showCurrentPassword = !form.showCurrentPassword" />
          </div>
        </div>
        <div class="col-12 col-md-4">
          <label class="form-label">New password</label>
          <div class="input-group">
            <input class="form-control" :type="form.showNewPassword ? 'text' : 'password'" v-model="form.newPassword" :disabled="busy" />
            <ActionButton class-name="btn btn-outline-secondary" label="Show" @click="form.showNewPassword = !form.showNewPassword" />
          </div>
        </div>
        <div class="col-12 col-md-4">
          <label class="form-label">Confirm password</label>
          <div class="input-group">
            <input class="form-control" :type="form.showConfirmPassword ? 'text' : 'password'" v-model="form.confirmNewPassword" :disabled="busy" />
            <ActionButton class-name="btn btn-outline-secondary" label="Show" @click="form.showConfirmPassword = !form.showConfirmPassword" />
          </div>
        </div>
      </div>

      <ul class="auth-rules settings-password-rules">
        <li
          class="auth-rule"
          :class="rule.ok ? 'auth-rule--ok' : 'auth-rule--pending'"
          v-for="(rule, index) in passwordRequirements"
          :key="`settings-password-rule-${index}`"
        >
          <i class="bi" :class="rule.ok ? 'bi-check-circle-fill' : 'bi-dot'"></i>
          {{ rule.text }}
        </li>
      </ul>

      <ActionButton
        label="Save settings"
        icon="bi-save"
        :busy="busy"
        busy-label="Saving..."
        class-name="btn btn-primary"
        @click="submit"
      />
    </div>
  </section>
</template>
