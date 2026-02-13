<script setup>
import ActionButton from '../common/ActionButton.vue'

const props = defineProps({
  filters: { type: Object, default: () => ({}) },
  activeLocationLabel: { type: String, default: '' },
  resultCount: { type: Number, default: 0 },
  totalCount: { type: Number, default: 0 },
  canReset: { type: Boolean, default: false },
})

const emit = defineEmits(['update:filters', 'reset'])

function updateField(key, value) {
  const current = props.filters && typeof props.filters === 'object' ? props.filters : {}
  emit('update:filters', {
    ...current,
    [key]: value,
  })
}

function updateRadius(value) {
  const parsed = Number(value)
  updateField('radiusKm', Number.isFinite(parsed) ? parsed : 0)
}
</script>

<template>
  <section class="card border-0 shadow-sm map-widget-card" data-aos="fade-up" data-aos-delay="55">
    <div class="card-body d-grid gap-3 p-3">
      <header class="d-flex flex-wrap align-items-start justify-content-between gap-2">
        <div>
          <h3 class="h6 mb-1">Search spots</h3>
          <p class="small text-secondary mb-0">Filter by text, tags, profile, visibility, and distance.</p>
        </div>
        <span class="badge text-bg-light">{{ resultCount }} / {{ totalCount }}</span>
      </header>

      <div class="map-search-grid">
        <label>
          <span class="small text-secondary">Search text</span>
          <input
            class="form-control"
            :value="String(filters.text || '')"
            placeholder="Title, description"
            @input="updateField('text', $event.target.value)"
          />
        </label>

        <label>
          <span class="small text-secondary">Tags</span>
          <input
            class="form-control"
            :value="String(filters.tagsText || '')"
            placeholder="nature, quiet"
            @input="updateField('tagsText', $event.target.value)"
          />
        </label>

        <label>
          <span class="small text-secondary">Profile</span>
          <input
            class="form-control"
            :value="String(filters.ownerText || '')"
            placeholder="@username or name"
            @input="updateField('ownerText', $event.target.value)"
          />
        </label>

        <label>
          <span class="small text-secondary">Visibility</span>
          <select
            class="form-select"
            :value="String(filters.visibility || 'all')"
            @change="updateField('visibility', $event.target.value)"
          >
            <option value="all">All</option>
            <option value="public">Public</option>
            <option value="following">Followers only</option>
            <option value="invite_only">Invite only</option>
            <option value="personal">Personal</option>
          </select>
        </label>

        <label>
          <span class="small text-secondary">Radius</span>
          <select
            class="form-select"
            :value="Number(filters.radiusKm || 0)"
            @change="updateRadius($event.target.value)"
          >
            <option :value="0">All distances</option>
            <option :value="1">1 km</option>
            <option :value="5">5 km</option>
            <option :value="10">10 km</option>
            <option :value="25">25 km</option>
            <option :value="50">50 km</option>
          </select>
        </label>

        <label class="map-search-checkbox">
          <input
            class="map-search-checkbox__input"
            type="checkbox"
            :checked="Boolean(filters.onlyFavorites)"
            @change="updateField('onlyFavorites', Boolean($event.target.checked))"
          />
          <span class="map-search-checkbox__label">Only liked spots</span>
        </label>
      </div>

      <div class="map-active-location" v-if="activeLocationLabel">
        <span class="badge text-bg-info">Location: {{ activeLocationLabel }}</span>
      </div>

      <div class="d-flex justify-content-end" v-if="canReset">
        <ActionButton class-name="btn btn-sm btn-outline-secondary" label="Reset spot filters" @click="emit('reset')" />
      </div>
    </div>
  </section>
</template>
