import { http } from './client'
export const optimizeApi = {
  grid:        (req: Record<string, unknown>) => http.post('/optimize/grid', req),
  walkForward: (req: Record<string, unknown>, trainYears = 3, testYears = 1) =>
    http.post('/optimize/walk-forward', req, { params: { train_years: trainYears, test_years: testYears } }),
}
export const strategyApi = {
  list: () => http.get('/strategies/'),
  get:  (name: string) => http.get(`/strategies/${name}`),
}
