<template>
  <div class="space-y-5 animate-fade-in">
    <SectionHeader title="Backtest Lab" description="Configure, run, and analyse strategy backtests on historical data" />

    <div class="grid grid-cols-1 xl:grid-cols-3 gap-5">
      <!-- ── LEFT: Config Form ───────────────────────────────────────────── -->
      <div class="xl:col-span-1 space-y-4">
        <div class="glass p-4 space-y-4">
          <h3 class="text-sm font-semibold text-surface-200">Configuration</h3>

          <!-- Strategy -->
          <div class="space-y-1.5">
            <label class="text-xs text-surface-400">Strategy</label>
            <select v-model="form.strategy" class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-3 py-2 outline-none focus:border-primary-500">
              <option v-for="(label, key) in STRATEGY_LABELS" :key="key" :value="key">{{ label }}</option>
            </select>
            <p v-if="strategyDesc" class="text-xs text-surface-500 italic">{{ strategyDesc }}</p>
          </div>

          <!-- Tickers -->
          <div class="space-y-1.5">
            <label class="text-xs text-surface-400">Tickers</label>
            <TickerSearch v-model="form.tickers" :multi="true" />
          </div>

          <!-- Date Range -->
          <div class="space-y-1.5">
            <label class="text-xs text-surface-400">Date Range</label>
            <DateRangePicker v-model="dateRange" />
          </div>

          <!-- Capital + Benchmark -->
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1">
              <label class="text-xs text-surface-400">Initial Capital ($)</label>
              <input type="number" v-model.number="form.initial_capital" min="1000"
                class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-3 py-2 outline-none focus:border-primary-500" />
            </div>
            <div class="space-y-1">
              <label class="text-xs text-surface-400">Benchmark</label>
              <input type="text" v-model="form.benchmark_ticker"
                class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-3 py-2 outline-none focus:border-primary-500" />
            </div>
          </div>

          <!-- Commission + Slippage sliders -->
          <div class="space-y-3">
            <div class="space-y-1">
              <div class="flex justify-between text-xs">
                <span class="text-surface-400">Commission</span>
                <span class="text-surface-200 font-medium">{{ (form.commission_pct * 100).toFixed(2) }}%</span>
              </div>
              <input type="range" v-model.number="form.commission_pct" min="0" max="0.01" step="0.0001"
                class="w-full accent-primary-500" />
            </div>
            <div class="space-y-1">
              <div class="flex justify-between text-xs">
                <span class="text-surface-400">Slippage</span>
                <span class="text-surface-200 font-medium">{{ (form.slippage_pct * 100).toFixed(3) }}%</span>
              </div>
              <input type="range" v-model.number="form.slippage_pct" min="0" max="0.005" step="0.0001"
                class="w-full accent-primary-500" />
            </div>
          </div>

          <!-- Position sizing -->
          <div class="space-y-1.5">
            <label class="text-xs text-surface-400">Position Sizing</label>
            <div class="flex gap-2">
              <label v-for="ps in positionSizings" :key="ps.value"
                class="flex items-center gap-1.5 cursor-pointer text-xs text-surface-300">
                <input type="radio" :value="ps.value" v-model="form.position_sizing" class="accent-primary-500" />
                {{ ps.label }}
              </label>
            </div>
          </div>

          <!-- Strategy params -->
          <div v-if="strategyParams.length" class="space-y-3">
            <h4 class="text-xs font-semibold text-surface-400 uppercase tracking-wider">Strategy Parameters</h4>
            <div v-for="p in strategyParams" :key="p.key" class="space-y-1">
              <div class="flex justify-between text-xs">
                <span class="text-surface-400">{{ p.label }}</span>
                <span class="text-surface-200 font-medium">{{ form.strategy_params[p.key] }}</span>
              </div>
              <input v-if="p.type === 'range'" type="range"
                :min="p.min" :max="p.max" :step="p.step"
                :value="form.strategy_params[p.key]"
                @input="form.strategy_params[p.key] = Number(($event.target as HTMLInputElement).value)"
                class="w-full accent-primary-500" />
              <input v-else type="number"
                :value="form.strategy_params[p.key]"
                @input="form.strategy_params[p.key] = Number(($event.target as HTMLInputElement).value)"
                class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-md px-2 py-1 outline-none focus:border-primary-500" />
            </div>
          </div>

          <!-- Run button -->
          <button @click="runBacktest" :disabled="running || !form.tickers.length"
            class="btn-primary w-full flex items-center justify-center gap-2 py-2.5">
            <svg v-if="running" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" /></svg>
            {{ running ? 'Running…' : 'Run Backtest' }}
          </button>
        </div>

        <!-- History panel -->
        <div v-if="history.length" class="glass p-4 space-y-2">
          <h4 class="text-xs font-semibold text-surface-400 uppercase tracking-wider">Recent Runs</h4>
          <button v-for="h in history" :key="h.run_id"
            @click="loadHistoricResult(h.run_id)"
            class="w-full text-left px-3 py-2 rounded-lg hover:bg-surface-700/40 transition-colors"
            :class="result?.run_id === h.run_id ? 'bg-primary-600/20 border border-primary-600/30' : ''">
            <p class="text-xs font-medium text-surface-200">{{ STRATEGY_LABELS[h.strategy] ?? h.strategy }}</p>
            <p class="text-xs text-surface-500">Sharpe: {{ h.sharpe?.toFixed(3) ?? '—' }} · CAGR: {{ h.cagr !== null ? (h.cagr * 100).toFixed(1) + '%' : '—' }}</p>
          </button>
        </div>
      </div>

      <!-- ── RIGHT: Results ─────────────────────────────────────────────── -->
      <div class="xl:col-span-2 space-y-4">
        <!-- Empty state -->
        <div v-if="!result && !running" class="flex flex-col items-center justify-center h-64 text-surface-500 glass rounded-xl">
          <svg class="w-12 h-12 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.348a1.125 1.125 0 010 1.971l-11.54 6.347a1.125 1.125 0 01-1.667-.985V5.653z" />
          </svg>
          <p class="text-sm">Configure and run a backtest to see results</p>
        </div>

        <!-- Loading state -->
        <div v-if="running" class="flex flex-col items-center justify-center h-64 glass rounded-xl gap-3">
          <svg class="w-10 h-10 text-primary-500 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          <p class="text-sm text-surface-400">Running backtest…</p>
        </div>

        <template v-if="result && !running">
          <!-- KPI row -->
          <div class="grid grid-cols-3 sm:grid-cols-6 gap-3">
            <MetricCard title="CAGR"     :value="perf.cagr"        format="percent" :colorize="true" :delay="0"   />
            <MetricCard title="Sharpe"   :value="perf.sharpe"      format="number"  :colorize="true" :delay="60"  />
            <MetricCard title="Max DD"   :value="perf.max_drawdown" format="percent" :colorize="true" :delay="120" />
            <MetricCard title="Calmar"   :value="perf.calmar"      format="number"  :colorize="true" :delay="180" />
            <MetricCard title="Win Rate" :value="perf.win_rate"    format="percent" :delay="240"  />
            <MetricCard title="Trades"   :value="result.n_trades"  format="raw"     :delay="300"  />
          </div>

          <!-- Equity curve -->
          <ChartCard title="Equity Curve" :subtitle="`${result.strategy} vs ${form.benchmark_ticker}`" @refresh="runBacktest">
            <VChart v-if="equityOption" :option="equityOption" autoresize style="height:280px" />
          </ChartCard>

          <!-- Drawdown -->
          <ChartCard title="Drawdown Curve">
            <VChart v-if="drawdownOption" :option="drawdownOption" autoresize style="height:160px" />
          </ChartCard>

          <!-- Monthly Heatmap -->
          <ChartCard title="Monthly Returns Heatmap">
            <VChart v-if="heatmapOption" :option="heatmapOption" autoresize style="height:260px" />
          </ChartCard>

          <!-- Trade log -->
          <ChartCard title="Trade Log" subtitle="Last 100 trades">
            <DataTable :columns="tradeCols" :rows="tradeLog" :page-size="15" :searchable="true">
              <template #cell-ticker="{ value }">
                <TickerBadge :ticker="String(value)" />
              </template>
            </DataTable>
          </ChartCard>

          <!-- Actions -->
          <div class="flex gap-3">
            <a :href="reportUrl" target="_blank" class="btn-primary text-sm">Open HTML Report</a>
            <button @click="downloadJson" class="btn-ghost text-sm">Download JSON</button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import dayjs from 'dayjs'
