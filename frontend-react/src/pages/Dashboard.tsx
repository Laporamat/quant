import { useEffect, useState, useCallback } from 'react'
import dayjs from 'dayjs'
import { MetricCard, ChartCard, DataTable, SectionHeader, TickerBadge } from '@/components/shared/ui'
import EChart, { C, rebase } from '@/components/charts/EChart'
import { statsApi } from '@/api/statsApi'
import { dataApi }  from '@/api/dataApi'
import { http }     from '@/api/client'
import { useMarketStore } from '@/store/appStore'

const BENCH      = ['SPY','QQQ','IWM','GLD','TLT','VTI']
const SECTORS    = ['XLK','XLV','XLF','XLE','XLY','XLP','XLI','XLB','XLU','XLRE','XLC']
const SECT_NAMES = ['Tech','Health','Finance','Energy','ConsDisc','Staples','Industrial','Materials','Utilities','RealEstate','Comm']

export default function Dashboard() {
  const market = useMarketStore()
  const [universe, setUniverse] = useState<'sp100'|'set50'|'benchmark'>('sp100')
  const [noData, setNoData]     = useState(false)
  const [dlStatus, setDlStatus] = useState({ running: false, done: 0, total: 37, pct: 0 })
  const [benchmarks, setBenchmarks] = useState(BENCH.map(t => ({ ticker: t, cagr: null as number|null, total: null as number|null })))
  const [gainers, setGainers]   = useState<Record<string, unknown>[]>([])
  const [losers,  setLosers]    = useState<Record<string, unknown>[]>([])
  const [sectorOpt, setSectorOpt] = useState<any>(null)
  const [equityOpt, setEquityOpt] = useState<any>(null)
  const [gauge50,   setGauge50]   = useState<any>(null)
  const [gauge200,  setGauge200]  = useState<any>(null)
  const [loading,   setLoading]   = useState({ bench: false, movers: false, sector: false, equity: false, breadth: false })

  function setL(k: string, v: boolean) { setLoading(p => ({ ...p, [k]: v })) }

  const moverCols = [
    { key: 'ticker', label: 'Ticker', render: (_: unknown, r: any) => <TickerBadge ticker={r.ticker}/> },
    { key: 'cagr',   label: 'CAGR',   align: 'right' as const, colorize: true, format: (v: unknown) => `${((v as number)*100).toFixed(1)}%` },
    { key: 'total',  label: 'Total',  align: 'right' as const, colorize: true, format: (v: unknown) => `${((v as number)*100).toFixed(0)}%` },
  ]

  const checkData = useCallback(async () => {
    const r = await http.get('/data/available').catch(() => ({ data: [] }))
    if ((r.data as unknown[]).length === 0) setNoData(true)
    else { setNoData(false); loadAll() }
  }, [])

  useEffect(() => { checkData() }, [checkData])

  async function startDownload() {
    await http.post('/data/quickstart').catch(() => {})
    setDlStatus(s => ({ ...s, running: true }))
    const poll = setInterval(async () => {
      const r = await http.get('/data/quickstart/status').catch(() => null)
      if (!r) return
      setDlStatus(r.data as any)
      if (!r.data.running && r.data.done > 0) {
        clearInterval(poll)
        setNoData(false)
        loadAll()
      }
    }, 3000)
  }

  async function loadBenchmarks() {
    setL('bench', true)
    const results = await Promise.allSettled(BENCH.map(t => statsApi.returns(t)))
    setBenchmarks(BENCH.map((t, i) => {
      const r = results[i]
      return { ticker: t, cagr: r.status === 'fulfilled' ? r.value.data.cagr : null,
               total: r.status === 'fulfilled' ? r.value.data.total_return : null }
    }))
    setL('bench', false)
  }

  async function loadMovers() {
    setL('movers', true)
    const avail = market.availableTickers.filter(t =>
      !SECTORS.includes(t.ticker) && !['SPY','QQQ','IWM','GLD','TLT','VTI'].includes(t.ticker)
    ).slice(0, 50)
    if (!avail.length) { setL('movers', false); return }
    const results = await Promise.allSettled(avail.map(t => statsApi.returns(t.ticker)))
    const rows = results
      .map((r, i) => r.status === 'fulfilled'
        ? { ticker: avail[i].ticker, cagr: r.value.data.cagr, total: r.value.data.total_return }
        : null)
      .filter(Boolean) as Record<string, unknown>[]
    rows.sort((a, b) => (b.cagr as number) - (a.cagr as number))
    setGainers(rows.slice(0, 10))
    setLosers([...rows].sort((a, b) => (a.cagr as number) - (b.cagr as number)).slice(0, 10))
    setL('movers', false)
  }

  async function loadSectors() {
    setL('sector', true)
    const results = await Promise.allSettled(SECTORS.map(t => statsApi.returns(t)))
    const values  = results.map(r => r.status === 'fulfilled' ? +(r.value.data.cagr * 100).toFixed(2) : 0)
    setSectorOpt({
      tooltip: { ...C.TOOLTIP, trigger: 'axis' }, grid: { ...C.GRID, bottom: '20%' },
      xAxis: { ...C.XAXIS, data: SECT_NAMES, axisLabel: { ...C.XAXIS.axisLabel, rotate: 30 } },
      yAxis: { ...C.YAXIS, axisLabel: { ...C.YAXIS.axisLabel, formatter: '{value}%' } },
      series: [{ type: 'bar', data: values, barMaxWidth: 36,
        itemStyle: { color: (p: any) => p.value >= 0 ? '#22c55e' : '#ef4444', borderRadius: [4,4,0,0] } }],
    })
    setL('sector', false)
  }

  async function loadEquity() {
    setL('equity', true)
    const tickers = ['SPY','QQQ','GLD','TLT','IWM']
    const start   = dayjs().subtract(5, 'year').format('YYYY-MM-DD')
    const results = await Promise.allSettled(tickers.map(t => dataApi.prices(t, start)))
    let dates: string[] = []
    const series = results.map((r, i) => {
      if (r.status !== 'fulfilled') return null
      const bars = r.value.data.data
      if (!dates.length) dates = bars.map((b: any) => b.date)
      return { name: tickers[i], type: 'line', data: rebase(bars.map((b: any) => b.close)),
        symbol: 'none', lineStyle: { width: 1.5, color: C.COLORS[i] } }
    }).filter(Boolean)
    setEquityOpt({ tooltip: { ...C.TOOLTIP }, legend: { ...C.LEGEND, bottom: 0 },
      grid: { ...C.GRID, bottom: '22%' },
      xAxis: { ...C.XAXIS, data: dates }, yAxis: { ...C.YAXIS, axisLabel: { ...C.YAXIS.axisLabel, formatter: (v: number) => `${v.toFixed(1)}x` } },
      dataZoom: C.DATAZONE, series })
    setL('equity', false)
  }

  async function loadBreadth() {
    setL('breadth', true)
    const tickers = ['AAPL','MSFT','NVDA','GOOGL','AMZN','META','JPM','V','PG','XOM']
    const start   = dayjs().subtract(1, 'year').format('YYYY-MM-DD')
    const results = await Promise.allSettled(tickers.map(t => dataApi.prices(t, start)))
    let a50 = 0, a200 = 0, cnt = 0
    results.forEach(r => {
      if (r.status !== 'fulfilled') return
      const closes = r.value.data.data.map((b: any) => b.close)
      if (closes.length < 50) return; cnt++
      const last = closes.at(-1)!
      const sma50  = closes.slice(-50).reduce((a: number, b: number) => a + b, 0) / 50
      const sma200 = closes.length >= 200 ? closes.slice(-200).reduce((a: number, b: number) => a + b, 0) / 200 : 0
      if (last > sma50)  a50++
      if (sma200 && last > sma200) a200++
    })
    const p50 = cnt ? Math.round(a50/cnt*100) : 50
    const p200 = cnt ? Math.round(a200/cnt*100) : 50
    const mkGauge = (pct: number) => ({
      series: [{ type: 'gauge', radius: '90%', startAngle: 200, endAngle: -20, min: 0, max: 100,
        progress: { show: true, width: 12, itemStyle: { color: pct > 60 ? '#22c55e' : pct < 40 ? '#ef4444' : '#f59e0b' } },
        axisLine: { lineStyle: { width: 12, color: [[1, '#1e293b']] } },
        axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false }, pointer: { show: false },
        detail: { valueAnimation: true, fontSize: 22, fontWeight: 'bold', color: '#f1f5f9', formatter: '{value}%', offsetCenter: [0, '10%'] },
        data: [{ value: pct }] }]
    })
    setGauge50(mkGauge(p50)); setGauge200(mkGauge(p200))
    setL('breadth', false)
  }

  async function loadAvailable() {
    const r = await dataApi.available().catch(() => null)
    if (r) market.setAvailable(r.data)
  }

  function loadAll() {
    loadAvailable()
    loadBenchmarks(); loadMovers(); loadSectors(); loadEquity(); loadBreadth()
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* No-data banner */}
      {noData && (
        <div className="glass border border-primary-500/30 rounded-xl p-5">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="flex-1">
              <h3 className="font-semibold text-surface-100">ยังไม่มีข้อมูลในเครื่อง</h3>
              <p className="text-sm text-surface-400 mt-0.5">ต้องดาวน์โหลด historical data จาก Yahoo Finance ก่อน (ฟรี ไม่ต้อง API key)</p>
              {dlStatus.running && (
                <div className="mt-3 space-y-1.5">
                  <div className="flex justify-between text-xs text-surface-400">
                    <span>กำลังดาวน์โหลด {dlStatus.done}/{dlStatus.total} tickers</span>
                    <span>{dlStatus.pct}%</span>
                  </div>
                  <div className="h-2 bg-surface-700 rounded-full overflow-hidden">
                    <div className="h-full bg-primary-500 rounded-full transition-all duration-500" style={{ width: `${dlStatus.pct}%` }}/>
                  </div>
                </div>
              )}
            </div>
            <button onClick={startDownload} disabled={dlStatus.running} className="btn-primary shrink-0">
              {dlStatus.running
                ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block mr-2"/>กำลังโหลด…</>
                : 'Download Data'}
            </button>
          </div>
        </div>
      )}

      <SectionHeader title="Market Dashboard" description="20-year historical overview · SP100 · SET50 · Benchmarks">
        <div className="flex items-center gap-1 bg-surface-800 rounded-lg p-1">
          {(['sp100','set50','benchmark'] as const).map(u => (
            <button key={u} onClick={() => setUniverse(u)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${universe === u ? 'bg-primary-600 text-white' : 'text-surface-400 hover:text-white'}`}>
              {u === 'sp100' ? 'SP100' : u === 'set50' ? 'SET50' : 'Benchmark'}
            </button>
          ))}
        </div>
      </SectionHeader>

      {/* Benchmark KPI */}
      <div>
        <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">Benchmark Performance</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {benchmarks.map((bm, i) => (
            <a key={bm.ticker} href={`/ticker/${bm.ticker}`}
              className="metric-card border border-transparent hover:border-primary-600/40 cursor-pointer"
              style={{ animationDelay: `${i*60}ms` }}>
              <span className="text-xs font-mono font-bold text-primary-400">{bm.ticker}</span>
              <div className={`text-2xl font-bold tabular-nums mt-1 ${bm.cagr !== null ? (bm.cagr >= 0 ? 'text-bull' : 'text-bear') : 'text-surface-500'}`}>
                {bm.cagr !== null ? `${(bm.cagr*100).toFixed(1)}%` : '—'}
              </div>
              <div className="text-xs text-surface-500">{bm.total !== null ? `Total: ${(bm.total*100).toFixed(0)}%` : 'Loading…'}</div>
            </a>
          ))}
        </div>
      </div>

      {/* Movers + Sector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ChartCard title="Top Gainers" subtitle="Best 1-year return" loading={loading.movers} onRefresh={loadMovers}>
          <DataTable columns={moverCols} rows={gainers} pageSize={8}/>
        </ChartCard>
        <ChartCard title="Top Losers" subtitle="Worst 1-year return" loading={loading.movers} onRefresh={loadMovers}>
          <DataTable columns={moverCols} rows={losers} pageSize={8}/>
        </ChartCard>
        <ChartCard title="Sector Performance" subtitle="SPDR ETFs — 1Y CAGR" loading={loading.sector} onRefresh={loadSectors}>
          {sectorOpt && <EChart option={sectorOpt} style={{ height: 260 }}/>}
        </ChartCard>
      </div>

      {/* Breadth + Equity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Market Breadth" subtitle="% above SMA 50 / SMA 200" loading={loading.breadth} onRefresh={loadBreadth}>
          <div className="flex justify-around">
            {gauge50  && <div className="text-center"><EChart option={gauge50}  style={{ height:180,width:180 }}/><p className="text-xs text-surface-400 -mt-2">Above SMA 50</p></div>}
            {gauge200 && <div className="text-center"><EChart option={gauge200} style={{ height:180,width:180 }}/><p className="text-xs text-surface-400 -mt-2">Above SMA 200</p></div>}
          </div>
        </ChartCard>
        <ChartCard title="Benchmark Equity Curves" subtitle="Normalized · 5 years" loading={loading.equity} onRefresh={loadEquity}>
          {equityOpt && <EChart option={equityOpt} style={{ height: 200 }}/>}
        </ChartCard>
      </div>
    </div>
  )
}
