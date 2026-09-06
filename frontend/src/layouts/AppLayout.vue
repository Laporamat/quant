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
            class="hidden sm:flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full"
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

          <!-- User avatar / login button -->
          <RouterLink v-if="authStore.isLoggedIn" to="/profile"
            class="flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-surface-700/50 transition-colors">
            <div class="w-6 h-6 rounded-lg bg-primary-600/30 flex items-center justify-center text-xs font-bold text-primary-300 shrink-0">
              {{ authStore.displayName[0]?.toUpperCase() }}
            </div>
            <span class="hidden sm:block text-xs font-medium text-surface-200">{{ authStore.displayName }}</span>
          </RouterLink>
          <RouterLink v-else to="/login"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-600/20 hover:bg-primary-600/30 text-primary-300 text-xs font-medium border border-primary-600/30 transition-all">
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75"/>
            </svg>
            เข้าสู่ระบบ
          </RouterLink>
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
import { useAppStore }  from '@/stores/appStore'
import { useAuthStore } from '@/stores/authStore'
import { http } from '@/api/client'

const route      = useRoute()
const appStore   = useAppStore()
const authStore  = useAuthStore()

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
