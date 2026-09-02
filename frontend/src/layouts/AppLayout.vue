<template>
  <div class="flex h-screen overflow-hidden bg-surface-900 dark:bg-surface-900">
    <!-- Sidebar -->
    <AppSidebar />

    <!-- Main column -->
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <!-- Topbar -->
      <header class="flex items-center gap-3 px-5 h-14 border-b border-surface-700/50 bg-surface-900/80 backdrop-blur-sm shrink-0">
        <!-- Hamburger -->
        <button @click="appStore.toggleSidebar()" class="btn-ghost p-1.5 -ml-1">
          <IconBars3 class="w-5 h-5" />
        </button>

        <!-- Breadcrumb -->
        <nav class="flex items-center gap-1.5 text-sm text-surface-400 min-w-0">
          <span class="text-surface-500">QuantDash</span>
          <span>/</span>
          <span class="text-surface-100 truncate font-medium">{{ pageTitle }}</span>
        </nav>

        <div class="ml-auto flex items-center gap-3">
          <!-- API status -->
          <span
            class="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full"
            :class="{
              'bg-bull/10 text-bull': appStore.apiStatus === 'ok',
              'bg-bear/10 text-bear': appStore.apiStatus === 'error',
              'bg-surface-700 text-surface-400': appStore.apiStatus === 'loading',
            }"
          >
            <span class="w-1.5 h-1.5 rounded-full"
              :class="{
                'bg-bull animate-pulse': appStore.apiStatus === 'ok',
                'bg-bear': appStore.apiStatus === 'error',
                'bg-surface-400': appStore.apiStatus === 'loading',
              }"
            />
            {{ appStore.apiStatus === 'ok' ? 'API Connected' : appStore.apiStatus === 'error' ? 'API Down' : 'Connecting…' }}
          </span>

          <ThemeToggle />
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto scrollbar-thin">
        <div class="p-5 max-w-screen-2xl mx-auto">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar  from '@/components/shared/AppSidebar.vue'
import ThemeToggle from '@/components/shared/ThemeToggle.vue'
import { useAppStore } from '@/stores/appStore'
import { http } from '@/api/client'

const route    = useRoute()
const appStore = useAppStore()

const pageTitle = computed(() => String(route.meta?.title ?? 'Dashboard'))

// Health check — run after mount, non-blocking (don't await at module level)
onMounted(() => {
  // Small delay so it doesn't compete with the first paint
  setTimeout(async () => {
    try {
      await http.get('/health')
      appStore.apiStatus = 'ok'
    } catch {
      appStore.apiStatus = 'error'
    }
  }, 500)
})

// Icon inline components
const IconBars3 = { template: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5"/></svg>` }
</script>
