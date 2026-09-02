import { http } from './client'
import type { StrategyMeta } from '@/types'

export const strategyApi = {
  list() {
    return http.get<StrategyMeta[]>('/strategies/')
  },

  get(name: string) {
    return http.get<StrategyMeta>(`/strategies/${name}`)
  },
}
