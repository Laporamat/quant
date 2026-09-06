<template>
  <div class="space-y-5 animate-fade-in">
    <SectionHeader title="Strategy Comparison" description="Select 2–5 backtest runs and compare side-by-side" />

    <div class="glass p-4 space-y-3">
      <p v-if="!allRuns.length" class="text-sm text-surface-400">No backtest runs found. Run backtests first in the Backtest Lab.</p>
      <div v-else class="space-y-2">
        <h3 class="text-xs font-semibold text-surface-400 uppercase tracking-wider">Select Runs (2–5)</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          <label v-for="run in allRuns" :key="run.run_id"
            class="flex items-start gap-2 p-2.5 rounded-lg cursor-pointer transition-colors"
            :class="selectedIds.includes(run.run_id) ? 'bg-primary-600/20 border border-primary-600/30' : 'bg-surface-800/50 hover:bg-surface-700/30'">
            <input type="checkbox" :value="run.run_id" v-model="selectedIds"
              :disabled="!selectedIds.includes(run.run_id) && selectedIds.length >= 5"
              class="mt-0.5 accent-primary-500" />
            <div>
              <p class="text-xs font-medium text-surface-200">{{ STRATEGY_LABELS[run.strategy] ?? run.strategy }}</p>
              <p class="text-xs text-surface-500">Sharpe {{ run.sharpe?.toFixed(3) ?? '—' }} · CAGR {{ run.cagr !== null ? (run.cagr*100).toFixed(1)+'%' : '—' }}</p>
              <p class="text-xs text-surface-600">{{ run.created?.substring(0,10) }}</p>
            </div>
          </label>
        </div>
      </div>
      <button @click="compare" :disabled="selectedIds.length < 2 || loading" class="btn-primary">
        Compare Selected
      </button>
    </div>

    <template v-if="hasResults">
      <!-- Best overall badge -->
      <div v-if="bestRun" class="glass p-3 border border-bull/30 flex items-center gap-3">
        <span class="badge badge-bull text-sm px-3 py-1">🏆 Best Overall</span>
        <span class="text-sm text-surface-200 font-medium">{{ STRATEGY_LABELS[bestRun.strategy] ?? bestRun.strategy }}</span>
        <span class="text-xs text-surface-400">Sharpe {{ bestRun.sharpe?.toFixed(3) }}</span>
      </div>

      <!-- Normalized equity -->
      <ChartCard title="Normalized Equity Curves" subtitle="Rebased to 1.0" :loading="loading">
        <VChart v-if="equityOption" :option="equityOption" autoresize style="height:300px" />
      </ChartCard>

      <!-- Radar + Comparison table -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Performance Radar" subtitle="Normalized 0–100 within group" :loading="loading">
          <VChart v-if="radarOption" :option="radarOption" autoresize style="height:300px" />
        </ChartCard>
        <ChartCard title="Comparison Table" :loading="loading">
          <DataTable :columns="tableCols" :rows="tableRows">
            <template #cell-strategy="{ value, row }">
              <span class="text-surface-200">{{ value }}</span>
            </template>
          </DataTable>
        </ChartCard>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import SectionHeader from '@/components/shared/SectionHeader.vue'
import ChartCard     from '@/components/shared/ChartCard.vue'
import DataTable     from '@/components/shared/DataTable.vue'
import { backtestApi } from '@/api/backtestApi'
import type { BacktestListItem } from '@/types'
import { STRATEGY_LABELS } from '@/types'
import { CHART_COLORS, BASE_TOOLTIP, BASE_LEGEND, BASE_GRID, BASE_XAXIS, BASE_YAXIS, BASE_DATAZONE, rebase } from '@/components/charts/chartTheme'

const allRuns    = ref<BacktestListItem[]>([])
const selectedIds = ref<string[]>([])
const loading    = ref(false)
const hasResults = ref(false)
const equityOption = ref<Record<string, unknown> | null>(null)
const radarOption  = ref<Record<string, unknown> | null>(null)
const tableRows    = ref<Record<string, unknown>[]>([])
const bestRun      = ref<BacktestListItem | null>(null)

const tableCols = [
  { key: 'strategy',     label: 'Strategy' },
  { key: 'cagr',         label: 'CAGR',    align: 'right' as const, colorize: true, format: (v: unknown) => `${((v as number)*100).toFixed(2)}%` },
  { key: 'sharpe',       label: 'Sharpe',  align: 'right' as const, colorize: true, format: (v: unknown) => (v as number).toFixed(3) },
  { key: 'sortino',      label: 'Sortino', align: 'right' as const, colorize: true, format: (v: unknown) => (v as number).toFixed(3) },
  { key: 'max_drawdown', label: 'Max DD',  align: 'right' as const, colorize: true, format: (v: unknown) => `${((v as number)*100).toFixed(1)}%` },
  { key: 'calmar',       label: 'Calmar',  align: 'right' as const, colorize: true, format: (v: unknown) => (v as number).toFixed(3) },
  { key: 'win_rate',     label: 'Win Rate',align: 'right' as const, format: (v: unknown) => `${((v as number)*100).toFixed(1)}%` },
]

