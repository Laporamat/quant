<template>
  <div class="space-y-6 animate-fade-in">

    <!-- ── No-data banner ──────────────────────────────────────────────────── -->
    <div v-if="noData" class="glass border border-primary-500/30 rounded-xl p-6">
      <div class="flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <div class="w-12 h-12 rounded-xl bg-primary-600/20 flex items-center justify-center shrink-0">
          <svg class="w-6 h-6 text-primary-400" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-base font-semibold text-surface-100">ยังไม่มีข้อมูลในเครื่อง</h3>
          <p class="text-sm text-surface-400 mt-0.5">
            ต้องดาวน์โหลด historical data จาก Yahoo Finance ก่อน (ฟรี ไม่ต้อง API key)
            — Benchmarks + Sector ETFs + Top 20 SP100 รวม ~37 tickers
          </p>

          <!-- Progress bar -->
          <div v-if="dlStatus.running || dlStatus.done > 0" class="mt-3 space-y-1.5">
            <div class="flex justify-between text-xs text-surface-400">
              <span>{{ dlStatus.running ? 'กำลังดาวน์โหลด…' : 'เสร็จแล้ว' }}
                {{ dlStatus.done }}/{{ dlStatus.total }} tickers</span>
              <span>{{ dlStatus.pct }}%</span>
            </div>
            <div class="h-2 bg-surface-700 rounded-full overflow-hidden">
              <div class="h-full bg-primary-500 rounded-full transition-all duration-500"
                :style="{ width: dlStatus.pct + '%' }" />
            </div>
            <p v-if="!dlStatus.running && dlStatus.done > 0" class="text-xs text-bull">
              ✓ โหลดข้อมูลเสร็จแล้ว — กำลังโหลด charts…
            </p>
          </div>
        </div>

        <button
          @click="startQuickstart"
          :disabled="dlStatus.running"
          class="btn-primary shrink-0 flex items-center gap-2 whitespace-nowrap"
        >
          <svg v-if="dlStatus.running" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          {{ dlStatus.running ? 'กำลังโหลด…' : 'Download Data ตอนนี้เลย' }}
        </button>
      </div>
    </div>
    <!-- Header -->
    <SectionHeader title="Market Dashboard" description="20-year historical overview — SP100 · SET50 · Benchmarks">
      <!-- Universe switcher -->
      <div class="flex items-center gap-1 bg-surface-800 rounded-lg p-1">
        <button
          v-for="u in universes" :key="u.key"
          @click="setUniverse(u.key)"
          class="px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-150"
          :class="activeUniverse === u.key
            ? 'bg-primary-600 text-white shadow'
            : 'text-surface-400 hover:text-white'"
        >{{ u.label }}</button>
      </div>
    </SectionHeader>

    <!-- Benchmark KPI row -->
    <div>
      <h3 class="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">Benchmark Performance</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          v-for="(bm, i) in benchmarks" :key="bm.ticker"
          :title="bm.ticker"
          :value="bm.cagr"
          format="percent"
          :delta="bm.cagr !== null ? bm.cagr * 100 : undefined"
          delta-label="CAGR"
          :subtitle="bm.total !== null ? `Total: ${(bm.total * 100).toFixed(0)}%` : 'Loading…'"
          :colorize="true"
          :delay="i * 60"
        />
      </div>
    </div>

    <!-- Movers + Sector row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Top Gainers -->
      <ChartCard title="Top Gainers" subtitle="Best 1-year return in universe" :loading="moversLoading" :empty="!gainers.length" :hide-refresh="false" @refresh="loadMovers">
        <DataTable :columns="moverCols" :rows="gainers" :page-size="8" />
      </ChartCard>

      <!-- Top Losers -->
      <ChartCard title="Top Losers" subtitle="Worst 1-year return in universe" :loading="moversLoading" :empty="!losers.length" @refresh="loadMovers">
        <DataTable :columns="moverCols" :rows="losers" :page-size="8" />
      </ChartCard>

      <!-- Sector Performance -->
      <ChartCard title="Sector Performance" subtitle="SPDR sector ETFs — 1-year return" :loading="sectorLoading" :empty="!sectorOption" @refresh="loadSectors">
        <VChart v-if="sectorOption" :option="sectorOption" autoresize style="height:260px" />
      </ChartCard>
    </div>

    <!-- Market Breadth + Regime -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Market Breadth Gauges -->
      <ChartCard title="Market Breadth" subtitle="% of SP100 above moving averages" :loading="breadthLoading" @refresh="loadBreadth">
        <div class="flex justify-around">
          <div class="text-center">
            <VChart v-if="gauge50" :option="gauge50" autoresize style="height:180px;width:180px" />
            <p class="text-xs text-surface-400 -mt-2">Above SMA 50</p>
          </div>
          <div class="text-center">
            <VChart v-if="gauge200" :option="gauge200" autoresize style="height:180px;width:180px" />
            <p class="text-xs text-surface-400 -mt-2">Above SMA 200</p>
          </div>
        </div>
      </ChartCard>

      <!-- Recent Benchmark equity curves -->
      <ChartCard title="Benchmark Equity Curves" subtitle="Normalized to 1.0 — 5 years" :loading="equityLoading" @refresh="loadEquityCurves">
        <VChart v-if="equityOption" :option="equityOption" autoresize style="height:200px" />
      </ChartCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import dayjs from 'dayjs'
