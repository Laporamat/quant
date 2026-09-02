<template>
  <button
    @click="themeStore.toggle()"
    class="relative w-10 h-10 rounded-lg btn-ghost flex items-center justify-center overflow-hidden"
    :title="themeStore.theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'"
  >
    <transition name="icon-spin" mode="out-in">
      <!-- Sun (light mode) -->
      <svg v-if="themeStore.theme === 'light'" key="sun"
        class="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
      </svg>
      <!-- Moon (dark mode) -->
      <svg v-else key="moon"
        class="w-5 h-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
      </svg>
    </transition>
  </button>
</template>

<script setup lang="ts">
import { useThemeStore } from '@/stores/appStore'
const themeStore = useThemeStore()
</script>

<style scoped>
.icon-spin-enter-active, .icon-spin-leave-active {
  transition: opacity 0.2s ease, transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.icon-spin-enter-from { opacity: 0; transform: rotate(-90deg) scale(0.5); }
.icon-spin-leave-to   { opacity: 0; transform: rotate(90deg) scale(0.5); }
</style>
