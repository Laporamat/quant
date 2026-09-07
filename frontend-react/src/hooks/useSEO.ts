import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

interface SEOProps {
  title:       string
  description: string
  image?:      string
  noindex?:    boolean
  schema?:     Record<string, unknown>
}

const BASE = 'QuantDash'
const DEFAULT_DESC = 'วิเคราะห์หุ้นเชิงปริมาณด้วยข้อมูลย้อนหลัง 20 ปี — OCaml Engine · Python ML · Backtest · AI Chat'

export function useSEO({ title, description, image, noindex, schema }: SEOProps) {
  const loc = useLocation()
  const fullTitle = title === BASE ? BASE : `${title} — ${BASE}`

  useEffect(() => {
    // Title
    document.title = fullTitle

    // Meta helpers
    function setMeta(sel: string, content: string) {
      let el = document.querySelector(sel) as HTMLMetaElement | null
      if (!el) {
        el = document.createElement('meta')
        if (sel.startsWith('[name')) el.setAttribute('name', sel.match(/name="([^"]+)"/)![1])
        else if (sel.startsWith('[property')) el.setAttribute('property', sel.match(/property="([^"]+)"/)![1])
        document.head.appendChild(el)
      }
      el.setAttribute('content', content)
    }

    setMeta('[name="description"]',           description)
    setMeta('[name="robots"]',                noindex ? 'noindex,nofollow' : 'index,follow')
    setMeta('[property="og:title"]',          fullTitle)
    setMeta('[property="og:description"]',    description)
    setMeta('[property="og:url"]',            window.location.href)
    setMeta('[property="og:image"]',          image ?? '/og-image.png')
    setMeta('[name="twitter:title"]',         fullTitle)
    setMeta('[name="twitter:description"]',   description)

    // Canonical
    let canon = document.querySelector('link[rel="canonical"]') as HTMLLinkElement | null
    if (!canon) { canon = document.createElement('link'); canon.rel = 'canonical'; document.head.appendChild(canon) }
    canon.href = `https://quantdash.app${loc.pathname}`

    // Inject/update JSON-LD schema
    if (schema) {
      const id = 'page-schema'
      let existing = document.getElementById(id)
      if (!existing) {
        existing = document.createElement('script')
        existing.id = id
        existing.setAttribute('type', 'application/ld+json')
        document.head.appendChild(existing)
      }
      existing.textContent = JSON.stringify(schema)
    }

    // Fire GA SPA pageview
    window.dispatchEvent(new CustomEvent('routechange', { detail: { title: fullTitle, url: window.location.href } }))
  }, [fullTitle, description, loc.pathname, image, noindex])
}

// Breadcrumb schema helper
export function breadcrumbSchema(crumbs: { name: string; url: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: crumbs.map((c, i) => ({
      '@type': 'ListItem',
      position: i + 1,
      name: c.name,
      item: `https://quantdash.app${c.url}`,
    })),
  }
}