import SectionHeader   from '@/components/shared/SectionHeader.vue'
import MetricCard      from '@/components/shared/MetricCard.vue'
import ChartCard       from '@/components/shared/ChartCard.vue'
import DataTable       from '@/components/shared/DataTable.vue'
import TickerSearch    from '@/components/shared/TickerSearch.vue'
import DateRangePicker from '@/components/shared/DateRangePicker.vue'
import { backtestApi } from '@/api/backtestApi'
import { strategyApi } from '@/api/strategyApi'
import { dataApi }     from '@/api/dataApi'
import TickerBadge     from '@/components/shared/TickerBadge.vue'
import type { BacktestResponse, BacktestListItem, DateRange } from '@/types'
import { CHART_COLORS, BASE_TOOLTIP, BASE_LEGEND, BASE_GRID, BASE_XAXIS, BASE_YAXIS, BASE_DATAZONE, rebase } from '@/components/charts/chartTheme'
import { STRATEGY_LABELS } from '@/types'

const dateRange = ref<DateRange>({ start: '2018-01-01', end: '2024-12-31' })
const form = ref({
  strategy:         'sma_crossover',
  tickers:          ['AAPL', 'MSFT'],
  initial_capital:  1_000_000,
  commission_pct:   0.0015,
  slippage_pct:     0.0005,
  max_position_pct: 0.10,
  position_sizing:  'equal',
  benchmark_ticker: 'SPY',
  strategy_params:  {} as Record<string, number>,
})

