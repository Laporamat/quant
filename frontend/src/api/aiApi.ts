import { http } from './client'

export interface ChatMessage { role: 'user' | 'assistant' | 'system'; content: string }

export const aiApi = {
  chat: (message: string, history: ChatMessage[] = [], ticker?: string) =>
    http.post<{ role: string; content: string; engine: string; ticker?: string }>('/ai/chat', {
      message, history, ticker,
    }),

  suggestions: (ticker?: string, context?: string) =>
    http.get<{ suggestions: string[] }>('/ai/suggestions', {
      params: { ticker, context },
    }),

  marketContext: (ticker: string) =>
    http.get<{ ticker: string; context: string }>(`/ai/context/${ticker}`),

  /** SSE streaming — returns EventSource URL */
  streamUrl: (message: string, ticker?: string) => {
    const params = new URLSearchParams({ message })
    if (ticker) params.append('ticker', ticker)
    return `/api/ai/stream?${params}`
  },
}
