<template>
  <div class="space-y-5 animate-fade-in">
    <SectionHeader title="Statistical Analysis Hub" description="Regime detection · Seasonality · Tail risk · Rolling statistics">
      <div class="flex items-center gap-2">
        <div class="w-36">
          <TickerSearch :model-value="[ticker]" @update:model-value="v => ticker = v[0] ?? 'SPY'" :multi="false" />
        </div>
        <DateRangePicker v-model="dateRange" />
      </div>
    </SectionHeader>

    <!-- Tab bar -->
    <div class="flex border-b border-surface-700/50 gap-1">
      <button v-for="tab in tabs" :key="tab.key"
        @click="activeTab = tab.key"
        class="tab-item" :class="{ active: activeTab === tab.key }">
        {{ tab.label }}
      </button>
    </div>

    <!-- ── Tab 1: Regime Detection ───────────────────────────────────────── -->
    <div v-if="activeTab === 'regime'" class="space-y-4">
      <div class="flex justify-end">
        <button @click="loadRegime" :disabled="regimeLoading" class="btn-primary text-sm">
          <svg v-if="regimeLoading" class="w-4 h-4 animate-spin inline mr-1" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          Analyse Regimes
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="lg:col-span-2">
          <ChartCard title="HMM Regime Chart" subtitle="Last 252 trading days" :loading="regimeLoading" :height="260" @refresh="loadRegime">
            <VChart v-if="regimeOption" :option="regimeOption" autoresize style="height:260px" />
          </ChartCard>
        </div>
        <ChartCard title="Regime Statistics" :loading="regimeLoading" :height="260">
          <DataTable v-if="regimeStats.length" :columns="regimeCols" :rows="regimeStats" />
        </ChartCard>
      </div>

      <!-- Interpretation -->
      <div v-if="regimeInterpretation" class="glass p-4 border-l-2 border-primary-500">
        <p class="text-sm text-surface-300 leading-relaxed">{{ regimeInterpretation }}</p>
      </div>
    </div>

    <!-- ── Tab 2: Seasonality ─────────────────────────────────────────────── -->
    <div v-if="activeTab === 'seasonality'" class="space-y-4">
      <div class="flex justify-end">
        <button @click="loadSeasonality" :disabled="seasonLoading" class="btn-primary text-sm">Analyse Seasonality</button>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Day-of-Week Effect" subtitle="Average return per weekday" :loading="seasonLoading" @refresh="loadSeasonality">
          <VChart v-if="dowOption" :option="dowOption" autoresize style="height:240px" />
        </ChartCard>
        <ChartCard title="Month-of-Year Effect" subtitle="Average return per calendar month" :loading="seasonLoading" @refresh="loadSeasonality">
          <VChart v-if="monthOption" :option="monthOption" autoresize style="height:240px" />
        </ChartCard>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="glass p-4 space-y-2">
          <h4 class="text-sm font-semibold text-surface-200">January Effect</h4>
          <template v-if="januaryEffect">
            <div class="flex items-center gap-2">
              <span class="badge" :class="januaryEffect.detected ? 'badge-bull' : 'badge-bear'">
                {{ januaryEffect.detected ? 'Detected' : 'Not Detected' }}
              </span>
              <span class="text-xs text-surface-400">p = {{ januaryEffect.p_value?.toFixed(4) }}</span>
            </div>
            <p class="text-xs text-surface-400">Avg Jan: <span class="text-surface-200 font-medium">{{ (januaryEffect.avg_jan * 100).toFixed(3) }}%</span> vs Other: <span class="text-surface-200 font-medium">{{ (januaryEffect.avg_other * 100).toFixed(3) }}%</span></p>
          </template>
        </div>
        <div class="glass p-4 space-y-2">
          <h4 class="text-sm font-semibold text-surface-200">Monday Effect</h4>
          <template v-if="mondayEffect">
            <div class="flex items-center gap-2">
              <span class="badge" :class="mondayEffect.detected ? 'badge-bull' : 'badge-bear'">
                {{ mondayEffect.detected ? 'Detected' : 'Not Detected' }}
              </span>
              <span class="text-xs text-surface-400">p = {{ mondayEffect.p_value?.toFixed(4) }}</span>
            </div>
            <p class="text-xs text-surface-400">Avg Mon: <span class="text-surface-200 font-medium">{{ (mondayEffect.avg_mon * 100).toFixed(3) }}%</span> vs Other: <span class="text-surface-200 font-medium">{{ (mondayEffect.avg_other * 100).toFixed(3) }}%</span></p>
          </template>
        </div>
      </div>
    </div>

    <!-- ── Tab 3: Tail Risk ───────────────────────────────────────────────── -->
    <div v-if="activeTab === 'tailrisk'" class="space-y-4">
      <div class="flex justify-end">
        <button @click="loadDistribution" :disabled="distLoading" class="btn-primary text-sm">Analyse Tail Risk</button>
      </div>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="lg:col-span-2">
          <ChartCard title="Tail Risk Curve" subtitle="Empirical loss quantiles" :loading="distLoading" @refresh="loadDistribution">
            <VChart v-if="tailOption" :option="tailOption" autoresize style="height:280px" />
          </ChartCard>
        </div>
        <div class="space-y-3">
          <ChartCard title="VaR Comparison" :loading="distLoading" :height="150">
            <DataTable v-if="varRows.length" :columns="varCols" :rows="varRows" />
          </ChartCard>
          <div v-if="bestFit" class="glass p-4 space-y-1.5">
            <h4 class="text-xs font-semibold text-surface-400 uppercase tracking-wider">Best Fit Distribution</h4>
            <p class="text-sm font-bold text-primary-400">{{ bestFit.name }}</p>
            <p class="text-xs text-surface-400">KS p-value: <span class="text-surface-200">{{ bestFit.ks_pvalue?.toFixed(4) }}</span></p>
            <p class="text-xs text-surface-400">KS stat: <span class="text-surface-200">{{ bestFit.ks_stat?.toFixed(4) }}</span></p>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Tab 4: Rolling Stats ───────────────────────────────────────────── -->
    <div v-if="activeTab === 'rolling'" class="space-y-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <label class="text-xs text-surface-400">Window (days)</label>
          <select v-model="rollingWindow" class="bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-md px-2 py-1 outline-none focus:border-primary-500">
            <option :value="63">63 (Quarter)</option>
            <option :value="126">126 (Half-year)</option>
            <option :value="252">252 (1 Year)</option>
            <option :value="504">504 (2 Years)</option>
          </select>
          <label class="text-xs text-surface-400">Benchmark</label>
          <input v-model="benchmark" class="w-20 bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-md px-2 py-1 outline-none focus:border-primary-500" />
        </div>
        <button @click="loadRolling" :disabled="rollingLoading" class="btn-primary text-sm">Compute Rolling</button>
      </div>

      <ChartCard title="Rolling Sharpe Ratio" :subtitle="`${rollingWindow}-day rolling window`" :loading="rollingLoading" @refresh="loadRolling">
        <VChart v-if="rollingSharpeOption" :option="rollingSharpeOption" autoresize style="height:200px" />
      </ChartCard>
      <ChartCard title="Rolling Annualised Volatility (%)" :subtitle="`${rollingWindow}-day rolling window`" :loading="rollingLoading">
        <VChart v-if="rollingVolOption" :option="rollingVolOption" autoresize style="height:200px" />
      </ChartCard>
      <ChartCard title="Rolling Beta vs Benchmark" :subtitle="`${rollingWindow}-day window vs ${benchmark}`" :loading="rollingLoading">
        <VChart v-if="rollingBetaOption" :option="rollingBetaOption" autoresize style="height:200px" />
      </ChartCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import dayjs from 'dayjs'
