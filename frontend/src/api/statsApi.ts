import { http } from './client'
import type {
  DescriptiveStats, ReturnSummary, RiskMetrics,
  DrawdownResponse, CorrelationResponse,
  RegimeResponse, SeasonalityResponse, DistributionResponse,
} from '@/types'

export const statsApi = {
  descriptive(ticker: string, start?: string, end?: string) {
    return http.get<DescriptiveStats>(`/stats/descriptive/${ticker}`, {
      params: { start_date: start, end_date: end },
    })
  },

  returns(ticker: string, start?: string, end?: string) {
    return http.get<ReturnSummary>(`/stats/returns/${ticker}`, {
      params: { start_date: start, end_date: end },
    })
  },

  risk(ticker: string, start?: string, end?: string) {
    return http.get<RiskMetrics>(`/stats/risk/${ticker}`, {
      params: { start_date: start, end_date: end },
    })
  },

  drawdown(ticker: string, start?: string, end?: string) {
    return http.get<DrawdownResponse>(`/stats/drawdown/${ticker}`, {
      params: { start_date: start, end_date: end },
    })
  },

  correlation(tickers: string[], start?: string, end?: string, method = 'pearson') {
    return http.post<CorrelationResponse>('/stats/correlation', {
      tickers, start_date: start, end_date: end, method,
    })
  },

  regime(ticker: string, nStates = 3, start?: string, end?: string) {
    return http.get<RegimeResponse>(`/stats/regime/${ticker}`, {
      params: { n_states: nStates, start_date: start, end_date: end },
    })
  },

  seasonality(ticker: string, start?: string, end?: string) {
    return http.get<SeasonalityResponse>(`/stats/seasonality/${ticker}`, {
      params: { start_date: start, end_date: end },
    })
  },

  distribution(ticker: string, start?: string, end?: string) {
    return http.get<DistributionResponse>(`/stats/distribution/${ticker}`, {
      params: { start_date: start, end_date: end },
    })
  },

  /** Rolling stats computed client-side from price data */
  async rolling(ticker: string, window = 252, start?: string, end?: string) {
    const res = await http.get<{ date: string[]; close: number[] }>(`/data/prices/${ticker}`, {
      params: { start_date: start, end_date: end },
    })
    return res
  },
}
