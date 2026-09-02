<template>
  <div :class="themeStore.theme">
    <AppLayout>
      <!--
        key = route.path so the transition fires on navigation.
        Suspense wraps lazy-loaded views — shows nothing extra
        (each view handles its own skeleton states).
      -->
      <router-view v-slot="{ Component, route }">
        <transition name="page" mode="out-in">
          <Suspense :key="route.path">
            <component :is="Component" />
            <template #fallback>
              <!-- Ultra-thin page skeleton shown while the JS chunk downloads -->
              <div class="space-y-4 animate-pulse py-2">
                <div class="h-7 w-48 bg-surface-700/50 rounded-lg" />
                <div class="grid grid-cols-3 gap-3">
                  <div v-for="i in 6" :key="i" class="h-20 bg-surface-700/40 rounded-xl" />
                </div>
                <div class="h-64 bg-surface-700/30 rounded-xl" />
              </div>
            </template>
          </Suspense>
        </transition>
      </router-view>
    </AppLayout>
    <ToastSystem />
  </div>
</template>

<script setup lang="ts">
import AppLayout   from '@/layouts/AppLayout.vue'
import ToastSystem from '@/components/shared/ToastSystem.vue'
import { useThemeStore } from '@/stores/appStore'

const themeStore = useThemeStore()
</script>