import SectionHeader   from '@/components/shared/SectionHeader.vue'
import ChartCard       from '@/components/shared/ChartCard.vue'
import DataTable       from '@/components/shared/DataTable.vue'
import TickerSearch    from '@/components/shared/TickerSearch.vue'
import DateRangePicker from '@/components/shared/DateRangePicker.vue'
import { statsApi } from '@/api/statsApi'
import { dataApi  } from '@/api/dataApi'
import type { DateRange } from '@/types'
import {
  BASE_TOOLTIP, BASE_GRID, BASE_XAXIS, BASE_YAXIS, BASE_DATAZONE,
  CHART_COLORS, sharpeSeries, volSeries, priceToReturns,
} from '@/components/charts/chartTheme'

const ticker    = ref('SPY')
const dateRange = ref<DateRange>({
  start: dayjs().subtract(10, 'year').format('YYYY-MM-DD'),
  end:   dayjs().format('YYYY-MM-DD'),
})
const activeTab = ref<'regime' | 'seasonality' | 'tailrisk' | 'rolling'>('regime')
const tabs = [
  { key: 'regime'      as const, label: '① Regime Detection' },
  { key: 'seasonality' as const, label: '② Seasonality' },
  { key: 'tailrisk'    as const, label: '③ Tail Risk' },
  { key: 'rolling'     as const, label: '④ Rolling Stats' },
]

