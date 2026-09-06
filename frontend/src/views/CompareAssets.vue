<template>
  <div class="space-y-5 animate-fade-in">
    <SectionHeader title="Multi-Asset Comparison" description="Compare up to 10 assets — normalized equity, correlation, risk-return scatter">
      <button @click="runCompare" :disabled="selected.length < 2 || loading" class="btn-primary flex items-center gap-2">
        <svg v-if="loading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
        Compare
      </button>
    </SectionHeader>

    <!-- Controls -->
    <div class="glass p-4 space-y-3">
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex-1 min-w-[220px]">
          <label class="text-xs text-surface-400 mb-1 block">Tickers (2–10)</label>
          <TickerSearch v-model="selected" :multi="true" />
        </div>
        <div>
          <label class="text-xs text-surface-400 mb-1 block">Date Range</label>
          <DateRangePicker v-model="dateRange" />
        </div>
      </div>
      <!-- Quick sets -->
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-xs text-surface-500">Quick Sets:</span>
        <button
          v-for="(tickers, name) in QUICK_SETS" :key="name"
          @click="selected = [...tickers]"
          class="px-2.5 py-1 text-xs bg-surface-700/50 hover:bg-primary-600/20 text-surface-300 hover:text-primary-300 rounded-md transition-all"
        >{{ name }}</button>
      </div>
    </div>

    <template v-if="hasResults">
      <!-- Normalized equity -->
      <ChartCard title="Normalized Equity Curves" subtitle="Rebased to 1.0 at start" :loading="loading" @refresh="runCompare">
        <VChart v-if="equityOption" :option="equityOption" autoresize style="height:300px" />
      </ChartCard>

      <!-- Correlation + Risk-Return -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Correlation Matrix" subtitle="Pearson — daily returns" :loading="loading">
          <VChart v-if="corrOption" :option="corrOption" autoresize style="height:300px" />
        </ChartCard>

        <ChartCard title="Risk–Return Scatter" subtitle="X=Ann Vol · Y=CAGR · Bubble=MaxDD" :loading="loading">
          <VChart v-if="scatterOption" :option="scatterOption" autoresize style="height:300px" />
        </ChartCard>
      </div>

      <!-- Comparison table -->
      <ChartCard title="Comparison Metrics" :loading="loading">
        <DataTable :columns="tableCols" :rows="tableRows" :searchable="false">
          <template #cell-ticker="{ value }">
            <TickerBadge :ticker="String(value)" />
          </template>
        </DataTable>
      </ChartCard>
    </template>

    <div v-else class="flex flex-col items-center justify-center py-20 text-surface-500">
      <svg class="w-12 h-12 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke-width="1" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
      <p class="text-sm">Select 2+ tickers and click Compare</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import dayjs from 'dayjs'
import SectionHeader   from '@/components/shared/SectionHeader.vue'
import ChartCard       from '@/components/shared/ChartCard.vue'
import DataTable       from '@/components/shared/DataTable.vue'
import TickerSearch    from '@/components/shared/TickerSearch.vue'
import DateRangePicker from '@/components/shared/DateRangePicker.vue'
import TickerBadge     from '@/components/shared/TickerBadge.vue'
import { dataApi }  from '@/api/dataApi'
import { statsApi } from '@/api/statsApi'
import type { DateRange } from '@/types'
import { CHART_COLORS, BASE_TOOLTIP, BASE_LEGEND, BASE_GRID, BASE_XAXIS, BASE_YAXIS, BASE_DATAZONE, rebase } from '@/components/charts/chartTheme'
import { QUICK_SETS } from '@/types'

const selected  = ref(['SPY', 'QQQ', 'GLD'])
const dateRange = ref<DateRange>({
  start: dayjs().subtract(5, 'year').format('YYYY-MM-DD'),
  end:   dayjs().format('YYYY-MM-DD'),
})
const loading    = ref(false)
const hasResults = ref(false)

const equityOption  = ref<Record<string, unknown> | null>(null)
const corrOption    = ref<Record<string, unknown> | null>(null)
const scatterOption = ref<Record<string, unknown> | null>(null)
const tableRows     = ref<Record<string, unknown>[]>([])

const tableCols = [
  { key: 'ticker',       label: 'Ticker' },
  { key: 'cagr',         label: 'CAGR',    align: 'right' as const, colorize: true, format: (v: unknown) => `${((v as number)*100).toFixed(2)}%` },
  { key: 'sharpe',       label: 'Sharpe',  align: 'right' as const, colorize: true, format: (v: unknown) => (v as number).toFixed(3) },
  { key: 'sortino',      label: 'Sortino', align: 'right' as const, colorize: true, format: (v: unknown) => (v as number).toFixed(3) },
  { key: 'max_drawdown', label: 'Max DD',  align: 'right' as const, colorize: true, format: (v: unknown) => `${((v as number)*100).toFixed(1)}%` },
  { key: 'ann_vol',      label: 'Ann Vol', align: 'right' as const, format: (v: unknown) => `${((v as number)*100).toFixed(1)}%` },
  { key: 'var_95',       label: 'VaR 95%', align: 'right' as const, colorize: true, format: (v: unknown) => `${((v as number)*100).toFixed(2)}%` },
]

