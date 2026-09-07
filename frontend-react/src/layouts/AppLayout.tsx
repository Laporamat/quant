import { useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from '@/components/shared/Sidebar'
import { useLayoutStore } from '@/store/appStore'
import { useAuthStore } from '@/store/authStore'
import { http } from '@/api/client'
import clsx from 'clsx'

export default function AppLayout() {
  const { sidebarOpen, toggleSidebar, apiStatus, setApiStatus, theme, toggleTheme } = useLayoutStore()
  const auth = useAuthStore()
  const loc  = useLocation()

  // Page title
  const title = loc.pathname.split('/').filter(Boolean).map(s =>
    s.charAt(0).toUpperCase() + s.slice(1).replace(/-/g, ' ')
  ).join(' › ') || 'Dashboard'

  // Health check
  useEffect(() => {
    http.get('/health').then(() => setApiStatus('ok')).catch(() => setApiStatus('error'))
  }, [setApiStatus])

  // Apply theme class
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  return (
    <div className="flex h-screen overflow-hidden bg-surface-900">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="flex items-center gap-3 px-4 h-14 border-b border-surface-700/50 bg-surface-900/80 backdrop-blur-sm shrink-0">
          <button onClick={toggleSidebar} className="btn-ghost p-1.5 -ml-1">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5"/>
            </svg>
          </button>

          <nav className="flex items-center gap-1.5 text-sm text-surface-400 min-w-0">
            <span className="text-surface-500">QuantDash</span>
            <span>/</span>
            <span className="text-surface-100 truncate font-medium">{title}</span>
          </nav>

          <div className="ml-auto flex items-center gap-3">
            {/* API status */}
            <span className={clsx('hidden sm:flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full',
              apiStatus === 'ok'      && 'bg-bull/10 text-bull',
              apiStatus === 'error'   && 'bg-bear/10 text-bear',
              apiStatus === 'loading' && 'bg-surface-700 text-surface-400')}>
              <span className={clsx('w-1.5 h-1.5 rounded-full',
                apiStatus === 'ok' && 'bg-bull animate-pulse',
                apiStatus === 'error' && 'bg-bear',
                apiStatus === 'loading' && 'bg-surface-400')} />
              {apiStatus === 'ok' ? 'API Connected' : apiStatus === 'error' ? 'API Down' : 'Connecting…'}
            </span>

            {/* Theme toggle */}
            <button onClick={toggleTheme} className="btn-ghost p-1.5" title="Toggle theme">
              {theme === 'dark' ? '🌙' : '☀️'}
            </button>

            {/* User */}
            {auth.isLoggedIn ? (
              <a href="/profile" className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg hover:bg-surface-700/50 transition-colors">
                <div className="w-6 h-6 rounded-md bg-primary-600/30 flex items-center justify-center text-xs font-bold text-primary-300">
                  {auth.displayName[0]?.toUpperCase()}
                </div>
                <span className="hidden sm:block text-xs font-medium text-surface-200">{auth.displayName}</span>
              </a>
            ) : (
              <a href="/login"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary-600/20 hover:bg-primary-600/30 text-primary-300 text-xs font-medium border border-primary-600/30 transition-all">
                เข้าสู่ระบบ
              </a>
            )}
          </div>
        </header>

        {/* Main */}
        <main className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="p-5 max-w-screen-2xl mx-auto page-enter">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
