import { http } from './client'
import type { BubbleResponse } from '@/types'

export const bubbleApi = {
  analyze(ticker: string, start?: string, end?: string) {
    return http.get<BubbleResponse>(`/stats/bubble/${ticker}`, {
      params: { start_date: start, end_date: end },
    })
  },
}
