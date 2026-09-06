import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/dashboard' },
  // ── Auth (no layout) ─────────────────────────────────────────────────────────
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true, hideLayout: true, title: 'เข้าสู่ระบบ' },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { public: true, hideLayout: true, title: 'สมัครสมาชิก' },
  },
  // ── App (require auth) ────────────────────────────────────────────────────────
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: 'Market Dashboard' },
  },
  {
    path: '/ai',
    name: 'TradingAI',
    component: () => import('@/views/TradingAIView.vue'),
    meta: { title: 'QuantAI' },
  },
  {
    path: '/trade',
    name: 'TradeSignal',
    component: () => import('@/views/TradeSignalView.vue'),
    meta: { title: 'Edge Trading' },
  },
  {
    path: '/ticker/:symbol',
    name: 'TickerDeepDive',
    component: () => import('@/views/TickerDeepDive.vue'),
    meta: { title: 'Ticker Analysis' },
  },
  { path: '/ticker', redirect: '/ticker/SPY' },
  {
    path: '/compare',
    name: 'Compare',
    component: () => import('@/views/CompareAssets.vue'),
    meta: { title: 'Compare Assets' },
  },
  {
    path: '/stats-hub',
    name: 'StatsHub',
    component: () => import('@/views/StatsHub.vue'),
    meta: { title: 'Statistical Analysis' },
  },
  {
    path: '/bubble',
    name: 'BubbleDetection',
    component: () => import('@/views/BubbleDetection.vue'),
    meta: { title: 'Bubble Detection' },
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: () => import('@/views/BacktestLab.vue'),
    meta: { title: 'Backtest Lab' },
  },
  {
    path: '/strategy-compare',
    name: 'StrategyCompare',
    component: () => import('@/views/StrategyCompare.vue'),
    meta: { title: 'Strategy Compare' },
  },
  {
    path: '/optimizer',
    name: 'Optimizer',
    component: () => import('@/views/StrategyOptimizer.vue'),
    meta: { title: 'Optimizer' },
  },
  {
    path: '/monte-carlo',
    name: 'MonteCarlo',
    component: () => import('@/views/MonteCarloView.vue'),
    meta: { title: 'Monte Carlo' },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { title: 'โปรไฟล์ของฉัน' },
  },
  {
    path: '/daytrade',
    name: 'DayTrade',
    component: () => import('@/views/DayTradeView.vue'),
    meta: { title: 'Day Trade · OCaml Engine' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0, behavior: 'smooth' }),
})

// ── Navigation guard ───────────────────────────────────────────────────────────
router.beforeEach(async (to) => {
  const { useAuthStore } = await import('@/stores/authStore')
  const authStore = useAuthStore()

  // First load — restore session from localStorage
  if (!authStore.initialized) {
    await authStore.init()
  }

  // Public pages: always allow
  if (to.meta.public) return true

  // Protected pages: redirect to login if not authenticated
  if (!authStore.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  return true
})

router.afterEach((to) => {
  document.title = to.meta.title
    ? `${String(to.meta.title)} — QuantDash`
    : 'QuantDash'
})

export default router
