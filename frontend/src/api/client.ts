import axios, { type AxiosInstance, type AxiosError } from 'axios'
import { useToastStore } from '@/stores/appStore'

const BASE_URL = import.meta.env.VITE_API_BASE ?? '/api'

export const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor ───────────────────────────────────────────────────────
http.interceptors.request.use((config) => config)

// ── Response interceptor — toast on error ────────────────────────────────────
http.interceptors.response.use(
  (res) => res,
  async (err: AxiosError) => {
    const detail =
      (err.response?.data as { detail?: string })?.detail ??
      err.message ??
      'Unknown error'

    // Attempt 1 retry for network errors only
    const config = err.config as typeof err.config & { _retry?: boolean }
    if (!err.response && !config._retry) {
      config._retry = true
      await new Promise((r) => setTimeout(r, 800))
      return http(config)
    }

    // Show toast (lazy-load store to avoid circular deps at module init)
    try {
      const toast = useToastStore()
      toast.error(`API Error: ${detail}`)
    } catch (_) { /* store not ready yet */ }

    return Promise.reject(err)
  }
)
