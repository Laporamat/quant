import { http } from './client'

export const tradeApi = {
  signals:  (ticker: string, holdingDays = 5) =>
    http.get(`/trade/signals/${ticker}`, { params: { holding_days: holdingDays } }),

  scan: (tickers: string[], holdingDays = 5, minEdge = 40, maxVar = 3) =>
    http.post('/trade/scan', {
      tickers, holding_days: holdingDays,
      min_edge_score: minEdge, max_var_pct: maxVar,
    }),

  edge:  (ticker: string) => http.get(`/trade/edge/${ticker}`),

  setup: (ticker: string, capital = 100000, maxRiskPct = 1.0) =>
    http.get(`/trade/setup/${ticker}`, {
      params: { capital, max_risk_pct: maxRiskPct },
    }),
}
