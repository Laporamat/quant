import { create } from 'zustand'

// ── Toast ──────────────────────────────────────────────────────────────────────
export type ToastType = 'success' | 'error' | 'warning' | 'info'
export interface Toast { id: string; type: ToastType; message: string }

interface ToastState {
  toasts: Toast[]
  add:    (type: ToastType, msg: string, ms?: number) => void
  remove: (id: string) => void
  success:(msg: string) => void
  error:  (msg: string) => void
  warning:(msg: string) => void
  info:   (msg: string) => void
}
export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  add(type, message, ms = 4000) {
    const id = Math.random().toString(36).slice(2)
    set(s => ({ toasts: [...s.toasts, { id, type, message }] }))
    setTimeout(() => get().remove(id), ms)
  },
  remove: id => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })),
  success: m => get().add('success', m),
  error:   m => get().add('error',   m),
  warning: m => get().add('warning', m),
  info:    m => get().add('info',    m),
}))

// ── Layout ─────────────────────────────────────────────────────────────────────
interface LayoutState {
  sidebarOpen: boolean
  apiStatus:   'ok' | 'error' | 'loading'
  theme:       'dark' | 'light'
  toggleSidebar: () => void
  setApiStatus:  (s: 'ok' | 'error' | 'loading') => void
  toggleTheme:   () => void
}
export const useLayoutStore = create<LayoutState>((set) => ({
  sidebarOpen: true,
  apiStatus:   'loading',
  theme:       (localStorage.getItem('theme') as 'dark'|'light') ?? 'dark',
  toggleSidebar: () => set(s => ({ sidebarOpen: !s.sidebarOpen })),
  setApiStatus:  (v) => set({ apiStatus: v }),
  toggleTheme:   () => set(s => {
    const next = s.theme === 'dark' ? 'light' : 'dark'
    localStorage.setItem('theme', next)
    document.documentElement.classList.toggle('dark', next === 'dark')
    return { theme: next }
  }),
}))

// ── Market ─────────────────────────────────────────────────────────────────────
interface MarketState {
  availableTickers: { ticker: string; rows: number; start: string; end: string }[]
  universeMap:      Record<string, string[]>
  setAvailable:     (t: MarketState['availableTickers']) => void
  setUniverse:      (name: string, tickers: string[]) => void
}
export const useMarketStore = create<MarketState>((set) => ({
  availableTickers: [],
  universeMap: {},
  setAvailable: t => set({ availableTickers: t }),
  setUniverse:  (name, tickers) => set(s => ({ universeMap: { ...s.universeMap, [name]: tickers } })),
}))
