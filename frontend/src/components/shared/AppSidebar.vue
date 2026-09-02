<template>
  <aside
    class="flex flex-col shrink-0 border-r border-surface-700/50 bg-surface-900 transition-[width] duration-300 overflow-hidden"
    :class="appStore.sidebarOpen ? 'w-56' : 'w-14'"
  >
    <!-- Logo -->
    <div class="flex items-center gap-2.5 px-3 h-14 border-b border-surface-700/50 shrink-0">
      <div class="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center shrink-0">
        <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <polyline points="3 17 9 11 13 15 21 7" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <Transition name="fade-text">
        <span v-if="appStore.sidebarOpen" class="font-bold text-white text-sm tracking-wide whitespace-nowrap">
          QuantDash
        </span>
      </Transition>
    </div>

    <!-- Nav items -->
    <nav class="flex-1 py-3 flex flex-col gap-0.5 overflow-y-auto overflow-x-hidden scrollbar-thin">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="relative flex items-center gap-3 px-3 py-2.5 mx-1.5 rounded-lg text-surface-400 hover:text-white hover:bg-surface-700/50 transition-colors duration-150 group"
        :class="{ 'text-white bg-primary-600/20 !text-primary-400': isActive(item.to) }"
      >
        <!-- Icon via path string — no extra component overhead -->
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" :d="item.iconPath" />
        </svg>

        <Transition name="fade-text">
          <span v-if="appStore.sidebarOpen" class="text-sm font-medium whitespace-nowrap">
            {{ item.label }}
          </span>
        </Transition>

        <!-- Tooltip when collapsed -->
        <div
          v-if="!appStore.sidebarOpen"
          class="pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-2 z-50
                 opacity-0 group-hover:opacity-100 transition-opacity duration-150"
        >
          <div class="bg-surface-700 text-white text-xs px-2.5 py-1.5 rounded-md shadow-lg whitespace-nowrap">
            {{ item.label }}
          </div>
        </div>
      </RouterLink>
    </nav>

    <!-- Bottom hint -->
    <Transition name="fade-text">
      <div v-if="appStore.sidebarOpen" class="px-4 py-3 border-t border-surface-700/50 shrink-0">
        <p class="text-xs text-surface-500">20yr Historical Data</p>
        <p class="text-xs text-surface-600">SP100 · SET50 · ETFs</p>
      </div>
    </Transition>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAppStore } from '@/stores/appStore'

const route    = useRoute()
const appStore = useAppStore()

function isActive(path: string) {
  if (path === '/dashboard') return route.path === '/dashboard'
  return route.path.startsWith(path)
}

// Single SVG path per icon — one <path> per nav item, no extra components
const navItems = [
  {
    to: '/dashboard',
    label: 'Dashboard',
    iconPath: 'M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25A2.25 2.25 0 0113.5 8.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z',
  },
  {
    to: '/ticker',
    label: 'Ticker Dive',
    iconPath: 'M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941',
  },
  {
    to: '/compare',
    label: 'Compare',
    iconPath: 'M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 01-2.031.352 5.988 5.988 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.97z',
  },
  {
    to: '/stats-hub',
    label: 'Stats Hub',
    iconPath: 'M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15m-6.075-6.948a2.25 2.25 0 01-.659-1.591V3.104',
  },
  {
    to: '/bubble',
    label: 'Bubble Detect',
    iconPath: 'M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z',
  },
  {
    to: '/backtest',
    label: 'Backtest Lab',
    iconPath: 'M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z',
  },
  {
    to: '/strategy-compare',
    label: 'Strat Compare',
    iconPath: 'M7.5 7.5h-.75A2.25 2.25 0 004.5 9.75v7.5a2.25 2.25 0 002.25 2.25h7.5a2.25 2.25 0 002.25-2.25v-7.5a2.25 2.25 0 00-2.25-2.25h-.75m-6 3.75l3 3m0 0l3-3m-3 3V1.5m6 9h.75a2.25 2.25 0 012.25 2.25v7.5a2.25 2.25 0 01-2.25 2.25h-7.5a2.25 2.25 0 01-2.25-2.25v-.75',
  },
  {
    to: '/optimizer',
    label: 'Optimizer',
    iconPath: 'M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75',
  },
  {
    to: '/monte-carlo',
    label: 'Monte Carlo',
    iconPath: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z',
  },
]
</script>

<style scoped>
.fade-text-enter-active { transition: opacity .15s ease, transform .15s ease; }
.fade-text-leave-active { transition: opacity .1s ease; }
.fade-text-enter-from   { opacity: 0; transform: translateX(-6px); }
.fade-text-leave-to     { opacity: 0; }
</style>
