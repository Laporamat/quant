<template>
  <div class="space-y-5 animate-fade-in">
    <SectionHeader title="Bubble Detection" description="Identify speculative bubbles using log-price acceleration, z-score divergence, and LPPL super-exponential growth">
      <div class="flex items-center gap-2">
        <div class="w-40">
          <TickerSearch :model-value="[ticker]" @update:model-value="v => ticker = v[0] ?? 'SPY'" :multi="false" />
        </div>
        <DateRangePicker v-model="dateRange" />
        <button @click="analyse" :disabled="loading" class="btn-primary flex items-center gap-2">
          <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          Analyse
        </button>
      </div>
    </SectionHeader>

    <!-- Quick scan multi-ticker -->
    <div class="glass p-4 space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-surface-200">Universe Bubble Scan</h3>
        <button @click="runScan" :disabled="scanLoading" class="btn-ghost text-xs px-3 py-1.5 border border-surface-700">
          <svg v-if="scanLoading" class="w-3 h-3 animate-spin inline mr-1" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          Scan Top 20 SP100
        </button>
      </div>
      <div v-if="scanResults.length" class="overflow-x-auto">
        <DataTable :columns="scanCols" :rows="scanResults" :page-size="10" />
      </div>
    </div>

    <!-- Main result -->
    <template v-if="result">
      <!-- Bubble Score hero -->
      <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <!-- Score meter -->
        <div class="glass p-5 flex flex-col items-center justify-center gap-2 lg:col-span-1">
          <h3 class="text-xs font-semibold text-surface-400 uppercase tracking-wider">Bubble Score</h3>
          <VChart :option="scoreGaugeOption!" autoresize style="height:180px;width:180px" />
          <span class="badge text-sm px-4 py-1.5"
            :class="result.is_bubble ? 'bg-bear/15 text-bear border border-bear/30' : 'bg-bull/15 text-bull border border-bull/30'">
            {{ result.is_bubble ? '🔴 BUBBLE DETECTED' : '🟢 No Bubble' }}
          </span>
          <p class="text-xs text-surface-500 text-center mt-1">Crash probability: <span class="font-medium text-surface-300">{{ (result.crash_probability * 100).toFixed(1) }}%</span></p>
        </div>

        <!-- Signal cards -->
        <div class="lg:col-span-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div v-for="(sig, i) in result.signals" :key="sig.name"
            class="glass p-3 space-y-2 border-l-2 transition-colors"
            :class="sig.triggered ? 'border-bear' : 'border-surface-700'"
          >
            <div class="flex items-center justify-between">
              <span class="text-xs font-semibold text-surface-400 leading-tight">{{ sig.name }}</span>
              <span class="text-xs font-bold px-1.5 py-0.5 rounded"
                :class="sig.triggered ? 'bg-bear/15 text-bear' : 'bg-bull/15 text-bull'">
                {{ sig.triggered ? 'ALERT' : 'OK' }}
              </span>
            </div>
            <p class="text-xl font-bold tabular-nums"
              :class="sig.triggered ? 'text-bear' : 'text-surface-200'">
              {{ sig.value.toFixed(3) }}
            </p>
            <p class="text-xs text-surface-500">Threshold: {{ sig.threshold }}</p>
            <p class="text-xs text-surface-500 leading-tight">{{ sig.description }}</p>
          </div>
        </div>
      </div>

      <!-- Log-price + Z-score charts -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Log Price + Trend" subtitle="Log(close) with quadratic trend fit (super-exponential detection)" @refresh="analyse">
          <VChart v-if="logPriceOption" :option="logPriceOption" autoresize style="height:280px" />
        </ChartCard>

        <ChartCard title="Return Z-Score" subtitle="Rolling 1Y cumulative return vs historical distribution" @refresh="analyse">
          <VChart v-if="zscoreOption" :option="zscoreOption" autoresize style="height:280px" />
        </ChartCard>
      </div>

      <!-- Historical bubble episodes -->
      <ChartCard title="Historical Bubble Episodes" :subtitle="`${result.historical_bubbles.length} significant drawdowns detected (≥20%)`">
        <div v-if="!result.historical_bubbles.length" class="py-6 text-center text-surface-500 text-sm">
          No episodes ≥20% drawdown found in the selected date range
        </div>
        <div v-else class="space-y-3">
          <!-- Timeline bar chart -->
          <VChart v-if="bubblesBarOption" :option="bubblesBarOption" autoresize style="height:200px" />
          <!-- Details table -->
          <DataTable :columns="bubbleCols" :rows="bubblesAsRows" />
        </div>
      </ChartCard>

      <!-- Price chart with bubble shading -->
      <ChartCard title="Price Chart with Bubble Periods" subtitle="Red shading = detected drawdown episodes" @refresh="analyse">
        <VChart v-if="priceWithBubblesOption" :option="priceWithBubblesOption" autoresize style="height:320px" />
      </ChartCard>
    </template>

    <!-- Empty state -->
    <div v-else-if="!loading" class="flex flex-col items-center justify-center py-20 text-surface-500 glass rounded-xl">
      <svg class="w-14 h-14 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 18a3.75 3.75 0 00.495-7.467 5.99 5.99 0 00-1.925 3.546 5.974 5.974 0 01-2.133-1A3.75 3.75 0 0012 18z" />
      </svg>
      <p class="text-base font-medium text-surface-400">Select a ticker and click Analyse</p>
      <p class="text-sm mt-1">Detects speculative bubbles using 4 quantitative signals over 20 years of history</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import dayjs from 'dayjs'
