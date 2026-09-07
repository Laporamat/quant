import { http } from './client'

export const dataApi = {
  available: () => http.get('/data/available'),
  prices:    (ticker: string, start?: string, end?: string, freq?: string) =>
    http.get(`/data/prices/${ticker}`, { params: { start_date: start, end_date: end, freq } }),
  universe:  (name: string) => http.get(`/data/universe/${name}`),
  universes: () => http.get<string[]>('/data/universes'),
  sectors:   (name: string) => http.get(`/data/universe/${name}/sectors`),
  download:  (tickers: string[], force = false) => http.post('/data/download', { tickers, force }),
  quickstart: () => http.post('/data/quickstart'),
  quickstartStatus: () => http.get('/data/quickstart/status'),
}
