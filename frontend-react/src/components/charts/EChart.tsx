import { useEffect, useRef, useCallback } from 'react'
import type { EChartsOption } from 'echarts'

// Lazy-load echarts modules
let echartsCore: typeof import('echarts/core') | null = null
const registeredComponents = new Set<string>()

async function getEcharts() {
  if (echartsCore) return echartsCore
  const [core, { CanvasRenderer },
    { LineChart, BarChart, CandlestickChart, HeatmapChart, ScatterChart, GaugeChart, RadarChart },
    { TitleComponent, TooltipComponent, GridComponent, LegendComponent,
      DataZoomComponent, MarkLineComponent, VisualMapComponent, AxisPointerComponent }
  ] = await Promise.all([
    import('echarts/core'),
    import('echarts/renderers'),
    import('echarts/charts'),
    import('echarts/components'),
  ])
  if (!registeredComponents.has('core')) {
    core.use([CanvasRenderer,
      LineChart, BarChart, CandlestickChart, HeatmapChart, ScatterChart, GaugeChart, RadarChart,
      TitleComponent, TooltipComponent, GridComponent, LegendComponent,
      DataZoomComponent, MarkLineComponent, VisualMapComponent, AxisPointerComponent])
    registeredComponents.add('core')
  }
  echartsCore = core
  return core
}

interface EChartProps {
  option:  EChartsOption
  style?:  React.CSSProperties
  className?: string
}

export default function EChart({ option, style, className }: EChartProps) {
  const divRef  = useRef<HTMLDivElement>(null)
  const chartRef = useRef<ReturnType<typeof import('echarts/core')['init']> | null>(null)

  const init = useCallback(async () => {
    if (!divRef.current) return
    const ec = await getEcharts()
    if (chartRef.current) {
      chartRef.current.setOption(option, { notMerge: false, lazyUpdate: true })
      return
    }
    const chart = ec.init(divRef.current, 'dark-custom')
    chart.setOption(option)
    chartRef.current = chart as never
  }, [option])

  useEffect(() => { init() }, [init])

  // Resize observer
  useEffect(() => {
    const obs = new ResizeObserver(() => (chartRef.current as any)?.resize?.())
    if (divRef.current) obs.observe(divRef.current)
    return () => obs.disconnect()
  }, [])

  useEffect(() => () => { (chartRef.current as any)?.dispose?.() }, [])

  return <div ref={divRef} style={{ width: '100%', height: 300, ...style }} className={className} />
}

// ── Shared chart theme helpers ─────────────────────────────────────────────────
export const C = {
  COLORS: ['#3b82f6','#22c55e','#f59e0b','#ef4444','#a78bfa','#06b6d4','#f97316','#ec4899'],
  TOOLTIP: { trigger:'axis' as const, backgroundColor:'#1e293b', borderColor:'#334155',
             borderWidth:1, textStyle:{ color:'#f1f5f9', fontSize:12 } },
  LEGEND:  { textStyle:{ color:'#94a3b8', fontSize:11 }, icon:'circle', itemWidth:8, itemHeight:8 },
  GRID:    { left:'1%', right:'2%', top:'8%', bottom:'12%', containLabel:true },
  XAXIS:   { type:'category' as const, axisLine:{ lineStyle:{ color:'#334155' } },
             axisTick:{ show:false }, axisLabel:{ color:'#64748b', fontSize:11 }, splitLine:{ show:false } },
  YAXIS:   { type:'value' as const, axisLine:{ show:false }, axisTick:{ show:false },
             axisLabel:{ color:'#64748b', fontSize:11 },
             splitLine:{ lineStyle:{ color:'#1e293b', type:'dashed' as const } } },
  DATAZONE:[
    { type:'inside', xAxisIndex:0, filterMode:'none' as const },
    { type:'slider', xAxisIndex:0, height:20, bottom:2, borderColor:'#334155',
      fillerColor:'rgba(59,130,246,0.12)', handleStyle:{ color:'#3b82f6' }, textStyle:{ color:'#64748b' } },
  ],
}

export function rebase(arr: number[]): number[] {
  if (!arr.length || arr[0] === 0) return arr
  const b = arr[0]; return arr.map(v => +(v/b).toFixed(6))
}
export function pctChange(arr: number[]): number[] {
  const out: number[] = []
  for (let i = 1; i < arr.length; i++) out.push((arr[i]-arr[i-1])/arr[i-1])
  return out
}
