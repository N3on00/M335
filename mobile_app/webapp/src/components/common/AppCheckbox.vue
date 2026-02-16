<script setup>
const props = defineProps({
  modelValue: { type: Boolean, default: false },
  label: { type: String, default: '' },
  id: { type: String, default: '' },
  name: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  wrapperClass: { type: String, default: 'app-checkbox' },
  inputClass: { type: String, default: 'app-checkbox__input' },
  labelClass: { type: String, default: 'app-checkbox__label' },
})

const emit = defineEmits(['update:modelValue', 'change'])

function onChange(event) {
  const checked = Boolean(event?.target?.checked)
  emit('update:modelValue', checked)
  emit('change', checked)
}
</script>

<template>
  <label :class="wrapperClass" :for="id || undefined">
    <input
      :id="id || undefined"
      :name="name || undefined"
      type="checkbox"
      :class="inputClass"
      :checked="Boolean(modelValue)"
      :disabled="disabled"
      @change="onChange"
    />
    <span :class="labelClass"><slot>{{ label }}</slot></span>
  </label>
</template>
