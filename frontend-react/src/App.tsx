import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useLayoutStore } from '@/store/appStore'
import AppLayout from '@/layouts/AppLayout'
import Toast     from '@/components/shared/Toast'

// Pages
import Login          from '@/pages/Login'
import Register       from '@/pages/Register'
import Dashboard      from '@/pages/Dashboard'
import TickerDeepDive from '@/pages/TickerDeepDive'
import CompareAssets  from '@/pages/CompareAssets'
import StatsHub       from '@/pages/StatsHub'
import BubbleDetection from '@/pages/BubbleDetection'
import BacktestLab    from '@/pages/BacktestLab'
import MonteCarlo     from '@/pages/MonteCarlo'
import Optimizer      from '@/pages/Optimizer'
import EdgeTrading    from '@/pages/EdgeTrading'
import TradingAI      from '@/pages/TradingAI'
import Profile        from '@/pages/Profile'
import NotFound       from '@/pages/NotFound'

// ── StrategyCompare (simple redirect page) ───────────────────────────────────
function StrategyCompare() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-surface-500 glass rounded-xl">
      <p className="text-sm font-medium text-surface-300">Strategy Compare</p>
      <p className="text-xs mt-1">รัน Backtest หลายครั้งก่อน แล้วกลับมาที่นี่เพื่อ compare</p>
      <a href="/backtest" className="btn-primary text-sm mt-4">→ ไปที่ Backtest Lab</a>
    </div>
  )
}

// ── RequireAuth guard ─────────────────────────────────────────────────────────
function RequireAuth() {
  const auth = useAuthStore()
  const loc  = useLocation()

  useEffect(() => { if (!auth.initialized) auth.init() }, [auth])

  if (!auth.initialized) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface-950">
        <span className="w-10 h-10 border-4 border-primary-500/30 border-t-primary-500 rounded-full animate-spin"/>
      </div>
    )
  }
  if (!auth.isLoggedIn) {
    return <Navigate to={`/login?redirect=${encodeURIComponent(loc.pathname)}`} replace/>
  }
  return <Outlet/>
}

// ── Theme init ────────────────────────────────────────────────────────────────
function ThemeInit() {
  const { theme } = useLayoutStore()
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])
  return null
}

// ── Root App ──────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <ThemeInit/>
      <Toast/>
      <Routes>
        {/* Public auth routes — no layout */}
        <Route path="/login"    element={<Login/>}/>
        <Route path="/register" element={<Register/>}/>

        {/* Protected routes — wrapped in AppLayout */}
        <Route element={<RequireAuth/>}>
          <Route element={<AppLayout/>}>
            <Route path="/"                  element={<Navigate to="/dashboard" replace/>}/>
            <Route path="/dashboard"         element={<Dashboard/>}/>
            <Route path="/ticker"            element={<Navigate to="/ticker/SPY" replace/>}/>
            <Route path="/ticker/:symbol"    element={<TickerDeepDive/>}/>
            <Route path="/compare"           element={<CompareAssets/>}/>
            <Route path="/stats-hub"         element={<StatsHub/>}/>
            <Route path="/bubble"            element={<BubbleDetection/>}/>
            <Route path="/backtest"          element={<BacktestLab/>}/>
            <Route path="/strategy-compare"  element={<StrategyCompare/>}/>
            <Route path="/optimizer"         element={<Optimizer/>}/>
            <Route path="/monte-carlo"       element={<MonteCarlo/>}/>
            <Route path="/trade"             element={<EdgeTrading/>}/>
            <Route path="/ai"               element={<TradingAI/>}/>
            <Route path="/profile"           element={<Profile/>}/>
          </Route>
        </Route>

        <Route path="*" element={<NotFound/>}/>
      </Routes>
    </BrowserRouter>
  )
}
