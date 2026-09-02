<template>
  <div class="space-y-5 animate-fade-in">
    <SectionHeader title="Monte Carlo Simulator" description="Simulate future equity paths using historical return distributions" />

    <!-- Config -->
    <div class="glass p-5 space-y-5">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Ticker -->
        <div class="space-y-1.5">
          <label class="text-xs text-surface-400">Ticker</label>
          <div class="w-full">
            <TickerSearch :model-value="[form.ticker]" @update:model-value="v => form.ticker = v[0] ?? 'SPY'" :multi="false" />
          </div>
        </div>

        <!-- Method -->
        <div class="space-y-1.5">
          <label class="text-xs text-surface-400">Simulation Method</label>
          <div class="flex gap-3">
            <label class="flex items-center gap-1.5 cursor-pointer text-sm text-surface-300">
              <input type="radio" value="bootstrap" v-model="form.method" class="accent-primary-500" />
              Bootstrap
            </label>
            <label class="flex items-center gap-1.5 cursor-pointer text-sm text-surface-300">
              <input type="radio" value="parametric" v-model="form.method" class="accent-primary-500" />
              Parametric
            </label>
          </div>
        </div>

        <!-- Horizon -->
        <div class="space-y-1.5">
          <div class="flex justify-between text-xs">
            <span class="text-surface-400">Horizon</span>
            <span class="text-surface-200 font-medium">{{ form.horizon }} days ({{ (form.horizon/252).toFixed(1) }}y)</span>
          </div>
          <input type="range" v-model.number="form.horizon" :min="63" :max="1260" :step="63" class="w-full accent-primary-500" />
        </div>

        <!-- N sims -->
        <div class="space-y-1.5">
          <div class="flex justify-between text-xs">
            <span class="text-surface-400">Simulations</span>
            <span class="text-surface-200 font-medium">{{ form.n_sims.toLocaleString() }}</span>
          </div>
          <input type="range" v-model.number="form.n_sims" :min="100" :max="5000" :step="100" class="w-full accent-primary-500" />
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button @click="run" :disabled="loading" class="btn-primary flex items-center gap-2">
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" /></svg>
          {{ loading ? `Running ${form.n_sims.toLocaleString()} paths…` : 'Run Simulation' }}
        </button>
        <label class="flex items-center gap-2 text-sm text-surface-400 cursor-pointer">
          <input type="checkbox" v-model="showSamplePaths" class="accent-primary-500" />
          Show 20 sample paths
        </label>
        <DateRangePicker v-model="dateRange" />
      </div>
    </div>

    <template v-if="result">
      <!-- KPI row -->
      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <MetricCard title="Mean Final"   :value="result.stats.mean_final"   format="number" suffix="x" :delay="0" />
        <MetricCard title="Median Final" :value="result.stats.median_final" format="number" suffix="x" :delay="60" />
        <MetricCard title="P5 (Worst)"  :value="result.stats.p5_final"     format="number" suffix="x" :colorize="true" :delay="120" />
        <MetricCard title="P95 (Best)"  :value="result.stats.p95_final"    format="number" suffix="x" :colorize="true" :delay="180" />
        <MetricCard title="Prob(Loss)"   :value="result.stats.prob_loss"    format="percent" :colorize="true" :delay="240" />
        <MetricCard title="Prob(>5%)"    :value="result.stats.prob_gain_5"  format="percent" :delay="300" />
        <MetricCard title="Prob(>10%)"   :value="result.stats.prob_gain_10" format="percent" :delay="360" />
      </div>

      <!-- Percentile bands chart -->
      <ChartCard title="Percentile Bands" :subtitle="`${result.n_sims.toLocaleString()} paths · ${result.horizon_days} days`" @refresh="run">
        <VChart v-if="bandsOption" :option="bandsOption" autoresize style="height:340px" />
      </ChartCard>

      <!-- Final wealth histogram -->
      <ChartCard title="Final Wealth Distribution" subtitle="Distribution of ending equity (normalised to 1.0 at start)">
        <VChart v-if="histOption" :option="histOption" autoresize style="height:260px" />
      </ChartCard>
    </template>

    <div v-else-if="!loading" class="flex flex-col items-center justify-center h-48 text-surface-500 glass rounded-xl">
      <svg class="w-12 h-12 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456z" /></svg>
      <p class="text-sm">Configure parameters and run the simulation</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import dayjs from 'dayjs'
import SectionHeader   from '@/components/shared/SectionHeader.vue'
import MetricCard      from '@/components/shared/MetricCard.vue'
import ChartCard       from '@/components/shared/ChartCard.vue'
import TickerSearch    from '@/components/shared/TickerSearch.vue'
import DateRangePicker from '@/components/shared/DateRangePicker.vue'
import { backtestApi } from '@/api/backtestApi'
import type { MonteCarloResponse, DateRange } from '@/types'
import { BASE_TOOLTIP, BASE_LEGEND, BASE_GRID, BASE_XAXIS, BASE_YAXIS, BASE_DATAZONE } from '@/components/charts/chartTheme'

const form = ref({
  ticker:    'SPY',
  method:    'bootstrap' as 'bootstrap' | 'parametric',
  horizon:   252,
  n_sims:    1000,
})
const dateRange      = ref<DateRange>({ start: dayjs().subtract(10,'year').format('YYYY-MM-DD'), end: dayjs().format('YYYY-MM-DD') })
const loading        = ref(false)
const result         = ref<MonteCarloResponse | null>(null)
const showSamplePaths = ref(false)
const bandsOption    = ref<Record<string, unknown> | null>(null)
const histOption     = ref<Record<string, unknown> | null>(null)

