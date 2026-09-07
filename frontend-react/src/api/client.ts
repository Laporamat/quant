import axios, { type AxiosError } from 'axios'

export const http = axios.create({
  baseURL: '/api',
  timeout: 60_000,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// Restore token on module load
const t = localStorage.getItem('qd_access')
if (t) http.defaults.headers.common['Authorization'] = `Bearer ${t}`

let _refreshing: Promise<string> | null = null

http.interceptors.response.use(
  r => r,
  async (err: AxiosError) => {
    const status = err.response?.status
    const cfg    = err.config as typeof err.config & { _retry?: boolean }

    if (status === 401 && !cfg._retry && !cfg.url?.includes('/auth/')) {
      cfg._retry = true
      try {
        if (!_refreshing) {
          _refreshing = (async () => {
            const r = await axios.post('/api/auth/refresh', {}, { withCredentials: true })
            const tok = r.data.access_token as string
            localStorage.setItem('qd_access', tok)
            http.defaults.headers.common['Authorization'] = `Bearer ${tok}`
            return tok
          })().finally(() => { _refreshing = null })
        }
        await _refreshing
        cfg.headers = { ...cfg.headers, Authorization: http.defaults.headers.common['Authorization'] }
        return http(cfg)
      } catch {
        localStorage.removeItem('qd_access')
        delete http.defaults.headers.common['Authorization']
        if (!window.location.pathname.startsWith('/login'))
          window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`
        return Promise.reject(err)
      }
    }

    if (!err.response && !cfg._retry) {
      cfg._retry = true
      await new Promise(r => setTimeout(r, 800))
      return http(cfg)
    }
    return Promise.reject(err)
  }
)