import SectionHeader from '@/components/shared/SectionHeader.vue'
import MetricCard    from '@/components/shared/MetricCard.vue'
import ChartCard     from '@/components/shared/ChartCard.vue'
import DataTable     from '@/components/shared/DataTable.vue'
import { statsApi }  from '@/api/statsApi'
import { dataApi }   from '@/api/dataApi'
import { indicatorsApi } from '@/api/indicatorsApi'
import { http }          from '@/api/client'
import { useMarketStore } from '@/stores/marketStore'
import {
  CHART_COLORS, BASE_TOOLTIP, BASE_LEGEND, BASE_GRID,
  BASE_XAXIS, BASE_YAXIS, BASE_DATAZONE, rebase,
} from '@/components/charts/chartTheme'

const marketStore = useMarketStore()
const activeUniverse = computed(() => marketStore.activeUniverse)

// ── No-data detection + quickstart download ──────────────────────────────────
const noData = ref(false)
const dlStatus = ref({ running: false, done: 0, total: 37, pct: 0, errors: [] as string[] })
let pollTimer: ReturnType<typeof setInterval> | null = null

async function checkDataAvailable() {
  try {
    const res = await http.get('/data/available')
    noData.value = (res.data as unknown[]).length === 0
  } catch {
    noData.value = true
  }
}

async function startQuickstart() {
  try {
    await http.post('/data/quickstart')
    dlStatus.value.running = true
    // Poll status every 3 s
    pollTimer = setInterval(async () => {
      try {
        const res = await http.get('/data/quickstart/status')
        dlStatus.value = res.data as typeof dlStatus.value
        if (!dlStatus.value.running && dlStatus.value.done > 0) {
          clearInterval(pollTimer!)
          pollTimer = null
          noData.value = false
          loadAll()          // reload charts now that data exists
        }
      } catch { /* ignore */ }
    }, 3000)
  } catch { /* toast handled by interceptor */ }
}

onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })

const universes = [
  { key: 'sp100'     as const, label: 'SP100'     },
  { key: 'set50'     as const, label: 'SET50'     },
  { key: 'benchmark' as const, label: 'Benchmark' },
]

function setUniverse(k: 'sp100' | 'set50' | 'benchmark') {
  marketStore.setUniverse(k)
  loadAll()
}

// ── Benchmarks ────────────────────────────────────────────────────────────────
const BENCH = ['SPY', 'QQQ', 'IWM', 'GLD', 'TLT', 'VTI']
const benchmarks = ref<{ ticker: string; cagr: number | null; total: number | null }[]>(
  BENCH.map((t) => ({ ticker: t, cagr: null, total: null }))
)

