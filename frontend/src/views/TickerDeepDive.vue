<template>
  <div class="space-y-5 animate-fade-in">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
      <div class="flex-1">
        <div class="flex items-baseline gap-2">
          <h1 class="text-2xl font-bold text-surface-100">{{ symbol }}</h1>
          <span v-if="lastPrice" class="text-lg font-semibold tabular-nums"
            :class="dailyReturn >= 0 ? 'text-bull' : 'text-bear'">
            ${{ lastPrice.toFixed(2) }}
            <span class="text-sm">({{ dailyReturn >= 0 ? '+' : '' }}{{ (dailyReturn*100).toFixed(2) }}%)</span>
          </span>
        </div>
        <p class="text-sm text-surface-400 mt-0.5">Historical Deep Dive · {{ dateRange.start }} → {{ dateRange.end }}</p>
      </div>

      <!-- Ticker Search + Date Range -->
      <div class="flex flex-col sm:flex-row gap-2">
        <div class="w-48">
          <TickerSearch :model-value="[symbol]" @update:model-value="onTickerChange" :multi="false" placeholder="Change ticker…" />
        </div>
        <DateRangePicker v-model="dateRange" />
      </div>
    </div>

    <!-- Candlestick + Indicators -->
    <ChartCard title="Price Chart" :loading="priceLoading" :error="priceError" :height="380" @refresh="loadPrice">
      <template #toolbar>
        <div class="flex gap-1.5 text-xs">
          <label v-for="ov in overlays" :key="ov.key" class="flex items-center gap-1 cursor-pointer">
            <input type="checkbox" v-model="ov.active" class="accent-primary-500" @change="buildCandleOption" />
            <span class="text-surface-400">{{ ov.label }}</span>
          </label>
        </div>
      </template>
      <VChart v-if="candleOption" :option="candleOption" autoresize style="height:360px" />
    </ChartCard>

    <!-- RSI + MACD -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ChartCard title="RSI (14)" :loading="indicatorLoading" :height="150" @refresh="loadIndicators">
        <VChart v-if="rsiOption" :option="rsiOption" autoresize style="height:140px" />
      </ChartCard>
      <ChartCard title="MACD (12,26,9)" :loading="indicatorLoading" :height="150" @refresh="loadIndicators">
        <VChart v-if="macdOption" :option="macdOption" autoresize style="height:140px" />
      </ChartCard>
    </div>

    <!-- Stats cards -->
    <div>
      <h3 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">Descriptive Statistics</h3>
      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <MetricCard v-if="desc" title="Count"      :value="desc.count"          format="raw"  :delay="0"  />
        <MetricCard v-if="desc" title="Mean Daily" :value="desc.mean"           format="percent" :colorize="true" :delay="60" />
        <MetricCard v-if="desc" title="Std Dev"    :value="desc.std"            format="percent" :delay="120" />
        <MetricCard v-if="desc" title="Skewness"   :value="desc.skewness"       format="number"  :delay="180" />
        <MetricCard v-if="desc" title="Kurtosis"   :value="desc.kurtosis"       format="number"  :delay="240" />
        <MetricCard v-if="desc" title="Hurst Exp." :value="desc.hurst"          format="number"  :delay="300" />
        <MetricCard v-if="desc" title="Autocorr 1" :value="desc.autocorr_1"     format="number"  :delay="360" />
        <MetricCard v-if="desc" title="JB p-value" :value="desc.jb_pvalue"      format="number"  :delay="420" />
        <template v-if="!desc && statsLoading">
          <div v-for="i in 8" :key="i" class="glass p-4 h-20 animate-skeleton" />
        </template>
      </div>
    </div>

    <div>
      <h3 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">Risk Metrics</h3>
      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <MetricCard v-if="risk" title="Sharpe"      :value="risk.sharpe"        format="number"  :colorize="true" :delay="0" />
        <MetricCard v-if="risk" title="Sortino"     :value="risk.sortino"       format="number"  :colorize="true" :delay="60" />
        <MetricCard v-if="risk" title="Calmar"      :value="risk.calmar"        format="number"  :colorize="true" :delay="120" />
        <MetricCard v-if="risk" title="Omega"       :value="risk.omega"         format="number"  :delay="180" />
        <MetricCard v-if="risk" title="Max Drawdown":value="risk.max_drawdown"  format="percent" :colorize="true" :delay="240" />
        <MetricCard v-if="risk" title="Ann. Vol"    :value="risk.ann_volatility" format="percent" :delay="300" />
        <MetricCard v-if="risk" title="VaR 95%"     :value="risk.var_95"        format="percent" :colorize="true" :delay="360" />
        <MetricCard v-if="risk" title="CVaR 95%"    :value="risk.cvar_95"       format="percent" :colorize="true" :delay="420" />
        <template v-if="!risk && statsLoading">
          <div v-for="i in 8" :key="i" class="glass p-4 h-20 animate-skeleton" />
        </template>
      </div>
    </div>

    <!-- Monthly Heatmap + Drawdown + Distribution -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ChartCard title="Monthly Returns Heatmap" subtitle="Year × Month (% return)" :loading="statsLoading" @refresh="loadStats">
        <VChart v-if="heatmapOption" :option="heatmapOption" autoresize style="height:320px" />
      </ChartCard>

      <ChartCard title="Underwater / Drawdown Curve" :loading="ddLoading" @refresh="loadDrawdown">
        <VChart v-if="ddOption" :option="ddOption" autoresize style="height:320px" />
      </ChartCard>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ChartCard title="Return Distribution" subtitle="Daily returns histogram + normal overlay" :loading="distLoading" @refresh="loadDistribution">
        <VChart v-if="distOption" :option="distOption" autoresize style="height:280px" />
      </ChartCard>

      <!-- Quick stats sidebar -->
      <div class="glass p-5 space-y-3">
        <h3 class="text-sm font-semibold text-surface-200">Return Summary</h3>
        <template v-if="returnSummary">
          <div v-for="row in returnRows" :key="row.label" class="flex justify-between items-center py-1.5 border-b border-surface-700/30 last:border-0">
            <span class="text-xs text-surface-400">{{ row.label }}</span>
            <span class="text-sm font-semibold tabular-nums" :class="row.color ? (row.value >= 0 ? 'text-bull' : 'text-bear') : 'text-surface-200'">
              {{ row.formatted }}
            </span>
          </div>
        </template>
        <div v-else-if="statsLoading" class="space-y-2">
          <div v-for="i in 6" :key="i" class="h-4 bg-surface-700 rounded animate-skeleton" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import MetricCard     from '@/components/shared/MetricCard.vue'
