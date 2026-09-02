<template>
  <div class="space-y-5 animate-fade-in">
    <SectionHeader title="Strategy Optimizer" description="Grid search + walk-forward optimization" />

    <div class="grid grid-cols-1 xl:grid-cols-3 gap-5">
      <!-- Config -->
      <div class="xl:col-span-1 space-y-4">
        <div class="glass p-4 space-y-4">
          <h3 class="text-sm font-semibold text-surface-200">Configuration</h3>

          <div class="space-y-1.5">
            <label class="text-xs text-surface-400">Strategy</label>
            <select v-model="form.strategy" class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-3 py-2 outline-none focus:border-primary-500">
              <option v-for="(label, key) in STRATEGY_LABELS" :key="key" :value="key">{{ label }}</option>
            </select>
          </div>

          <div class="space-y-1.5">
            <label class="text-xs text-surface-400">Tickers</label>
            <TickerSearch v-model="form.tickers" :multi="true" />
          </div>

          <div class="space-y-1.5">
            <label class="text-xs text-surface-400">Date Range</label>
            <DateRangePicker v-model="dateRange" />
          </div>

          <div class="space-y-1.5">
            <label class="text-xs text-surface-400">Optimise Metric</label>
            <select v-model="form.metric" class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded-lg px-2 py-1.5 outline-none focus:border-primary-500">
              <option value="sharpe">Sharpe Ratio</option>
              <option value="cagr">CAGR</option>
              <option value="calmar">Calmar Ratio</option>
              <option value="sortino">Sortino Ratio</option>
              <option value="max_drawdown">Max Drawdown (min)</option>
            </select>
          </div>

          <!-- Parameter grid builder -->
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <h4 class="text-xs font-semibold text-surface-400 uppercase tracking-wider">Parameter Grid</h4>
              <button @click="addParam" class="btn-ghost text-xs px-2 py-1">+ Add</button>
            </div>
            <div v-for="(param, i) in paramGrid" :key="i" class="bg-surface-800/50 rounded-lg p-2.5 space-y-1.5">
              <div class="flex gap-2">
                <input v-model="param.key" placeholder="param name" class="flex-1 bg-surface-800 border border-surface-700 text-xs text-surface-200 rounded px-2 py-1 outline-none" />
                <button @click="paramGrid.splice(i, 1)" class="text-bear/70 hover:text-bear text-xs px-1">✕</button>
              </div>
              <input v-model="param.values" placeholder="e.g. 10,20,30 or 10:100:10"
                class="w-full bg-surface-800 border border-surface-700 text-xs text-surface-200 rounded px-2 py-1 outline-none" />
              <p class="text-xs text-surface-500">Values: {{ parseValues(param.values).join(', ') || '—' }}</p>
            </div>
          </div>

          <button @click="runGrid" :disabled="running || !form.tickers.length || !paramGrid.length" class="btn-primary w-full flex items-center justify-center gap-2">
            <svg v-if="running" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            {{ running ? `Running ${totalConfigs} configs…` : `Run Grid (${totalConfigs} configs)` }}
          </button>
        </div>

        <!-- Walk-Forward section -->
        <div class="glass p-4 space-y-3">
          <h3 class="text-sm font-semibold text-surface-200">Walk-Forward Analysis</h3>
          <div class="grid grid-cols-2 gap-2">
            <div class="space-y-1">
              <label class="text-xs text-surface-400">Train Years</label>
              <input type="number" v-model.number="wfTrainYears" min="1" max="10" class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded px-2 py-1 outline-none" />
            </div>
            <div class="space-y-1">
              <label class="text-xs text-surface-400">Test Years</label>
              <input type="number" v-model.number="wfTestYears" min="1" max="5" class="w-full bg-surface-800 border border-surface-700 text-sm text-surface-200 rounded px-2 py-1 outline-none" />
            </div>
          </div>
          <button @click="runWalkForward" :disabled="wfRunning || !form.tickers.length" class="btn-primary w-full text-sm">
            <svg v-if="wfRunning" class="w-4 h-4 animate-spin inline mr-1" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            Run Walk-Forward
          </button>
        </div>
      </div>

      <!-- Results -->
      <div class="xl:col-span-2 space-y-4">
        <template v-if="results.length">
          <!-- Top 5 best params -->
          <div>
            <h3 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">Top 5 Best Parameters</h3>
            <div class="grid grid-cols-1 sm:grid-cols-5 gap-3">
              <div v-for="(r, i) in top5" :key="i" class="glass p-3 space-y-1.5">
                <span class="badge badge-blue text-xs">#{{ i + 1 }}</span>
                <p class="text-xs text-surface-400 mt-1">{{ form.metric }}: <span class="text-surface-100 font-bold">{{ (r[form.metric] as number)?.toFixed(4) }}</span></p>
                <div class="space-y-0.5">
                  <p v-for="(v, k) in r" :key="String(k)" v-if="!['rank', form.metric].includes(String(k))" class="text-xs text-surface-400">
                    {{ k }}: <span class="text-surface-200">{{ v }}</span>
                  </p>
                </div>
                <button @click="applyToBacktest(r)" class="btn-ghost text-xs w-full px-2 py-1 mt-1 border border-surface-700">Apply →</button>
              </div>
            </div>
          </div>

          <!-- Results table -->
          <ChartCard title="All Results" :subtitle="`${results.length} configurations`">
            <DataTable :columns="resultCols" :rows="results" :page-size="20" :searchable="false" />
          </ChartCard>

          <!-- Surface plot (if 2 params) -->
          <ChartCard v-if="surfaceOption" title="Optimization Surface" subtitle="2D heatmap of metric value">
            <VChart :option="surfaceOption" autoresize style="height:320px" />
          </ChartCard>
        </template>

        <!-- Walk-forward results -->
        <template v-if="wfResults.length">
          <ChartCard title="Walk-Forward Results" subtitle="Out-of-sample performance per fold">
            <VChart v-if="wfOption" :option="wfOption" autoresize style="height:260px" />
          </ChartCard>
        </template>

        <div v-if="!results.length && !wfResults.length" class="flex flex-col items-center justify-center h-48 text-surface-500 glass rounded-xl">
          <p class="text-sm">Configure parameters and run the optimizer</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import SectionHeader   from '@/components/shared/SectionHeader.vue'