// ── Regime ────────────────────────────────────────────────────────────────────
const regimeLoading      = ref(false)
const regimeOption       = ref<Record<string, unknown> | null>(null)
const regimeStats        = ref<Record<string, unknown>[]>([])
const regimeInterpretation = ref('')

const REGIME_COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#a78bfa']
const REGIME_LABELS = ['Bull', 'Bear', 'Sideways', 'Volatile']

const regimeCols = [
  { key: 'label',      label: 'Regime' },
  { key: 'pct_time',   label: '% Time',   align: 'right' as const, format: (v: unknown) => `${((v as number)*100).toFixed(1)}%` },
  { key: 'avg_return', label: 'Avg Ret',  align: 'right' as const, colorize: true, format: (v: unknown) => `${((v as number)*100).toFixed(3)}%` },
  { key: 'volatility', label: 'Vol',      align: 'right' as const, format: (v: unknown) => `${((v as number)*100).toFixed(2)}%` },
]

async function loadRegime() {
  regimeLoading.value = true
  try {
    const res = await statsApi.regime(ticker.value, 3, dateRange.value.start, dateRange.value.end)
    const d = res.data
    const dates   = d.regimes.map((r) => r.date)
    const regimes = d.regimes.map((r) => r.regime)

    // Build stacked area: one series per regime state
    const nStates = new Set(regimes).size
    const seriesData = Array.from({ length: nStates }, (_, si) =>
      regimes.map((r) => (r === si ? 1 : 0))
    )

    regimeOption.value = {
      tooltip:  { ...BASE_TOOLTIP, trigger: 'axis' },
      legend:   { data: REGIME_LABELS.slice(0, nStates), bottom: 0, textStyle: { color: '#94a3b8' } },
      grid:     { ...BASE_GRID, bottom: '18%' },
      xAxis:    { ...BASE_XAXIS, data: dates },
      yAxis:    { ...BASE_YAXIS, max: 1, axisLabel: { show: false } },
      dataZoom: BASE_DATAZONE,
      series:   seriesData.map((data, si) => ({
        name: REGIME_LABELS[si] ?? `State ${si}`,
        type: 'line', data, stack: 'regime',
        symbol: 'none', smooth: false,
        areaStyle: { color: REGIME_COLORS[si] + '99' },
        lineStyle: { width: 0 },
      })),
    }

    // Stats table
    regimeStats.value = d.stats.map((s) => ({
      ...s,
      label: REGIME_LABELS[s.regime as number] ?? `State ${s.regime}`,
    }))

    // Interpretation text
    if (d.stats.length) {
      const bull = d.stats.find((s) => s.regime === 0)
      const bear = d.stats.find((s) => s.regime === 1)
      const pBull = bull ? ((bull.pct_time as number) * 100).toFixed(1) : '?'
      const pBear = bear ? ((bear.pct_time as number) * 100).toFixed(1) : '?'
      regimeInterpretation.value = `${ticker.value} was in Bull regime ${pBull}% and Bear regime ${pBear}% of the time over the selected period. ${bull && (bull.avg_return as number) > 0 ? 'Positive average returns in bull state confirm upward trend bias.' : ''}`
    }
  } finally {
    regimeLoading.value = false
  }
}