import ChartCard      from '@/components/shared/ChartCard.vue'
import TickerSearch   from '@/components/shared/TickerSearch.vue'
import DateRangePicker from '@/components/shared/DateRangePicker.vue'
import { dataApi }       from '@/api/dataApi'
import { statsApi }      from '@/api/statsApi'
import { indicatorsApi } from '@/api/indicatorsApi'
import type { DescriptiveStats, RiskMetrics, ReturnSummary, DateRange } from '@/types'
import {
  CHART_COLORS, BASE_TOOLTIP, BASE_LEGEND, BASE_GRID,
  BASE_XAXIS, BASE_YAXIS, BASE_DATAZONE,
} from '@/components/charts/chartTheme'

const route  = useRoute()
const router = useRouter()

const symbol = computed(() => String(route.params.symbol ?? 'AAPL').toUpperCase())

const dateRange = ref<DateRange>({
  start: dayjs().subtract(5, 'year').format('YYYY-MM-DD'),
  end:   dayjs().format('YYYY-MM-DD'),
})

function onTickerChange(v: string[]) {
  if (v[0]) router.push(`/ticker/${v[0]}`)
}

// ── Price / Candle ────────────────────────────────────────────────────────────
const priceLoading = ref(false)
const priceError   = ref<string | null>(null)
const candleOption = ref<Record<string, unknown> | null>(null)
const ohlcvBars    = ref<{ date: string; open: number; high: number; low: number; close: number; volume: number }[]>([])

