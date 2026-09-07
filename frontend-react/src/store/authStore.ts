import { create } from 'zustand'
import { authApi, type AuthUser } from '@/api/authApi'
import { http } from '@/api/client'

interface AuthState {
  user:         AuthUser | null
  loading:      boolean
  initialized:  boolean
  isLoggedIn:   boolean
  isAdmin:      boolean
  displayName:  string
  // actions
  init:         () => Promise<void>
  login:        (login: string, password: string) => Promise<{ ok: boolean; error?: string }>
  register:     (email: string, username: string, password: string, displayName?: string) => Promise<{ ok: boolean; error?: string }>
  logout:       () => Promise<void>
  updateProfile:(name: string) => Promise<void>
}

function setToken(tok: string) {
  localStorage.setItem('qd_access', tok)
  http.defaults.headers.common['Authorization'] = `Bearer ${tok}`
}
function clearToken() {
  localStorage.removeItem('qd_access')
  delete http.defaults.headers.common['Authorization']
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null, loading: false, initialized: false,
  get isLoggedIn()  { return !!get().user },
  get isAdmin()     { return get().user?.role === 'admin' },
  get displayName() { return get().user?.display_name || get().user?.username || 'User' },

  async init() {
    if (get().initialized) return
    set({ initialized: true })
    const tok = localStorage.getItem('qd_access')
    if (!tok) return
    http.defaults.headers.common['Authorization'] = `Bearer ${tok}`
    try {
      const r = await authApi.me()
      set({ user: r.data })
    } catch {
      try {
        const r = await authApi.refresh()
        setToken(r.data.access_token)
        set({ user: r.data.user })
      } catch { clearToken() }
    }
  },

  async login(login, password) {
    set({ loading: true })
    try {
      const r = await authApi.login(login, password)
      setToken(r.data.access_token)
      set({ user: r.data.user })
      return { ok: true }
    } catch (e: any) {
      const detail = e.response?.data?.detail
      return { ok: false, error: typeof detail === 'string' ? detail : 'เข้าสู่ระบบไม่สำเร็จ' }
    } finally {
      set({ loading: false })
    }
  },

  async register(email, username, password, displayName) {
    set({ loading: true })
    try {
      const r = await authApi.register(email, username, password, displayName)
      setToken(r.data.access_token)
      set({ user: r.data.user })
      return { ok: true }
    } catch (e: any) {
      const detail = e.response?.data?.detail
      const msg = typeof detail === 'object' ? detail?.message : detail
      return { ok: false, error: msg || 'สมัครสมาชิกไม่สำเร็จ' }
    } finally {
      set({ loading: false })
    }
  },

  async logout() {
    await authApi.logout()
    clearToken()
    set({ user: null })
  },

  async updateProfile(name) {
    const r = await authApi.updateProfile(name)
    set({ user: r.data })
  },
}))