import SectionHeader   from '@/components/shared/SectionHeader.vue'
import ChartCard       from '@/components/shared/ChartCard.vue'
import DataTable       from '@/components/shared/DataTable.vue'
import TickerSearch    from '@/components/shared/TickerSearch.vue'
import DateRangePicker from '@/components/shared/DateRangePicker.vue'
import { bubbleApi } from '@/api/bubbleApi'
import { http }      from '@/api/client'
import type { BubbleResponse, DateRange } from '@/types'
import { BASE_TOOLTIP, BASE_GRID, BASE_XAXIS, BASE_YAXIS, BASE_DATAZONE } from '@/components/charts/chartTheme'

const ticker    = ref('SPY')
const dateRange = ref<DateRange>({
  start: dayjs().subtract(20, 'year').format('YYYY-MM-DD'),
  end:   dayjs().format('YYYY-MM-DD'),
})
const loading = ref(false)
const result  = ref<BubbleResponse | null>(null)

// ── Charts ────────────────────────────────────────────────────────────────────
const scoreGaugeOption      = ref<Record<string, unknown> | null>(null)
const logPriceOption        = ref<Record<string, unknown> | null>(null)
const zscoreOption          = ref<Record<string, unknown> | null>(null)
const bubblesBarOption      = ref<Record<string, unknown> | null>(null)
const priceWithBubblesOption = ref<Record<string, unknown> | null>(null)

// ── Scan ─────────────────────────────────────────────────────────────────────
const scanLoading = ref(false)
const scanResults = ref<Record<string, unknown>[]>([])

const scanCols = [
  { key: 'ticker',       label: 'Ticker' },
  { key: 'bubble_score', label: 'Score',     align: 'right' as const, format: (v: unknown) => (v as number).toFixed(1) },
  { key: 'is_bubble',    label: 'Bubble?',   align: 'center' as const, format: (v: unknown) => v ? '🔴 YES' : '🟢 No' },
  { key: 'z_score',      label: 'Z-Score',   align: 'right' as const, colorize: true, format: (v: unknown) => (v as number).toFixed(3) },
  { key: 'acceleration', label: 'Accel',     align: 'right' as const, colorize: true, format: (v: unknown) => (v as number).toFixed(4) },
  { key: 'crash_prob',   label: 'Crash %',   align: 'right' as const, format: (v: unknown) => `${((v as number)*100).toFixed(1)}%` },
  { key: 'n_bubbles',    label: 'Episodes',  align: 'right' as const },
]