const positionSizings = [
  { value: 'equal', label: 'Equal' },
  { value: 'vol_target', label: 'Vol-Target' },
  { value: 'kelly', label: 'Kelly' },
]

// Dynamic params per strategy
const STRATEGY_PARAMS: Record<string, { key: string; label: string; type: string; default: number; min?: number; max?: number; step?: number }[]> = {
  sma_crossover:   [
    { key: 'sma_fast', label: 'Fast SMA', type: 'range', default: 20, min: 5, max: 100, step: 5 },
    { key: 'sma_slow', label: 'Slow SMA', type: 'range', default: 50, min: 20, max: 300, step: 10 },
  ],
  momentum:        [{ key: 'lookback', label: 'Lookback', type: 'range', default: 252, min: 60, max: 504, step: 21 }],
  mean_reversion:  [
    { key: 'rsi_oversold',   label: 'RSI Oversold',   type: 'range', default: 30, min: 15, max: 40, step: 1 },
    { key: 'rsi_overbought', label: 'RSI Overbought', type: 'range', default: 70, min: 60, max: 85, step: 1 },
  ],
  breakout:        [{ key: 'period', label: 'Donchian Period', type: 'range', default: 20, min: 10, max: 60, step: 5 }],
}

const strategyParams = computed(() => STRATEGY_PARAMS[form.value.strategy] ?? [])
const strategyDesc   = ref('')

