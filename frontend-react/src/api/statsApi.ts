import { http } from './client'

const p = (start?: string, end?: string) => ({ params: { start_date: start, end_date: end } })

export const statsApi = {
  descriptive:  (t: string, s?: string, e?: string) => http.get(`/stats/descriptive/${t}`,  p(s,e)),
  returns:      (t: string, s?: string, e?: string) => http.get(`/stats/returns/${t}`,      p(s,e)),
  risk:         (t: string, s?: string, e?: string) => http.get(`/stats/risk/${t}`,         p(s,e)),
  drawdown:     (t: string, s?: string, e?: string) => http.get(`/stats/drawdown/${t}`,     p(s,e)),
  correlation:  (tickers: string[], s?: string, e?: string, method = 'pearson') =>
    http.post('/stats/correlation', { tickers, start_date: s, end_date: e, method }),
  regime:       (t: string, n = 3, s?: string, e?: string) =>
    http.get(`/stats/regime/${t}`, { params: { n_states: n, start_date: s, end_date: e } }),
  seasonality:  (t: string, s?: string, e?: string) => http.get(`/stats/seasonality/${t}`, p(s,e)),
  distribution: (t: string, s?: string, e?: string) => http.get(`/stats/distribution/${t}`,p(s,e)),
  bubble:       (t: string, s?: string, e?: string) => http.get(`/stats/bubble/${t}`,      p(s,e)),
  bubbleScan:   (tickers: string[], s?: string, e?: string) =>
    http.post('/stats/bubble/scan', tickers, { params: { start_date: s, end_date: e } }),
}