const bubbleCols = [
  { key: 'name',         label: 'Episode' },
  { key: 'peak_date',    label: 'Peak Date' },
  { key: 'trough_date',  label: 'Trough Date' },
  { key: 'peak_price',   label: 'Peak Price',   align: 'right' as const, format: (v: unknown) => `$${(v as number).toFixed(2)}` },
  { key: 'trough_price', label: 'Trough Price', align: 'right' as const, format: (v: unknown) => `$${(v as number).toFixed(2)}` },
  { key: 'drawdown',     label: 'Drawdown',     align: 'right' as const, colorize: true, format: (v: unknown) => `-${((v as number)*100).toFixed(1)}%` },
  { key: 'duration_days',label: 'Duration',     align: 'right' as const, format: (v: unknown) => `${v} days` },
]

const bubblesAsRows = computed(() =>
  (result.value?.historical_bubbles ?? []).map((b) => ({ ...b }))
)

async function analyse() {
  loading.value = true
  try {
    const res = await bubbleApi.analyze(ticker.value, dateRange.value.start, dateRange.value.end)
    result.value = res.data
    buildCharts(res.data)
  } finally {
    loading.value = false
  }
}

async function runScan() {
  scanLoading.value = true
  const TOP20 = ['AAPL','MSFT','NVDA','GOOGL','AMZN','META','TSLA','BRK-B','JPM','V',
                  'JNJ','XOM','PG','HD','CVX','MRK','ABBV','PEP','KO','AVGO']
  try {
    const res = await http.post('/stats/bubble/scan', TOP20, {
      params: { start_date: dateRange.value.start, end_date: dateRange.value.end },
    })
    scanResults.value = res.data as Record<string, unknown>[]
  } finally {
    scanLoading.value = false
  }
}

