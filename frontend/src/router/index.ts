import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: 'Market Dashboard', icon: 'grid' },
  },
  {
    path: '/ai',
    name: 'TradingAI',
    component: () => import('@/views/TradingAIView.vue'),
    meta: { title: 'QuantAI — Trading Assistant', icon: 'ai' },
  },
  {
    path: '/trade',
    name: 'TradeSignal',
    component: () => import('@/views/TradeSignalView.vue'),
    meta: { title: 'Statistical Edge Trading', icon: 'bolt' },
  },
  {
    path: '/ticker/:symbol',
    name: 'TickerDeepDive',
    component: () => import('@/views/TickerDeepDive.vue'),
    meta: { title: 'Ticker Analysis', icon: 'chart-line' },
  },
  {
    // /ticker without symbol → redirect to SPY
    path: '/ticker',
    redirect: '/ticker/SPY',
  },
  {
    path: '/compare',
    name: 'Compare',
    component: () => import('@/views/CompareAssets.vue'),
    meta: { title: 'Compare Assets', icon: 'scale' },
  },
  {
    path: '/stats-hub',
    name: 'StatsHub',
    component: () => import('@/views/StatsHub.vue'),
    meta: { title: 'Statistical Analysis', icon: 'beaker' },
  },
  {
    path: '/bubble',
    name: 'BubbleDetection',
    component: () => import('@/views/BubbleDetection.vue'),
    meta: { title: 'Bubble Detection', icon: 'fire' },
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: () => import('@/views/BacktestLab.vue'),
    meta: { title: 'Backtest Lab', icon: 'play' },
  },
  {
    path: '/strategy-compare',
    name: 'StrategyCompare',
    component: () => import('@/views/StrategyCompare.vue'),
    meta: { title: 'Strategy Compare', icon: 'git-merge' },
  },
  {
    path: '/optimizer',
    name: 'Optimizer',
    component: () => import('@/views/StrategyOptimizer.vue'),
    meta: { title: 'Optimizer', icon: 'adjustments' },
  },
  {
    path: '/monte-carlo',
    name: 'MonteCarlo',
    component: () => import('@/views/MonteCarloView.vue'),
    meta: { title: 'Monte Carlo', icon: 'sparkles' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0, behavior: 'smooth' }),
})

router.afterEach((to) => {
  document.title = to.meta.title
    ? `${String(to.meta.title)} — QuantDash`
    : 'QuantDash'
})

export default router
