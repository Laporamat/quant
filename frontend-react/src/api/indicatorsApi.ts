import { http } from './client'
export const indicatorsApi = {
  ma:        (t: string, periods = '20,50,200', ma_type = 'sma', s?: string, e?: string) =>
    http.get(`/indicators/ma/${t}`, { params: { periods, ma_type, start_date: s, end_date: e } }),
  rsi:       (t: string, period = 14, s?: string, e?: string) =>
    http.get(`/indicators/rsi/${t}`, { params: { period, start_date: s, end_date: e } }),
  macd:      (t: string, fast = 12, slow = 26, signal = 9, s?: string, e?: string) =>
    http.get(`/indicators/macd/${t}`, { params: { fast, slow, signal, start_date: s, end_date: e } }),
  bollinger: (t: string, period = 20, std_dev = 2.0, s?: string, e?: string) =>
    http.get(`/indicators/bollinger/${t}`, { params: { period, std_dev, start_date: s, end_date: e } }),
}
