import { Link, useLocation } from 'react-router-dom'

const LABELS: Record<string, string> = {
  dashboard: 'Dashboard', ticker: 'Ticker Dive', compare: 'Compare Assets',
  'stats-hub': 'Stats Hub', bubble: 'Bubble Detection', backtest: 'Backtest Lab',
  optimizer: 'Optimizer', 'monte-carlo': 'Monte Carlo', trade: 'Edge Trading',
  ai: 'QuantAI', profile: 'Profile', about: 'About', faq: 'FAQ',
  privacy: 'Privacy Policy', terms: 'Terms', 'case-studies': 'Case Studies',
  'thank-you': 'Thank You',
}

interface BreadcrumbsProps { extra?: { label: string; href?: string }[] }

export default function Breadcrumbs({ extra }: BreadcrumbsProps) {
  const loc    = useLocation()
  const parts  = loc.pathname.split('/').filter(Boolean)

  const crumbs = [
    { label: 'Home', href: '/' },
    ...parts.map((p, i) => ({
      label: LABELS[p] ?? p.charAt(0).toUpperCase() + p.slice(1).replace(/-/g, ' '),
      href:  '/' + parts.slice(0, i + 1).join('/'),
    })),
    ...(extra ?? []),
  ]

  if (crumbs.length <= 1) return null

  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-surface-500 mb-4">
      {crumbs.map((c, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <span className="text-surface-700">/</span>}
          {i < crumbs.length - 1 && c.href ? (
            <Link to={c.href} className="hover:text-primary-400 transition-colors">{c.label}</Link>
          ) : (
            <span className="text-surface-300 font-medium">{c.label}</span>
          )}
        </span>
      ))}
    </nav>
  )
}
