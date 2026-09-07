import { useState } from 'react'
import dayjs from 'dayjs'
import { ChartCard, DataTable, SectionHeader, DateRangePicker, TickerBadge } from '@/components/shared/ui'
import EChart, { C } from '@/components/charts/EChart'
import { statsApi } from '@/api/statsApi'
import { useToastStore } from '@/store/appStore'

export default function BubbleDetection() {
  const toast = useToastStore()
  const [ticker, setTicker]   = useState('SPY')
  const [start,  setStart]    = useState(dayjs().subtract(20,'year').format('YYYY-MM-DD'))
  const [end,    setEnd]       = useState(dayjs().format('YYYY-MM-DD'))
  const [loading, setLoading]  = useState(false)
  const [result,  setResult]   = useState<any>(null)
  const [gaugeOpt, setGO]      = useState<any>(null)
  const [logOpt,   setLO]      = useState<any>(null)
  const [zOpt,     setZO]      = useState<any>(null)
  const [barOpt,   setBO]      = useState<any>(null)
  const [priceOpt, setPO]      = useState<any>(null)
  const [scanLoading, setSL]   = useState(false)
  const [scanResults, setSR]   = useState<any[]>([])

  const SCAN_COLS = [
    { key:'ticker',       label:'Ticker', render:(_:unknown,r:any) => <TickerBadge ticker={r.ticker}/> },
    { key:'bubble_score', label:'Score',  align:'right' as const, format:(v:unknown) => (v as number).toFixed(1) },
    { key:'is_bubble',    label:'Bubble?',align:'center' as const, render:(v:unknown) => <span className={v?'text-bear font-bold':'text-bull'}>{v?'🔴 YES':'🟢 No'}</span> },
    { key:'z_score',      label:'Z-Score',align:'right' as const, colorize:true, format:(v:unknown) => (v as number).toFixed(3) },
    { key:'crash_prob',   label:'Crash%', align:'right' as const, format:(v:unknown) => `${((v as number)*100).toFixed(1)}%` },
  ]
  const BUBBLE_COLS = [
    { key:'name',         label:'Episode' },
    { key:'peak_date',    label:'Peak' },
    { key:'trough_date',  label:'Trough' },
    { key:'drawdown',     label:'Drawdown', align:'right' as const, colorize:true, format:(v:unknown) => `-${((v as number)*100).toFixed(1)}%` },
    { key:'duration_days',label:'Days',     align:'right' as const },
  ]

  async function analyse() {
    setLoading(true); setResult(null)
    try {
      const r = await statsApi.bubble(ticker, start, end)
      setResult(r.data); buildCharts(r.data)
    } catch { toast.error('วิเคราะห์ Bubble ล้มเหลว') } finally { setLoading(false) }
  }

  async function runScan() {
    setSL(true)
    const TOP20 = ['AAPL','MSFT','NVDA','GOOGL','AMZN','META','TSLA','JPM','V','JNJ','XOM','PG','HD','CVX','MRK','ABBV','PEP','KO','AVGO','COST']
    try {
      const r = await statsApi.bubbleScan(TOP20, start, end)
      setSR(r.data)
    } catch { toast.error('Scan ล้มเหลว') } finally { setSL(false) }
  }

  function buildCharts(d: any) {
    const score = d.bubble_score
    const gc    = score >= 60 ? '#ef4444' : score >= 35 ? '#f59e0b' : '#22c55e'
    setGO({ series:[{ type:'gauge', radius:'90%', startAngle:200, endAngle:-20, min:0, max:100,
      progress:{ show:true, width:12, itemStyle:{ color:gc } },
      axisLine:{ lineStyle:{ width:12, color:[[1,'#1e293b']] } },
      axisTick:{ show:false }, splitLine:{ show:false }, axisLabel:{ show:false }, pointer:{ show:false },
      detail:{ valueAnimation:true, fontSize:28, fontWeight:'bold', color:gc, formatter:'{value}', offsetCenter:[0,'15%'] },
      data:[{ value:score }] }] })

    const ps    = d.price_series
    const dates = ps.map((p: any) => p.date)
    const logP  = ps.map((p: any) => p.log_price)
    const n = logP.length, slope = (logP[n-1]-logP[0])/n
    const trend = Array.from({length:n},(_,i) => +(logP[0]+slope*i).toFixed(6))
    setLO({ tooltip:{ ...C.TOOLTIP }, legend:{ data:['Log Price','Linear Trend'], bottom:0, textStyle:{ color:'#94a3b8' } },
      grid:{ ...C.GRID, bottom:'18%' }, xAxis:{ ...C.XAXIS, data:dates }, yAxis:{ ...C.YAXIS },
      dataZoom: C.DATAZONE,
      series:[
        { name:'Log Price',    type:'line', data:logP,  symbol:'none', lineStyle:{ color:'#3b82f6', width:1.5 } },
        { name:'Linear Trend', type:'line', data:trend, symbol:'none', lineStyle:{ color:'#f59e0b', width:1.2, type:'dashed' } },
      ] })

    const zs = d.zscore_series
    setZO({ tooltip:{ ...C.TOOLTIP }, grid:{ ...C.GRID, bottom:'18%' },
      xAxis:{ ...C.XAXIS, data:zs.map((z:any)=>z.date) }, yAxis:{ ...C.YAXIS }, dataZoom: C.DATAZONE,
      visualMap:{ show:false, dimension:1, pieces:[{ gt:2, lte:100, color:'rgba(239,68,68,0.7)' },{ gt:1, lte:2, color:'rgba(245,158,11,0.7)' },{ gt:-1, lte:1, color:'rgba(59,130,246,0.7)' },{ gt:-100, lte:-1, color:'rgba(34,197,94,0.5)' }] },
      series:[
        { type:'line', data:zs.map((z:any)=>z.zscore), symbol:'none', lineStyle:{ width:1.5 }, areaStyle:{ opacity:.3 } },
        { type:'line', data:Array(zs.length).fill(2), symbol:'none', lineStyle:{ color:'#ef4444', type:'dashed', width:1 } },
        { type:'line', data:Array(zs.length).fill(-2), symbol:'none', lineStyle:{ color:'#22c55e', type:'dashed', width:1 } },
      ] })

    const bubs = d.historical_bubbles
    if (bubs.length) {
      setBO({ tooltip:{ ...C.TOOLTIP }, grid:{ ...C.GRID },
        xAxis:{ ...C.XAXIS, data:bubs.map((b:any)=>b.peak_date.substring(0,7)), axisLabel:{ color:'#64748b', rotate:30, fontSize:10 } },
        yAxis:{ ...C.YAXIS, axisLabel:{ ...C.YAXIS.axisLabel, formatter:(v:number)=>`${v.toFixed(0)}%` } },
        series:[{ type:'bar', data:bubs.map((b:any)=>+(b.drawdown*100).toFixed(1)), barMaxWidth:40,
          itemStyle:{ color:'#ef4444', borderRadius:[4,4,0,0], opacity:.85 },
          label:{ show:true, position:'top', color:'#f1f5f9', fontSize:9, formatter:(p:any)=>bubs[p.dataIndex].name.split(' ').at(-1) } }] })
    }

    const closes = ps.map((p: any) => p.close)
    const mkAreas = bubs.map((b:any) => [{ xAxis:b.peak_date, itemStyle:{ color:'rgba(239,68,68,0.12)' } },{ xAxis:b.trough_date }])
    setPO({ tooltip:{ ...C.TOOLTIP }, grid:{ ...C.GRID, bottom:'18%' }, xAxis:{ ...C.XAXIS, data:dates }, yAxis:{ ...C.YAXIS, scale:true },
      dataZoom: C.DATAZONE,
      series:[{ type:'line', data:closes, symbol:'none', lineStyle:{ color:'#3b82f6', width:1.5 }, markArea:{ silent:true, data:mkAreas } }] })
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <SectionHeader title="Bubble Detection" description="Log-price acceleration · Z-score divergence · LPPL · Historical episodes">
        <div className="flex items-center gap-2 flex-wrap">
          <input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} placeholder="Ticker" className="input-base w-24 text-sm py-1.5"/>
          <DateRangePicker start={start} end={end} onChange={(s,e)=>{ setStart(s); setEnd(e) }}/>
          <button onClick={analyse} disabled={loading} className="btn-primary flex items-center gap-2">
            {loading?<><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>…</>:'Analyse'}
          </button>
        </div>
      </SectionHeader>

      {/* Quick scan */}
      <div className="glass p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-surface-200">Universe Bubble Scan (Top 20)</h3>
          <button onClick={runScan} disabled={scanLoading} className="btn-ghost text-xs px-3 py-1.5 border border-surface-700">
            {scanLoading?'Scanning…':'Scan Top 20'}
          </button>
        </div>
        {scanResults.length > 0 && <DataTable columns={SCAN_COLS} rows={scanResults} pageSize={10}/>}
      </div>

      {/* Main result */}
      {result ? (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <div className="glass p-5 flex flex-col items-center justify-center gap-2">
              <p className="text-xs font-semibold text-surface-400 uppercase tracking-wider">Bubble Score</p>
              {gaugeOpt && <EChart option={gaugeOpt} style={{ height:180, width:180 }}/>}
              <span className={`badge text-sm px-4 py-1.5 ${result.is_bubble?'bg-bear/15 text-bear border border-bear/30':'bg-bull/15 text-bull border border-bull/30'}`}>
                {result.is_bubble?'🔴 BUBBLE DETECTED':'🟢 No Bubble'}
              </span>
              <p className="text-xs text-surface-500">Crash prob: <span className="font-medium text-surface-300">{(result.crash_probability*100).toFixed(1)}%</span></p>
            </div>
            <div className="lg:col-span-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
              {result.signals?.map((sig: any) => (
                <div key={sig.name} className={`glass p-3 space-y-2 border-l-2 ${sig.triggered?'border-bear':'border-surface-700'}`}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-surface-400 leading-tight">{sig.name}</span>
                    <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${sig.triggered?'bg-bear/15 text-bear':'bg-bull/15 text-bull'}`}>{sig.triggered?'ALERT':'OK'}</span>
                  </div>
                  <p className={`text-xl font-bold tabular-nums ${sig.triggered?'text-bear':'text-surface-200'}`}>{sig.value?.toFixed(3)}</p>
                  <p className="text-xs text-surface-500 leading-tight">{sig.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Log Price + Trend" subtitle="Super-exponential detection" onRefresh={analyse}>
              {logOpt && <EChart option={logOpt} style={{ height:280 }}/>}
            </ChartCard>
            <ChartCard title="Return Z-Score" subtitle="Rolling 1Y cumulative return vs history" onRefresh={analyse}>
              {zOpt && <EChart option={zOpt} style={{ height:280 }}/>}
            </ChartCard>
          </div>

          <ChartCard title={`Historical Bubble Episodes (${result.historical_bubbles?.length})`}>
            {barOpt && <EChart option={barOpt} style={{ height:200 }}/>}
            {result.historical_bubbles?.length > 0 && (
              <div className="mt-3"><DataTable columns={BUBBLE_COLS} rows={result.historical_bubbles}/></div>
            )}
          </ChartCard>

          <ChartCard title="Price Chart with Bubble Periods" subtitle="Red shading = drawdown episodes" onRefresh={analyse}>
            {priceOpt && <EChart option={priceOpt} style={{ height:320 }}/>}
          </ChartCard>
        </>
      ) : !loading && (
        <div className="flex flex-col items-center justify-center py-20 text-surface-500 glass rounded-xl">
          <p className="text-base">เลือก ticker แล้วกด Analyse</p>
          <p className="text-sm mt-1">ตรวจ Bubble ด้วย Z-Score · LPPL · Log-Price Acceleration</p>
        </div>
      )}
    </div>
  )
}