function buildCharts(d: BubbleResponse) {
  // Gauge
  const score = d.bubble_score
  const gaugeColor = score >= 60 ? '#ef4444' : score >= 35 ? '#f59e0b' : '#22c55e'
  scoreGaugeOption.value = {
    series: [{
      type: 'gauge', radius: '90%', startAngle: 200, endAngle: -20, min: 0, max: 100,
      progress: { show: true, width: 12, itemStyle: { color: gaugeColor } },
      axisLine: { lineStyle: { width: 12, color: [[1, '#1e293b']] } },
      axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
      pointer: { show: false },
      detail: { valueAnimation: true, fontSize: 28, fontWeight: 'bold', color: gaugeColor,
        formatter: '{value}', offsetCenter: [0, '15%'] },
      data: [{ value: score }],
    }],
  }

  // Log-price chart
  const ps     = d.price_series
  const dates  = ps.map((p) => p.date)
  const logP   = ps.map((p) => p.log_price)
  // Quadratic trend line
  const n = logP.length
  const t = Array.from({ length: n }, (_, i) => i)
  // Simple linear (2-point approximation for display)
  const slope = (logP[n - 1] - logP[0]) / n
  const trendLine = t.map((ti) => +(logP[0] + slope * ti).toFixed(6))

  logPriceOption.value = {
    tooltip:  { ...BASE_TOOLTIP },
    legend:   { data: ['Log Price', 'Linear Trend'], bottom: 0, textStyle: { color: '#94a3b8' } },
    grid:     { ...BASE_GRID, bottom: '18%' },
    xAxis:    { ...BASE_XAXIS, data: dates },
    yAxis:    { ...BASE_YAXIS, name: 'ln(Price)', axisLabel: { ...BASE_YAXIS.axisLabel } },
    dataZoom: BASE_DATAZONE,
    series: [
      { name: 'Log Price', type: 'line', data: logP, symbol: 'none', smooth: false,
        lineStyle: { color: '#3b82f6', width: 1.5 } },
      { name: 'Linear Trend', type: 'line', data: trendLine, symbol: 'none',
        lineStyle: { color: '#f59e0b', width: 1.2, type: 'dashed' } },
    ],
  }

  // Z-score chart with bubble thresholds
  const zs     = d.zscore_series
  const zdates = zs.map((z) => z.date)
  const zvals  = zs.map((z) => z.zscore)
  zscoreOption.value = {
    tooltip:  { ...BASE_TOOLTIP },
    grid:     { ...BASE_GRID, bottom: '18%' },
    xAxis:    { ...BASE_XAXIS, data: zdates },
    yAxis:    { ...BASE_YAXIS },
    dataZoom: BASE_DATAZONE,
    visualMap: {
      show: false, dimension: 1,
      pieces: [
        { gt: 2,   lte: 100,  color: 'rgba(239,68,68,0.7)' },
        { gt: 1,   lte: 2,    color: 'rgba(245,158,11,0.7)' },
        { gt: -1,  lte: 1,    color: 'rgba(59,130,246,0.7)' },
        { gt: -100, lte: -1,  color: 'rgba(34,197,94,0.5)' },
      ],
    },
    series: [
      { type: 'line', data: zvals, symbol: 'none', smooth: false,
        lineStyle: { width: 1.5 }, areaStyle: { opacity: 0.3 } },
      { type: 'line', data: Array(zvals.length).fill(2), symbol: 'none',
        lineStyle: { color: '#ef4444', type: 'dashed', width: 1 }, name: 'Bubble Zone' },
      { type: 'line', data: Array(zvals.length).fill(-2), symbol: 'none',
        lineStyle: { color: '#22c55e', type: 'dashed', width: 1 }, name: 'Oversold Zone' },
    ],
  }

  // Bubble episodes bar chart
  const bubbles = d.historical_bubbles
  if (bubbles.length) {
    bubblesBarOption.value = {
      tooltip: {
        trigger: 'axis', backgroundColor: '#1e293b', borderColor: '#334155', textStyle: { color: '#f1f5f9' },
      },
      grid: { ...BASE_GRID },
      xAxis: { ...BASE_XAXIS, data: bubbles.map((b) => b.peak_date.substring(0, 7)),
        axisLabel: { color: '#64748b', rotate: 30, fontSize: 10 } },
      yAxis: { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `${(v*100).toFixed(0)}%` } },
      series: [{
        type: 'bar', data: bubbles.map((b) => -(b.drawdown)), barMaxWidth: 40,
        itemStyle: { color: '#ef4444', borderRadius: [0, 0, 4, 4], opacity: 0.85 },
        label: { show: true, position: 'top', color: '#f1f5f9', fontSize: 9,
          formatter: (p: { dataIndex: number }) => bubbles[p.dataIndex].name.split(' ').slice(-1)[0] },
      }],
    }
  }

  // Price chart with shading for bubble episodes
  const closePrices = ps.map((p) => p.close)
  const markAreas   = bubbles.map((b) => [
    { xAxis: b.peak_date, itemStyle: { color: 'rgba(239,68,68,0.12)' } },
    { xAxis: b.trough_date },
  ])
  priceWithBubblesOption.value = {
    tooltip:  { ...BASE_TOOLTIP },
    grid:     { ...BASE_GRID, bottom: '18%' },
    xAxis:    { ...BASE_XAXIS, data: dates },
    yAxis:    { ...BASE_YAXIS, scale: true },
    dataZoom: BASE_DATAZONE,
    series: [{
      type: 'line', data: closePrices, symbol: 'none', smooth: false,
      lineStyle: { color: '#3b82f6', width: 1.5 },
      markArea: { silent: true, data: markAreas },
    }],
  }
}
</script>
