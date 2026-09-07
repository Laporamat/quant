import { useState, useEffect } from 'react'
import { MetricCard, ChartCard, DataTable, SectionHeader, DateRangePicker } from '@/components/shared/ui'
import EChart, { C, rebase } from '@/components/charts/EChart'
import { backtestApi } from '@/api/backtestApi'
import { strategyApi } from '@/api/optimizeApi'
import { useToastStore } from '@/store/appStore'

const STRATEGY_LABELS: Record<string,string> = {
  buy_and_hold:'Buy & Hold', sma_crossover:'SMA Crossover', momentum:'Momentum',
  mean_reversion:'Mean Reversion', breakout:'Breakout', pairs_trading:'Pairs Trading',
  multi_factor:'Multi-Factor', volatility_targeting:'Vol Targeting', trend_following:'Trend Following', ml:'ML Strategy',
}
const STRATEGY_PARAMS: Record<string,{ key:string;label:string;min:number;max:number;step:number;default:number }[]> = {
  sma_crossover: [{ key:'sma_fast',label:'Fast SMA',min:5,max:100,step:5,default:20 },{ key:'sma_slow',label:'Slow SMA',min:20,max:300,step:10,default:50 }],
  momentum:      [{ key:'lookback',label:'Lookback',min:60,max:504,step:21,default:252 }],
  mean_reversion:[{ key:'rsi_oversold',label:'RSI Oversold',min:15,max:40,step:1,default:30 },{ key:'rsi_overbought',label:'RSI Overbought',min:60,max:85,step:1,default:70 }],
}

const TRADE_COLS = [
  { key:'date',       label:'Date' },
  { key:'ticker',     label:'Ticker' },
  { key:'side',       label:'Side' },
  { key:'entry',      label:'Entry',  align:'right' as const, format:(v:unknown) => `$${(v as number)?.toFixed(2) ?? '—'}` },
  { key:'pnl',        label:'PnL',    align:'right' as const, colorize:true, format:(v:unknown) => `$${(v as number)?.toFixed(0) ?? '—'}` },
  { key:'return_pct', label:'Ret%',   align:'right' as const, colorize:true, format:(v:unknown) => `${((v as number)*100).toFixed(2)}%` },
]

