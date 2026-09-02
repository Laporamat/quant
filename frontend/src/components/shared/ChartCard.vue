<template>
  <div class="chart-card">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <div>
        <h3 class="text-sm font-semibold text-surface-100">{{ title }}</h3>
        <p v-if="subtitle" class="text-xs text-surface-400 mt-0.5">{{ subtitle }}</p>
      </div>
      <div class="flex items-center gap-1">
        <slot name="toolbar" />
        <button
          v-if="!hideRefresh"
          @click="$emit('refresh')"
          class="btn-ghost p-1.5 text-surface-400 hover:text-white"
          title="Refresh"
        >
          <svg class="w-4 h-4" :class="loading ? 'animate-spin' : ''" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading" class="flex items-center justify-center" :style="{ height: `${height}px` }">
      <div class="w-full h-full bg-surface-700/50 rounded-lg animate-skeleton" />
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="flex flex-col items-center justify-center gap-2 text-surface-400" :style="{ height: `${height}px` }">
      <svg class="w-8 h-8 text-bear/50" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
      </svg>
      <p class="text-sm">{{ error }}</p>
      <button @click="$emit('refresh')" class="btn-ghost text-xs px-3 py-1">Retry</button>
    </div>

    <!-- Empty state -->
    <div v-else-if="empty" class="flex flex-col items-center justify-center gap-2 text-surface-500" :style="{ height: `${height}px` }">
      <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
      <p class="text-sm">No data available</p>
    </div>

    <!-- Content -->
    <div v-else>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  title:        string
  subtitle?:    string
  loading?:     boolean
  error?:       string | null
  empty?:       boolean
  height?:      number
  hideRefresh?: boolean
}>(), {
  loading:      false,
  error:        null,
  empty:        false,
  height:       300,
  hideRefresh:  false,
})

defineEmits<{ refresh: [] }>()
</script>
