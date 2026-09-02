// ─── Core market types ────────────────────────────────────────────────────────

export interface OHLCVBar {
  date:   string
  open:   number
  high:   number
  low:    number
  close:  number
  volume: number
}

export interface PriceResponse {
  ticker: string
  data:   OHLCVBar[]
  rows:   number
  start:  string
  end:    string
}

export interface TickerInfo {
  ticker:    string
  rows:      number
  start:     string
  end:       string
  last_price?: number
}

export interface UniverseResponse {
  name:    string
  tickers: string[]
  count:   number
}

export interface SectorBreakdown {
  universe: string
  sectors:  Record<string, string[]>
}

// ─── Stats types ──────────────────────────────────────────────────────────────

export interface DescriptiveStats {
  ticker:     string
  count:      number
  mean:       number
  median:     number
  std:        number
  min:        number
  max:        number
  skewness:   number
  kurtosis:   number
  jb_pvalue:  number
  is_normal:  boolean
  autocorr_1: number | null
  hurst:      number | null
}

export interface ReturnSummary {
  ticker:             string
  total_return:       number
  cagr:               number
  avg_daily_return:   number
  avg_monthly_return: number
  best_day:           number
  worst_day:          number
  pct_positive_days:  number
}

export interface RiskMetrics {
  ticker:        string
  sharpe:        number
  sortino:       number
  calmar:        number
  omega:         number
  max_drawdown:  number
  ann_volatility: number
  var_95:        number
  cvar_95:       number
  tail_ratio:    number
  ulcer_index:   number
}

export interface DrawdownEntry {
  start:        string
  end:          string
  drawdown:     number
  duration_days: number
}

export interface DrawdownResponse {
  ticker:  string
  summary: Record<string, number>
  top_10:  DrawdownEntry[]
}

export interface CorrelationResponse {
  tickers: string[]
  matrix:  Record<string, Record<string, number>>
}

export interface RegimePoint {
  date:   string
  regime: number
}

export interface RegimeStat {
  regime:     number
  label:      string
  pct_time:   number
  avg_return: number
  volatility: number
  count:      number
}

export interface RegimeResponse {
  ticker:  string
  regimes: RegimePoint[]
  stats:   RegimeStat[]
}

export interface SeasonalityEffect {
  label:      string
  mean_return: number
  std:        number
  count:      number
}

export interface SeasonalityResponse {
  ticker:          string
  day_of_week:     SeasonalityEffect[]
  month:           SeasonalityEffect[]
  january_effect:  { detected: boolean; p_value: number; avg_jan: number; avg_other: number }
  monday_effect:   { detected: boolean; p_value: number; avg_mon: number; avg_other: number }
}

export interface DistributionResponse {
  ticker:    string
  tail_risk: Record<string, number>
  best_fit:  { name: string; params: number[]; ks_stat: number; ks_pvalue: number }
  t_fit:     { df: number; loc: number; scale: number }
}

// ─── Backtest types ───────────────────────────────────────────────────────────

export interface BacktestRequest {
  strategy:         string
  tickers:          string[]
  start_date:       string
  end_date:         string
  initial_capital:  number
  commission_pct:   number
  slippage_pct:     number
  max_position_pct: number
  position_sizing:  string
  benchmark_ticker: string
  strategy_params:  Record<string, unknown>
}

export interface BacktestResponse {
  run_id:          string
  strategy:        string
  start_date:      string
  end_date:        string
  initial_capital: number
  performance:     Record<string, number>
  equity_curve:    Record<string, number>
  n_trades:        number
  run_time_s:      number
}

export interface BacktestListItem {
  run_id:   string
  strategy: string
  created:  string
  sharpe:   number | null
  cagr:     number | null
}

export interface TradeLogEntry {
  date:     string
  ticker:   string
  side:     string
  entry:    number
  exit:     number
  pnl:      number
  return_pct: number
  duration: number
}

export interface BacktestDetail {
  run_id:      string
  strategy:    string
  performance: Record<string, number>
  trade_log:   TradeLogEntry[]
  created:     string
}

