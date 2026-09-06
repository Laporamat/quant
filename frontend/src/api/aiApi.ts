import { http } from './client'

export interface ChatMessage { role: 'user' | 'assistant' | 'system'; content: string }

export type Provider = 'auto' | 'openai' | 'anthropic' | 'rule_based'

export interface ProviderInfo {
  id: string; name: string; available: boolean; icon: string
}

export interface BenchmarkResult {
  provider: string; model?: string; available: boolean
  content:  string | null; latency_ms: number
  error:    string | null; char_count?: number
}

export const aiApi = {
  /** Chat — provider: auto | openai | anthropic | rule_based */
  chat: (message: string, history: ChatMessage[] = [], ticker?: string, provider: Provider = 'auto') =>
    http.post<{ role: string; content: string; provider: string; ticker?: string }>('/ai/chat', {
      message, history, ticker, provider,
    }),

  /** Benchmark — run all 3 providers on the same question */
  benchmark: (message: string, ticker?: string) =>
    http.post<{
      question: string; ticker?: string; market_ctx: string
      results: BenchmarkResult[]
    }>('/ai/benchmark', { message, ticker }),

  /** Available providers */
  providers: () =>
    http.get<{ providers: ProviderInfo[] }>('/ai/providers'),

  suggestions: (ticker?: string, context?: string) =>
    http.get<{ suggestions: string[] }>('/ai/suggestions', {
      params: { ticker, context },
    }),

  marketContext: (ticker: string) =>
    http.get<{ ticker: string; context: string }>(`/ai/context/${ticker}`),

  /** SSE streaming URL */
  streamUrl: (message: string, ticker?: string, provider: Provider = 'auto') => {
    const p = new URLSearchParams({ message, provider })
    if (ticker) p.append('ticker', ticker)
    return `/api/ai/stream?${p}`
  },
}