import ChartCard       from '@/components/shared/ChartCard.vue'
import DataTable       from '@/components/shared/DataTable.vue'
import TickerSearch    from '@/components/shared/TickerSearch.vue'
import DateRangePicker from '@/components/shared/DateRangePicker.vue'
import { optimizeApi } from '@/api/optimizeApi'
import type { DateRange } from '@/types'
import { STRATEGY_LABELS } from '@/types'
import { CHART_COLORS, BASE_TOOLTIP, BASE_GRID, BASE_XAXIS, BASE_YAXIS } from '@/components/charts/chartTheme'

const router = useRouter()

const form = ref({
  strategy: 'sma_crossover',
  tickers:  ['AAPL'],
  metric:   'sharpe',
})
const dateRange = ref<DateRange>({ start: '2015-01-01', end: '2024-12-31' })
const paramGrid = ref([
  { key: 'sma_fast', values: '10,20,30' },
  { key: 'sma_slow', values: '50,100,200' },
])

function addParam() { paramGrid.value.push({ key: '', values: '' }) }

function parseValues(str: string): number[] {
  if (!str) return []
  if (str.includes(':')) {
    const [start, end, step] = str.split(':').map(Number)
    const out: number[] = []
    for (let v = start; v <= end; v += step) out.push(v)
    return out
  }
  return str.split(',').map(Number).filter((n) => !isNaN(n))
}

const totalConfigs = computed(() => {
  return paramGrid.value.reduce((acc, p) => acc * Math.max(parseValues(p.values).length, 1), 1)
})

const running = ref(false)
const results = ref<Record<string, unknown>[]>([])
const top5    = computed(() => results.value.slice(0, 5))

const resultCols = computed(() => {
  if (!results.value.length) return []
  return Object.keys(results.value[0]).map((k) => ({
    key: k, label: k, align: 'right' as const,
    format: (v: unknown) => typeof v === 'number' ? v.toFixed(4) : String(v ?? '—'),
  }))
})

const surfaceOption = ref<Record<string, unknown> | null>(null)