async function loadBenchmarks() {
  const results = await Promise.allSettled(BENCH.map((t) => statsApi.returns(t)))
  results.forEach((r, i) => {
    if (r.status === 'fulfilled') {
      benchmarks.value[i].cagr  = r.value.data.cagr
      benchmarks.value[i].total = r.value.data.total_return
    }
  })
}

// ── Movers ────────────────────────────────────────────────────────────────────
const moversLoading = ref(false)
const gainers = ref<Record<string, unknown>[]>([])
const losers  = ref<Record<string, unknown>[]>([])

const moverCols = [
  { key: 'ticker', label: 'Ticker', sortable: false },
  { key: 'cagr',   label: 'CAGR',   align: 'right' as const, colorize: true,
    format: (v: unknown) => `${((v as number) * 100).toFixed(1)}%` },
  { key: 'total',  label: 'Total',  align: 'right' as const, colorize: true,
    format: (v: unknown) => `${((v as number) * 100).toFixed(0)}%` },
]

async function loadMovers() {
  moversLoading.value = true
  try {
    const tickers = marketStore.currentTickers.slice(0, 30)
    if (!tickers.length) return
    const results = await Promise.allSettled(
      tickers.map((t) => statsApi.returns(t))
    )
    const rows = results
      .map((r, i) => r.status === 'fulfilled'
        ? { ticker: tickers[i], cagr: r.value.data.cagr, total: r.value.data.total_return }
        : null)
      .filter(Boolean) as Record<string, unknown>[]

    rows.sort((a, b) => (b.cagr as number) - (a.cagr as number))
    gainers.value = rows.slice(0, 10)
    losers.value  = [...rows].sort((a, b) => (a.cagr as number) - (b.cagr as number)).slice(0, 10)
  } finally {
    moversLoading.value = false
  }
}

// ── Sector ────────────────────────────────────────────────────────────────────
const sectorLoading = ref(false)
const sectorOption  = ref<Record<string, unknown> | null>(null)
const SECTOR_ETFS = ['XLK','XLV','XLF','XLE','XLY','XLP','XLI','XLB','XLU','XLRE','XLC']
const SECTOR_NAMES = ['Tech','Health','Finance','Energy','ConsDisc','ConsStaples','Industrials','Materials','Utilities','RealEstate','Comm']

async function loadSectors() {
  sectorLoading.value = true
  try {
    const results = await Promise.allSettled(SECTOR_ETFS.map((t) => statsApi.returns(t)))
    const values = results.map((r) =>
      r.status === 'fulfilled' ? +(r.value.data.cagr * 100).toFixed(2) : 0
    )
    sectorOption.value = {
      tooltip: { ...BASE_TOOLTIP, trigger: 'axis' },
      grid:    { ...BASE_GRID, bottom: '18%' },
      xAxis:   { ...BASE_XAXIS, data: SECTOR_NAMES, axisLabel: { ...BASE_XAXIS.axisLabel, rotate: 30 } },
      yAxis:   { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: '{value}%' } },
      series:  [{
        type: 'bar', data: values, barMaxWidth: 36,
        itemStyle: {
          color: (p: { value: number }) => p.value >= 0 ? '#22c55e' : '#ef4444',
          borderRadius: [4, 4, 0, 0],
        },
      }],
    }
  } finally {
    sectorLoading.value = false
  }
}

// ── Market Breadth ─────────────────────────────────────────────────────────────
const breadthLoading = ref(false)
const gauge50  = ref<Record<string, unknown> | null>(null)
const gauge200 = ref<Record<string, unknown> | null>(null)

