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
    const status = err.response?.status
    const detail =
      (err.response?.data as { detail?: string })?.detail ??
      err.message ??
      'Unknown error'

    // Attempt 1 retry for network errors only (no response at all)
    const config = err.config as typeof err.config & { _retry?: boolean; _silent?: boolean }
    if (!err.response && !config._retry) {
      config._retry = true
      await new Promise((r) => setTimeout(r, 800))
      return http(config)
    }

    // 404 = data simply not downloaded yet — don't spam toast
    // 422 = validation — show once, quietly
    // Only toast on real server errors (5xx) or explicit non-404 client errors
    const shouldToast =
      !config._silent &&
      status !== 404 &&
      status !== 422 &&
      !(status && status >= 200 && status < 300)

    if (shouldToast) {
      try {
        const toast = useToastStore()
        toast.error(`API Error ${status ?? ''}: ${detail}`)
      } catch (_) { /* store not ready yet */ }
    }

    return Promise.reject(err)
  }
)