// ── Seasonality ───────────────────────────────────────────────────────────────
const seasonLoading = ref(false)
const dowOption     = ref<Record<string, unknown> | null>(null)
const monthOption   = ref<Record<string, unknown> | null>(null)
const januaryEffect = ref<{ detected: boolean; p_value: number; avg_jan: number; avg_other: number } | null>(null)
const mondayEffect  = ref<{ detected: boolean; p_value: number; avg_mon: number; avg_other: number } | null>(null)

function makeEffectBar(labels: string[], values: number[], stds: number[], color = '#3b82f6') {
  return {
    tooltip:  { ...BASE_TOOLTIP },
    grid:     { ...BASE_GRID },
    xAxis:    { ...BASE_XAXIS, data: labels },
    yAxis:    { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `${(v*100).toFixed(2)}%` } },
    series: [{
      type: 'bar', data: values.map((v, i) => ({
        value: v,
        itemStyle: { color: v >= 0 ? '#22c55e' : '#ef4444', borderRadius: [4, 4, 0, 0] },
      })), barMaxWidth: 40,
    }],
  }
}

async function loadSeasonality() {
  seasonLoading.value = true
  try {
    const res = await statsApi.seasonality(ticker.value, dateRange.value.start, dateRange.value.end)
    const d = res.data

    const DOW_LABELS = ['Mon','Tue','Wed','Thu','Fri']
    dowOption.value = makeEffectBar(
      d.day_of_week.map((r) => DOW_LABELS[Number(r.label)] ?? r.label),
      d.day_of_week.map((r) => r.mean_return),
      d.day_of_week.map((r) => r.std),
    )

    const MONTH_LABELS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    monthOption.value = makeEffectBar(
      d.month.map((r) => MONTH_LABELS[Number(r.label) - 1] ?? r.label),
      d.month.map((r) => r.mean_return),
      d.month.map((r) => r.std),
    )

    januaryEffect.value = d.january_effect as typeof januaryEffect.value
    mondayEffect.value  = d.monday_effect as typeof mondayEffect.value
  } finally {
    seasonLoading.value = false
  }
}

// ── Tail Risk ─────────────────────────────────────────────────────────────────
const distLoading = ref(false)
const tailOption  = ref<Record<string, unknown> | null>(null)
const varRows     = ref<Record<string, unknown>[]>([])
const bestFit     = ref<{ name: string; ks_pvalue: number; ks_stat: number } | null>(null)

const varCols = [
  { key: 'method', label: 'Method' },
  { key: 'var95',  label: 'VaR 95%', align: 'right' as const, colorize: true, format: (v: unknown) => `${((v as number)*100).toFixed(3)}%` },
  { key: 'var99',  label: 'VaR 99%', align: 'right' as const, colorize: true, format: (v: unknown) => `${((v as number)*100).toFixed(3)}%` },
]

async function loadDistribution() {
  distLoading.value = true
  try {
    const res = await statsApi.distribution(ticker.value, dateRange.value.start, dateRange.value.end)
    const d = res.data
    const tr = d.tail_risk

    varRows.value = [
      { method: 'Historical',  var95: tr.var_95_hist  ?? tr.var_95,  var99: tr.var_99_hist  ?? tr.var_99 },
      { method: 'Parametric',  var95: tr.var_95_param ?? tr.var_95,  var99: tr.var_99_param ?? tr.var_99 },
      { method: 'Cornish-Fisher', var95: tr.var_95_cf ?? tr.var_95, var99: tr.var_99_cf ?? tr.var_99 },
    ]

    bestFit.value = d.best_fit as typeof bestFit.value

    // Empirical tail quantile chart
    const quantiles = [0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.10,0.15,0.20]
    const qValues   = quantiles.map((q) => {
      const key = `var_${Math.round(q*100)}`
      return tr[key] ?? null
    })
    tailOption.value = {
      tooltip:  { ...BASE_TOOLTIP },
      grid:     { ...BASE_GRID },
      xAxis:    { ...BASE_XAXIS, data: quantiles.map((q) => `${(q*100).toFixed(0)}%`), name: 'Loss Quantile' },
      yAxis:    { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `${(v*100).toFixed(2)}%` } },
      series: [{
        name: 'VaR', type: 'line',
        data: qValues.map((v) => v !== null ? +(v).toFixed(6) : null),
        symbol: 'circle', symbolSize: 5,
        lineStyle: { color: '#ef4444', width: 2 },
        itemStyle: { color: '#ef4444' },
        areaStyle: { color: 'rgba(239,68,68,0.1)' },
      }],
    }
  } finally {
    distLoading.value = false
  }
}

