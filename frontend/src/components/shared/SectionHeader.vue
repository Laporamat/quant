<template>
  <div class="flex items-start justify-between mb-5">
    <div>
      <h2 class="text-lg font-bold text-surface-100">{{ title }}</h2>
      <p v-if="description" class="text-sm text-surface-400 mt-0.5">{{ description }}</p>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string; description?: string }>()
</script>