export default function BacktestLab() {
  const toast   = useToastStore()
  const [strategy, setStrategy] = useState('sma_crossover')
  const [tickers,  setTickers]  = useState('AAPL,MSFT')
  const [capital,  setCapital]  = useState(1000000)
  const [bench,    setBench]    = useState('SPY')
  const [commission, setComm]   = useState(0.0015)
  const [slippage,   setSlip]   = useState(0.0005)
  const [sizing,     setSizing] = useState('equal')
  const [start,      setStart]  = useState('2018-01-01')
  const [end,        setEnd]    = useState('2024-12-31')
  const [params,     setParams] = useState<Record<string,number>>({})
  const [running,    setRunning]= useState(false)
  const [result,     setResult] = useState<any>(null)
  const [history,    setHistory]= useState<any[]>([])
  const [tradeLog,   setTradeLog]= useState<any[]>([])
  const [equityOpt,  setEqOpt]  = useState<any>(null)
  const [ddOpt,      setDdOpt]  = useState<any>(null)
  const [heatOpt,    setHeatOpt]= useState<any>(null)
  const [stratDesc,  setStratDesc] = useState('')

  // Load strategy description + reset params when strategy changes
  useEffect(() => {
    const defaults: Record<string,number> = {}
    ;(STRATEGY_PARAMS[strategy] ?? []).forEach(p => { defaults[p.key] = p.default })
    setParams(defaults)
    strategyApi.get(strategy).then(r => setStratDesc(r.data.description ?? '')).catch(() => setStratDesc(''))
  }, [strategy])

  useEffect(() => {
    backtestApi.list().then(r => setHistory(r.data)).catch(() => {})
  }, [])

  async function run() {
    const tickerList = tickers.split(',').map(t => t.trim().toUpperCase()).filter(Boolean)
    if (!tickerList.length) { toast.error('กรุณาระบุ ticker'); return }
    setRunning(true); setResult(null)
    try {
      const r = await backtestApi.run({
        strategy, tickers: tickerList, start_date: start, end_date: end,
        initial_capital: capital, commission_pct: commission, slippage_pct: slippage,
        max_position_pct: 0.10, position_sizing: sizing, benchmark_ticker: bench,
        strategy_params: params,
      })
      setResult(r.data)
      buildCharts(r.data)
      const detail = await backtestApi.get(r.data.run_id)
      setTradeLog(detail.data.trade_log ?? [])
      setHistory(h => [{ run_id: r.data.run_id, strategy, created: new Date().toISOString(),
        sharpe: r.data.performance?.sharpe, cagr: r.data.performance?.cagr }, ...h.slice(0,9)])
      toast.success('Backtest เสร็จแล้ว!')
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Backtest ล้มเหลว')
    } finally {
      setRunning(false)
    }
  }

  function buildCharts(d: any) {
    const dates  = Object.keys(d.equity_curve)
    const equity = Object.values(d.equity_curve) as number[]
    const rebased = rebase(equity)

    setEqOpt({ tooltip:{ ...C.TOOLTIP }, legend:{ ...C.LEGEND, bottom:0 },
      grid:{ ...C.GRID, bottom:'18%' },
      xAxis:{ ...C.XAXIS, data:dates }, yAxis:{ ...C.YAXIS, axisLabel:{ ...C.YAXIS.axisLabel, formatter:(v:number) => `${v.toFixed(1)}x` } },
      dataZoom: C.DATAZONE,
      series:[{ name:d.strategy, type:'line', data:rebased, symbol:'none', lineStyle:{ color:'#3b82f6', width:2 }, areaStyle:{ color:'rgba(59,130,246,0.08)' } }] })

    let peak = equity[0]
    const uw = equity.map(v => { if (v > peak) peak = v; return +((v/peak-1)*100).toFixed(4) })
    setDdOpt({ tooltip:{ ...C.TOOLTIP }, grid:{ ...C.GRID },
      xAxis:{ ...C.XAXIS, data:dates }, yAxis:{ ...C.YAXIS, axisLabel:{ ...C.YAXIS.axisLabel, formatter:'{value}%' } },
      series:[{ type:'line', data:uw, symbol:'none', lineStyle:{ color:'#ef4444', width:1 }, areaStyle:{ color:'rgba(239,68,68,0.25)' } }] })

    const mm: Record<string,Record<string,number>> = {}
    for (let i = 1; i < dates.length; i++) {
      const yr = dates[i].substring(0,4), mo = dates[i].substring(5,7)
      const r  = (equity[i]-equity[i-1])/equity[i-1]
      if (!mm[yr]) mm[yr] = {}; mm[yr][mo] = (mm[yr][mo] ?? 0) + r
    }
    const years  = Object.keys(mm).sort()
    const months = ['01','02','03','04','05','06','07','08','09','10','11','12']
    const ML     = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    const hData: [number,number,number][] = []
    years.forEach((yr,yi) => months.forEach((mo,mi) => { const v=mm[yr]?.[mo]; if (v!=null) hData.push([mi,yi,+(v*100).toFixed(2)]) }))
    setHeatOpt({ tooltip:{ trigger:'item', backgroundColor:'#1e293b', borderColor:'#334155', textStyle:{ color:'#f1f5f9' },
      formatter:(p:any) => `${years[p.data[1]]} ${ML[p.data[0]]}: <b>${p.data[2].toFixed(2)}%</b>` },
      grid:{ left:'8%',right:'5%',top:'3%',bottom:'18%' },
      xAxis:{ type:'category', data:ML, ...C.XAXIS },
      yAxis:{ type:'category', data:years, ...C.YAXIS, axisLabel:{ color:'#64748b', fontSize:10 } },
      visualMap:{ min:-10,max:10,calculable:true,orient:'horizontal',left:'center',bottom:0, inRange:{ color:['#ef4444','#1e293b','#22c55e'] }, textStyle:{ color:'#94a3b8', fontSize:10 } },
      series:[{ type:'heatmap', data:hData, label:{ show:years.length<=12, formatter:(p:any) => `${p.data[2].toFixed(1)}`, fontSize:9, color:'#f1f5f9' } }] })
  }

  const perf = result?.performance ?? {}

  return (
    <div className="space-y-5 animate-fade-in">
      <SectionHeader title="Backtest Lab" description="ทดสอบ strategy กับข้อมูลอดีต 20 ปี"/>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Config */}
        <div className="xl:col-span-1 space-y-4">
          <div className="glass p-4 space-y-4">
            <h3 className="text-sm font-semibold text-surface-200">Configuration</h3>

            <div className="space-y-1.5">
              <label className="text-xs text-surface-400">Strategy</label>
              <select value={strategy} onChange={e => setStrategy(e.target.value)} className="input-base">
                {Object.entries(STRATEGY_LABELS).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              {stratDesc && <p className="text-xs text-surface-500 italic">{stratDesc}</p>}
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-surface-400">Tickers (comma-separated)</label>
              <input value={tickers} onChange={e => setTickers(e.target.value)} placeholder="AAPL,MSFT,NVDA" className="input-base"/>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-surface-400">Date Range</label>
              <DateRangePicker start={start} end={end} onChange={(s,e) => { setStart(s); setEnd(e) }}/>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs text-surface-400">Capital ($)</label>
                <input type="number" value={capital} onChange={e => setCapital(+e.target.value)} className="input-base"/>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-surface-400">Benchmark</label>
                <input value={bench} onChange={e => setBench(e.target.value)} className="input-base"/>
              </div>
            </div>

            <div className="space-y-2">
              <div>
                <div className="flex justify-between text-xs mb-1"><span className="text-surface-400">Commission</span><span className="text-surface-200">{(commission*100).toFixed(2)}%</span></div>
                <input type="range" value={commission} min={0} max={0.01} step={0.0001} onChange={e => setComm(+e.target.value)} className="w-full accent-primary-500"/>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1"><span className="text-surface-400">Slippage</span><span className="text-surface-200">{(slippage*100).toFixed(3)}%</span></div>
                <input type="range" value={slippage} min={0} max={0.005} step={0.0001} onChange={e => setSlip(+e.target.value)} className="w-full accent-primary-500"/>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-surface-400">Position Sizing</label>
              <div className="flex gap-3">
                {[{v:'equal',l:'Equal'},{v:'vol_target',l:'Vol-Target'},{v:'kelly',l:'Kelly'}].map(p => (
                  <label key={p.v} className="flex items-center gap-1.5 cursor-pointer text-xs text-surface-300">
                    <input type="radio" value={p.v} checked={sizing===p.v} onChange={() => setSizing(p.v)} className="accent-primary-500"/> {p.l}
                  </label>
                ))}
              </div>
            </div>

            {/* Dynamic strategy params */}
            {(STRATEGY_PARAMS[strategy] ?? []).map(p => (
              <div key={p.key} className="space-y-1">
                <div className="flex justify-between text-xs"><span className="text-surface-400">{p.label}</span><span className="text-surface-200">{params[p.key]}</span></div>
                <input type="range" value={params[p.key] ?? p.default} min={p.min} max={p.max} step={p.step}
                  onChange={e => setParams(ps => ({ ...ps, [p.key]: +e.target.value }))} className="w-full accent-primary-500"/>
              </div>
            ))}

            <button onClick={run} disabled={running} className={`btn-primary w-full flex items-center justify-center gap-2 py-2.5 ${running ? 'opacity-70' : ''}`}>
              {running ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>Running…</> : '▶ Run Backtest'}
            </button>
          </div>

          {history.length > 0 && (
            <div className="glass p-4 space-y-2">
              <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider">Recent Runs</h4>
              {history.map(h => (
                <button key={h.run_id} className="w-full text-left px-3 py-2 rounded-lg hover:bg-surface-700/40 transition-colors"
                  onClick={async () => { const r = await backtestApi.get(h.run_id); buildCharts({ ...r.data, equity_curve: r.data.equity_curve ?? {} }); setResult(r.data); setTradeLog(r.data.trade_log ?? []) }}>
                  <p className="text-xs font-medium text-surface-200">{STRATEGY_LABELS[h.strategy] ?? h.strategy}</p>
                  <p className="text-xs text-surface-500">Sharpe {h.sharpe?.toFixed(3) ?? '—'} · CAGR {h.cagr != null ? (h.cagr*100).toFixed(1)+'%' : '—'}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Results */}
        <div className="xl:col-span-2 space-y-4">
          {!result && !running && (
            <div className="flex flex-col items-center justify-center h-64 text-surface-500 glass rounded-xl">
              <p className="text-sm">Configure and run a backtest</p>
            </div>
          )}
          {running && (
            <div className="flex flex-col items-center justify-center h-64 glass rounded-xl gap-3">
              <span className="w-10 h-10 border-4 border-primary-500/30 border-t-primary-500 rounded-full animate-spin"/>
              <p className="text-sm text-surface-400">Running backtest…</p>
            </div>
          )}
          {result && !running && (
            <>
              <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
                <MetricCard title="CAGR"     value={perf.cagr}         format="percent" colorize/>
                <MetricCard title="Sharpe"   value={perf.sharpe}       format="number"  colorize/>
                <MetricCard title="Max DD"   value={perf.max_drawdown} format="percent" colorize/>
                <MetricCard title="Calmar"   value={perf.calmar}       format="number"  colorize/>
                <MetricCard title="Win Rate" value={perf.win_rate}     format="percent"/>
                <MetricCard title="Trades"   value={result.n_trades}   format="raw"/>
              </div>
              <ChartCard title={`Equity Curve — ${result.strategy}`} onRefresh={run}>
                {equityOpt && <EChart option={equityOpt} style={{ height: 280 }}/>}
              </ChartCard>
              <ChartCard title="Drawdown"><EChart option={ddOpt} style={{ height: 160 }}/></ChartCard>
              <ChartCard title="Monthly Returns Heatmap">{heatOpt && <EChart option={heatOpt} style={{ height: 260 }}/>}</ChartCard>
              <ChartCard title="Trade Log" subtitle={`${tradeLog.length} trades`}>
                <DataTable columns={TRADE_COLS} rows={tradeLog} pageSize={15} searchable/>
              </ChartCard>
              <div className="flex gap-3">
                <a href={backtestApi.report(result.run_id)} target="_blank" rel="noreferrer" className="btn-primary text-sm">Open HTML Report</a>
                <button onClick={() => { const b = new Blob([JSON.stringify(result,null,2)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download=`backtest_${result.run_id}.json`; a.click() }} className="btn-ghost text-sm">Download JSON</button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
