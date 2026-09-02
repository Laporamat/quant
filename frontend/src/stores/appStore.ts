import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Theme, Toast } from '@/types'

// ─── Theme store ──────────────────────────────────────────────────────────────
export const useThemeStore = defineStore('theme', () => {
  const theme = ref<Theme>((localStorage.getItem('theme') as Theme) ?? 'dark')

  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem('theme', theme.value)
    document.documentElement.classList.toggle('dark', theme.value === 'dark')
  }

  function init() {
    document.documentElement.classList.toggle('dark', theme.value === 'dark')
  }

  return { theme, toggle, init }
})

// ─── Toast store ──────────────────────────────────────────────────────────────
export const useToastStore = defineStore('toast', () => {
  const toasts = ref<Toast[]>([])

  function add(type: Toast['type'], message: string, duration = 4000) {
    const id = Math.random().toString(36).slice(2)
    toasts.value.push({ id, type, message })
    setTimeout(() => remove(id), duration)
  }

  function remove(id: string) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  const success = (m: string) => add('success', m)
  const error   = (m: string) => add('error', m)
  const warning = (m: string) => add('warning', m)
  const info    = (m: string) => add('info', m)

  return { toasts, add, remove, success, error, warning, info }
})

// ─── App / layout store ───────────────────────────────────────────────────────
export const useAppStore = defineStore('app', () => {
  const sidebarOpen  = ref(true)
  const apiStatus    = ref<'ok' | 'error' | 'loading'>('loading')
  const globalLoading = ref(false)

  function toggleSidebar() { sidebarOpen.value = !sidebarOpen.value }

  return { sidebarOpen, apiStatus, globalLoading, toggleSidebar }
})
