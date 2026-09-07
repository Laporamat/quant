import { useState } from 'react'
import dayjs from 'dayjs'
import { ChartCard, DataTable, SectionHeader, DateRangePicker, TickerBadge } from '@/components/shared/ui'
import EChart, { C, rebase } from '@/components/charts/EChart'
import { dataApi }  from '@/api/dataApi'
import { statsApi } from '@/api/statsApi'
import { useToastStore } from '@/store/appStore'

const QUICK_SETS: Record<string,string[]> = {
  'FAANG':['AAPL','AMZN','GOOGL','META','NFLX'],
  'AI Leaders':['NVDA','MSFT','GOOGL','META','AMD'],
  'Benchmarks':['SPY','QQQ','IWM','GLD','TLT'],
  'Financials':['JPM','BAC','GS','MS','BLK'],
}

export default function CompareAssets() {
  const toast = useToastStore()
  const [selected, setSelected] = useState(['SPY','QQQ','GLD'])
  const [input,    setInput]    = useState('')
  const [start,    setStart]    = useState(dayjs().subtract(5,'year').format('YYYY-MM-DD'))
  const [end,      setEnd]      = useState(dayjs().format('YYYY-MM-DD'))
  const [loading,  setLoading]  = useState(false)
  const [hasRes,   setHasRes]   = useState(false)
  const [equityOpt, setEO]      = useState<any>(null)
  const [corrOpt,   setCO]      = useState<any>(null)
  const [scatterOpt,setSO]      = useState<any>(null)
  const [tableRows, setTR]      = useState<any[]>([])

  const TABLE_COLS = [
    { key:'ticker',       label:'Ticker', render:(_:unknown,r:any) => <TickerBadge ticker={r.ticker}/> },
    { key:'cagr',         label:'CAGR',      align:'right' as const, colorize:true, format:(v:unknown)=>`${((v as number)*100).toFixed(2)}%` },
    { key:'sharpe',       label:'Sharpe',    align:'right' as const, colorize:true, format:(v:unknown)=>(v as number).toFixed(3) },
    { key:'max_drawdown', label:'Max DD',    align:'right' as const, colorize:true, format:(v:unknown)=>`${((v as number)*100).toFixed(1)}%` },
    { key:'ann_vol',      label:'Ann Vol',   align:'right' as const, format:(v:unknown)=>`${((v as number)*100).toFixed(1)}%` },
    { key:'var_95',       label:'VaR 95%',   align:'right' as const, colorize:true, format:(v:unknown)=>`${((v as number)*100).toFixed(2)}%` },
  ]

  function addTicker() {
    const t = input.trim().toUpperCase()
    if (t && selected.length < 10 && !selected.includes(t)) setSelected(s=>[...s,t])
    setInput('')
  }

  async function compare() {
    if (selected.length < 2) { toast.error('เลือก ticker อย่างน้อย 2 ตัว'); return }
    setLoading(true)
    try {
      const tickers = selected.slice(0,10)
      const [priceResults, riskResults, corrRes] = await Promise.all([
        Promise.allSettled(tickers.map(t=>dataApi.prices(t,start,end))),
        Promise.allSettled(tickers.map(t=>statsApi.risk(t,start,end))),
        statsApi.correlation(tickers,start,end),
      ])
      const retResults = await Promise.allSettled(tickers.map(t=>statsApi.returns(t,start,end)))

      // Equity
      let dates: string[] = []
      const equitySeries = priceResults.map((r,i) => {
        if (r.status!=='fulfilled') return null
        const bars = r.value.data.data
        if (!dates.length) dates = bars.map((b:any)=>b.date)
        return { name:tickers[i], type:'line', data:rebase(bars.map((b:any)=>b.close)), symbol:'none', lineStyle:{ width:1.8, color:C.COLORS[i%C.COLORS.length] } }
      }).filter(Boolean)
      setEO({ tooltip:{ ...C.TOOLTIP }, legend:{ ...C.LEGEND, bottom:0 }, grid:{ ...C.GRID, bottom:'18%' },
        xAxis:{ ...C.XAXIS, data:dates }, yAxis:{ ...C.YAXIS, axisLabel:{ ...C.YAXIS.axisLabel, formatter:(v:number)=>`${v.toFixed(1)}x` } },
        dataZoom: C.DATAZONE, series:equitySeries })

      // Correlation
      const corrD = corrRes.data
      const corrTickers = corrD.tickers
      const heatData: [number,number,number][] = []
      corrTickers.forEach((r:string,ri:number) => corrTickers.forEach((c:string,ci:number) => {
        heatData.push([ci,ri,+(corrD.matrix[r][c]??0).toFixed(3)])
      }))
      setCO({ tooltip:{ trigger:'item', backgroundColor:'#1e293b', borderColor:'#334155', textStyle:{ color:'#f1f5f9' },
        formatter:(p:any)=>`${corrTickers[p.data[1]]} × ${corrTickers[p.data[0]]}: <b>${p.data[2].toFixed(3)}</b>` },
        grid:{ left:'12%',right:'5%',top:'5%',bottom:'18%' },
        xAxis:{ type:'category', data:corrTickers, ...C.XAXIS, axisLabel:{ color:'#64748b', rotate:30 } },
        yAxis:{ type:'category', data:corrTickers, ...C.YAXIS },
        visualMap:{ min:-1,max:1,calculable:true,orient:'horizontal',left:'center',bottom:0, inRange:{ color:['#ef4444','#1e293b','#3b82f6'] }, textStyle:{ color:'#94a3b8', fontSize:10 } },
        series:[{ type:'heatmap', data:heatData, label:{ show:corrTickers.length<=8, fontSize:10, color:'#f1f5f9', formatter:(p:any)=>p.data[2].toFixed(2) } }] })

      // Table + scatter
      const rows: any[] = []
      const scatterData: any[] = []
      riskResults.forEach((r,i) => {
        if (r.status!=='fulfilled') return
        const d = r.value.data
        const ret = retResults[i].status==='fulfilled' ? retResults[i].value.data.cagr : 0
        rows.push({ ticker:tickers[i], cagr:ret, sharpe:d.sharpe, max_drawdown:d.max_drawdown, ann_vol:d.ann_volatility, var_95:d.var_95 })
        scatterData.push([+(d.ann_volatility*100).toFixed(2),+(ret*100).toFixed(2),Math.abs(d.max_drawdown*100),tickers[i]])
      })
      setTR(rows)
      setSO({ tooltip:{ backgroundColor:'#1e293b', borderColor:'#334155', textStyle:{ color:'#f1f5f9' },
        formatter:(p:any)=>`<b>${p.data[3]}</b><br/>Vol: ${p.data[0].toFixed(1)}%<br/>CAGR: ${p.data[1].toFixed(1)}%<br/>MaxDD: ${p.data[2].toFixed(1)}%` },
        grid:{ ...C.GRID },
        xAxis:{ ...C.XAXIS, type:'value', name:'Ann Volatility (%)', nameTextStyle:{ color:'#64748b' } },
        yAxis:{ ...C.YAXIS, name:'CAGR (%)', nameTextStyle:{ color:'#64748b' } },
        series:[{ type:'scatter', data:scatterData,
          symbolSize:(d:any)=>Math.max(10,d[2]*0.8), itemStyle:{ color:(p:any)=>C.COLORS[p.dataIndex%C.COLORS.length], opacity:.85 },
          label:{ show:true, position:'right', formatter:(p:any)=>p.data[3], color:'#94a3b8', fontSize:11 } }] })

      setHasRes(true)
    } catch { toast.error('Compare ล้มเหลว') } finally { setLoading(false) }
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <SectionHeader title="Multi-Asset Comparison" description="เปรียบเทียบ 2–10 assets">
        <button onClick={compare} disabled={selected.length<2||loading} className="btn-primary flex items-center gap-2">
          {loading?<><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>…</>:'Compare'}
        </button>
      </SectionHeader>

      {/* Controls */}
      <div className="glass p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          {selected.map(t=>(
            <span key={t} className="inline-flex items-center gap-1 px-2 py-0.5 bg-primary-600/20 text-primary-300 text-xs rounded-full">
              {t}<button onClick={()=>setSelected(s=>s.filter(x=>x!==t))} className="hover:text-white">×</button>
            </span>
          ))}
          <input value={input} onChange={e=>setInput(e.target.value.toUpperCase())}
            onKeyDown={e=>{ if(e.key==='Enter'){addTicker()} }}
            placeholder="Add ticker + Enter" className="input-base text-xs py-1.5 w-40"/>
          <button onClick={addTicker} className="btn-ghost text-xs border border-surface-700 px-3 py-1.5">Add</button>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-surface-500">Quick Sets:</span>
          {Object.entries(QUICK_SETS).map(([name,tickers])=>(
            <button key={name} onClick={()=>setSelected(tickers)}
              className="px-2.5 py-1 text-xs bg-surface-700/50 hover:bg-primary-600/20 text-surface-300 hover:text-primary-300 rounded-md transition-all">{name}</button>
          ))}
        </div>
        <DateRangePicker start={start} end={end} onChange={(s,e)=>{ setStart(s); setEnd(e) }}/>
      </div>

      {hasRes ? (
        <>
          <ChartCard title="Normalized Equity Curves" subtitle="Rebased to 1.0 at start" loading={loading} onRefresh={compare}>
            {equityOpt && <EChart option={equityOpt} style={{ height:300 }}/>}
          </ChartCard>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Correlation Matrix" loading={loading}>
              {corrOpt && <EChart option={corrOpt} style={{ height:300 }}/>}
            </ChartCard>
            <ChartCard title="Risk–Return Scatter" subtitle="X=Ann Vol · Y=CAGR · Size=MaxDD" loading={loading}>
              {scatterOpt && <EChart option={scatterOpt} style={{ height:300 }}/>}
            </ChartCard>
          </div>
          <ChartCard title="Comparison Metrics" loading={loading}>
            <DataTable columns={TABLE_COLS} rows={tableRows}/>
          </ChartCard>
        </>
      ) : !loading && (
        <div className="flex flex-col items-center justify-center py-20 text-surface-500">
          <p className="text-sm">เลือก 2+ tickers แล้วกด Compare</p>
        </div>
      )}
    </div>
  )
}
