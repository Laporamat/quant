import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import dayjs from 'dayjs'
import type { ReturnSummary, TickerInfo } from '@/types'
import { dataApi } from '@/api/dataApi'
import { statsApi } from '@/api/statsApi'

export const useMarketStore = defineStore('market', () => {
  // Universe state
  const activeUniverse = ref<'sp100' | 'set50' | 'benchmark'>('sp100')
  const universeTickerMap = ref<Record<string, string[]>>({})
  const availableTickers  = ref<TickerInfo[]>([])

  // Benchmark returns cache
  const benchmarkReturns = ref<Record<string, ReturnSummary>>({})

  // Date range
  const defaultStart = computed(() =>
    dayjs().subtract(20, 'year').format('YYYY-MM-DD')
  )
  const defaultEnd = computed(() => dayjs().format('YYYY-MM-DD'))

  const currentTickers = computed(
    () => universeTickerMap.value[activeUniverse.value] ?? []
  )

  async function loadUniverse(name: string) {
    if (universeTickerMap.value[name]) return
    try {
      const res = await dataApi.universe(name)
      universeTickerMap.value[name] = res.data.tickers
    } catch (_) { /* handled by interceptor */ }
  }

  async function loadAvailable() {
    try {
      const res = await dataApi.available()
      availableTickers.value = res.data
    } catch (_) { /* handled by interceptor */ }
  }

  async function loadBenchmarkReturns(tickers: string[]) {
    const missing = tickers.filter((t) => !benchmarkReturns.value[t])
    if (!missing.length) return
    const results = await Promise.allSettled(
      missing.map((t) => statsApi.returns(t))
    )
    results.forEach((r, i) => {
      if (r.status === 'fulfilled') {
        benchmarkReturns.value[missing[i]] = r.value.data
      }
    })
  }

  function setUniverse(name: 'sp100' | 'set50' | 'benchmark') {
    activeUniverse.value = name
    loadUniverse(name)
  }

  return {
    activeUniverse,
    universeTickerMap,
    availableTickers,
    benchmarkReturns,
    currentTickers,
    defaultStart,
    defaultEnd,
    loadUniverse,
    loadAvailable,
    loadBenchmarkReturns,
    setUniverse,
  }
})