const lastPrice  = computed(() => ohlcvBars.value.at(-1)?.close ?? 0)
const dailyReturn = computed(() => {
  if (ohlcvBars.value.length < 2) return 0
  const a = ohlcvBars.value.at(-2)!.close
  const b = ohlcvBars.value.at(-1)!.close
  return (b - a) / a
})

const overlays = ref([
  { key: 'sma20',  label: 'SMA 20',  active: true,  color: '#f59e0b', period: 20  },
  { key: 'sma50',  label: 'SMA 50',  active: true,  color: '#3b82f6', period: 50  },
  { key: 'sma200', label: 'SMA 200', active: false, color: '#a78bfa', period: 200 },
  { key: 'bb',     label: 'BB(20)',  active: false, color: '#06b6d4', period: 20  },
])

let maData:  Record<string, number[]> = {}
let bbData:  { upper: number[]; lower: number[] } = { upper: [], lower: [] }

async function loadPrice() {
  priceLoading.value = true
  priceError.value   = null
  try {
    const res = await dataApi.prices(symbol.value, dateRange.value.start, dateRange.value.end)
    ohlcvBars.value = res.data.data

    // Load MA overlays
    const periods = [...new Set(overlays.value.map((o) => o.period))].join(',')
    const [maRes, bbRes] = await Promise.allSettled([
      indicatorsApi.ma(symbol.value, periods, 'sma', dateRange.value.start, dateRange.value.end),
      indicatorsApi.bollinger(symbol.value, 20, 2.0, dateRange.value.start, dateRange.value.end),
    ])
    if (maRes.status === 'fulfilled') maData = maRes.value.data as Record<string, number[]>
    if (bbRes.status === 'fulfilled') {
      // API returns array of records: [{date, upper, middle, lower}, ...]
      // OR object with arrays: {upper: [...], lower: [...]}
      const bd = bbRes.value.data
      if (Array.isArray(bd)) {
        // records format
        bbData.upper = (bd as Record<string, number>[]).map((r) => r.upper ?? 0)
        bbData.lower = (bd as Record<string, number>[]).map((r) => r.lower ?? 0)
      } else {
        // object-of-arrays format
        const obj = bd as Record<string, number[]>
        bbData.upper = obj.upper ?? []
        bbData.lower = obj.lower ?? []
      }
    }
    buildCandleOption()
  } catch (e: unknown) {
    priceError.value = (e as Error).message
  } finally {
    priceLoading.value = false
  }
}

function buildCandleOption() {
  const bars  = ohlcvBars.value
  const dates = bars.map((b) => b.date)
  const ohlc  = bars.map((b) => [b.open, b.close, b.low, b.high])
  const vols  = bars.map((b) => b.volume)

  const overlaySeries = overlays.value
    .filter((o) => o.active && o.key !== 'bb')
    .map((o) => ({
      name: o.label, type: 'line',
      data: maData[`sma_${o.period}`] ?? [],
      smooth: false, symbol: 'none',
      lineStyle: { width: 1.2, color: o.color },
      xAxisIndex: 0, yAxisIndex: 0,
    }))

  if (overlays.value.find((o) => o.key === 'bb' && o.active)) {
    overlaySeries.push(
      { name: 'BB Upper', type: 'line', data: bbData.upper, smooth: false, symbol: 'none',
        lineStyle: { width: 1, color: '#06b6d4', type: 'dashed' }, xAxisIndex: 0, yAxisIndex: 0 } as never,
      { name: 'BB Lower', type: 'line', data: bbData.lower, smooth: false, symbol: 'none',
        lineStyle: { width: 1, color: '#06b6d4', type: 'dashed' }, xAxisIndex: 0, yAxisIndex: 0 } as never,
    )
  }

  candleOption.value = {
    tooltip:  { ...BASE_TOOLTIP },
    legend:   { ...BASE_LEGEND, top: 0, data: overlaySeries.map((s) => s.name) },
    grid:     [
      { left: '1%', right: '2%', top: '10%', height: '60%', containLabel: true },
      { left: '1%', right: '2%', top: '75%', height: '15%', containLabel: true },
    ],
    xAxis:    [
      { ...BASE_XAXIS, data: dates, gridIndex: 0 },
      { ...BASE_XAXIS, data: dates, gridIndex: 1 },
    ],
    yAxis:    [
      { ...BASE_YAXIS, gridIndex: 0, scale: true },
      { ...BASE_YAXIS, gridIndex: 1, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `${(v/1e6).toFixed(0)}M` } },
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], filterMode: 'none' },
      { type: 'slider', xAxisIndex: [0, 1], bottom: 2, height: 20,
        borderColor: '#334155', fillerColor: 'rgba(59,130,246,0.12)',
        handleStyle: { color: '#3b82f6' }, textStyle: { color: '#64748b' } },
    ],
    series: [
      {
        name: symbol.value, type: 'candlestick',
        data: ohlc, xAxisIndex: 0, yAxisIndex: 0,
        itemStyle: {
          color: '#22c55e', color0: '#ef4444',
          borderColor: '#22c55e', borderColor0: '#ef4444',
        },
      },
      {
        name: 'Volume', type: 'bar', data: vols,
        xAxisIndex: 1, yAxisIndex: 1, barMaxWidth: 8,
        itemStyle: { color: 'rgba(99,102,241,0.5)' },
      },
      ...overlaySeries,
    ],
  }
}

