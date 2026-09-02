/** Shared ECharts option fragments for consistent dark-mode styling */

export const CHART_COLORS = [
  '#3b82f6', '#22c55e', '#f59e0b', '#ef4444',
  '#a78bfa', '#06b6d4', '#f97316', '#ec4899',
  '#84cc16', '#14b8a6',
]

export const BASE_TOOLTIP = {
  trigger:          'axis' as const,
  backgroundColor:  '#1e293b',
  borderColor:      '#334155',
  borderWidth:      1,
  textStyle:        { color: '#f1f5f9', fontSize: 12 },
  axisPointer:      { type: 'cross' as const, lineStyle: { color: '#334155' } },
}

export const BASE_LEGEND = {
  textStyle: { color: '#94a3b8', fontSize: 12 },
  icon:      'circle',
  itemWidth: 8,
  itemHeight: 8,
}

export const BASE_GRID = {
  left: '1%', right: '2%', top: '8%', bottom: '12%', containLabel: true,
}

export const BASE_XAXIS = {
  type:        'category' as const,
  axisLine:    { lineStyle: { color: '#334155' } },
  axisTick:    { show: false },
  axisLabel:   { color: '#64748b', fontSize: 11 },
  splitLine:   { show: false },
}

export const BASE_YAXIS = {
  type:        'value' as const,
  axisLine:    { show: false },
  axisTick:    { show: false },
  axisLabel:   { color: '#64748b', fontSize: 11 },
  splitLine:   { lineStyle: { color: '#1e293b', type: 'dashed' as const } },
}

export const BASE_DATAZONE = [{
  type:       'inside',
  xAxisIndex: 0,
  filterMode: 'none',
}, {
  type:       'slider',
  xAxisIndex: 0,
  height:     20,
  bottom:     2,
  borderColor: '#334155',
  fillerColor: 'rgba(59,130,246,0.12)',
  handleStyle: { color: '#3b82f6' },
  dataBackground: { lineStyle: { color: '#334155' }, areaStyle: { color: 'rgba(59,130,246,0.06)' } },
  textStyle:  { color: '#64748b' },
}]

/** Rebase an array of numbers so index-0 = 1.0 */
export function rebase(arr: number[]): number[] {
  if (!arr.length || arr[0] === 0) return arr
  const base = arr[0]
  return arr.map((v) => +(v / base).toFixed(6))
}

/** Compute rolling window stats over an array */
export function rollingFn(
  arr: number[],
  window: number,
  fn: (slice: number[]) => number
): (number | null)[] {
  return arr.map((_, i) => {
    if (i < window - 1) return null
    return fn(arr.slice(i - window + 1, i + 1))
  })
}

/** Sharpe from daily returns array (annualised) */
export function sharpeSeries(returns: number[], window = 252): (number | null)[] {
  return rollingFn(returns, window, (sl) => {
    const mean = sl.reduce((a, b) => a + b, 0) / sl.length
    const std  = Math.sqrt(sl.reduce((a, b) => a + (b - mean) ** 2, 0) / sl.length)
    if (std === 0) return 0
    return +((mean / std) * Math.sqrt(252)).toFixed(4)
  })
}

/** Annualised volatility */
export function volSeries(returns: number[], window = 252): (number | null)[] {
  return rollingFn(returns, window, (sl) => {
    const mean = sl.reduce((a, b) => a + b, 0) / sl.length
    const variance = sl.reduce((a, b) => a + (b - mean) ** 2, 0) / sl.length
    return +(Math.sqrt(variance * 252) * 100).toFixed(4)
  })
}

/** Price returns array from price array */
export function priceToReturns(prices: number[]): number[] {
  const out: number[] = []
  for (let i = 1; i < prices.length; i++) {
    out.push((prices[i] - prices[i - 1]) / prices[i - 1])
  }
  return out
}
