import { http } from './client'
import type { PriceResponse, TickerInfo, UniverseResponse, SectorBreakdown } from '@/types'

export const dataApi = {
  /** Download / refresh OHLCV for a list of tickers */
  download(tickers: string[], force = false) {
    return http.post<{ success: string[]; failed: string[]; total: number; message: string }>(
      '/data/download', { tickers, force }
    )
  },

  /** List all tickers with data on disk */
  available() {
    return http.get<TickerInfo[]>('/data/available')
  },

  /** OHLCV bars for a ticker */
  prices(ticker: string, start?: string, end?: string, freq?: string) {
    return http.get<PriceResponse>(`/data/prices/${ticker}`, {
      params: { start_date: start, end_date: end, freq },
    })
  },

  /** Metadata for a ticker */
  status(ticker: string) {
    return http.get<TickerInfo>(`/data/status/${ticker}`)
  },

  /** List universe names */
  universes() {
    return http.get<string[]>('/data/universes')
  },

  /** Tickers in a universe */
  universe(name: string) {
    return http.get<UniverseResponse>(`/data/universe/${name}`)
  },

  /** Sector breakdown for a universe */
  sectors(name: string) {
    return http.get<SectorBreakdown>(`/data/universe/${name}/sectors`)
  },
}