async function runGrid() {
  if (!form.value.tickers.length || !paramGrid.value.length) return
  running.value = true
  try {
    const grid: Record<string, unknown[]> = {}
    paramGrid.value.forEach((p) => { if (p.key) grid[p.key] = parseValues(p.values) })

    const res = await optimizeApi.grid({
      strategy:   form.value.strategy,
      tickers:    form.value.tickers,
      start_date: dateRange.value.start,
      end_date:   dateRange.value.end,
      param_grid: grid,
      metric:     form.value.metric,
      maximize:   form.value.metric !== 'max_drawdown',
      n_jobs:     -1,
    })

    results.value = (res.data.all_results ?? [])
      .sort((a: Record<string, unknown>, b: Record<string, unknown>) =>
        (b[form.value.metric] as number) - (a[form.value.metric] as number))
      .map((r: Record<string, unknown>, i: number) => ({ ...r, rank: i + 1 }))

    // Surface plot if exactly 2 params
    const keys = paramGrid.value.filter((p) => p.key).map((p) => p.key)
    if (keys.length === 2) buildSurface(keys[0], keys[1])
  } finally {
    running.value = false
  }
}

function buildSurface(xKey: string, yKey: string) {
  const xVals = [...new Set(results.value.map((r) => r[xKey] as number))].sort((a, b) => a - b)
  const yVals = [...new Set(results.value.map((r) => r[yKey] as number))].sort((a, b) => a - b)
  const metric = form.value.metric
  const data: [number, number, number][] = []
  results.value.forEach((r) => {
    const xi = xVals.indexOf(r[xKey] as number)
    const yi = yVals.indexOf(r[yKey] as number)
    if (xi >= 0 && yi >= 0) data.push([xi, yi, +(r[metric] as number).toFixed(4)])
  })
  const vals = data.map((d) => d[2])
  const mn = Math.min(...vals), mx = Math.max(...vals)
  surfaceOption.value = {
    tooltip: {
      trigger: 'item', backgroundColor: '#1e293b', borderColor: '#334155', textStyle: { color: '#f1f5f9' },
      formatter: (p: { data: [number, number, number] }) =>
        `${xKey}=${xVals[p.data[0]]} ${yKey}=${yVals[p.data[1]]}: <b>${p.data[2].toFixed(4)}</b>`,
    },
    grid: { left: '10%', right: '5%', top: '5%', bottom: '18%' },
    xAxis: { type: 'category', data: xVals.map(String), name: xKey, ...{ axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { color: '#64748b' }, axisTick: { show: false } } },
    yAxis: { type: 'category', data: yVals.map(String), name: yKey, ...{ axisLine: { show: false }, axisLabel: { color: '#64748b' }, axisTick: { show: false } } },
    visualMap: { min: mn, max: mx, calculable: true, orient: 'horizontal', left: 'center', bottom: 0,
      inRange: { color: ['#ef4444', '#f59e0b', '#22c55e'] }, textStyle: { color: '#94a3b8', fontSize: 10 } },
    series: [{ type: 'heatmap', data,
      label: { show: data.length <= 25, formatter: (p: { data: [number, number, number] }) => p.data[2].toFixed(2), color: '#f1f5f9', fontSize: 10 } }],
  }
}

function applyToBacktest(params: Record<string, unknown>) {
  router.push({ path: '/backtest', query: { params: JSON.stringify(params), strategy: form.value.strategy } })
}

// Walk-forward
const wfRunning = ref(false)
const wfResults = ref<Record<string, unknown>[]>([])
const wfOption  = ref<Record<string, unknown> | null>(null)
const wfTrainYears = ref(3)
const wfTestYears  = ref(1)

async function runWalkForward() {
  wfRunning.value = true
  try {
    const grid: Record<string, unknown[]> = {}
    paramGrid.value.forEach((p) => { if (p.key) grid[p.key] = parseValues(p.values) })
    const res = await optimizeApi.walkForward({
      strategy:   form.value.strategy,
      tickers:    form.value.tickers,
      start_date: dateRange.value.start,
      end_date:   dateRange.value.end,
      param_grid: grid,
      metric:     form.value.metric,
      maximize:   true,
    }, wfTrainYears.value, wfTestYears.value)

    wfResults.value = res.data as Record<string, unknown>[]
    const folds = wfResults.value.map((_, i) => `Fold ${i + 1}`)
    const metric = form.value.metric
    wfOption.value = {
      tooltip: { ...BASE_TOOLTIP },
      grid:    { ...BASE_GRID },
      xAxis:   { ...BASE_XAXIS, data: folds },
      yAxis:   { ...BASE_YAXIS },
      series: [{
        type: 'bar', data: wfResults.value.map((r) => (r[metric] as number ?? 0).toFixed(4)),
        itemStyle: { color: (p: { value: number }) => p.value >= 0 ? '#22c55e' : '#ef4444', borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 40,
      }],
    }
  } finally {
    wfRunning.value = false
  }
}
</script>
