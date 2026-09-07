/** Reusable UI primitives */
import { ReactNode, useState } from 'react'
import clsx from 'clsx'

// ── MetricCard ────────────────────────────────────────────────────────────────
interface MetricCardProps {
  title: string; value?: number | string | null
  format?: 'number' | 'percent' | 'currency' | 'raw'
  colorize?: boolean; suffix?: string; subtitle?: string
}
export function MetricCard({ title, value, format = 'number', colorize, suffix, subtitle }: MetricCardProps) {
  const fmt = () => {
    if (value === null || value === undefined) return '—'
    if (typeof value === 'string') return value
    if (isNaN(value as number)) return '—'
    const v = value as number
    if (format === 'percent')  return `${(v * 100).toFixed(2)}%`
    if (format === 'currency') return `$${v.toLocaleString('en-US', { maximumFractionDigits: 0 })}`
    if (format === 'raw')      return String(v)
    return v.toLocaleString('en-US', { maximumFractionDigits: 4 })
  }
  const colored = colorize && typeof value === 'number'
    ? (value >= 0 ? 'text-bull' : 'text-bear') : 'text-surface-100'

  return (
    <div className="metric-card animate-fade-in">
      <span className="text-xs font-medium text-surface-400 uppercase tracking-wider">{title}</span>
      <div className={clsx('text-2xl font-bold tabular-nums mt-1', colored)}>
        {fmt()}{suffix && <span className="text-sm text-surface-400 ml-1">{suffix}</span>}
      </div>
      {subtitle && <p className="text-xs text-surface-500 mt-0.5">{subtitle}</p>}
    </div>
  )
}