// ── Indicators: RSI + MACD ────────────────────────────────────────────────────
const indicatorLoading = ref(false)
const rsiOption  = ref<Record<string, unknown> | null>(null)
const macdOption = ref<Record<string, unknown> | null>(null)

async function loadIndicators() {
  indicatorLoading.value = true
  try {
    const [rsiRes, macdRes] = await Promise.all([
      indicatorsApi.rsi(symbol.value, 14, dateRange.value.start, dateRange.value.end),
      indicatorsApi.macd(symbol.value, 12, 26, 9, dateRange.value.start, dateRange.value.end),
    ])

    // RSI
    const rsiData = rsiRes.data as { date: string[]; rsi: number[] }
    rsiOption.value = {
      tooltip: { ...BASE_TOOLTIP },
      grid:    { left: '1%', right: '2%', top: '5%', bottom: '12%', containLabel: true },
      xAxis:   { ...BASE_XAXIS, data: rsiData.date },
      yAxis:   { ...BASE_YAXIS, min: 0, max: 100 },
      series: [
        { name: 'RSI', type: 'line', data: rsiData.rsi, symbol: 'none', smooth: false,
          lineStyle: { color: '#f59e0b', width: 1.5 } },
        { name: 'OB', type: 'line', data: Array(rsiData.rsi.length).fill(70), symbol: 'none',
          lineStyle: { color: '#ef4444', type: 'dashed', width: 1 } },
        { name: 'OS', type: 'line', data: Array(rsiData.rsi.length).fill(30), symbol: 'none',
          lineStyle: { color: '#22c55e', type: 'dashed', width: 1 } },
      ],
    }

    // MACD
    const md = macdRes.data as { date: string; macd: number; signal: number; histogram: number }[]
    const dates = md.map((r) => r.date)
    const hist  = md.map((r) => r.histogram)
    macdOption.value = {
      tooltip: { ...BASE_TOOLTIP },
      grid:    { left: '1%', right: '2%', top: '5%', bottom: '12%', containLabel: true },
      xAxis:   { ...BASE_XAXIS, data: dates },
      yAxis:   { ...BASE_YAXIS },
      series: [
        { name: 'MACD',   type: 'line', data: md.map((r) => r.macd),   symbol: 'none', lineStyle: { color: '#3b82f6', width: 1.5 } },
        { name: 'Signal', type: 'line', data: md.map((r) => r.signal), symbol: 'none', lineStyle: { color: '#f97316', width: 1.5 } },
        { name: 'Hist',   type: 'bar',  data: hist, barMaxWidth: 4,
          itemStyle: { color: (p: { value: number }) => p.value >= 0 ? '#22c55e' : '#ef4444' } },
      ],
    }
  } finally {
    indicatorLoading.value = false
  }
}

