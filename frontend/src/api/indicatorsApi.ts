import { http } from './client'

export const indicatorsApi = {
  ma(ticker: string, periods = '20,50,200', maType = 'sma', start?: string, end?: string) {
    return http.get(`/indicators/ma/${ticker}`, {
      params: { periods, ma_type: maType, start_date: start, end_date: end },
    })
  },

  rsi(ticker: string, period = 14, start?: string, end?: string) {
    return http.get<{ date: string[]; rsi: number[] }>(`/indicators/rsi/${ticker}`, {
      params: { period, start_date: start, end_date: end },
    })
  },

  macd(ticker: string, fast = 12, slow = 26, signal = 9, start?: string, end?: string) {
    return http.get(`/indicators/macd/${ticker}`, {
      params: { fast, slow, signal, start_date: start, end_date: end },
    })
  },

  bollinger(ticker: string, period = 20, stdDev = 2.0, start?: string, end?: string) {
    return http.get(`/indicators/bollinger/${ticker}`, {
      params: { period, std_dev: stdDev, start_date: start, end_date: end },
    })
  },

  atr(ticker: string, period = 14, start?: string, end?: string) {
    return http.get(`/indicators/atr/${ticker}`, {
      params: { period, start_date: start, end_date: end },
    })
  },

  adx(ticker: string, period = 14, start?: string, end?: string) {
    return http.get(`/indicators/adx/${ticker}`, {
      params: { period, start_date: start, end_date: end },
    })
  },

  all(ticker: string, start?: string, end?: string, tail = 300) {
    return http.get(`/indicators/all/${ticker}`, {
      params: { start_date: start, end_date: end, tail },
    })
  },
}
