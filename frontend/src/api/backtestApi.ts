import { http } from './client'
import type {
  BacktestRequest, BacktestResponse, BacktestListItem,
  BacktestDetail, MonteCarloRequest, MonteCarloResponse,
} from '@/types'

export const backtestApi = {
  run(req: BacktestRequest) {
    return http.post<BacktestResponse>('/backtest/run', req)
  },

  list() {
    return http.get<BacktestListItem[]>('/backtest/list')
  },

  get(runId: string) {
    return http.get<BacktestDetail>(`/backtest/${runId}`)
  },

  reportUrl(runId: string) {
    return `/api/backtest/${runId}/report`
  },

  monteCarlo(req: MonteCarloRequest) {
    return http.post<MonteCarloResponse>('/backtest/monte-carlo', req)
  },
}
