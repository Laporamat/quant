import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import dayjs from 'dayjs'
import { MetricCard, ChartCard, DateRangePicker, SectionHeader } from '@/components/shared/ui'
import EChart, { C, rebase, pctChange } from '@/components/charts/EChart'
import { dataApi } from '@/api/dataApi'
import { statsApi } from '@/api/statsApi'
import { indicatorsApi } from '@/api/indicatorsApi'
import { useMarketStore } from '@/store/appStore'

export default function TickerDeepDive() {
  const { symbol = 'SPY' } = useParams()
  const nav    = useNavigate()
  const market = useMarketStore()
  const ticker = symbol.toUpperCase()

  const [start, setStart] = useState(dayjs().subtract(5, 'year').format('YYYY-MM-DD'))
  const [end,   setEnd]   = useState(dayjs().format('YYYY-MM-DD'))
  const [filter, setFilter] = useState('')

  const [priceLoading, setPL] = useState(false)
  const [statsLoading, setSL] = useState(false)
  const [candleOpt,  setCandleOpt]  = useState<any>(null)
  const [rsiOpt,     setRsiOpt]     = useState<any>(null)
  const [macdOpt,    setMacdOpt]    = useState<any>(null)
  const [heatmapOpt, setHeatmapOpt] = useState<any>(null)
  const [ddOpt,      setDdOpt]      = useState<any>(null)
  const [distOpt,    setDistOpt]    = useState<any>(null)
  const [desc,  setDesc]  = useState<any>(null)
  const [risk,  setRisk]  = useState<any>(null)
  const [ret,   setRet]   = useState<any>(null)
  const [overlays, setOverlays] = useState([
    { key:'sma20',  label:'SMA 20',  active:true,  color:'#f59e0b', period:20 },
    { key:'sma50',  label:'SMA 50',  active:true,  color:'#3b82f6', period:50 },
    { key:'sma200', label:'SMA 200', active:false, color:'#a78bfa', period:200 },
  ])

  const available = market.availableTickers
    .map(t => t.ticker)
    .filter(t => !['XLK','XLV','XLF','XLE','XLY','XLP','XLI','XLB','XLU','XLRE','XLC'].includes(t))
    .sort()
    .filter(t => !filter || t.includes(filter.toUpperCase()))

  const loadAll = useCallback(async () => {
    setPL(true); setSL(true)
    try {
      const [priceRes, maRes, rsiRes, macdRes, dRes, riskRes, retRes, mRes, ddRes] = await Promise.allSettled([
        dataApi.prices(ticker, start, end),
        indicatorsApi.ma(ticker, '20,50,200', 'sma', start, end),
        indicatorsApi.rsi(ticker, 14, start, end),
        indicatorsApi.macd(ticker, 12, 26, 9, start, end),
        statsApi.descriptive(ticker, start, end),
        statsApi.risk(ticker, start, end),
        statsApi.returns(ticker, start, end),
        dataApi.prices(ticker, start, end, 'M'),
        statsApi.drawdown(ticker, start, end),
      ])
      setPL(false)

      // Candle
      if (priceRes.status === 'fulfilled') {
        const bars = priceRes.value.data.data
        const dates = bars.map((b: any) => b.date)
        const ohlc  = bars.map((b: any) => [b.open, b.close, b.low, b.high])
        const vols  = bars.map((b: any) => b.volume)
        const maD   = maRes.status === 'fulfilled' ? maRes.value.data as any : {}
        const overlaySeries = overlays.filter(o => o.active).map(o => ({
          name: o.label, type: 'line', data: maD[`sma_${o.period}`] ?? [],
          symbol: 'none', lineStyle: { width: 1.2, color: o.color }, xAxisIndex: 0, yAxisIndex: 0,
        }))
        setCandleOpt({
          tooltip: { ...C.TOOLTIP },
          grid: [{ left:'1%',right:'2%',top:'10%',height:'60%',containLabel:true }, { left:'1%',right:'2%',top:'75%',height:'15%',containLabel:true }],
          xAxis: [{ ...C.XAXIS, data: dates, gridIndex:0 }, { ...C.XAXIS, data: dates, gridIndex:1 }],
          yAxis: [{ ...C.YAXIS, gridIndex:0, scale:true }, { ...C.YAXIS, gridIndex:1 }],
          dataZoom: [{ type:'inside', xAxisIndex:[0,1], filterMode:'none' }, { type:'slider', xAxisIndex:[0,1], bottom:2, height:20, borderColor:'#334155', fillerColor:'rgba(59,130,246,0.12)', handleStyle:{ color:'#3b82f6' }, textStyle:{ color:'#64748b' } }],
          series: [
            { name: ticker, type:'candlestick', data:ohlc, xAxisIndex:0, yAxisIndex:0,
              itemStyle:{ color:'#22c55e', color0:'#ef4444', borderColor:'#22c55e', borderColor0:'#ef4444' } },
            { name:'Volume', type:'bar', data:vols, xAxisIndex:1, yAxisIndex:1, barMaxWidth:8, itemStyle:{ color:'rgba(99,102,241,0.5)' } },
            ...overlaySeries,
          ],
        })

        // Drawdown from price
        if (ddRes.status === 'fulfilled') {
          let peak = bars[0]?.close ?? 1
          const uw = bars.map((b: any) => { if (b.close > peak) peak = b.close; return +((b.close/peak-1)*100).toFixed(4) })
          setDdOpt({ tooltip: { ...C.TOOLTIP }, grid: { ...C.GRID },
            xAxis: { ...C.XAXIS, data: dates }, yAxis: { ...C.YAXIS, axisLabel: { ...C.YAXIS.axisLabel, formatter: '{value}%' } },
            series: [{ type:'line', data:uw, symbol:'none', lineStyle:{ color:'#ef4444', width:1 }, areaStyle:{ color: { type:'linear', x:0,y:0,x2:0,y2:1, colorStops:[{ offset:0, color:'rgba(239,68,68,0.4)' },{ offset:1, color:'rgba(239,68,68,0.02)' }] } } }] })
        }

        // Distribution
        const closes  = bars.map((b: any) => b.close)
        const rets    = pctChange(closes)
        const bins    = 60, mn = Math.min(...rets), mx = Math.max(...rets), w = (mx-mn)/bins
        const hist    = Array(bins).fill(0)
        rets.forEach(r => { const i = Math.min(Math.floor((r-mn)/w), bins-1); hist[i]++ })
        const labels  = hist.map((_, i) => ((mn+(i+.5)*w)*100).toFixed(2))
        const mean    = rets.reduce((a,b) => a+b, 0)/rets.length
        const std     = Math.sqrt(rets.reduce((a,b) => a+(b-mean)**2, 0)/rets.length)
        const normal  = labels.map(l => { const x = parseFloat(l)/100; return +(rets.length*w*(1/(std*Math.sqrt(2*Math.PI)))*Math.exp(-.5*((x-mean)/std)**2)).toFixed(2) })
        setDistOpt({ tooltip: { ...C.TOOLTIP }, legend: { ...C.LEGEND, bottom:0 }, grid: { ...C.GRID },
          xAxis: { ...C.XAXIS, data:labels, axisLabel:{ color:'#64748b', fontSize:10, rotate:30, formatter:'{value}%' } },
          yAxis: { ...C.YAXIS },
          series: [
            { name:'Frequency', type:'bar', data:hist, barMaxWidth:12, itemStyle:{ color:'rgba(59,130,246,0.6)', borderRadius:[2,2,0,0] } },
            { name:'Normal',    type:'line', data:normal, smooth:true, symbol:'none', lineStyle:{ color:'#f59e0b', width:2 } },
          ] })
      }

      // RSI
      if (rsiRes.status === 'fulfilled') {
        const d = rsiRes.value.data as any
        setRsiOpt({ tooltip: { ...C.TOOLTIP }, grid: { left:'1%',right:'2%',top:'5%',bottom:'12%',containLabel:true },
          xAxis: { ...C.XAXIS, data:d.date }, yAxis: { ...C.YAXIS, min:0, max:100 },
          series: [
            { name:'RSI', type:'line', data:d.rsi, symbol:'none', lineStyle:{ color:'#f59e0b', width:1.5 } },
            { type:'line', data:Array(d.rsi.length).fill(70), symbol:'none', lineStyle:{ color:'#ef4444', type:'dashed', width:1 } },
            { type:'line', data:Array(d.rsi.length).fill(30), symbol:'none', lineStyle:{ color:'#22c55e', type:'dashed', width:1 } },
          ] })
      }

      // MACD
      if (macdRes.status === 'fulfilled') {
        const md = macdRes.value.data as any[]
        setMacdOpt({ tooltip: { ...C.TOOLTIP }, grid: { left:'1%',right:'2%',top:'5%',bottom:'12%',containLabel:true },
          xAxis: { ...C.XAXIS, data:md.map(r => r.date) }, yAxis: { ...C.YAXIS },
          series: [
            { name:'MACD',   type:'line', data:md.map(r => r.macd),      symbol:'none', lineStyle:{ color:'#3b82f6', width:1.5 } },
            { name:'Signal', type:'line', data:md.map(r => r.signal),    symbol:'none', lineStyle:{ color:'#f97316', width:1.5 } },
            { name:'Hist',   type:'bar',  data:md.map(r => r.histogram), barMaxWidth:4, itemStyle:{ color:(p:any) => p.value >= 0 ? '#22c55e' : '#ef4444' } },
          ] })
      }

      // Stats
      if (dRes.status === 'fulfilled')   setDesc(dRes.value.data)
      if (riskRes.status === 'fulfilled') setRisk(riskRes.value.data)
      if (retRes.status === 'fulfilled')  setRet(retRes.value.data)

      // Monthly heatmap
      if (mRes.status === 'fulfilled') {
        const bars = mRes.value.data.data
        const mm: Record<string,Record<string,number>> = {}
        for (let i = 1; i < bars.length; i++) {
          const yr = bars[i].date.substring(0,4), mo = bars[i].date.substring(5,7)
          const r  = (bars[i].close - bars[i-1].close) / bars[i-1].close
          if (!mm[yr]) mm[yr] = {}; mm[yr][mo] = +(r*100).toFixed(2)
        }
        const years  = Object.keys(mm).sort()
        const months = ['01','02','03','04','05','06','07','08','09','10','11','12']
        const ML     = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        const hData: [number,number,number][] = []
        years.forEach((yr,yi) => months.forEach((mo,mi) => { const v = mm[yr]?.[mo]; if (v != null) hData.push([mi,yi,v]) }))
        const absMax = Math.max(...hData.map(d => Math.abs(d[2])), 1)
        setHeatmapOpt({ tooltip:{ trigger:'item', backgroundColor:'#1e293b', borderColor:'#334155', textStyle:{ color:'#f1f5f9' },
          formatter:(p:any) => `${years[p.data[1]]} ${ML[p.data[0]]}: <b>${p.data[2].toFixed(2)}%</b>` },
          grid:{ left:'8%',right:'5%',top:'3%',bottom:'15%' },
          xAxis:{ type:'category', data:ML, ...C.XAXIS },
          yAxis:{ type:'category', data:years, ...C.YAXIS, axisLabel:{ color:'#64748b', fontSize:10 } },
          visualMap:{ min:-absMax, max:absMax, calculable:true, orient:'horizontal', left:'center', bottom:0,
            inRange:{ color:['#ef4444','#1e293b','#22c55e'] }, textStyle:{ color:'#94a3b8', fontSize:10 } },
          series:[{ type:'heatmap', data:hData, label:{ show:years.length<=15, formatter:(p:any) => `${p.data[2].toFixed(1)}`, fontSize:9, color:'#f1f5f9' } }] })
      }
    } finally {
      setPL(false); setSL(false)
    }
  }, [ticker, start, end, overlays])

  useEffect(() => { loadAll() }, [ticker, start, end])
  useEffect(() => { if (!market.availableTickers.length) dataApi.available().then(r => market.setAvailable(r.data)) }, [])

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-surface-100">{ticker}</h1>
          <p className="text-sm text-surface-400 mt-0.5">Historical Deep Dive · {start} → {end}</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-2">
          <input value={filter} onChange={e => setFilter(e.target.value)} placeholder="Filter ticker…"
            className="input-base text-xs py-1.5 w-36"/>
          <DateRangePicker start={start} end={end} onChange={(s,e) => { setStart(s); setEnd(e) }}/>
        </div>
      </div>

      {/* Ticker browser */}
      <div className="glass p-3">
        <p className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-2">
          Available Tickers ({available.length})
        </p>
        <div className="flex flex-wrap gap-1.5 max-h-20 overflow-y-auto scrollbar-thin">
          {available.map(t => (
            <button key={t} onClick={() => nav(`/ticker/${t}`)}
              className={`px-2 py-0.5 rounded text-xs font-mono font-semibold transition-all ${t === ticker ? 'bg-primary-600 text-white' : 'bg-surface-700/60 text-surface-300 hover:bg-primary-600/20 hover:text-primary-300'}`}>
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Overlay toggles */}
      <ChartCard title="Price Chart" loading={priceLoading} onRefresh={loadAll}
        toolbar={
          <div className="flex gap-2 text-xs">
            {overlays.map((ov,i) => (
              <label key={ov.key} className="flex items-center gap-1 cursor-pointer">
                <input type="checkbox" checked={ov.active} className="accent-primary-500"
                  onChange={() => setOverlays(ovs => ovs.map((o,j) => j===i ? { ...o, active: !o.active } : o))}/>
                <span className="text-surface-400">{ov.label}</span>
              </label>
            ))}
          </div>
        }>
        {candleOpt && <EChart option={candleOpt} style={{ height: 360 }}/>}
      </ChartCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="RSI (14)" loading={priceLoading}>{rsiOpt && <EChart option={rsiOpt} style={{ height: 140 }}/>}</ChartCard>
        <ChartCard title="MACD (12,26,9)" loading={priceLoading}>{macdOpt && <EChart option={macdOpt} style={{ height: 140 }}/>}</ChartCard>
      </div>

      {/* Descriptive stats */}
      <div>
        <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">Descriptive Statistics</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {desc ? <>
            <MetricCard title="Count"      value={desc.count}      format="raw"/>
            <MetricCard title="Mean Daily" value={desc.mean}       format="percent" colorize/>
            <MetricCard title="Std Dev"    value={desc.std}        format="percent"/>
            <MetricCard title="Skewness"   value={desc.skewness}   format="number"/>
            <MetricCard title="Kurtosis"   value={desc.kurtosis}   format="number"/>
            <MetricCard title="Hurst"      value={desc.hurst}      format="number"/>
            <MetricCard title="Autocorr1"  value={desc.autocorr_1} format="number"/>
            <MetricCard title="JB p-val"   value={desc.jb_pvalue}  format="number"/>
          </> : statsLoading && Array(8).fill(0).map((_,i) => <div key={i} className="glass p-4 h-20 animate-skeleton rounded-xl"/>)}
        </div>
      </div>

      {/* Risk metrics */}
      <div>
        <h3 className="text-xs font-semibold text-surface-400 uppercase tracking-wider mb-3">Risk Metrics</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {risk ? <>
            <MetricCard title="Sharpe"    value={risk.sharpe}         format="number" colorize/>
            <MetricCard title="Sortino"   value={risk.sortino}        format="number" colorize/>
            <MetricCard title="Calmar"    value={risk.calmar}         format="number" colorize/>
            <MetricCard title="Omega"     value={risk.omega}          format="number"/>
            <MetricCard title="Max DD"    value={risk.max_drawdown}   format="percent" colorize/>
            <MetricCard title="Ann. Vol"  value={risk.ann_volatility} format="percent"/>
            <MetricCard title="VaR 95%"   value={risk.var_95}         format="percent" colorize/>
            <MetricCard title="CVaR 95%"  value={risk.cvar_95}        format="percent" colorize/>
          </> : statsLoading && Array(8).fill(0).map((_,i) => <div key={i} className="glass p-4 h-20 animate-skeleton rounded-xl"/>)}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Monthly Returns Heatmap" subtitle="Year × Month" loading={statsLoading} onRefresh={loadAll}>
          {heatmapOpt && <EChart option={heatmapOpt} style={{ height: 320 }}/>}
        </ChartCard>
        <ChartCard title="Underwater / Drawdown" loading={priceLoading} onRefresh={loadAll}>
          {ddOpt && <EChart option={ddOpt} style={{ height: 320 }}/>}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Return Distribution" loading={priceLoading}>
          {distOpt && <EChart option={distOpt} style={{ height: 280 }}/>}
        </ChartCard>
        {ret && (
          <div className="glass p-5 space-y-3">
            <h3 className="text-sm font-semibold text-surface-200">Return Summary</h3>
            {[
              { label: 'Total Return',   value: `${(ret.total_return*100).toFixed(1)}%`,      pos: ret.total_return >= 0 },
              { label: 'CAGR',           value: `${(ret.cagr*100).toFixed(2)}%`,              pos: ret.cagr >= 0 },
              { label: 'Avg Daily',      value: `${(ret.avg_daily_return*100).toFixed(4)}%`,  pos: ret.avg_daily_return >= 0 },
              { label: 'Best Day',       value: `+${(ret.best_day*100).toFixed(2)}%`,         pos: true },
              { label: 'Worst Day',      value: `${(ret.worst_day*100).toFixed(2)}%`,         pos: false },
              { label: '% Positive',     value: `${(ret.pct_positive_days*100).toFixed(1)}%`, pos: ret.pct_positive_days > 0.5 },
            ].map(row => (
              <div key={row.label} className="flex justify-between items-center py-1.5 border-b border-surface-700/30 last:border-0">
                <span className="text-xs text-surface-400">{row.label}</span>
                <span className={`text-sm font-semibold ${row.pos ? 'text-bull' : 'text-bear'}`}>{row.value}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
