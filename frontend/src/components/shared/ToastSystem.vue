<template>
  <Teleport to="body">
    <div class="fixed bottom-5 right-5 z-[9999] flex flex-col gap-2 pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toastStore.toasts"
          :key="toast.id"
          class="pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl shadow-card-lg border max-w-sm w-full animate-slide-up"
          :class="{
            'bg-surface-800 border-bull/30':     toast.type === 'success',
            'bg-surface-800 border-bear/30':     toast.type === 'error',
            'bg-surface-800 border-side/30':     toast.type === 'warning',
            'bg-surface-800 border-primary-500/30': toast.type === 'info',
          }"
        >
          <!-- Icon -->
          <span class="mt-0.5 shrink-0" :class="{
            'text-bull': toast.type === 'success',
            'text-bear': toast.type === 'error',
            'text-side': toast.type === 'warning',
            'text-primary-400': toast.type === 'info',
          }">
            <svg v-if="toast.type === 'success'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <svg v-else-if="toast.type === 'error'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <svg v-else-if="toast.type === 'warning'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126z" /></svg>
            <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" /></svg>
          </span>

          <p class="flex-1 text-sm text-surface-100 leading-snug">{{ toast.message }}</p>

          <button @click="toastStore.remove(toast.id)" class="text-surface-500 hover:text-surface-200 transition-colors shrink-0">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useToastStore } from '@/stores/appStore'
const toastStore = useToastStore()
</script>

<style scoped>
.toast-enter-active { transition: all .3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.toast-leave-active { transition: all .2s ease; }
.toast-enter-from   { opacity: 0; transform: translateX(32px); }
.toast-leave-to     { opacity: 0; transform: translateX(32px); }
.toast-move         { transition: transform .3s ease; }
</style>
