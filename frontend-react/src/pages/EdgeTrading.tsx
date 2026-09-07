import { useState, useEffect } from 'react'
import { MetricCard, ChartCard, DataTable, SectionHeader, TickerBadge } from '@/components/shared/ui'
import EChart, { C } from '@/components/charts/EChart'
import { tradeApi } from '@/api/tradeApi'
import { dataApi }  from '@/api/dataApi'
import { useMarketStore, useToastStore } from '@/store/appStore'

const SCAN_COLS = [
  { key:'ticker',        label:'Ticker', render:(_:unknown,r:any) => <TickerBadge ticker={r.ticker}/> },
  { key:'signal',        label:'Signal', align:'center' as const, render:(v:unknown) => <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${v==='LONG'?'bg-bull/15 text-bull':v==='SHORT'?'bg-bear/15 text-bear':'bg-surface-700 text-surface-400'}`}>{String(v)}</span> },
  { key:'edge_score',    label:'Edge',   align:'right' as const, colorize:true, format:(v:unknown) => (v as number).toFixed(1) },
  { key:'win_rate',      label:'WinRate',align:'right' as const, colorize:true, format:(v:unknown) => `${((v as number)*100).toFixed(1)}%` },
  { key:'expected_value',label:'EV%',    align:'right' as const, colorize:true, format:(v:unknown) => `${(v as number).toFixed(3)}%` },
  { key:'half_kelly',    label:'Kelly½', align:'right' as const, format:(v:unknown) => `${(v as number).toFixed(1)}%` },
  { key:'var_1day_pct',  label:'VaR',    align:'right' as const, format:(v:unknown) => `${(v as number).toFixed(2)}%` },
  { key:'sharpe',        label:'Sharpe', align:'right' as const, colorize:true, format:(v:unknown) => (v as number).toFixed(2) },
  { key:'rsi',           label:'RSI',    align:'right' as const },
]

export default function EdgeTrading() {
  const market  = useMarketStore()
  const toast   = useToastStore()
  const [ticker, setTicker]   = useState('SPY')
  const [capital, setCapital] = useState(100000)
  const [holding, setHolding] = useState(5)
  const [loading,  setLoading] = useState(false)
  const [setup,    setSetup]   = useState<any>(null)
  const [signals,  setSignals] = useState<any>(null)
  const [coneOpt,  setConeOpt] = useState<any>(null)
  const [scanLoading, setSL]   = useState(false)
  const [scanResults, setSR]   = useState<any[]>([])
  const [scanMinEdge, setSME]  = useState(45)
  const [scanMaxVar,  setSMV]  = useState(3)
  const [tab, setTab]          = useState<'setup'|'scan'>('setup')
  const [edgeData, setEdgeData]= useState<any>(null)
  const [edgeLoading, setEL]   = useState(false)
  const [holdPeriodOpt, setHPO]= useState<any>(null)

  useEffect(() => {
    if (!market.availableTickers.length)
      dataApi.available().then(r => market.setAvailable(r.data)).catch(() => {})
  }, [])

  async function loadAll() {
    setLoading(true); setSetup(null)
    try {
      const [sigRes, setupRes] = await Promise.all([
        tradeApi.signals(ticker, holding),
        tradeApi.setup(ticker, capital, 1.0),
      ])
      setSignals(sigRes.data); setSetup(setupRes.data)
      buildCone(setupRes.data.cone)
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'โหลดข้อมูลล้มเหลว')
    } finally { setLoading(false) }
  }

  function buildCone(cone: any) {
    if (!cone?.daily?.length) return
    const days  = cone.daily.map((d: any) => `Day ${d.day}`)
    const upper = cone.daily.map((d: any) => d.upper)
    const lower = cone.daily.map((d: any) => d.lower)
    const mid   = cone.daily.map((d: any) => d.expected)
    const sl    = Array(days.length).fill(setup?.stop_price)
    const tp1   = Array(days.length).fill(setup?.tp1_price)
    setConeOpt({ tooltip:{ ...C.TOOLTIP }, legend:{ ...C.LEGEND, bottom:0 },
      grid:{ ...C.GRID, bottom:'18%' },
      xAxis:{ ...C.XAXIS, data:days }, yAxis:{ ...C.YAXIS, scale:true, axisLabel:{ ...C.YAXIS.axisLabel, formatter:(v:number) => `$${v.toFixed(1)}` } },
      dataZoom: C.DATAZONE,
      series:[
        { name:'Upper 95%', type:'line', data:upper, symbol:'none', lineStyle:{ color:'#22c55e', width:1, type:'dashed' }, areaStyle:{ color:'rgba(34,197,94,0.07)' } },
        { name:'Expected',  type:'line', data:mid,   symbol:'none', lineStyle:{ color:'#f1f5f9', width:2.5 } },
        { name:'Lower 95%', type:'line', data:lower, symbol:'none', lineStyle:{ color:'#ef4444', width:1, type:'dashed' }, areaStyle:{ color:'rgba(239,68,68,0.07)' } },
        { name:'Stop-Loss', type:'line', data:sl,    symbol:'none', lineStyle:{ color:'#ef4444', width:1.5 } },
        { name:'TP1',       type:'line', data:tp1,   symbol:'none', lineStyle:{ color:'#22c55e', width:1.5 } },
      ] })
  }

  async function runScan() {
    const tickers = market.availableTickers
      .map(t => t.ticker)
      .filter(t => !['XLK','XLV','XLF','XLE','XLY','XLP','XLI','XLB','XLU','XLRE','XLC'].includes(t))
    if (!tickers.length) { toast.error('ไม่พบข้อมูล ticker ในระบบ'); return }
    setSL(true); setSR([])
    try {
      const r = await tradeApi.scan(tickers, holding, scanMinEdge, scanMaxVar)
      setSR(r.data.results ?? [])
      if ((r.data.results ?? []).length === 0) toast.info('ไม่พบ opportunity ที่ตรงเงื่อนไข')
    } finally { setSL(false) }
  }

  async function loadEdge() {
    setEL(true)
    try {
      const r = await tradeApi.edge(ticker)
      setEdgeData(r.data)
      const periods = Object.keys(r.data.by_holding_period)
      const winRates = periods.map((p: string) => +(r.data.by_holding_period[p].win_rate * 100).toFixed(2))
      const evs      = periods.map((p: string) => +(r.data.by_holding_period[p].expected_value).toFixed(4))
      setHPO({ tooltip:{ ...C.TOOLTIP }, legend:{ ...C.LEGEND, bottom:0 }, grid:{ ...C.GRID },
        xAxis:{ ...C.XAXIS, data:periods },
        yAxis:[{ ...C.YAXIS, axisLabel:{ ...C.YAXIS.axisLabel, formatter:'{value}%' } }, { ...C.YAXIS, position:'right', axisLabel:{ color:'#64748b', formatter:'{value}%' } }],
        series:[
          { name:'Win Rate %', type:'bar', data:winRates, yAxisIndex:0, barMaxWidth:40, itemStyle:{ color:(p:any) => p.value>50?'#22c55e':'#ef4444', borderRadius:[4,4,0,0] } },
          { name:'EV%', type:'line', data:evs, yAxisIndex:1, symbol:'circle', symbolSize:6, lineStyle:{ color:'#3b82f6', width:2 }, itemStyle:{ color:'#3b82f6' } },
        ] })
    } finally { setEL(false) }
  }

  const edgeColor = (s: number) => s >= 65 ? 'text-bull' : s >= 45 ? 'text-side' : 'text-bear'
  const s = setup

  return (
    <div className="space-y-5 animate-fade-in">
      <SectionHeader title="Statistical Edge Trading" description="กำไรน้อยแต่ต่อเนื่อง · ขาดทุนน้อยที่สุด · คำนวณจากข้อมูลอดีต 20 ปี">
        <div className="flex items-center gap-2 flex-wrap">
          <input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} placeholder="Ticker" className="input-base w-24 text-sm py-1.5"/>
          <select value={holding} onChange={e => setHolding(+e.target.value)} className="input-base text-sm py-1.5 w-28">
            {[1,3,5,10,21].map(d => <option key={d} value={d}>Hold {d}d</option>)}
          </select>
          <select value={capital} onChange={e => setCapital(+e.target.value)} className="input-base text-sm py-1.5 w-28">
            {[10000,50000,100000,500000,1000000].map(c => <option key={c} value={c}>${(c/1000).toFixed(0)}K</option>)}
          </select>
          <button onClick={loadAll} disabled={loading} className="btn-primary flex items-center gap-2">
            {loading ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>Loading…</> : 'Analyse'}
          </button>
          <button onClick={runScan} disabled={scanLoading} className="btn-ghost border border-surface-700 text-sm px-3 py-2">
            {scanLoading ? '…' : '🔍 Scan All'}
          </button>
        </div>
      </SectionHeader>

      {/* Tabs */}
      <div className="flex border-b border-surface-700/50 gap-1">
        {[{k:'setup',l:'🎯 Trade Setup'},{k:'scan',l:'🔍 Scan'},{k:'edge',l:'📊 Edge Stats'}].map(t => (
          <button key={t.k} onClick={() => { setTab(t.k as any); if (t.k==='edge'&&!edgeData) loadEdge() }}
            className={`tab-item ${tab===t.k?'tab-active':''}`}>{t.l}</button>
        ))}
      </div>

      {tab === 'setup' && (
        <>
          {loading && <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">{Array(8).fill(0).map((_,i) => <div key={i} className="glass h-20 animate-skeleton rounded-xl"/>)}</div>}
          {s && signals && (
            <>
              {/* Signal strip */}
              <div className="glass p-4 flex flex-col sm:flex-row items-start sm:items-center gap-4">
                <div className="flex items-center gap-3">
                  <div className={`w-14 h-14 rounded-xl flex items-center justify-center text-2xl font-black ${signals.signal==='LONG'?'bg-bull/20 text-bull':signals.signal==='SHORT'?'bg-bear/20 text-bear':'bg-surface-700 text-surface-400'}`}>
                    {signals.signal==='LONG'?'↑':signals.signal==='SHORT'?'↓':'–'}
                  </div>
                  <div>
                    <p className="text-xs text-surface-400 uppercase tracking-wider">Signal</p>
                    <p className={`text-lg font-bold ${signals.signal==='LONG'?'text-bull':signals.signal==='SHORT'?'text-bear':'text-surface-400'}`}>{signals.signal}</p>
                  </div>
                </div>
                <div className="flex gap-4 flex-wrap text-sm">
                  {[['RSI', signals.mean_reversion?.rsi?.toFixed(1)], ['Z-Score', signals.mean_reversion?.z_score?.toFixed(2)], ['Regime', signals.regime]].map(([l,v]) => (
                    <div key={l}><span className="text-xs text-surface-500">{l}</span><span className="ml-1 font-semibold text-surface-200">{v}</span></div>
                  ))}
                </div>
                <div className="ml-auto flex flex-col items-center gap-1">
                  <span className="text-xs text-surface-400 uppercase tracking-wider">Edge Score</span>
                  <span className={`text-3xl font-black ${edgeColor(signals.edge_score)}`}>{signals.edge_score?.toFixed(0)}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {/* Setup */}
                <div className="glass p-4 space-y-2">
                  <h3 className="text-sm font-semibold text-surface-200">Trade Setup</h3>
                  {[['Entry', `$${s.entry?.toFixed(2)}`, ''],
                    ['Stop-Loss (2×VaR)', `$${s.stop_price?.toFixed(2)} (${s.stop_pct?.toFixed(2)}%)`, 'text-bear'],
                    ['TP1 (1.5R)', `$${s.tp1_price?.toFixed(2)} (+${s.tp1_pct?.toFixed(2)}%)`, 'text-bull'],
                    ['TP2 (2.5R)', `$${s.tp2_price?.toFixed(2)} (+${s.tp2_pct?.toFixed(2)}%)`, 'text-bull']].map(([l,v,c]) => (
                    <div key={l} className="flex justify-between items-center py-2 border-b border-surface-700/30 last:border-0">
                      <span className="text-xs text-surface-400">{l}</span>
                      <span className={`font-mono font-bold text-sm ${c || 'text-surface-100'}`}>{v}</span>
                    </div>
                  ))}
                  <div className="pt-2 space-y-1">
                    {[['Position Size', `${s.position_size_pct?.toFixed(1)}% ($${s.position_value?.toFixed(0)})`],
                      ['Half-Kelly', `${s.half_kelly_pct?.toFixed(1)}%`],
                      ['Max Loss', `$${s.max_loss_dollar?.toFixed(0)} (${s.max_loss_cap_pct?.toFixed(2)}% capital)`]].map(([l,v]) => (
                      <div key={l} className="flex justify-between text-xs">
                        <span className="text-surface-400">{l}</span>
                        <span className="text-surface-200 font-medium">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Probabilities */}
                <div className="glass p-4 space-y-3">
                  <h3 className="text-sm font-semibold text-surface-200">Outcome Probabilities ({holding}d)</h3>
                  {[
                    { l:`Hit TP1 (+${s.tp1_pct?.toFixed(2)}%)`, v: s.p_tp1, c:'bg-bull' },
                    { l:`Hit TP2 (+${s.tp2_pct?.toFixed(2)}%)`, v: s.p_tp2, c:'bg-bull/50' },
                    { l:'No clear move',                          v: s.p_neutral, c:'bg-surface-500' },
                    { l:`Hit Stop (${s.stop_pct?.toFixed(2)}%)`, v: s.p_stop, c:'bg-bear' },
                  ].map(row => (
                    <div key={row.l}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-surface-400">{row.l}</span>
                        <span className="font-semibold">{(row.v*100).toFixed(1)}%</span>
                      </div>
                      <div className="h-2 bg-surface-700 rounded-full overflow-hidden">
                        <div className={`h-full ${row.c} rounded-full transition-all duration-700`} style={{ width:`${row.v*100}%` }}/>
                      </div>
                    </div>
                  ))}
                  <div className="pt-2 border-t border-surface-700/30">
                    <div className="flex justify-between text-xs">
                      <span className="text-surface-400">Expected Value</span>
                      <span className={`font-bold ${s.ev_trade_pct>=0?'text-bull':'text-bear'}`}>
                        {s.ev_trade_pct>=0?'+':''}{s.ev_trade_pct?.toFixed(3)}% (${s.ev_dollar?.toFixed(0)})
                      </span>
                    </div>
                  </div>
                </div>

                {/* Risk */}
                <div className="glass p-4 space-y-2">
                  <h3 className="text-sm font-semibold text-surface-200">Risk Metrics</h3>
                  {[['Win Rate', `${(s.win_rate*100).toFixed(1)}%`, s.win_rate>0.5?'text-bull':'text-bear'],
                    ['W/L Ratio', s.wl_ratio?.toFixed(2), s.wl_ratio>=1.5?'text-bull':'text-side'],
                    ['Sharpe', s.sharpe?.toFixed(3), s.sharpe>=1?'text-bull':s.sharpe>=0?'text-side':'text-bear'],
                    ['VaR 1D', `${s.var_1day_pct?.toFixed(3)}%`, 'text-bear'],
                  ].map(([l,v,c]) => (
                    <div key={l} className="flex justify-between items-center py-1.5 border-b border-surface-700/30 last:border-0">
                      <span className="text-xs text-surface-400">{l}</span>
                      <span className={`text-sm font-bold ${c}`}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cone */}
              <ChartCard title={`GBM Probability Cone — ${holding} Trading Days`} subtitle="95% confidence · OCaml GBM engine">
                {coneOpt && <EChart option={coneOpt} style={{ height: 260 }}/>}
              </ChartCard>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <MetricCard title="VaR 1D 95%" value={s.var_1day_pct/100} format="percent" colorize/>
                <MetricCard title="Sharpe"      value={s.sharpe}            format="number"  colorize/>
                <MetricCard title="W/L Ratio"   value={s.wl_ratio}          format="number"/>
                <MetricCard title="Ann. Vol"    value={signals.ann_volatility} suffix="%" format="raw"/>
              </div>
            </>
          )}
          {!loading && !s && <div className="flex items-center justify-center h-48 text-surface-500 glass rounded-xl text-sm">เลือก ticker แล้วกด Analyse</div>}
        </>
      )}

      {tab === 'scan' && (
        <div className="space-y-4">
          <div className="glass p-4 flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-xs text-surface-400">Min Edge</label>
              <input type="range" value={scanMinEdge} min={20} max={80} step={5} onChange={e => setSME(+e.target.value)} className="w-28 accent-primary-500"/>
              <span className="text-xs text-surface-200 w-6">{scanMinEdge}</span>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs text-surface-400">Max VaR</label>
              <input type="range" value={scanMaxVar} min={0.5} max={5} step={0.5} onChange={e => setSMV(+e.target.value)} className="w-28 accent-primary-500"/>
              <span className="text-xs text-surface-200 w-10">{scanMaxVar}%</span>
            </div>
            <button onClick={runScan} disabled={scanLoading} className="btn-primary ml-auto">
              {scanLoading ? '…' : 'Scan'}
            </button>
          </div>
          {scanResults.length > 0
            ? <DataTable columns={SCAN_COLS} rows={scanResults} searchable/>
            : !scanLoading && <div className="flex items-center justify-center h-32 text-surface-500 glass rounded-xl text-sm">กด Scan เพื่อหา opportunities</div>}
        </div>
      )}

      {tab === 'edge' && (
        <div className="space-y-4">
          <button onClick={loadEdge} disabled={edgeLoading} className="btn-primary text-sm">
            {edgeLoading ? '…' : 'Load 20yr Edge Stats'}
          </button>
          {edgeData && (
            <>
              <ChartCard title="Win Rate by Holding Period" loading={edgeLoading}>
                {holdPeriodOpt && <EChart option={holdPeriodOpt} style={{ height: 220 }}/>}
              </ChartCard>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[{l:'Bull Market',k:'bull_market'},{l:'Bear Market',k:'bear_market'}].map(m => (
                  <div key={m.k} className="glass p-4">
                    <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">{m.l} Edge (5d)</h3>
                    {edgeData.by_regime?.[m.k] && (
                      <div className="space-y-1.5 text-sm">
                        {[['Win Rate', `${(edgeData.by_regime[m.k].win_rate*100).toFixed(1)}%`, edgeData.by_regime[m.k].win_rate>0.5?'text-bull':'text-bear'],
                          ['Avg Win', `+${edgeData.by_regime[m.k].avg_win?.toFixed(3)}%`, 'text-bull'],
                          ['Avg Loss', `${edgeData.by_regime[m.k].avg_loss?.toFixed(3)}%`, 'text-bear'],
                          ['Kelly', `${edgeData.by_regime[m.k].kelly_pct?.toFixed(1)}%`, 'text-primary-400']].map(([l,v,c]) => (
                          <div key={l} className="flex justify-between"><span className="text-surface-400">{l}</span><span className={c as string}>{v}</span></div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              {edgeData.drawdown_stats && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="glass p-3 text-center"><p className="text-xs text-surface-400 mb-1">Max Drawdown</p><p className="text-xl font-bold text-bear">{edgeData.drawdown_stats.max_drawdown_pct?.toFixed(1)}%</p></div>
                  <div className="glass p-3 text-center"><p className="text-xs text-surface-400 mb-1">Avg Drawdown</p><p className="text-xl font-bold text-side">{edgeData.drawdown_stats.avg_drawdown_pct?.toFixed(1)}%</p></div>
                  <div className="glass p-3 text-center"><p className="text-xs text-surface-400 mb-1">Avg Recovery</p><p className="text-xl font-bold text-surface-200">{edgeData.drawdown_stats.avg_recovery_days?.toFixed(0)} days</p></div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
