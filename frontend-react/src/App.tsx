import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'
import { useLayoutStore } from '@/store/appStore'
import AppLayout  from '@/layouts/AppLayout'
import Toast      from '@/components/shared/Toast'
import StickyCTA  from '@/components/shared/StickyCTA'

// ── Auth pages ────────────────────────────────────────────────────────────────
import Login    from '@/pages/Login'
import Register from '@/pages/Register'
import ThankYou from '@/pages/ThankYou'

// ── Public marketing pages (no auth needed) ───────────────────────────────────
import About        from '@/pages/About'
import FAQ          from '@/pages/FAQ'
import CaseStudies  from '@/pages/CaseStudies'
import Privacy      from '@/pages/Privacy'
import Terms        from '@/pages/Terms'
import NotFound     from '@/pages/NotFound'

// ── App pages (require auth) ──────────────────────────────────────────────────
import Dashboard       from '@/pages/Dashboard'
import TickerDeepDive  from '@/pages/TickerDeepDive'
import CompareAssets   from '@/pages/CompareAssets'
import StatsHub        from '@/pages/StatsHub'
import BubbleDetection from '@/pages/BubbleDetection'
import BacktestLab     from '@/pages/BacktestLab'
import MonteCarlo      from '@/pages/MonteCarlo'
import Optimizer       from '@/pages/Optimizer'
import EdgeTrading     from '@/pages/EdgeTrading'
import TradingAI       from '@/pages/TradingAI'
import Profile         from '@/pages/Profile'

// ── Simple placeholder pages ──────────────────────────────────────────────────
function StrategyCompare() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-surface-500 glass rounded-xl gap-3">
      <p className="text-sm font-medium text-surface-300">Strategy Compare</p>
      <p className="text-xs">รัน Backtest หลายครั้งก่อน แล้วกลับมาที่นี่เพื่อ compare</p>
      <a href="/backtest" className="btn-primary text-sm">→ ไปที่ Backtest Lab</a>
    </div>
  )
}

// ── Public layout wrapper (no auth guard, but has header/footer links) ─────────
function PublicLayout() {
  return (
    <div className="min-h-screen bg-surface-950">
      {/* Minimal top bar */}
      <nav className="border-b border-surface-800 bg-surface-950/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <a href="/" className="flex items-center gap-2 font-bold text-surface-100">
            <div className="w-7 h-7 rounded-lg bg-primary-600 flex items-center justify-center">
              <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="3 17 9 11 13 15 21 7" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            QuantDash
          </a>
          <div className="flex items-center gap-1">
            <a href="/about"        className="btn-ghost text-xs px-3 py-1.5 hidden sm:block">About</a>
            <a href="/faq"          className="btn-ghost text-xs px-3 py-1.5 hidden sm:block">FAQ</a>
            <a href="/case-studies" className="btn-ghost text-xs px-3 py-1.5 hidden sm:block">Cases</a>
            <a href="/login"        className="btn-ghost text-xs px-3 py-1.5">Login</a>
            <a href="/register"     className="btn-primary text-xs px-3 py-1.5">สมัครฟรี</a>
          </div>
        </div>
      </nav>
      <main className="max-w-5xl mx-auto px-4 pb-16">
        <Outlet />
      </main>
      {/* Footer */}
      <footer className="border-t border-surface-800 py-8 mt-8">
        <div className="max-w-5xl mx-auto px-4">
          <div className="flex flex-wrap justify-between gap-4 text-xs text-surface-500">
            <p>© 2024 QuantDash · OCaml · Python · React</p>
            <div className="flex gap-4">
              {[{h:'/about',l:'About'},{h:'/faq',l:'FAQ'},{h:'/case-studies',l:'Cases'},{h:'/privacy',l:'Privacy'},{h:'/terms',l:'Terms'}].map(l=>(
                <a key={l.h} href={l.h} className="hover:text-primary-400 transition-colors">{l.l}</a>
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

// ── RequireAuth guard ──────────────────────────────────────────────────────────
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

// ── Theme sync ─────────────────────────────────────────────────────────────────
function ThemeInit() {
  const { theme } = useLayoutStore()
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])
  return null
}

// ── Root ───────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <BrowserRouter>
      <ThemeInit/>
      <Toast/>
      <StickyCTA/>

      <Routes>
        {/* ── Auth (full-page, no layout) ── */}
        <Route path="/login"     element={<Login/>}/>
        <Route path="/register"  element={<Register/>}/>
        <Route path="/thank-you" element={<ThankYou/>}/>

        {/* ── Public marketing (PublicLayout) ── */}
        <Route element={<PublicLayout/>}>
          <Route path="/about"        element={<About/>}/>
          <Route path="/faq"          element={<FAQ/>}/>
          <Route path="/case-studies" element={<CaseStudies/>}/>
          <Route path="/privacy"      element={<Privacy/>}/>
          <Route path="/terms"        element={<Terms/>}/>
        </Route>

        {/* ── Protected app (AppLayout + RequireAuth) ── */}
        <Route element={<RequireAuth/>}>
          <Route element={<AppLayout/>}>
            <Route path="/"                 element={<Navigate to="/dashboard" replace/>}/>
            <Route path="/dashboard"        element={<Dashboard/>}/>
            <Route path="/ticker"           element={<Navigate to="/ticker/SPY" replace/>}/>
            <Route path="/ticker/:symbol"   element={<TickerDeepDive/>}/>
            <Route path="/compare"          element={<CompareAssets/>}/>
            <Route path="/stats-hub"        element={<StatsHub/>}/>
            <Route path="/bubble"           element={<BubbleDetection/>}/>
            <Route path="/backtest"         element={<BacktestLab/>}/>
            <Route path="/strategy-compare" element={<StrategyCompare/>}/>
            <Route path="/optimizer"        element={<Optimizer/>}/>
            <Route path="/monte-carlo"      element={<MonteCarlo/>}/>
            <Route path="/trade"            element={<EdgeTrading/>}/>
            <Route path="/ai"              element={<TradingAI/>}/>
            <Route path="/profile"          element={<Profile/>}/>
          </Route>
        </Route>

        <Route path="*" element={<NotFound/>}/>
      </Routes>
    </BrowserRouter>
  )
}
