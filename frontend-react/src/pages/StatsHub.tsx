import { useState } from 'react'
import dayjs from 'dayjs'
import { ChartCard, DataTable, SectionHeader, DateRangePicker } from '@/components/shared/ui'
import EChart, { C } from '@/components/charts/EChart'
import { statsApi } from '@/api/statsApi'
import { dataApi }  from '@/api/dataApi'
import { useToastStore } from '@/store/appStore'

// rolling helpers
function rollingFn(arr: number[], w: number, fn: (s: number[]) => number) {
  return arr.map((_, i) => i < w - 1 ? null : fn(arr.slice(i - w + 1, i + 1)))
}
function sharpeSeries(r: number[], w = 252) {
  return rollingFn(r, w, sl => { const m = sl.reduce((a,b)=>a+b,0)/sl.length, s = Math.sqrt(sl.reduce((a,b)=>a+(b-m)**2,0)/sl.length); return s===0?0:+(m/s*Math.sqrt(252)).toFixed(4) })
}
function volSeries(r: number[], w = 252) {
  return rollingFn(r, w, sl => { const m = sl.reduce((a,b)=>a+b,0)/sl.length; return +(Math.sqrt(sl.reduce((a,b)=>a+(b-m)**2,0)/sl.length*252)*100).toFixed(4) })
}

const TABS = [
  { k:'regime',      l:'① Regime' },
  { k:'seasonality', l:'② Seasonality' },
  { k:'tailrisk',    l:'③ Tail Risk' },
  { k:'rolling',     l:'④ Rolling Stats' },
] as const
type Tab = typeof TABS[number]['k']