// ── Stats ─────────────────────────────────────────────────────────────────────
const statsLoading  = ref(false)
const desc          = ref<DescriptiveStats | null>(null)
const risk          = ref<RiskMetrics | null>(null)
const returnSummary = ref<ReturnSummary | null>(null)
const heatmapOption = ref<Record<string, unknown> | null>(null)

const returnRows = computed(() => {
  if (!returnSummary.value) return []
  const s = returnSummary.value
  return [
    { label: 'Total Return',       formatted: `${(s.total_return * 100).toFixed(1)}%`,      value: s.total_return,       color: true },
    { label: 'CAGR',               formatted: `${(s.cagr * 100).toFixed(2)}%`,              value: s.cagr,               color: true },
    { label: 'Avg Daily Return',   formatted: `${(s.avg_daily_return * 100).toFixed(4)}%`,  value: s.avg_daily_return,   color: true },
    { label: 'Avg Monthly Return', formatted: `${(s.avg_monthly_return * 100).toFixed(2)}%`, value: s.avg_monthly_return, color: true },
    { label: 'Best Day',           formatted: `+${(s.best_day * 100).toFixed(2)}%`,         value: s.best_day,           color: false },
    { label: 'Worst Day',          formatted: `${(s.worst_day * 100).toFixed(2)}%`,         value: s.worst_day,          color: false },
    { label: '% Positive Days',    formatted: `${(s.pct_positive_days * 100).toFixed(1)}%`, value: s.pct_positive_days,  color: false },
  ]
})

async function loadStats() {
  statsLoading.value = true
  try {
    const [dRes, rRes, retRes, priceRes] = await Promise.all([
      statsApi.descriptive(symbol.value, dateRange.value.start, dateRange.value.end),
      statsApi.risk(symbol.value, dateRange.value.start, dateRange.value.end),
      statsApi.returns(symbol.value, dateRange.value.start, dateRange.value.end),
      dataApi.prices(symbol.value, dateRange.value.start, dateRange.value.end, 'M'),
    ])
    desc.value          = dRes.data
    risk.value          = rRes.data
    returnSummary.value = retRes.data

    // Build monthly heatmap
    const bars = priceRes.data.data
    const monthMap: Record<string, Record<string, number>> = {}
    for (let i = 1; i < bars.length; i++) {
      const yr  = bars[i].date.substring(0, 4)
      const mo  = bars[i].date.substring(5, 7)
      const ret = (bars[i].close - bars[i - 1].close) / bars[i - 1].close
      if (!monthMap[yr]) monthMap[yr] = {}
      monthMap[yr][mo] = +(ret * 100).toFixed(2)
    }
    const years  = Object.keys(monthMap).sort()
    const months = ['01','02','03','04','05','06','07','08','09','10','11','12']
    const MONTH_LABELS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    const heatData: [number, number, number][] = []
    years.forEach((yr, yi) => {
      months.forEach((mo, mi) => {
        const v = monthMap[yr]?.[mo] ?? null
        if (v !== null) heatData.push([mi, yi, v])
      })
    })
    const absMax = Math.max(...heatData.map((d) => Math.abs(d[2])), 1)
    heatmapOption.value = {
      tooltip: {
        ...BASE_TOOLTIP, trigger: 'item',
        formatter: (p: { data: [number, number, number] }) =>
          `${years[p.data[1]]} ${MONTH_LABELS[p.data[0]]}: <b>${p.data[2].toFixed(2)}%</b>`,
      },
      grid:       { left: '8%', right: '5%', top: '3%', bottom: '15%' },
      xAxis:      { type: 'category', data: MONTH_LABELS, ...BASE_XAXIS },
      yAxis:      { type: 'category', data: years, ...BASE_YAXIS, axisLabel: { color: '#64748b', fontSize: 10 } },
      visualMap:  {
        min: -absMax, max: absMax, calculable: true,
        orient: 'horizontal', left: 'center', bottom: 0,
        inRange: { color: ['#ef4444', '#1e293b', '#22c55e'] },
        textStyle: { color: '#94a3b8', fontSize: 10 },
      },
      series: [{
        type: 'heatmap', data: heatData,
        label: { show: years.length <= 15, formatter: (p: { data: [number, number, number] }) => `${p.data[2].toFixed(1)}`, fontSize: 9, color: '#f1f5f9' },
        emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.4)' } },
      }],
    }
  } finally {
    statsLoading.value = false
  }
}

