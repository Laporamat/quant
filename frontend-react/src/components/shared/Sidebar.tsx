import { NavLink } from 'react-router-dom'
import { useLayoutStore } from '@/store/appStore'
import { useAuthStore } from '@/store/authStore'

interface NavItem { to: string; label: string; icon: string }

const NAV: NavItem[] = [
  { to: '/dashboard',        label: 'Dashboard',      icon: '▦' },
  { to: '/ai',               label: '🤖 QuantAI',     icon: '✦' },
  { to: '/trade',            label: '🎯 Edge Trade',   icon: '◎' },
  { to: '/ticker/SPY',       label: 'Ticker Dive',    icon: '↗' },
  { to: '/compare',          label: 'Compare',        icon: '⇄' },
  { to: '/stats-hub',        label: 'Stats Hub',      icon: '⚗' },
  { to: '/bubble',           label: 'Bubble Detect',  icon: '🔥' },
  { to: '/backtest',         label: 'Backtest Lab',   icon: '▶' },
  { to: '/strategy-compare', label: 'Strat Compare',  icon: '⊕' },
  { to: '/optimizer',        label: 'Optimizer',      icon: '⧖' },
  { to: '/monte-carlo',      label: 'Monte Carlo',    icon: '✦' },
  { to: '/daytrade',         label: 'Day Trade',      icon: '◈' },
]

export default function Sidebar() {
  const { sidebarOpen } = useLayoutStore()
  const auth = useAuthStore()

  return (
    <aside
      className={`flex flex-col shrink-0 border-r border-surface-700/50 bg-surface-900 transition-[width] duration-300 overflow-hidden ${sidebarOpen ? 'w-52' : 'w-12'}`}>
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-3 h-14 border-b border-surface-700/50 shrink-0">
        <div className="w-7 h-7 rounded-lg bg-primary-600 flex items-center justify-center shrink-0">
          <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="3 17 9 11 13 15 21 7" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        {sidebarOpen && <span className="font-bold text-white text-sm tracking-wide whitespace-nowrap">QuantDash</span>}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-2 flex flex-col gap-0.5 overflow-y-auto scrollbar-thin">
        {NAV.map(item => (
          <NavLink key={item.to} to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-2.5 px-2.5 py-2 mx-1.5 rounded-lg transition-colors duration-150 group relative ` +
              (isActive
                ? 'bg-primary-600/20 text-primary-300'
                : 'text-surface-400 hover:text-white hover:bg-surface-700/50')
            }>
            <span className="w-5 h-5 flex items-center justify-center shrink-0 text-sm">{item.icon}</span>
            {sidebarOpen && <span className="text-sm font-medium whitespace-nowrap">{item.label}</span>}
            {!sidebarOpen && (
              <div className="absolute left-full ml-2 z-50 hidden group-hover:flex">
                <div className="bg-surface-700 text-white text-xs px-2.5 py-1.5 rounded-md shadow-lg whitespace-nowrap">
                  {item.label}
                </div>
              </div>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User */}
      <div className="border-t border-surface-700/50 shrink-0">
        {auth.isLoggedIn ? (
          <NavLink to="/profile"
            className="flex items-center gap-2 px-2.5 py-3 mx-1.5 mb-1 rounded-lg hover:bg-surface-700/40 transition-colors">
            <div className="w-6 h-6 rounded-md bg-primary-600/30 flex items-center justify-center text-xs font-bold text-primary-300 shrink-0">
              {auth.displayName[0]?.toUpperCase()}
            </div>
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-surface-200 truncate">{auth.displayName}</p>
                <p className="text-xs text-surface-500">{auth.user?.role}</p>
              </div>
            )}
          </NavLink>
        ) : (
          <NavLink to="/login"
            className="flex items-center gap-2 px-2.5 py-3 mx-1.5 mb-1 rounded-lg hover:bg-primary-600/20 transition-colors text-primary-400 text-sm font-medium">
            <span className="w-5 h-5 flex items-center justify-center shrink-0">→</span>
            {sidebarOpen && 'เข้าสู่ระบบ'}
          </NavLink>
        )}
        {sidebarOpen && auth.isLoggedIn && (
          <p className="text-xs text-surface-600 px-4 pb-3">20yr · SP100 · SET50</p>
        )}
      </div>
    </aside>
  )
}
