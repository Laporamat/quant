import { http } from './client'
export interface ChatMessage { role: 'user' | 'assistant'; content: string }
export const aiApi = {
  chat:        (message: string, history: ChatMessage[] = [], ticker?: string, provider = 'auto') =>
    http.post('/ai/chat', { message, history, ticker, provider }),
  suggestions: (ticker?: string) => http.get('/ai/suggestions', { params: { ticker } }),
  context:     (ticker: string) => http.get(`/ai/context/${ticker}`),
  providers:   () => http.get('/ai/providers'),
  benchmark:   (message: string, ticker?: string) => http.post('/ai/benchmark', { message, ticker }),
  streamUrl:   (message: string, ticker?: string, provider = 'auto') => {
    const p = new URLSearchParams({ message, provider })
    if (ticker) p.append('ticker', ticker)
    return `/api/ai/stream?${p}`
  },
}