async function runCompare() {
  if (selected.value.length < 2) return
  loading.value = true
  try {
    const tickers = selected.value.slice(0, 10)
    const [priceResults, riskResults, corrRes] = await Promise.all([
      Promise.allSettled(tickers.map((t) => dataApi.prices(t, dateRange.value.start, dateRange.value.end))),
      Promise.allSettled(tickers.map((t) => statsApi.risk(t, dateRange.value.start, dateRange.value.end))),
      statsApi.correlation(tickers, dateRange.value.start, dateRange.value.end),
    ])

    // Equity curves
    let commonDates: string[] = []
    const equitySeries = priceResults.map((r, i) => {
      if (r.status !== 'fulfilled') return null
      const bars = r.value.data.data
      if (!commonDates.length) commonDates = bars.map((b) => b.date)
      const rebased = rebase(bars.map((b) => b.close))
      return {
        name: tickers[i], type: 'line', data: rebased,
        symbol: 'none', smooth: false,
        lineStyle: { width: 1.8, color: CHART_COLORS[i % CHART_COLORS.length] },
      }
    }).filter(Boolean)

    equityOption.value = {
      tooltip:  { ...BASE_TOOLTIP },
      legend:   { ...BASE_LEGEND, bottom: 0 },
      grid:     { ...BASE_GRID, bottom: '18%' },
      xAxis:    { ...BASE_XAXIS, data: commonDates },
      yAxis:    { ...BASE_YAXIS, axisLabel: { ...BASE_YAXIS.axisLabel, formatter: (v: number) => `${v.toFixed(1)}x` } },
      dataZoom: BASE_DATAZONE,
      series:   equitySeries,
    }

    // Correlation heatmap
    const corrData = corrRes.data
    const corrTickers = corrData.tickers
    const heatData: [number, number, number][] = []
    corrTickers.forEach((r, ri) => {
      corrTickers.forEach((c, ci) => {
        heatData.push([ci, ri, +(corrData.matrix[r][c] ?? 0).toFixed(3)])
      })
    })
    corrOption.value = {
      tooltip: {
        trigger: 'item',
        backgroundColor: '#1e293b', borderColor: '#334155', textStyle: { color: '#f1f5f9' },
        formatter: (p: { data: [number, number, number] }) =>
          `${corrTickers[p.data[1]]} × ${corrTickers[p.data[0]]}: <b>${p.data[2].toFixed(3)}</b>`,
      },
      grid: { left: '12%', right: '5%', top: '5%', bottom: '18%' },
      xAxis: { type: 'category', data: corrTickers, ...BASE_XAXIS, axisLabel: { color: '#64748b', rotate: 30 } },
      yAxis: { type: 'category', data: corrTickers, ...BASE_YAXIS },
      visualMap: {
        min: -1, max: 1, calculable: true, orient: 'horizontal',
        left: 'center', bottom: 0,
        inRange: { color: ['#ef4444', '#1e293b', '#3b82f6'] },
        textStyle: { color: '#94a3b8', fontSize: 10 },
      },
      series: [{
        type: 'heatmap', data: heatData,
        label: { show: corrTickers.length <= 8, fontSize: 10, color: '#f1f5f9',
          formatter: (p: { data: [number, number, number] }) => p.data[2].toFixed(2) },
        emphasis: { itemStyle: { shadowBlur: 6 } },
      }],
    }

    // Table + Risk-Return scatter
    const rows: Record<string, unknown>[] = []
    const scatterData: [number, number, number, string][] = []
    riskResults.forEach((r, i) => {
      if (r.status !== 'fulfilled') return
      const d = r.value.data
      rows.push({
        ticker:       tickers[i],
        cagr:         d.max_drawdown < 0 ? d.calmar * d.max_drawdown : 0, // approximate from calmar
        sharpe:       d.sharpe,
        sortino:      d.sortino,
        max_drawdown: d.max_drawdown,
        ann_vol:      d.ann_volatility,
        var_95:       d.var_95,
      })
      scatterData.push([
        +(d.ann_volatility * 100).toFixed(2),
        +(d.sharpe * 10).toFixed(2),           // proxy for return
        Math.abs(d.max_drawdown * 100),
        tickers[i],
      ])
    })
    tableRows.value = rows

    // Also get CAGR from returns
    const retResults = await Promise.allSettled(tickers.map((t) => statsApi.returns(t, dateRange.value.start, dateRange.value.end)))
    retResults.forEach((r, i) => {
      if (r.status === 'fulfilled') {
        const row = rows.find((rw) => rw.ticker === tickers[i])
        if (row) row.cagr = r.value.data.cagr
        if (scatterData[i]) scatterData[i][1] = +(r.value.data.cagr * 100).toFixed(2)
      }
    })

    scatterOption.value = {
      tooltip: {
        backgroundColor: '#1e293b', borderColor: '#334155', textStyle: { color: '#f1f5f9' },
        formatter: (p: { data: [number, number, number, string] }) =>
          `<b>${p.data[3]}</b><br/>Vol: ${p.data[0].toFixed(1)}%<br/>CAGR: ${p.data[1].toFixed(1)}%<br/>MaxDD: ${p.data[2].toFixed(1)}%`,
      },
      grid: { ...BASE_GRID },
      xAxis: { ...BASE_XAXIS, type: 'value', name: 'Ann Volatility (%)', nameLocation: 'end', nameTextStyle: { color: '#64748b' } },
      yAxis: { ...BASE_YAXIS, name: 'CAGR (%)', nameLocation: 'end', nameTextStyle: { color: '#64748b' } },
      series: [{
        type: 'scatter',
        data: scatterData,
        symbolSize: (d: [number, number, number]) => Math.max(10, d[2] * 0.8),
        itemStyle: { color: (p: { dataIndex: number }) => CHART_COLORS[p.dataIndex % CHART_COLORS.length], opacity: 0.85 },
        label: { show: true, position: 'right', formatter: (p: { data: [number, number, number, string] }) => p.data[3], color: '#94a3b8', fontSize: 11 },
      }],
    }

    hasResults.value = true
  } finally {
    loading.value = false
  }
}
</script>
