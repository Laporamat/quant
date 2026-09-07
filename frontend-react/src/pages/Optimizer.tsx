import { useState } from 'react'
import { ChartCard, DataTable, SectionHeader } from '@/components/shared/ui'
import EChart, { C } from '@/components/charts/EChart'
import { optimizeApi, strategyApi } from '@/api/optimizeApi'
import { useToastStore } from '@/store/appStore'

const STRATEGY_LABELS: Record<string,string> = {
  sma_crossover:'SMA Crossover', momentum:'Momentum', mean_reversion:'Mean Reversion',
  breakout:'Breakout', trend_following:'Trend Following', buy_and_hold:'Buy & Hold',
}

export default function Optimizer() {
  const toast = useToastStore()
  const [strategy, setStrategy] = useState('sma_crossover')
  const [tickers,  setTickers]  = useState('AAPL')
  const [metric,   setMetric]   = useState('sharpe')
  const [start,    setStart]    = useState('2015-01-01')
  const [end,      setEnd]      = useState('2024-12-31')
  const [paramGrid, setParamGrid] = useState([{ key:'sma_fast',values:'10,20,30' },{ key:'sma_slow',values:'50,100,200' }])
  const [running,   setRunning]  = useState(false)
  const [results,   setResults]  = useState<any[]>([])
  const [surfaceOpt,setSO]       = useState<any>(null)
  const [wfRunning, setWFR]      = useState(false)
  const [wfResults, setWFRs]     = useState<any[]>([])
  const [wfOpt,     setWFO]      = useState<any>(null)
  const [trainYrs,  setTY]       = useState(3)
  const [testYrs,   setTEY]      = useState(1)

  function parseValues(s: string) {
    if (!s) return []
    if (s.includes(':')) { const [a,b,c]=s.split(':').map(Number); const o=[]; for(let v=a;v<=b;v+=c) o.push(v); return o }
    return s.split(',').map(Number).filter(n=>!isNaN(n))
  }
  const totalConfigs = paramGrid.reduce((a,p)=>a*Math.max(parseValues(p.values).length,1),1)

  async function runGrid() {
    const tlist = tickers.split(',').map(t=>t.trim().toUpperCase()).filter(Boolean)
    if (!tlist.length) { toast.error('กรุณาระบุ ticker'); return }
    setRunning(true); setResults([])
    try {
      const grid: Record<string,unknown[]> = {}
      paramGrid.forEach(p => { if(p.key) grid[p.key]=parseValues(p.values) })
      const r = await optimizeApi.grid({ strategy, tickers:tlist, start_date:start, end_date:end, param_grid:grid, metric, maximize:metric!=='max_drawdown', n_jobs:-1 })
      const sorted = (r.data.all_results??[]).sort((a: any,b: any)=>(b[metric]??0)-(a[metric]??0)).map((r: any,i: number)=>({ ...r,rank:i+1 }))
      setResults(sorted)
      // Surface if 2 params
      const keys = paramGrid.filter(p=>p.key).map(p=>p.key)
      if (keys.length===2) buildSurface(sorted, keys[0], keys[1])
      toast.success(`Grid search เสร็จ ${sorted.length} configs`)
    } catch { toast.error('Grid search ล้มเหลว') } finally { setRunning(false) }
  }

  function buildSurface(data: any[], xKey: string, yKey: string) {
    const xs = [...new Set(data.map(r=>r[xKey]))].sort((a:any,b:any)=>a-b)
    const ys = [...new Set(data.map(r=>r[yKey]))].sort((a:any,b:any)=>a-b)
    const pts: [number,number,number][] = data.map(r => [xs.indexOf(r[xKey]),ys.indexOf(r[yKey]),+(r[metric]??0).toFixed(4)])
    const vals = pts.map(d=>d[2]), mn=Math.min(...vals), mx=Math.max(...vals)
    setSO({ tooltip:{ trigger:'item', backgroundColor:'#1e293b', borderColor:'#334155', textStyle:{ color:'#f1f5f9' }, formatter:(p:any)=>`${xKey}=${xs[p.data[0]]} ${yKey}=${ys[p.data[1]]}: <b>${p.data[2].toFixed(4)}</b>` },
      grid:{ left:'10%',right:'5%',top:'5%',bottom:'18%' },
      xAxis:{ type:'category', data:xs.map(String), name:xKey, axisLine:{ lineStyle:{ color:'#334155' } }, axisLabel:{ color:'#64748b' }, axisTick:{ show:false } },
      yAxis:{ type:'category', data:ys.map(String), name:yKey, axisLine:{ show:false }, axisLabel:{ color:'#64748b' }, axisTick:{ show:false } },
      visualMap:{ min:mn,max:mx,calculable:true,orient:'horizontal',left:'center',bottom:0, inRange:{ color:['#ef4444','#f59e0b','#22c55e'] }, textStyle:{ color:'#94a3b8', fontSize:10 } },
      series:[{ type:'heatmap', data:pts, label:{ show:pts.length<=25, formatter:(p:any)=>p.data[2].toFixed(2), color:'#f1f5f9', fontSize:10 } }] })
  }

  async function runWF() {
    const tlist = tickers.split(',').map(t=>t.trim().toUpperCase()).filter(Boolean)
    setWFR(true); setWFRs([])
    try {
      const grid: Record<string,unknown[]> = {}
      paramGrid.forEach(p => { if(p.key) grid[p.key]=parseValues(p.values) })
      const r = await optimizeApi.walkForward({ strategy, tickers:tlist, start_date:start, end_date:end, param_grid:grid, metric, maximize:true, n_jobs:-1 }, trainYrs, testYrs)
      const folds = Array.isArray(r.data) ? r.data : []
      setWFRs(folds)
      setWFO({ tooltip:{ ...C.TOOLTIP }, grid:{ ...C.GRID },
        xAxis:{ ...C.XAXIS, data:folds.map((_:any,i:number)=>`Fold ${i+1}`) }, yAxis:{ ...C.YAXIS },
        series:[{ type:'bar', data:folds.map((f:any)=>+(f[metric]??f.oos_sharpe??0).toFixed(4)), barMaxWidth:40, itemStyle:{ color:(p:any)=>p.value>=0?'#22c55e':'#ef4444', borderRadius:[4,4,0,0] } }] })
    } catch { toast.error('Walk-forward ล้มเหลว') } finally { setWFR(false) }
  }

  const resultCols = results.length ? Object.keys(results[0]).map(k=>({
    key:k, label:k, align:'right' as const,
    format:(v:unknown)=>typeof v==='number'?v.toFixed(4):String(v??'—'),
  })) : []

  return (
    <div className="space-y-5 animate-fade-in">
      <SectionHeader title="Strategy Optimizer" description="Grid Search + Walk-Forward"/>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        <div className="xl:col-span-1 space-y-4">
          <div className="glass p-4 space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs text-surface-400">Strategy</label>
              <select value={strategy} onChange={e=>setStrategy(e.target.value)} className="input-base">
                {Object.entries(STRATEGY_LABELS).map(([k,v])=><option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-surface-400">Tickers</label>
              <input value={tickers} onChange={e=>setTickers(e.target.value)} placeholder="AAPL,MSFT" className="input-base"/>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div><label className="text-xs text-surface-400">Start</label><input type="date" value={start} onChange={e=>setStart(e.target.value)} className="input-base text-xs"/></div>
              <div><label className="text-xs text-surface-400">End</label><input type="date" value={end} onChange={e=>setEnd(e.target.value)} className="input-base text-xs"/></div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-surface-400">Metric</label>
              <select value={metric} onChange={e=>setMetric(e.target.value)} className="input-base">
                {['sharpe','cagr','calmar','sortino','max_drawdown'].map(m=><option key={m} value={m}>{m}</option>)}
              </select>
            </div>
            {/* Param grid */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider">Parameter Grid</h4>
                <button onClick={()=>setParamGrid(g=>[...g,{key:'',values:''}])} className="btn-ghost text-xs px-2 py-1">+ Add</button>
              </div>
              {paramGrid.map((p,i)=>(
                <div key={i} className="bg-surface-800/50 rounded-lg p-2.5 space-y-1.5">
                  <div className="flex gap-2">
                    <input value={p.key} onChange={e=>setParamGrid(g=>g.map((x,j)=>j===i?{...x,key:e.target.value}:x))} placeholder="param name" className="flex-1 input-base text-xs py-1"/>
                    <button onClick={()=>setParamGrid(g=>g.filter((_,j)=>j!==i))} className="text-bear/70 hover:text-bear text-xs px-1">✕</button>
                  </div>
                  <input value={p.values} onChange={e=>setParamGrid(g=>g.map((x,j)=>j===i?{...x,values:e.target.value}:x))} placeholder="10,20,30 or 10:100:10" className="w-full input-base text-xs py-1"/>
                  <p className="text-xs text-surface-500">Values: {parseValues(p.values).join(', ')||'—'}</p>
                </div>
              ))}
            </div>
            <button onClick={runGrid} disabled={running||!paramGrid.length} className="btn-primary w-full flex items-center justify-center gap-2">
              {running?<><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>Running {totalConfigs} configs…</>:`Run Grid (${totalConfigs} configs)`}
            </button>
          </div>

          {/* Walk-forward */}
          <div className="glass p-4 space-y-3">
            <h3 className="text-sm font-semibold text-surface-200">Walk-Forward</h3>
            <div className="grid grid-cols-2 gap-2">
              <div><label className="text-xs text-surface-400">Train Years</label><input type="number" value={trainYrs} onChange={e=>setTY(+e.target.value)} min={1} max={10} className="input-base text-sm"/></div>
              <div><label className="text-xs text-surface-400">Test Years</label><input type="number" value={testYrs} onChange={e=>setTEY(+e.target.value)} min={1} max={5} className="input-base text-sm"/></div>
            </div>
            <button onClick={runWF} disabled={wfRunning} className="btn-primary w-full text-sm">
              {wfRunning?'Running…':'Run Walk-Forward'}
            </button>
          </div>
        </div>

        <div className="xl:col-span-2 space-y-4">
          {results.length > 0 && (
            <>
              {/* Top 5 */}
              <div>
                <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">Top 5 Best Parameters</h3>
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
                  {results.slice(0,5).map((r,i)=>(
                    <div key={i} className="glass p-3 space-y-1.5">
                      <span className="badge badge-blue">#{i+1}</span>
                      <p className="text-xs text-surface-400">{metric}: <span className="text-surface-100 font-bold">{(r[metric] as number)?.toFixed(4)}</span></p>
                      {Object.entries(r).filter(([k])=>!['rank',metric].includes(k)&&typeof r[k]==='number').slice(0,4).map(([k,v])=>(
                        <p key={k} className="text-xs text-surface-400">{k}: <span className="text-surface-200">{String(v)}</span></p>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
              <ChartCard title={`All Results (${results.length} configs)`}>
                <DataTable columns={resultCols} rows={results} pageSize={20}/>
              </ChartCard>
              {surfaceOpt && (
                <ChartCard title="Optimization Surface">
                  <EChart option={surfaceOpt} style={{ height:320 }}/>
                </ChartCard>
              )}
            </>
          )}
          {wfResults.length > 0 && (
            <ChartCard title="Walk-Forward Results">
              {wfOpt && <EChart option={wfOpt} style={{ height:260 }}/>}
            </ChartCard>
          )}
          {!results.length && !wfResults.length && (
            <div className="flex items-center justify-center h-48 text-surface-500 glass rounded-xl">
              <p className="text-sm">Configure parameters and run</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