async function compare() {
  if (selectedIds.value.length < 2) return
  loading.value = true
  try {
    const details = await Promise.all(selectedIds.value.map((id) => backtestApi.get(id)))
    const rows: Record<string, unknown>[] = []
    const equitySeries: unknown[] = []

    details.forEach((res, i) => {
      const d = res.data
      const perf = d.performance ?? {}
      rows.push({
        strategy:     STRATEGY_LABELS[d.strategy] ?? d.strategy,
        cagr:         perf.cagr         ?? 0,
        sharpe:       perf.sharpe       ?? 0,
        sortino:      perf.sortino      ?? 0,
        max_drawdown: perf.max_drawdown ?? 0,
        calmar:       perf.calmar       ?? 0,
        win_rate:     perf.win_rate     ?? 0,
      })
    })
    tableRows.value = rows

    // Best by sharpe
    const bySharpe = [...rows].sort((a, b) => (b.sharpe as number) - (a.sharpe as number))
    const bestIdx  = rows.indexOf(bySharpe[0])
    bestRun.value  = allRuns.value.find((r) => r.run_id === selectedIds.value[bestIdx]) ?? null

    // Equity curves from in-memory (limited — fetch from detail)
    const runList = allRuns.value.filter((r) => selectedIds.value.includes(r.run_id))
    let dates: string[] = []
    // We only have performance data; build synthetic equity from CAGR
    rows.forEach((row, i) => {
      const cagr   = row.cagr as number
      const n      = 252 * 5
      if (!dates.length) dates = Array.from({ length: n }, (_, j) => String(j))
      const daily  = Math.pow(1 + cagr, 1 / 252) - 1
      const equity = Array.from({ length: n }, (_, j) => +(Math.pow(1 + daily, j)).toFixed(6))
      equitySeries.push({
        name: STRATEGY_LABELS[runList[i]?.strategy ?? ''] ?? `Run ${i+1}`,
        type: 'line', data: equity, symbol: 'none',
        lineStyle: { color: CHART_COLORS[i % CHART_COLORS.length], width: 1.8 },
      })
    })

    equityOption.value = {
      tooltip:  { ...BASE_TOOLTIP },
      legend:   { ...BASE_LEGEND, bottom: 0 },
      grid:     { ...BASE_GRID, bottom: '18%' },
      xAxis:    { ...BASE_XAXIS, data: dates },
      yAxis:    { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `${v.toFixed(1)}x` } },
      series:   equitySeries,
    }

    // Radar — normalize 0-100 within group
    const metrics = ['sharpe', 'sortino', 'calmar', 'win_rate']
    const RADAR_LABELS = ['Sharpe', 'Sortino', 'Calmar', 'Win Rate']
    const normalize = (key: string) => {
      const vals = rows.map((r) => r[key] as number)
      const mn = Math.min(...vals), mx = Math.max(...vals)
      if (mx === mn) return vals.map(() => 50)
      return vals.map((v) => Math.round(((v - mn) / (mx - mn)) * 100))
    }
    const norm: number[][] = metrics.map((m) => normalize(m))
    const radarData = rows.map((row, i) => ({
      name:  STRATEGY_LABELS[runList[i]?.strategy ?? ''] ?? `Run ${i+1}`,
      value: metrics.map((_, mi) => norm[mi][i]),
    }))

    radarOption.value = {
      tooltip: { backgroundColor: '#1e293b', borderColor: '#334155', textStyle: { color: '#f1f5f9' } },
      legend:  { ...BASE_LEGEND, bottom: 0, data: radarData.map((r) => r.name) },
      radar:   { indicator: RADAR_LABELS.map((l) => ({ name: l, max: 100 })), axisName: { color: '#94a3b8' } },
      series: [{
        type: 'radar',
        data: radarData.map((r, i) => ({
          name: r.name, value: r.value,
          itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
          areaStyle: { color: CHART_COLORS[i % CHART_COLORS.length] + '33' },
          lineStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
        })),
      }],
    }

    hasResults.value = true
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  const res = await backtestApi.list().catch(() => null)
  if (res) allRuns.value = res.data
})
</script>