function makeGauge(pct: number, color: string) {
  return {
    series: [{
      type: 'gauge',
      radius: '90%',
      startAngle: 200, endAngle: -20,
      min: 0, max: 100,
      progress: { show: true, width: 12, itemStyle: { color } },
      axisLine: { lineStyle: { width: 12, color: [[1, '#1e293b']] } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      pointer: { show: false },
      detail: { valueAnimation: true, fontSize: 22, fontWeight: 'bold', color: '#f1f5f9', formatter: '{value}%', offsetCenter: [0, '10%'] },
      data: [{ value: pct }],
    }],
  }
}

async function loadBreadth() {
  breadthLoading.value = true
  try {
    const tickers = ['AAPL','MSFT','GOOGL','AMZN','NVDA','META','TSLA','JPM','V','PG',
                     'HD','CVX','MRK','ABBV','PEP','KO','AVGO','COST','TMO','WMT'].slice(0, 20)
    const end   = dayjs().format('YYYY-MM-DD')
    const start = dayjs().subtract(1, 'year').format('YYYY-MM-DD')
    const results = await Promise.allSettled(
      tickers.map((t) => indicatorsApi.ma(t, '50,200', 'sma', start, end))
    )
    let above50 = 0, above200 = 0, counted = 0
    results.forEach((r) => {
      if (r.status !== 'fulfilled') return
      const d = r.value.data as Record<string, number[]>
      const price = d['close'] ?? d['sma_50'] ?? []
      const s50   = d['sma_50']  ?? []
      const s200  = d['sma_200'] ?? []
      if (!price.length) return
      counted++
      const last = price.length - 1
      if (s50.length  && price[last] > s50[last])  above50++
      if (s200.length && price[last] > s200[last]) above200++
    })
    const p50  = counted ? Math.round((above50  / counted) * 100) : 50
    const p200 = counted ? Math.round((above200 / counted) * 100) : 50
    const col50  = p50  > 60 ? '#22c55e' : p50  < 40 ? '#ef4444' : '#f59e0b'
    const col200 = p200 > 60 ? '#22c55e' : p200 < 40 ? '#ef4444' : '#f59e0b'
    gauge50.value  = makeGauge(p50,  col50)
    gauge200.value = makeGauge(p200, col200)
  } finally {
    breadthLoading.value = false
  }
}

// ── Equity Curves ─────────────────────────────────────────────────────────────
const equityLoading = ref(false)
const equityOption  = ref<Record<string, unknown> | null>(null)

async function loadEquityCurves() {
  equityLoading.value = true
  try {
    const TICKERS = ['SPY','QQQ','GLD','TLT','IWM']
    const start   = dayjs().subtract(5, 'year').format('YYYY-MM-DD')
    const end     = dayjs().format('YYYY-MM-DD')
    const results = await Promise.allSettled(
      TICKERS.map((t) => dataApi.prices(t, start, end))
    )
    let dates: string[] = []
    const series = results.map((r, i) => {
      if (r.status !== 'fulfilled') return null
      const bars = r.value.data.data
      if (!dates.length) dates = bars.map((b) => b.date)
      const prices  = bars.map((b) => b.close)
      const rebased = rebase(prices)
      return {
        name: TICKERS[i], type: 'line',
        data: rebased, smooth: false, symbol: 'none',
        lineStyle: { width: 1.5, color: CHART_COLORS[i] },
        emphasis: { lineStyle: { width: 2.5 } },
      }
    }).filter(Boolean)

    equityOption.value = {
      tooltip:  { ...BASE_TOOLTIP },
      legend:   { ...BASE_LEGEND, bottom: 0 },
      grid:     { ...BASE_GRID, bottom: '22%' },
      xAxis:    { ...BASE_XAXIS, data: dates },
      yAxis:    { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `${v.toFixed(1)}x` } },
      dataZoom: BASE_DATAZONE,
      series,
    }
  } finally {
    equityLoading.value = false
  }
}

function loadAll() {
  loadBenchmarks()
  loadMovers()
  loadSectors()
  loadBreadth()
  loadEquityCurves()
}

onMounted(() => {
  marketStore.loadUniverse('sp100')
  checkDataAvailable().then(() => {
    if (!noData.value) loadAll()
  })
})
</script>
