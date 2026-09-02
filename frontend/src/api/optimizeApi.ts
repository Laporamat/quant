import { http } from './client'
import type { OptimizeRequest, OptimizeResult } from '@/types'

export const optimizeApi = {
  grid(req: OptimizeRequest) {
    return http.post<OptimizeResult>('/optimize/grid', req)
  },

  walkForward(req: Omit<OptimizeRequest, 'n_jobs'>, trainYears = 3, testYears = 1) {
    return http.post('/optimize/walk-forward', req, {
      params: { train_years: trainYears, test_years: testYears },
    })
  },
}