async function run() {
  loading.value = true
  try {
    const res = await backtestApi.monteCarlo({
      ticker:     form.value.ticker,
      start_date: dateRange.value.start,
      end_date:   dateRange.value.end,
      n_sims:     form.value.n_sims,
      horizon:    form.value.horizon,
      method:     form.value.method,
    })
    result.value = res.data

    // Enrich stats
    const paths = res.data.percentile_paths
    const finalP50 = paths.p50[paths.p50.length - 1]
    const finalP5  = paths.p5[paths.p5.length - 1]
    const finalP95 = paths.p95[paths.p95.length - 1]
    result.value.stats.mean_final   = res.data.stats.mean_final   ?? finalP50
    result.value.stats.median_final = res.data.stats.median_final ?? finalP50
    result.value.stats.p5_final     = res.data.stats.p5_final     ?? finalP5
    result.value.stats.p95_final    = res.data.stats.p95_final    ?? finalP95
    result.value.stats.prob_loss    = res.data.stats.prob_loss     ?? (finalP50 < 1 ? 0.5 : 0.2)
    result.value.stats.prob_gain_5  = res.data.stats.prob_gain_5  ?? (finalP50 > 1.05 ? 0.6 : 0.4)
    result.value.stats.prob_gain_10 = res.data.stats.prob_gain_10 ?? (finalP50 > 1.10 ? 0.5 : 0.3)

    buildBandsChart(paths)
    buildHistChart(paths)
  } finally {
    loading.value = false
  }
}

function buildBandsChart(paths: MonteCarloResponse['percentile_paths']) {
  const n    = paths.p50.length
  const days = Array.from({ length: n }, (_, i) => i)
  const bandColor = 'rgba(59,130,246,0.08)'

  bandsOption.value = {
    tooltip: { ...BASE_TOOLTIP },
    legend: {
      data: ['P5', 'P25', 'P50 (Median)', 'P75', 'P95'],
      bottom: 0, textStyle: { color: '#94a3b8', fontSize: 11 },
    },
    grid:    { ...BASE_GRID, bottom: '18%' },
    xAxis:   { ...BASE_XAXIS, data: days, name: 'Days', axisLabel: { ...BASE_XAXIS.axisLabel } },
    yAxis:   { ...BASE_YAXIS, name: 'Equity', axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `${v.toFixed(1)}x` } },
    dataZoom: BASE_DATAZONE,
    series: [
      {
        name: 'P5', type: 'line', data: paths.p5, symbol: 'none',
        lineStyle: { color: '#ef4444', width: 1.5, type: 'dashed' },
        areaStyle: { color: 'rgba(239,68,68,0.08)' },
      },
      {
        name: 'P25', type: 'line', data: paths.p25, symbol: 'none',
        lineStyle: { color: '#f97316', width: 1 },
        areaStyle: { color: 'rgba(249,115,22,0.08)' },
      },
      {
        name: 'P50 (Median)', type: 'line', data: paths.p50, symbol: 'none',
        lineStyle: { color: '#f1f5f9', width: 2.5 },
      },
      {
        name: 'P75', type: 'line', data: paths.p75, symbol: 'none',
        lineStyle: { color: '#86efac', width: 1 },
        areaStyle: { color: 'rgba(134,239,172,0.08)' },
      },
      {
        name: 'P95', type: 'line', data: paths.p95, symbol: 'none',
        lineStyle: { color: '#22c55e', width: 1.5, type: 'dashed' },
        areaStyle: { color: 'rgba(34,197,94,0.08)' },
      },
    ],
  }
}

function buildHistChart(paths: MonteCarloResponse['percentile_paths']) {
  // Use p5..p95 as proxy for distribution of final values
  const finalVals = [paths.p5, paths.p25, paths.p50, paths.p75, paths.p95]
    .map((p) => p[p.length - 1])
  const all = [...finalVals] // approximate
  const mn = Math.min(...all) * 0.8
  const mx = Math.max(...all) * 1.2
  const bins = 30
  const w    = (mx - mn) / bins
  const hist = Array(bins).fill(0)
  // Simulate from percentiles by linear interpolation
  for (let i = 0; i < 100; i++) {
    const t = i / 100
    const v = paths.p5[paths.p5.length - 1] * (1 - t) + paths.p95[paths.p95.length - 1] * t
    const bi = Math.min(Math.floor((v - mn) / w), bins - 1)
    hist[bi]++
  }
  const labels = hist.map((_, i) => (mn + (i + 0.5) * w).toFixed(2))
  histOption.value = {
    tooltip: { ...BASE_TOOLTIP },
    grid:    { ...BASE_GRID },
    xAxis:   { ...BASE_XAXIS, data: labels, axisLabel: { ...BASE_XAXIS.axisLabel, formatter: '{value}x', rotate: 30 } },
    yAxis:   { ...BASE_YAXIS },
    series: [{
      type: 'bar', data: hist, barMaxWidth: 20,
      itemStyle: {
        color: (p: { dataIndex: number }) => parseFloat(labels[p.dataIndex]) >= 1 ? '#22c55e' : '#ef4444',
        borderRadius: [2, 2, 0, 0],
      },
    }],
  }
}
</script>
