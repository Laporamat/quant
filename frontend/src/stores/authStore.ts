import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authApi, type AuthUser } from '@/api/authApi'
import { useToastStore } from '@/stores/appStore'
import { http } from '@/api/client'

const ACCESS_KEY  = 'qd_access'   // localStorage key for access token
const REFRESH_KEY = 'qd_refresh'  // localStorage key for refresh token

export const useAuthStore = defineStore('auth', () => {
  const user         = ref<AuthUser | null>(null)
  const accessToken  = ref<string | null>(localStorage.getItem(ACCESS_KEY))
  const refreshToken = ref<string | null>(localStorage.getItem(REFRESH_KEY))
  const loading      = ref(false)
  const initialized  = ref(false)

  const isLoggedIn  = computed(() => !!user.value && !!accessToken.value)
  const isAdmin     = computed(() => user.value?.role === 'admin')
  const isAnalyst   = computed(() => ['admin','analyst'].includes(user.value?.role ?? ''))
  const displayName = computed(() => user.value?.display_name || user.value?.username || 'User')

  // ── Token management ─────────────────────────────────────────────────────────
  function _setTokens(access: string, refresh?: string) {
    accessToken.value = access
    localStorage.setItem(ACCESS_KEY, access)
    if (refresh) {
      refreshToken.value = refresh
      localStorage.setItem(REFRESH_KEY, refresh)
    }
    // Inject into axios
    http.defaults.headers.common['Authorization'] = `Bearer ${access}`
  }

  function _clearTokens() {
    accessToken.value  = null
    refreshToken.value = null
    user.value         = null
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
    delete http.defaults.headers.common['Authorization']
  }

  // ── Initialise on app start — try to restore session ─────────────────────────
  async function init() {
    if (initialized.value) return
    initialized.value = true
    const stored = localStorage.getItem(ACCESS_KEY)
    if (!stored) return

    http.defaults.headers.common['Authorization'] = `Bearer ${stored}`
    try {
      const res  = await authApi.me()
      user.value = res.data
    } catch {
      // Access token expired — try refresh
      try {
        const rRes = await authApi.refresh()
        _setTokens(rRes.data.access_token)
        user.value = rRes.data.user
      } catch {
        _clearTokens()
      }
    }
  }

  // ── Register ─────────────────────────────────────────────────────────────────
  async function register(email: string, username: string, password: string, display_name?: string) {
    loading.value = true
    try {
      const res = await authApi.register(email, username, password, display_name)
      _setTokens(res.data.access_token)
      user.value = res.data.user
      useToastStore().success(`ยินดีต้อนรับ ${user.value.display_name}! 🎉`)
      return { ok: true }
    } catch (e: any) {
      const detail = e.response?.data?.detail
      const msg    = typeof detail === 'object' ? detail.message : detail
      return { ok: false, error: msg || 'สมัครสมาชิกไม่สำเร็จ' }
    } finally {
      loading.value = false
    }
  }

  // ── Login ─────────────────────────────────────────────────────────────────────
  async function login(loginVal: string, password: string) {
    loading.value = true
    try {
      const res = await authApi.login(loginVal, password)
      _setTokens(res.data.access_token)
      user.value = res.data.user
      useToastStore().success(`ยินดีต้อนรับกลับ ${user.value.display_name}!`)
      return { ok: true }
    } catch (e: any) {
      const detail = e.response?.data?.detail
      return { ok: false, error: detail || 'เข้าสู่ระบบไม่สำเร็จ' }
    } finally {
      loading.value = false
    }
  }

  // ── Logout ────────────────────────────────────────────────────────────────────
  async function logout() {
    await authApi.logout(refreshToken.value ?? undefined)
    _clearTokens()
    useToastStore().info('ออกจากระบบแล้ว')
  }

  // ── Silent token refresh (called by axios interceptor) ────────────────────────
  let _refreshing: Promise<string> | null = null
  async function silentRefresh(): Promise<string> {
    if (_refreshing) return _refreshing  // prevent concurrent refresh
    _refreshing = (async () => {
      try {
        const res = await authApi.refresh()
        _setTokens(res.data.access_token)
        if (res.data.user) user.value = res.data.user
        return res.data.access_token
      } catch {
        _clearTokens()
        throw new Error('Session expired')
      } finally {
        _refreshing = null
      }
    })()
    return _refreshing
  }

  // ── Update profile ────────────────────────────────────────────────────────────
  async function updateProfile(displayName: string) {
    const res  = await authApi.updateProfile(displayName)
    user.value = res.data
    useToastStore().success('อัปเดตโปรไฟล์แล้ว')
  }

  return {
    user, accessToken, loading, initialized,
    isLoggedIn, isAdmin, isAnalyst, displayName,
    init, register, login, logout, silentRefresh, updateProfile,
  }
})
