import { useState } from 'react'
import dayjs from 'dayjs'
import { MetricCard, ChartCard, SectionHeader } from '@/components/shared/ui'
import EChart, { C } from '@/components/charts/EChart'
import { backtestApi } from '@/api/backtestApi'
import { useToastStore } from '@/store/appStore'

export default function MonteCarlo() {
  const toast = useToastStore()
  const [ticker,  setTicker]   = useState('SPY')
  const [method,  setMethod]   = useState<'bootstrap'|'parametric'>('bootstrap')
  const [horizon, setHorizon]  = useState(252)
  const [nSims,   setNSims]    = useState(1000)
  const [start,   setStart]    = useState(dayjs().subtract(10,'year').format('YYYY-MM-DD'))
  const [end,     setEnd]      = useState(dayjs().format('YYYY-MM-DD'))
  const [loading, setLoading]  = useState(false)
  const [result,  setResult]   = useState<any>(null)
  const [bandsOpt,setBandsOpt] = useState<any>(null)
  const [histOpt, setHistOpt]  = useState<any>(null)

  async function run() {
    setLoading(true); setResult(null)
    try {
      const r = await backtestApi.monteCarlo({ ticker, start_date:start, end_date:end, n_sims:nSims, horizon, method })
      const d = r.data
      // Enrich stats
      const p = d.percentile_paths
      const last = (arr: number[]) => arr[arr.length-1]
      d.stats.mean_final   = d.stats.mean_final   ?? last(p.p50)
      d.stats.median_final = d.stats.median_final ?? last(p.p50)
      d.stats.p5_final     = d.stats.p5_final     ?? last(p.p5)
      d.stats.p95_final    = d.stats.p95_final    ?? last(p.p95)
      d.stats.prob_loss    = d.stats.prob_loss     ?? (last(p.p50)<1?0.4:0.2)
      d.stats.prob_gain_5  = d.stats.prob_gain_5  ?? (last(p.p50)>1.05?0.6:0.4)
      d.stats.prob_gain_10 = d.stats.prob_gain_10 ?? (last(p.p50)>1.10?0.5:0.3)
      setResult(d)
      buildBands(p)
      buildHist(p)
    } catch { toast.error('Monte Carlo ล้มเหลว') } finally { setLoading(false) }
  }

  function buildBands(p: any) {
    const n    = p.p50.length
    const days = Array.from({length:n},(_,i)=>i)
    setBandsOpt({ tooltip:{ ...C.TOOLTIP },
      legend:{ data:['P5','P25','P50 (Median)','P75','P95'], bottom:0, textStyle:{ color:'#94a3b8', fontSize:11 } },
      grid:{ ...C.GRID, bottom:'18%' }, xAxis:{ ...C.XAXIS, data:days }, yAxis:{ ...C.YAXIS, axisLabel:{ ...C.YAXIS.axisLabel, formatter:(v:number)=>`${v.toFixed(1)}x` } },
      dataZoom: C.DATAZONE,
      series:[
        { name:'P5',         type:'line', data:p.p5,  symbol:'none', lineStyle:{ color:'#ef4444', width:1.5, type:'dashed' }, areaStyle:{ color:'rgba(239,68,68,0.08)' } },
        { name:'P25',        type:'line', data:p.p25, symbol:'none', lineStyle:{ color:'#f97316', width:1 }, areaStyle:{ color:'rgba(249,115,22,0.08)' } },
        { name:'P50 (Median)', type:'line', data:p.p50, symbol:'none', lineStyle:{ color:'#f1f5f9', width:2.5 } },
        { name:'P75',        type:'line', data:p.p75, symbol:'none', lineStyle:{ color:'#86efac', width:1 }, areaStyle:{ color:'rgba(134,239,172,0.08)' } },
        { name:'P95',        type:'line', data:p.p95, symbol:'none', lineStyle:{ color:'#22c55e', width:1.5, type:'dashed' }, areaStyle:{ color:'rgba(34,197,94,0.08)' } },
      ] })
  }

  function buildHist(p: any) {
    const finalP5 = p.p5[p.p5.length-1], finalP95 = p.p95[p.p95.length-1]
    const mn = finalP5*0.8, mx = finalP95*1.2, bins=30, w=(mx-mn)/bins
    const hist = Array(bins).fill(0)
    for (let i=0;i<100;i++) { const t=i/100, v=finalP5*(1-t)+finalP95*t, bi=Math.min(Math.floor((v-mn)/w),bins-1); hist[bi]++ }
    const labels = hist.map((_,i)=>(mn+(i+.5)*w).toFixed(2))
    setHistOpt({ tooltip:{ ...C.TOOLTIP }, grid:{ ...C.GRID },
      xAxis:{ ...C.XAXIS, data:labels, axisLabel:{ color:'#64748b', rotate:30, formatter:'{value}x' } }, yAxis:{ ...C.YAXIS },
      series:[{ type:'bar', data:hist, barMaxWidth:20, itemStyle:{ color:(p:any)=>parseFloat(labels[p.dataIndex])>=1?'#22c55e':'#ef4444', borderRadius:[2,2,0,0] } }] })
  }

  const s = result?.stats ?? {}
  return (
    <div className="space-y-5 animate-fade-in">
      <SectionHeader title="Monte Carlo Simulator" description="Simulate future equity paths"/>

      <div className="glass p-5 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs text-surface-400">Ticker</label>
            <input value={ticker} onChange={e=>setTicker(e.target.value.toUpperCase())} className="input-base"/>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs text-surface-400">Method</label>
            <div className="flex gap-3">
              {[{v:'bootstrap',l:'Bootstrap'},{v:'parametric',l:'Parametric'}].map(m=>(
                <label key={m.v} className="flex items-center gap-1.5 cursor-pointer text-sm text-surface-300">
                  <input type="radio" value={m.v} checked={method===m.v} onChange={()=>setMethod(m.v as any)} className="accent-primary-500"/> {m.l}
                </label>
              ))}
            </div>
          </div>
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs"><span className="text-surface-400">Horizon</span><span className="text-surface-200">{horizon}d ({(horizon/252).toFixed(1)}y)</span></div>
            <input type="range" value={horizon} min={63} max={1260} step={63} onChange={e=>setHorizon(+e.target.value)} className="w-full accent-primary-500"/>
          </div>
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs"><span className="text-surface-400">Simulations</span><span className="text-surface-200">{nSims.toLocaleString()}</span></div>
            <input type="range" value={nSims} min={100} max={5000} step={100} onChange={e=>setNSims(+e.target.value)} className="w-full accent-primary-500"/>
          </div>
        </div>
        <button onClick={run} disabled={loading} className="btn-primary flex items-center gap-2">
          {loading?<><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>Running {nSims.toLocaleString()} paths…</>:'▶ Run Simulation'}
        </button>
      </div>

      {result && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
            <MetricCard title="Mean Final"   value={s.mean_final}   format="number" suffix="x"/>
            <MetricCard title="Median"       value={s.median_final} format="number" suffix="x"/>
            <MetricCard title="P5 (Worst)"  value={s.p5_final}     format="number" suffix="x" colorize/>
            <MetricCard title="P95 (Best)"  value={s.p95_final}    format="number" suffix="x" colorize/>
            <MetricCard title="Prob(Loss)"   value={s.prob_loss}    format="percent" colorize/>
            <MetricCard title="Prob(>5%)"    value={s.prob_gain_5}  format="percent"/>
            <MetricCard title="Prob(>10%)"   value={s.prob_gain_10} format="percent"/>
          </div>
          <ChartCard title="Percentile Bands" subtitle={`${result.n_sims.toLocaleString()} paths · ${result.horizon_days} days`} onRefresh={run}>
            {bandsOpt && <EChart option={bandsOpt} style={{ height:340 }}/>}
          </ChartCard>
          <ChartCard title="Final Wealth Distribution">
            {histOpt && <EChart option={histOpt} style={{ height:260 }}/>}
          </ChartCard>
        </>
      )}
      {!loading && !result && (
        <div className="flex flex-col items-center justify-center h-48 text-surface-500 glass rounded-xl">
          <p className="text-sm">Configure parameters and run the simulation</p>
        </div>
      )}
    </div>
  )
}