watch(() => form.value.strategy, async (s) => {
  // Reset params to defaults
  const params: Record<string, number> = {}
  ;(STRATEGY_PARAMS[s] ?? []).forEach((p) => { params[p.key] = p.default })
  form.value.strategy_params = params
  try {
    const res = await strategyApi.get(s)
    strategyDesc.value = res.data.description
  } catch { strategyDesc.value = '' }
}, { immediate: true })

// ── Run ────────────────────────────────────────────────────────────────────────
const running        = ref(false)
const result         = ref<BacktestResponse | null>(null)
const history        = ref<BacktestListItem[]>([])
const equityOption   = ref<Record<string, unknown> | null>(null)
const drawdownOption = ref<Record<string, unknown> | null>(null)
const heatmapOption  = ref<Record<string, unknown> | null>(null)
const tradeLog       = ref<Record<string, unknown>[]>([])
const reportUrl      = ref('#')

const perf = computed(() => result.value?.performance ?? {})

const tradeCols = [
  { key: 'date',       label: 'Date' },
  { key: 'ticker',     label: 'Ticker' },
  { key: 'side',       label: 'Side' },
  { key: 'entry',      label: 'Entry',  align: 'right' as const, format: (v: unknown) => `$${(v as number).toFixed(2)}` },
  { key: 'exit',       label: 'Exit',   align: 'right' as const, format: (v: unknown) => v != null ? `$${(v as number).toFixed(2)}` : '—' },
  { key: 'pnl',        label: 'PnL',    align: 'right' as const, colorize: true, format: (v: unknown) => `$${(v as number).toFixed(0)}` },
  { key: 'return_pct', label: 'Ret%',   align: 'right' as const, colorize: true, format: (v: unknown) => `${((v as number)*100).toFixed(2)}%` },
]

async function runBacktest() {
  running.value = true
  result.value  = null
  try {
    const res = await backtestApi.run({
      strategy:         form.value.strategy,
      tickers:          form.value.tickers,
      start_date:       dateRange.value.start,
      end_date:         dateRange.value.end,
      initial_capital:  form.value.initial_capital,
      commission_pct:   form.value.commission_pct,
      slippage_pct:     form.value.slippage_pct,
      max_position_pct: form.value.max_position_pct,
      position_sizing:  form.value.position_sizing,
      benchmark_ticker: form.value.benchmark_ticker,
      strategy_params:  form.value.strategy_params,
    })
    result.value = res.data
    reportUrl.value = backtestApi.reportUrl(res.data.run_id)
    buildCharts(res.data)
    await loadDetailAndHistory(res.data.run_id)
  } finally {
    running.value = false
  }
}

async function loadDetailAndHistory(runId: string) {
  const [detailRes, listRes] = await Promise.allSettled([
    backtestApi.get(runId),
    backtestApi.list(),
  ])
  if (detailRes.status === 'fulfilled') {
    tradeLog.value = detailRes.value.data.trade_log as Record<string, unknown>[]
  }
  if (listRes.status === 'fulfilled') {
    history.value = listRes.value.data
  }
}

async function loadHistoricResult(runId: string) {
  running.value = true
  result.value  = null
  try {
    const res = await backtestApi.get(runId)
    const d   = res.data
    // Reconstruct full BacktestResponse shape — equity_curve now included from backend fix
    result.value = {
      run_id:          runId,
      strategy:        d.strategy,
      start_date:      d.created?.substring(0, 10) ?? dateRange.value.start,
      end_date:        dateRange.value.end,
      initial_capital: form.value.initial_capital,
      performance:     d.performance,
      equity_curve:    (d.equity_curve ?? {}) as Record<string, number>,
      n_trades:        (d.trade_log as unknown[])?.length ?? 0,
      run_time_s:      0,
    }
    tradeLog.value  = (d.trade_log ?? []) as Record<string, unknown>[]
    reportUrl.value = backtestApi.reportUrl(runId)
    // Rebuild all charts from the retrieved equity_curve
    if (Object.keys(result.value.equity_curve).length > 0) {
      buildCharts(result.value)
    }
  } finally {
    running.value = false
  }
}

