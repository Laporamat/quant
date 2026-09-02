<template>
  <div class="metric-card animate-slide-up" :style="{ animationDelay: `${delay}ms` }">
    <div class="flex items-start justify-between">
      <span class="text-xs font-medium text-surface-400 uppercase tracking-wider leading-none">{{ title }}</span>
      <span v-if="icon" class="text-surface-500" v-html="icon" />
    </div>

    <div class="flex items-baseline gap-2 mt-1.5">
      <span class="text-2xl font-bold tabular-nums" :class="valueClass">
        {{ formattedValue }}
      </span>
      <span v-if="suffix" class="text-sm text-surface-400">{{ suffix }}</span>
    </div>

    <div v-if="delta !== undefined" class="flex items-center gap-1 mt-1">
      <span class="text-xs font-medium" :class="delta >= 0 ? 'text-bull' : 'text-bear'">
        {{ delta >= 0 ? '↑' : '↓' }} {{ Math.abs(delta).toFixed(2) }}%
      </span>
      <span class="text-xs text-surface-500">{{ deltaLabel }}</span>
    </div>

    <p v-if="subtitle" class="text-xs text-surface-500 mt-1">{{ subtitle }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  title:      string
  value:      number | string | null
  suffix?:    string
  delta?:     number
  deltaLabel?: string
  subtitle?:  string
  icon?:      string
  format?:    'number' | 'percent' | 'currency' | 'raw'
  colorize?:  boolean   // green if positive, red if negative
  delay?:     number
}>(), {
  format:   'number',
  colorize: false,
  delay:    0,
})

const formattedValue = computed(() => {
  if (props.value === null || props.value === undefined) return '—'
  if (typeof props.value === 'string') return props.value
  const v = props.value as number
  if (isNaN(v)) return '—'
  switch (props.format) {
    case 'percent':  return `${(v * 100).toFixed(2)}%`
    case 'currency': return `$${v.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
    case 'raw':      return String(v)
    default:         return v.toLocaleString('en-US', { maximumFractionDigits: 4 })
  }
})

const valueClass = computed(() => {
  if (!props.colorize || typeof props.value !== 'number') return 'text-surface-100'
  return (props.value as number) >= 0 ? 'text-bull' : 'text-bear'
})
</script>
