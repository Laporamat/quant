import axios, { type AxiosInstance, type AxiosError } from 'axios'
import { useToastStore } from '@/stores/appStore'

const BASE_URL = import.meta.env.VITE_API_BASE ?? '/api'

export const http: AxiosInstance = axios.create({
  baseURL:         BASE_URL,
  timeout:         60_000,
  withCredentials: true,   // send HttpOnly cookies (refresh token)
  headers:         { 'Content-Type': 'application/json' },
})

// Restore access token from localStorage on module load
const storedToken = localStorage.getItem('qd_access')
if (storedToken) {
  http.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
}

// ── Response interceptor ───────────────────────────────────────────────────────
http.interceptors.response.use(
  (res) => res,
  async (err: AxiosError) => {
    const status = err.response?.status
    const config = err.config as typeof err.config & {
      _retry?: boolean; _silent?: boolean
    }

    // ── 401 → try silent refresh once ────────────────────────────────────────
    if (status === 401 && !config._retry && !config.url?.includes('/auth/')) {
      config._retry = true
      try {
        // Lazy-import to avoid circular dep at module init
        const { useAuthStore } = await import('@/stores/authStore')
        const authStore = useAuthStore()
        const newToken  = await authStore.silentRefresh()
        config.headers  = config.headers ?? {}
        config.headers['Authorization'] = `Bearer ${newToken}`
        return http(config)
      } catch {
        // Refresh failed — redirect to login
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`
        }
        return Promise.reject(err)
      }
    }

    // ── Retry on network error (no response) ─────────────────────────────────
    if (!err.response && !config._retry) {
      config._retry = true
      await new Promise((r) => setTimeout(r, 800))
      return http(config)
    }

    // ── Toast on server errors only (not 401/404/422) ─────────────────────────
    const shouldToast =
      !config._silent &&
      status !== undefined &&
      status !== 401 &&
      status !== 404 &&
      status !== 422 &&
      !(status >= 200 && status < 300)

    if (shouldToast) {
      const detail =
        (err.response?.data as { detail?: string })?.detail ?? err.message ?? 'Unknown error'
      try {
        useToastStore().error(`Error ${status}: ${detail}`)
      } catch { /* store not ready */ }
    }

    return Promise.reject(err)
  }
)