function buildCharts(data: BacktestResponse) {
  const dates  = Object.keys(data.equity_curve)
  const equity = Object.values(data.equity_curve)
  const rebased = rebase(equity)

  equityOption.value = {
    tooltip:  { ...BASE_TOOLTIP },
    legend:   { ...BASE_LEGEND, bottom: 0 },
    grid:     { ...BASE_GRID, bottom: '18%' },
    xAxis:    { ...BASE_XAXIS, data: dates },
    yAxis:    { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `${v.toFixed(1)}x` } },
    dataZoom: BASE_DATAZONE,
    series: [{
      name: data.strategy, type: 'line', data: rebased,
      symbol: 'none', lineStyle: { color: '#3b82f6', width: 2 },
      areaStyle: { color: 'rgba(59,130,246,0.08)' },
    }],
  }

  // Drawdown
  let peak = equity[0]
  const uw = equity.map((v) => { if (v > peak) peak = v; return +((v / peak - 1) * 100).toFixed(4) })
  drawdownOption.value = {
    tooltip: { ...BASE_TOOLTIP },
    grid:    { ...BASE_GRID },
    xAxis:   { ...BASE_XAXIS, data: dates },
    yAxis:   { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: '{value}%' } },
    series: [{
      type: 'line', data: uw, symbol: 'none',
      lineStyle: { color: '#ef4444', width: 1 },
      areaStyle: { color: 'rgba(239,68,68,0.25)' },
    }],
  }

  // Monthly heatmap
  const monthMap: Record<string, Record<string, number>> = {}
  for (let i = 1; i < dates.length; i++) {
    const yr  = dates[i].substring(0, 4)
    const mo  = dates[i].substring(5, 7)
    const ret = (equity[i] - equity[i - 1]) / equity[i - 1]
    if (!monthMap[yr]) monthMap[yr] = {}
    monthMap[yr][mo] = (monthMap[yr][mo] ?? 0) + ret
  }
  const years  = Object.keys(monthMap).sort()
  const months = ['01','02','03','04','05','06','07','08','09','10','11','12']
  const ML     = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  const hData: [number, number, number][] = []
  years.forEach((yr, yi) => {
    months.forEach((mo, mi) => {
      const v = monthMap[yr]?.[mo]
      if (v !== undefined) hData.push([mi, yi, +(v * 100).toFixed(2)])
    })
  })
  heatmapOption.value = {
    tooltip: {
      trigger: 'item', backgroundColor: '#1e293b', borderColor: '#334155', textStyle: { color: '#f1f5f9' },
      formatter: (p: { data: [number, number, number] }) => `${years[p.data[1]]} ${ML[p.data[0]]}: <b>${p.data[2].toFixed(2)}%</b>`,
    },
    grid: { left: '8%', right: '5%', top: '3%', bottom: '18%' },
    xAxis: { type: 'category', data: ML, ...BASE_XAXIS },
    yAxis: { type: 'category', data: years, ...BASE_YAXIS, axisLabel: { color: '#64748b', fontSize: 10 } },
    visualMap: {
      min: -10, max: 10, calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
      inRange: { color: ['#ef4444', '#1e293b', '#22c55e'] }, textStyle: { color: '#94a3b8', fontSize: 10 },
    },
    series: [{ type: 'heatmap', data: hData,
      label: { show: years.length <= 12, formatter: (p: { data: [number, number, number] }) => `${p.data[2].toFixed(1)}`, fontSize: 9, color: '#f1f5f9' } }],
  }
}

function downloadJson() {
  if (!result.value) return
  const blob = new Blob([JSON.stringify(result.value, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = `backtest_${result.value.run_id}.json`; a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  const res = await backtestApi.list().catch(() => null)
  if (res) history.value = res.data
})
</script>