// ── Drawdown ──────────────────────────────────────────────────────────────────
const ddLoading = ref(false)
const ddOption  = ref<Record<string, unknown> | null>(null)

async function loadDrawdown() {
  ddLoading.value = true
  try {
    const res = await statsApi.drawdown(symbol.value, dateRange.value.start, dateRange.value.end)
    const top = res.data.top_10 as { start: string; end: string; drawdown: number }[]
    const prRes = await dataApi.prices(symbol.value, dateRange.value.start, dateRange.value.end)
    const bars  = prRes.data.data
    const dates = bars.map((b) => b.date)
    // Compute underwater curve
    let peak = bars[0]?.close ?? 1
    const uw = bars.map((b) => {
      if (b.close > peak) peak = b.close
      return +((b.close / peak - 1) * 100).toFixed(4)
    })
    ddOption.value = {
      tooltip: { ...BASE_TOOLTIP },
      grid:    { ...BASE_GRID },
      xAxis:   { ...BASE_XAXIS, data: dates },
      yAxis:   { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: '{value}%' } },
      series: [{
        name: 'Drawdown', type: 'line', data: uw,
        symbol: 'none', smooth: false,
        lineStyle: { color: '#ef4444', width: 1 },
        areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: 'rgba(239,68,68,0.4)' }, { offset: 1, color: 'rgba(239,68,68,0.02)' }] } },
      }],
    }
  } finally {
    ddLoading.value = false
  }
}

// ── Distribution ──────────────────────────────────────────────────────────────
const distLoading = ref(false)
const distOption  = ref<Record<string, unknown> | null>(null)

async function loadDistribution() {
  distLoading.value = true
  try {
    const prRes = await dataApi.prices(symbol.value, dateRange.value.start, dateRange.value.end)
    const closes  = prRes.data.data.map((b) => b.close)
    const returns = closes.slice(1).map((c, i) => (c - closes[i]) / closes[i])

    // Build histogram
    const bins  = 60
    const minR  = Math.min(...returns)
    const maxR  = Math.max(...returns)
    const width = (maxR - minR) / bins
    const hist  = Array(bins).fill(0)
    returns.forEach((r) => {
      const i = Math.min(Math.floor((r - minR) / width), bins - 1)
      hist[i]++
    })
    const labels = hist.map((_, i) => ((minR + (i + 0.5) * width) * 100).toFixed(2))
    const mean   = returns.reduce((a, b) => a + b, 0) / returns.length
    const std    = Math.sqrt(returns.reduce((a, b) => a + (b - mean) ** 2, 0) / returns.length)
    const normal = labels.map((l) => {
      const x = parseFloat(l) / 100
      return +(returns.length * width * (1 / (std * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * ((x - mean) / std) ** 2)).toFixed(2)
    })
    distOption.value = {
      tooltip: { ...BASE_TOOLTIP },
      legend:  { ...BASE_LEGEND, bottom: 0 },
      grid:    { ...BASE_GRID },
      xAxis:   { ...BASE_XAXIS, data: labels, axisLabel: { color: '#64748b', fontSize: 10, rotate: 30, formatter: '{value}%' } },
      yAxis:   { ...BASE_YAXIS },
      series: [
        { name: 'Frequency', type: 'bar', data: hist, barMaxWidth: 12,
          itemStyle: { color: 'rgba(59,130,246,0.6)', borderRadius: [2, 2, 0, 0] } },
        { name: 'Normal', type: 'line', data: normal, smooth: true, symbol: 'none',
          lineStyle: { color: '#f59e0b', width: 2 } },
      ],
    }
  } finally {
    distLoading.value = false
  }
}

function loadAll() {
  loadPrice()
  loadIndicators()
  loadStats()
  loadDrawdown()
  loadDistribution()
}

watch(() => symbol.value, loadAll)
watch(() => dateRange.value, loadAll, { deep: true })
onMounted(loadAll)
</script>