// ── ChartCard ─────────────────────────────────────────────────────────────────
interface ChartCardProps {
  title: string; subtitle?: string; loading?: boolean; error?: string | null
  children: ReactNode; toolbar?: ReactNode; onRefresh?: () => void; height?: number
}
export function ChartCard({ title, subtitle, loading, error, children, toolbar, onRefresh, height = 300 }: ChartCardProps) {
  return (
    <div className="chart-card glass p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-surface-100">{title}</h3>
          {subtitle && <p className="text-xs text-surface-400 mt-0.5">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-1">
          {toolbar}
          {onRefresh && (
            <button onClick={onRefresh} className="btn-ghost p-1.5 text-surface-400 hover:text-white">
              <svg className={clsx('w-4 h-4', loading && 'animate-spin')} fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"/>
              </svg>
            </button>
          )}
        </div>
      </div>
      {loading ? (
        <div className="animate-skeleton rounded-lg bg-surface-700/50" style={{ height }} />
      ) : error ? (
        <div className="flex flex-col items-center justify-center gap-2 text-surface-400" style={{ height }}>
          <p className="text-sm">{error}</p>
          {onRefresh && <button onClick={onRefresh} className="btn-ghost text-xs px-3 py-1">Retry</button>}
        </div>
      ) : children}
    </div>
  )
}

// ── DataTable ─────────────────────────────────────────────────────────────────
export interface Col {
  key: string; label: string; align?: 'left' | 'right' | 'center'
  format?: (v: unknown, row?: Record<string, unknown>) => string
  colorize?: boolean
  render?: (v: unknown, row: Record<string, unknown>) => ReactNode
}
interface DataTableProps {
  columns: Col[]; rows: Record<string, unknown>[]
  pageSize?: number; searchable?: boolean; loading?: boolean
}
export function DataTable({ columns, rows, pageSize = 20, searchable, loading }: DataTableProps) {
  const [q, setQ]       = useState('')
  const [page, setPage] = useState(0)
  const [sort, setSort] = useState<{ key: string; dir: 1 | -1 } | null>(null)

  const filtered = rows
    .filter(r => !q || Object.values(r).some(v => String(v).toLowerCase().includes(q.toLowerCase())))
    .sort((a, b) => {
      if (!sort) return 0
      const av = a[sort.key] as number, bv = b[sort.key] as number
      if (av == null) return 1; if (bv == null) return -1
      return (av > bv ? 1 : av < bv ? -1 : 0) * sort.dir
    })

  const total = Math.ceil(filtered.length / pageSize)
  const paged = filtered.slice(page * pageSize, (page + 1) * pageSize)

  const colorCls = (v: unknown) => typeof v === 'number' && !isNaN(v)
    ? v >= 0 ? 'text-bull' : 'text-bear' : ''

  return (
    <div className="flex flex-col gap-2">
      {searchable && (
        <input value={q} onChange={e => { setQ(e.target.value); setPage(0) }}
          placeholder="Search…"
          className="input-base max-w-xs text-xs py-1.5"/>
      )}
      <div className="overflow-x-auto rounded-lg border border-surface-700/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-800/50">
              {columns.map(c => (
                <th key={c.key}
                  onClick={() => setSort(s => s?.key === c.key ? { key: c.key, dir: s.dir === 1 ? -1 : 1 } : { key: c.key, dir: -1 })}
                  className={clsx('px-3 py-2.5 text-xs font-semibold text-surface-400 uppercase tracking-wider cursor-pointer select-none',
                    c.align === 'right' ? 'text-right' : c.align === 'center' ? 'text-center' : 'text-left')}>
                  {c.label} {sort?.key === c.key ? (sort.dir === 1 ? '↑' : '↓') : ''}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array(6).fill(0).map((_, i) => (
                <tr key={i} className="border-t border-surface-700/30">
                  {columns.map(c => (
                    <td key={c.key} className="px-3 py-2.5">
                      <div className="h-3 bg-surface-700 rounded animate-skeleton" style={{ width: `${50 + Math.random() * 30}%` }}/>
                    </td>
                  ))}
                </tr>
              ))
            ) : paged.length === 0 ? (
              <tr><td colSpan={columns.length} className="px-3 py-8 text-center text-surface-500">No data</td></tr>
            ) : (
              paged.map((row, i) => (
                <tr key={i} className="border-t border-surface-700/30 hover:bg-surface-700/20 transition-colors">
                  {columns.map(c => (
                    <td key={c.key}
                      className={clsx('px-3 py-2.5 tabular-nums',
                        c.align === 'right' ? 'text-right' : c.align === 'center' ? 'text-center' : '',
                        c.colorize ? colorCls(row[c.key]) : 'text-surface-200')}>
                      {c.render
                        ? c.render(row[c.key], row)
                        : c.format
                          ? c.format(row[c.key], row)
                          : String(row[c.key] ?? '—')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {total > 1 && (
        <div className="flex items-center justify-between text-xs text-surface-400">
          <span>{filtered.length} rows</span>
          <div className="flex items-center gap-1">
            <button onClick={() => setPage(p => Math.max(0, p-1))} disabled={page === 0} className="btn-ghost px-2 py-1 disabled:opacity-30">←</button>
            <span>{page+1}/{total}</span>
            <button onClick={() => setPage(p => Math.min(total-1, p+1))} disabled={page >= total-1} className="btn-ghost px-2 py-1 disabled:opacity-30">→</button>
          </div>
        </div>
      )}
    </div>
  )
}

// ── DateRange ─────────────────────────────────────────────────────────────────
import dayjs from 'dayjs'
const PRESETS = [
  { l:'1M', d:30 },{ l:'3M', d:90 },{ l:'6M', d:180 },{ l:'1Y', d:365 },
  { l:'3Y', d:1095 },{ l:'5Y', d:1825 },{ l:'10Y', d:3650 },{ l:'MAX', d:7300 },
]
interface DateRangePickerProps { start: string; end: string; onChange: (s: string, e: string) => void }
export function DateRangePicker({ start, end, onChange }: DateRangePickerProps) {
  const [active, setActive] = useState('5Y')
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <div className="flex items-center gap-1">
        {PRESETS.map(p => (
          <button key={p.l} onClick={() => { setActive(p.l); onChange(dayjs().subtract(p.d,'day').format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')) }}
            className={clsx('px-2.5 py-1 text-xs rounded-md font-medium transition-all',
              active === p.l ? 'bg-primary-600 text-white' : 'bg-surface-800 text-surface-400 hover:text-white')}>
            {p.l}
          </button>
        ))}
      </div>
      <div className="flex items-center gap-1.5 text-xs">
        <input type="date" value={start} onChange={e => { setActive(''); onChange(e.target.value, end) }}
          className="bg-surface-800 border border-surface-700 text-surface-200 rounded-md px-2 py-1 outline-none focus:border-primary-500"/>
        <span className="text-surface-500">→</span>
        <input type="date" value={end} onChange={e => { setActive(''); onChange(start, e.target.value) }}
          className="bg-surface-800 border border-surface-700 text-surface-200 rounded-md px-2 py-1 outline-none focus:border-primary-500"/>
      </div>
    </div>
  )
}

// ── TickerBadge ───────────────────────────────────────────────────────────────
export function TickerBadge({ ticker }: { ticker: string }) {
  return (
    <a href={`/ticker/${ticker}`}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-mono text-xs font-semibold bg-primary-600/15 text-primary-300 border border-primary-600/25 hover:bg-primary-600/30 transition-all">
      {ticker} ↗
    </a>
  )
}

// ── Loading Skeleton ──────────────────────────────────────────────────────────
export function Skeleton({ className }: { className?: string }) {
  return <div className={clsx('animate-skeleton bg-surface-700 rounded', className)} />
}

// ── Section Header ────────────────────────────────────────────────────────────
export function SectionHeader({ title, description, children }: { title: string; description?: string; children?: ReactNode }) {
  return (
    <div className="flex items-start justify-between mb-5">
      <div>
        <h2 className="text-lg font-bold text-surface-100">{title}</h2>
        {description && <p className="text-sm text-surface-400 mt-0.5">{description}</p>}
      </div>
      {children}
    </div>
  )
}
