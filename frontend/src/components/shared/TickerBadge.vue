<template>
  <RouterLink
    :to="`/ticker/${ticker}`"
    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-mono text-xs font-semibold
           bg-primary-600/15 text-primary-300 border border-primary-600/25
           hover:bg-primary-600/30 hover:text-primary-200 hover:border-primary-500/50
           transition-all duration-150 cursor-pointer"
    :title="`Open ${ticker} deep dive`"
  >
    {{ ticker }}
    <svg class="w-2.5 h-2.5 opacity-60" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
    </svg>
  </RouterLink>
</template>

<script setup lang="ts">
defineProps<{ ticker: string }>()
</script>