// ── Rolling Stats ─────────────────────────────────────────────────────────────
const rollingLoading      = ref(false)
const rollingWindow       = ref(252)
const benchmark           = ref('SPY')
const rollingSharpeOption = ref<Record<string, unknown> | null>(null)
const rollingVolOption    = ref<Record<string, unknown> | null>(null)
const rollingBetaOption   = ref<Record<string, unknown> | null>(null)

function makeRollingChart(dates: string[], values: (number | null)[], name: string, color: string, yFmt?: (v: number) => string) {
  return {
    tooltip:  { ...BASE_TOOLTIP },
    grid:     { ...BASE_GRID, bottom: '14%' },
    xAxis:    { ...BASE_XAXIS, data: dates },
    yAxis:    { ...BASE_YAXIS, ...(yFmt ? { axisLabel: { ...BASE_YAXIS.axisLabel, formatter: yFmt } } : {}) },
    dataZoom: BASE_DATAZONE,
    series: [{
      name, type: 'line', data: values,
      symbol: 'none', smooth: false,
      lineStyle: { color, width: 1.5 },
      areaStyle: { color: color + '18' },
      markLine: {
        silent: true,
        lineStyle: { color: '#334155', type: 'dashed' },
        data: [{ yAxis: 0 }],
      },
    }],
  }
}

async function loadRolling() {
  rollingLoading.value = true
  try {
    const [prRes, bmRes] = await Promise.all([
      dataApi.prices(ticker.value,   dateRange.value.start, dateRange.value.end),
      dataApi.prices(benchmark.value, dateRange.value.start, dateRange.value.end),
    ])
    const bars  = prRes.data.data
    const bBars = bmRes.data.data

    const dates   = bars.slice(1).map((b) => b.date)
    const rets    = priceToReturns(bars.map((b) => b.close))
    const bmRets  = priceToReturns(bBars.map((b) => b.close))

    const sharpeArr = sharpeSeries(rets, rollingWindow.value)
    const volArr    = volSeries(rets, rollingWindow.value)

    // Beta = cov(r, bm) / var(bm)
    const betaArr = rets.map((_, i) => {
      if (i < rollingWindow.value - 1) return null
      const rSlice  = rets.slice(i - rollingWindow.value + 1, i + 1)
      const bmSlice = bmRets.slice(i - rollingWindow.value + 1, i + 1)
      if (bmSlice.length !== rSlice.length) return null
      const mR  = rSlice.reduce((a, b) => a + b, 0)  / rSlice.length
      const mBm = bmSlice.reduce((a, b) => a + b, 0) / bmSlice.length
      const cov = rSlice.reduce((a, r, j) => a + (r - mR) * (bmSlice[j] - mBm), 0) / rSlice.length
      const varBm = bmSlice.reduce((a, b) => a + (b - mBm) ** 2, 0) / bmSlice.length
      return varBm === 0 ? null : +(cov / varBm).toFixed(4)
    })

    rollingSharpeOption.value = makeRollingChart(dates, sharpeArr, 'Sharpe', '#3b82f6', (v) => v.toFixed(2))
    rollingVolOption.value    = makeRollingChart(dates, volArr,    'Vol %',  '#f59e0b', (v) => `${v.toFixed(1)}%`)
    rollingBetaOption.value   = makeRollingChart(dates, betaArr,   'Beta',   '#a78bfa', (v) => v.toFixed(2))
  } finally {
    rollingLoading.value = false
  }
}

watch([ticker, dateRange], () => {
  if (activeTab.value === 'regime')      loadRegime()
  else if (activeTab.value === 'seasonality') loadSeasonality()
  else if (activeTab.value === 'tailrisk')    loadDistribution()
  else                                        loadRolling()
}, { deep: true })
</script>
