<template>
  <div class="flex items-center gap-2 flex-wrap">
    <!-- Presets -->
    <div class="flex items-center gap-1">
      <button
        v-for="p in PRESET_RANGES"
        :key="p.label"
        @click="applyPreset(p.days)"
        class="px-2.5 py-1 text-xs rounded-md font-medium transition-all duration-150"
        :class="activePreset === p.label
          ? 'bg-primary-600 text-white'
          : 'bg-surface-800 text-surface-400 hover:text-white hover:bg-surface-700'"
      >
        {{ p.label }}
      </button>
    </div>

    <!-- Custom range -->
    <div class="flex items-center gap-1.5 text-xs">
      <input
        type="date"
        :value="modelValue.start"
        @change="onStartChange"
        class="bg-surface-800 border border-surface-700 text-surface-200 rounded-md px-2 py-1 focus:border-primary-500 outline-none"
      />
      <span class="text-surface-500">→</span>
      <input
        type="date"
        :value="modelValue.end"
        @change="onEndChange"
        class="bg-surface-800 border border-surface-700 text-surface-200 rounded-md px-2 py-1 focus:border-primary-500 outline-none"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import dayjs from 'dayjs'
import { PRESET_RANGES, type DateRange } from '@/types'

const props = defineProps<{ modelValue: DateRange }>()
const emit  = defineEmits<{ 'update:modelValue': [v: DateRange] }>()

const activePreset = ref('1Y')

function applyPreset(days: number) {
  const end   = dayjs().format('YYYY-MM-DD')
  const start = dayjs().subtract(days, 'day').format('YYYY-MM-DD')
  const preset = PRESET_RANGES.find((p) => p.days === days)
  if (preset) activePreset.value = preset.label
  emit('update:modelValue', { start, end })
}

function onStartChange(e: Event) {
  activePreset.value = ''
  emit('update:modelValue', { ...props.modelValue, start: (e.target as HTMLInputElement).value })
}

function onEndChange(e: Event) {
  activePreset.value = ''
  emit('update:modelValue', { ...props.modelValue, end: (e.target as HTMLInputElement).value })
}
</script>
