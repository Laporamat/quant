import { http } from './client'
export const tradeApi = {
  signals: (ticker: string, holdingDays = 5) =>
    http.get(`/trade/signals/${ticker}`, { params: { holding_days: holdingDays } }),
  scan:    (tickers: string[], holdingDays = 5, minEdge = 40, maxVar = 3) =>
    http.post('/trade/scan', { tickers, holding_days: holdingDays, min_edge_score: minEdge, max_var_pct: maxVar }),
  edge:    (ticker: string) => http.get(`/trade/edge/${ticker}`),
  setup:   (ticker: string, capital = 100000, maxRisk = 1.0) =>
    http.get(`/trade/setup/${ticker}`, { params: { capital, max_risk_pct: maxRisk } }),
}
export const daytradeApi = {
  realtime: (ticker: string, horizonDays = 5) =>
    http.get(`/daytrade/realtime/${ticker}`, { params: { horizon_days: horizonDays } }),
  option:   (req: Record<string, unknown>) => http.post('/daytrade/option', req),
  bond:     (req: Record<string, unknown>) => http.post('/daytrade/bond', req),
  chain:    (req: Record<string, unknown>) => http.post('/daytrade/chain', req),
}
