<template>
  <div :class="themeStore.theme">
    <AppLayout>
      <router-view v-slot="{ Component, route }">
        <transition name="page" mode="out-in">
          <component :is="Component" :key="route.path" />
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
