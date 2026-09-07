import { http } from './client'
export const backtestApi = {
  run:   (req: Record<string, unknown>) => http.post('/backtest/run', req),
  list:  () => http.get('/backtest/list'),
  get:   (id: string) => http.get(`/backtest/${id}`),
  report:(id: string) => `/api/backtest/${id}/report`,
  monteCarlo: (req: Record<string, unknown>) => http.post('/backtest/monte-carlo', req),
}