// ─── Optimize types ───────────────────────────────────────────────────────────

export interface OptimizeRequest {
  strategy:   string
  tickers:    string[]
  start_date: string
  end_date:   string
  param_grid: Record<string, unknown[]>
  metric:     string
  maximize:   boolean
  n_jobs:     number
}

export interface OptimizeResult {
  strategy:    string
  metric:      string
  best_params: Record<string, unknown>
  best_value:  number
  all_results: Array<Record<string, unknown>>
}

// ─── Monte Carlo types ────────────────────────────────────────────────────────

export interface MonteCarloRequest {
  ticker:     string
  start_date: string | null
  end_date:   string | null
  n_sims:     number
  horizon:    number
  method:     'bootstrap' | 'parametric'
}

export interface MonteCarloResponse {
  ticker:           string
  n_sims:           number
  horizon_days:     number
  stats:            Record<string, number>
  percentile_paths: { p5: number[]; p25: number[]; p50: number[]; p75: number[]; p95: number[] }
}

// ─── Strategy types ───────────────────────────────────────────────────────────

export interface StrategyMeta {
  name:         string
  display_name: string
  description:  string
  params:       Record<string, { default: unknown; description: string; type: string }>
  suitable_for: string[]
}

// ─── Bubble types ────────────────────────────────────────────────────────────

export interface BubbleResponse {
  ticker:         string
  start_date:     string
  end_date:       string
  bubble_score:   number          // 0-100
  is_bubble:      boolean
  pe_ratio_current: number | null
  pe_ratio_hist_avg: number | null
  pe_zscore:      number | null
  price_acceleration: number      // annualised 2nd derivative of log price
  log_return_zscore: number       // rolling 252d z-score of cumulative return
  crash_probability: number       // 0-1 empirical
  historical_bubbles: BubbleEvent[]
  price_series:   { date: string; close: number; log_price: number }[]
  zscore_series:  { date: string; zscore: number }[]
  signals:        BubbleSignal[]
}

export interface BubbleEvent {
  peak_date:   string
  trough_date: string
  peak_price:  number
  trough_price: number
  drawdown:    number
  duration_days: number
  name:        string
}

export interface BubbleSignal {
  name:        string
  triggered:   boolean
  value:       number
  threshold:   number
  description: string
}

// ─── UI helpers ───────────────────────────────────────────────────────────────

export type Theme = 'dark' | 'light'

export interface Toast {
  id:      string
  type:    'success' | 'error' | 'warning' | 'info'
  message: string
}

export interface DateRange {
  start: string
  end:   string
}

export const PRESET_RANGES: { label: string; days: number }[] = [
  { label: '1M',  days: 30   },
  { label: '3M',  days: 90   },
  { label: '6M',  days: 180  },
  { label: '1Y',  days: 365  },
  { label: '3Y',  days: 1095 },
  { label: '5Y',  days: 1825 },
  { label: '10Y', days: 3650 },
  { label: 'MAX', days: 7300 },
]

export const STRATEGY_LABELS: Record<string, string> = {
  buy_and_hold:         'Buy & Hold',
  sma_crossover:        'SMA Crossover',
  momentum:             'Momentum',
  mean_reversion:       'Mean Reversion',
  breakout:             'Breakout',
  pairs_trading:        'Pairs Trading',
  multi_factor:         'Multi-Factor',
  volatility_targeting: 'Volatility Targeting',
  trend_following:      'Trend Following',
  ml:                   'Machine Learning',
}

export const QUICK_SETS: Record<string, string[]> = {
  'FAANG':       ['AAPL', 'AMZN', 'GOOGL', 'META', 'NFLX'],
  'AI Leaders':  ['NVDA', 'MSFT', 'GOOGL', 'META', 'AMD'],
  'Benchmarks':  ['SPY', 'QQQ', 'IWM', 'GLD', 'TLT'],
  'Financials':  ['JPM', 'BAC', 'GS', 'MS', 'BLK'],
}