export default function StatsHub() {
  const toast = useToastStore()
  const [ticker,  setTicker]  = useState('SPY')
  const [start,   setStart]   = useState(dayjs().subtract(10,'year').format('YYYY-MM-DD'))
  const [end,     setEnd]     = useState(dayjs().format('YYYY-MM-DD'))
  const [tab,     setTab]     = useState<Tab>('regime')

  // Regime
  const [regLoading, setRL]  = useState(false)
  const [regimeOpt,  setRO]  = useState<any>(null)
  const [regStats,   setRS]  = useState<any[]>([])
  const [regText,    setRT]  = useState('')
  const REGIME_COLORS = ['#3b82f6','#ef4444','#f59e0b','#a78bfa']
  const REGIME_LABELS = ['Bull','Bear','Sideways','Volatile']
  const regimeCols = [
    { key:'label',      label:'Regime' },
    { key:'pct_time',   label:'% Time',  align:'right' as const, format:(v:unknown) => `${((v as number)*100).toFixed(1)}%` },
    { key:'avg_return', label:'Avg Ret', align:'right' as const, colorize:true, format:(v:unknown) => `${((v as number)*100).toFixed(2)}%` },
    { key:'volatility', label:'Vol',     align:'right' as const, format:(v:unknown) => `${((v as number)*100).toFixed(2)}%` },
  ]
  async function loadRegime() {
    setRL(true)
    try {
      const r = await statsApi.regime(ticker, 3, start, end)
      const d = r.data
      const dates   = d.regimes.map((r: any) => r.date)
      const regimes = d.regimes.map((r: any) => r.regime)
      const nS = new Set(regimes).size
      setRO({ tooltip:{ ...C.TOOLTIP }, legend:{ data:REGIME_LABELS.slice(0,nS), bottom:0, textStyle:{ color:'#94a3b8' } },
        grid:{ ...C.GRID, bottom:'18%' }, xAxis:{ ...C.XAXIS, data:dates }, yAxis:{ ...C.YAXIS, max:1, axisLabel:{ show:false } },
        dataZoom: C.DATAZONE,
        series: Array.from({length:nS},(_,si) => ({
          name:REGIME_LABELS[si]??`State ${si}`, type:'line', stack:'r',
          data:regimes.map((r:number) => r===si?1:0), symbol:'none',
          areaStyle:{ color:REGIME_COLORS[si]+'99' }, lineStyle:{ width:0 } }) ) })
      setRS(d.stats.map((s: any) => ({ ...s, label: REGIME_LABELS[s.regime]??`State ${s.regime}` })))
      const bull = d.stats.find((s:any) => s.regime===0), bear = d.stats.find((s:any) => s.regime===1)
      setRT(`${ticker} อยู่ใน Bull ${bull?((bull.pct_time as number)*100).toFixed(1):'?'}% และ Bear ${bear?((bear.pct_time as number)*100).toFixed(1):'?'}% ของช่วงเวลาที่เลือก`)
    } catch { toast.error('โหลด Regime ล้มเหลว') } finally { setRL(false) }
  }

  // Seasonality
  const [seaLoading, setSL] = useState(false)
  const [dowOpt,  setDOW]   = useState<any>(null)
  const [monOpt,  setMon]   = useState<any>(null)
  const [janEff,  setJan]   = useState<any>(null)
  const [monEff,  setMonE]  = useState<any>(null)
  function barOpt(labels: string[], values: number[]) {
    return { tooltip:{ ...C.TOOLTIP }, grid:{ ...C.GRID },
      xAxis:{ ...C.XAXIS, data:labels }, yAxis:{ ...C.YAXIS, axisLabel:{ ...C.YAXIS.axisLabel, formatter:(v:number) => `${(v*100).toFixed(2)}%` } },
      series:[{ type:'bar', data:values.map(v=>({ value:v, itemStyle:{ color:v>=0?'#22c55e':'#ef4444', borderRadius:[4,4,0,0] } })), barMaxWidth:40 }] }
  }
  async function loadSeasonality() {
    setSL(true)
    try {
      const r = await statsApi.seasonality(ticker, start, end)
      const d = r.data
      const DOW = ['Mon','Tue','Wed','Thu','Fri']
      const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
      setDOW(barOpt(d.day_of_week.map((r:any) => DOW[+(r.day_num??r.label)]??r.label), d.day_of_week.map((r:any)=>r.mean_return)))
      setMon(barOpt(d.month.map((r:any) => MON[+(r.month_num??r.label)-1]??r.label), d.month.map((r:any)=>r.mean_return)))
      setJan(d.january_effect); setMonE(d.monday_effect)
    } catch { toast.error('โหลด Seasonality ล้มเหลว') } finally { setSL(false) }
  }

  // Tail Risk
  const [distLoading, setDL] = useState(false)
  const [tailOpt,  setTail]  = useState<any>(null)
  const [varRows,  setVarR]  = useState<any[]>([])
  const [bestFit,  setBF]    = useState<any>(null)
  const varCols = [
    { key:'method', label:'Method' },
    { key:'var95',  label:'VaR 95%', align:'right' as const, colorize:true, format:(v:unknown) => v!=null?`${((v as number)*100).toFixed(3)}%`:'—' },
    { key:'var99',  label:'VaR 99%', align:'right' as const, colorize:true, format:(v:unknown) => v!=null?`${((v as number)*100).toFixed(3)}%`:'—' },
  ]
  async function loadDistribution() {
    setDL(true)
    try {
      const r = await statsApi.distribution(ticker, start, end)
      const d = r.data, tr = d.tail_risk
      setVarR([
        { method:'Historical',    var95:tr['var_hist_95']??tr['var_95'], var99:tr['var_hist_99']??tr['var_99'] },
        { method:'Parametric',    var95:tr['var_param_95']??tr['var_95'], var99:tr['var_param_99']??tr['var_99'] },
        { method:'Cornish-Fisher',var95:tr['var_cf_95']??tr['var_95'],   var99:tr['var_cf_99']??tr['var_99'] },
      ])
      setBF(tr['best_fit']??d.best_fit)
      const pts = ['VaR 90%','VaR 95%','VaR 99%','CVaR 90%','CVaR 95%','CVaR 99%'].map((l,i) => {
        const keys = [['var_hist_90'],['var_hist_95'],['var_hist_99'],['cvar_hist_90'],['cvar_hist_95'],['cvar_hist_99']]
        return { label:l, val:tr[keys[i][0]] }
      }).filter(p => p.val!=null)
      setTail({ tooltip:{ ...C.TOOLTIP }, grid:{ ...C.GRID }, xAxis:{ ...C.XAXIS, data:pts.map(p=>p.label) },
        yAxis:{ ...C.YAXIS, axisLabel:{ ...C.YAXIS.axisLabel, formatter:(v:number)=>`${(v*100).toFixed(2)}%` } },
        series:[{ type:'bar', data:pts.map(p=>+(p.val as number).toFixed(6)), barMaxWidth:40, itemStyle:{ color:'#ef4444', borderRadius:[4,4,0,0] } }] })
    } catch { toast.error('โหลด Tail Risk ล้มเหลว') } finally { setDL(false) }
  }

  // Rolling
  const [rollLoading, setRollL] = useState(false)
  const [rollW, setRollW]       = useState(252)
  const [bmTicker, setBm]       = useState('SPY')
  const [sharpeOpt, setSharpeO] = useState<any>(null)
  const [volOpt,    setVolO]    = useState<any>(null)
  const [betaOpt,   setBetaO]   = useState<any>(null)
  function rollChart(dates: string[], vals: (number|null)[], name: string, color: string) {
    return { tooltip:{ ...C.TOOLTIP }, grid:{ ...C.GRID, bottom:'14%' }, xAxis:{ ...C.XAXIS, data:dates }, yAxis:{ ...C.YAXIS },
      dataZoom: C.DATAZONE,
      series:[{ name, type:'line', data:vals, symbol:'none', lineStyle:{ color, width:1.5 }, areaStyle:{ color:color+'18' },
        markLine:{ silent:true, lineStyle:{ color:'#334155', type:'dashed' }, data:[{ yAxis:0 }] } }] }
  }
  async function loadRolling() {
    setRollL(true)
    try {
      const [pRes, bRes] = await Promise.all([dataApi.prices(ticker, start, end), dataApi.prices(bmTicker, start, end)])
      const bars  = pRes.data.data, bBars = bRes.data.data
      const dates = bars.slice(1).map((b: any) => b.date)
      const rets  = bars.slice(1).map((b: any, i: number) => (b.close - bars[i].close) / bars[i].close)
      const bRets = bBars.slice(1).map((b: any, i: number) => (b.close - bBars[i].close) / bBars[i].close)
      const sharpe = sharpeSeries(rets, rollW)
      const vol    = volSeries(rets, rollW)
      const beta   = rets.map((_,i) => {
        if (i < rollW-1) return null
        const rs=rets.slice(i-rollW+1,i+1), bs=bRets.slice(i-rollW+1,i+1)
        const mr=rs.reduce((a,b)=>a+b,0)/rs.length, mb=bs.reduce((a,b)=>a+b,0)/bs.length
        const cov=rs.reduce((a,r,j)=>a+(r-mr)*(bs[j]-mb),0)/rs.length
        const vb=bs.reduce((a,b)=>a+(b-mb)**2,0)/bs.length
        return vb===0?null:+(cov/vb).toFixed(4)
      })
      setSharpeO(rollChart(dates, sharpe, 'Sharpe', '#3b82f6'))
      setVolO(rollChart(dates, vol, 'Vol %', '#f59e0b'))
      setBetaO(rollChart(dates, beta, 'Beta', '#a78bfa'))
    } catch { toast.error('โหลด Rolling Stats ล้มเหลว') } finally { setRollL(false) }
  }

  function runTab() {
    if (tab==='regime')      loadRegime()
    else if (tab==='seasonality') loadSeasonality()
    else if (tab==='tailrisk')    loadDistribution()
    else loadRolling()
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <SectionHeader title="Statistical Analysis Hub" description="Regime · Seasonality · Tail Risk · Rolling Stats">
        <div className="flex items-center gap-2 flex-wrap">
          <input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())} placeholder="Ticker" className="input-base w-24 text-sm py-1.5"/>
          <DateRangePicker start={start} end={end} onChange={(s,e) => { setStart(s); setEnd(e) }}/>
        </div>
      </SectionHeader>

      {/* Tab bar */}
      <div className="flex border-b border-surface-700/50 gap-1">
        {TABS.map(t => (
          <button key={t.k} onClick={() => setTab(t.k)} className={`tab-item ${tab===t.k?'tab-active':''}`}>{t.l}</button>
        ))}
      </div>

      {/* Run button */}
      <div className="flex justify-end">
        <button onClick={runTab} className="btn-primary text-sm">Analyse {ticker}</button>
      </div>

      {/* Regime Tab */}
      {tab==='regime' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <ChartCard title="HMM Regime Chart" subtitle="Last 252 trading days" loading={regLoading} onRefresh={loadRegime}>
                {regimeOpt && <EChart option={regimeOpt} style={{ height:260 }}/>}
              </ChartCard>
            </div>
            <ChartCard title="Regime Statistics" loading={regLoading}>
              {regStats.length > 0 && <DataTable columns={regimeCols} rows={regStats}/>}
            </ChartCard>
          </div>
          {regText && <div className="glass p-4 border-l-2 border-primary-500"><p className="text-sm text-surface-300 leading-relaxed">{regText}</p></div>}
        </div>
      )}

      {/* Seasonality Tab */}
      {tab==='seasonality' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <ChartCard title="Day-of-Week Effect" loading={seaLoading} onRefresh={loadSeasonality}>
              {dowOpt && <EChart option={dowOpt} style={{ height:240 }}/>}
            </ChartCard>
            <ChartCard title="Month-of-Year Effect" loading={seaLoading} onRefresh={loadSeasonality}>
              {monOpt && <EChart option={monOpt} style={{ height:240 }}/>}
            </ChartCard>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[{ title:'January Effect', eff:janEff, posKey:'avg_jan', negKey:'avg_other', posLabel:'Avg Jan', negLabel:'Avg Other' },
              { title:'Monday Effect',  eff:monEff, posKey:'avg_mon', negKey:'avg_other', posLabel:'Avg Mon', negLabel:'Avg Other' }].map(({ title, eff, posKey, negKey, posLabel, negLabel }) => (
              <div key={title} className="glass p-4 space-y-2">
                <h4 className="text-sm font-semibold text-surface-200">{title}</h4>
                {eff && <>
                  <span className={`badge ${eff.detected?'badge-bull':'badge-bear'}`}>{eff.detected?'Detected':'Not Detected'}</span>
                  <span className="text-xs text-surface-400 ml-2">p = {eff.p_value?.toFixed(4)}</span>
                  <p className="text-xs text-surface-400">{posLabel}: <span className="text-surface-200 font-medium">{(eff[posKey]*100).toFixed(3)}%</span> vs {negLabel}: <span className="text-surface-200 font-medium">{(eff[negKey]*100).toFixed(3)}%</span></p>
                </>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tail Risk Tab */}
      {tab==='tailrisk' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2">
              <ChartCard title="VaR Comparison" loading={distLoading} onRefresh={loadDistribution}>
                {tailOpt && <EChart option={tailOpt} style={{ height:280 }}/>}
              </ChartCard>
            </div>
            <div className="space-y-3">
              <ChartCard title="VaR Table" loading={distLoading}>
                {varRows.length > 0 && <DataTable columns={varCols} rows={varRows}/>}
              </ChartCard>
              {bestFit && (
                <div className="glass p-4 space-y-1.5">
                  <h4 className="text-xs font-semibold text-surface-400 uppercase tracking-wider">Best Fit</h4>
                  <p className="text-sm font-bold text-primary-400">{bestFit.name}</p>
                  <p className="text-xs text-surface-400">KS p-value: <span className="text-surface-200">{bestFit.ks_pvalue?.toFixed(4)}</span></p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Rolling Tab */}
      {tab==='rolling' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3 flex-wrap">
            <label className="text-xs text-surface-400">Window</label>
            <select value={rollW} onChange={e => setRollW(+e.target.value)} className="input-base text-sm py-1.5 w-36">
              {[{v:63,l:'63 (Quarter)'},{v:126,l:'126 (Half-yr)'},{v:252,l:'252 (1 Year)'},{v:504,l:'504 (2 Years)'}].map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
            </select>
            <label className="text-xs text-surface-400">Benchmark</label>
            <input value={bmTicker} onChange={e => setBm(e.target.value.toUpperCase())} className="input-base w-20 text-sm py-1.5"/>
            <button onClick={loadRolling} disabled={rollLoading} className="btn-primary text-sm">Compute</button>
          </div>
          {[{ opt:sharpeOpt, title:'Rolling Sharpe' },{ opt:volOpt, title:'Rolling Volatility %' },{ opt:betaOpt, title:`Rolling Beta vs ${bmTicker}` }].map(({ opt, title }) => (
            <ChartCard key={title} title={title} loading={rollLoading}>
              {opt && <EChart option={opt} style={{ height:200 }}/>}
            </ChartCard>
          ))}
        </div>
      )}
    </div>
  )
}
