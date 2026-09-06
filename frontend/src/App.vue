<template>
  <div :class="themeStore.theme">
    <!-- Auth pages (Login/Register) have no app layout -->
    <template v-if="route.meta.hideLayout">
      <router-view v-slot="{ Component, route: r }">
        <transition name="page" mode="out-in">
          <component :is="Component" :key="r.path" />
        </transition>
      </router-view>
    </template>

    <!-- Main app with sidebar -->
    <template v-else>
      <AppLayout>
        <router-view v-slot="{ Component, route: r }">
          <transition name="page" mode="out-in">
            <component :is="Component" :key="r.path" />
          </transition>
        </router-view>
      </AppLayout>
    </template>

    <ToastSystem />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import AppLayout   from '@/layouts/AppLayout.vue'
import ToastSystem from '@/components/shared/ToastSystem.vue'
import { useThemeStore } from '@/stores/appStore'

const route      = useRoute()
const themeStore = useThemeStore()
</script>
