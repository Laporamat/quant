import { http } from './client'

export interface OptionRequest {
  spot: number; strike: number; volatility: number
  time_to_expiry: number; risk_free?: number; option_type?: 'call' | 'put'
}
export interface BondRequest {
  face_value?: number; coupon_rate: number; ytm: number
  frequency?: number; periods?: number
}
export interface ProbabilityRequest {
  spot: number; volatility: number; drift?: number
  horizon_days?: number; confidence?: number; targets?: number[]
}
export interface RiskRequest {
  daily_sigma: number; daily_mu?: number
  confidence?: number; win_probability?: number; win_loss_ratio?: number
}
export interface FullRequest {
  spot: number; volatility: number; drift?: number; risk_free?: number
  horizon_days?: number; recent_returns?: number[]
  win_probability?: number; win_loss_ratio?: number
}
export interface ChainRequest {
  spot: number; volatility: number; time_to_expiry: number
  risk_free?: number; strikes?: number[]
}

export const daytradeApi = {
  option:      (r: OptionRequest)      => http.post('/daytrade/option', r),
  bond:        (r: BondRequest)        => http.post('/daytrade/bond', r),
  probability: (r: ProbabilityRequest) => http.post('/daytrade/probability', r),
  risk:        (r: RiskRequest)        => http.post('/daytrade/risk', r),
  chain:       (r: ChainRequest)       => http.post('/daytrade/chain', r),
  full:        (r: FullRequest)        => http.post('/daytrade/full', r),
  realtime:    (ticker: string, horizonDays = 5, riskFree = 0.05) =>
    http.get(`/daytrade/realtime/${ticker}`, {
      params: { horizon_days: horizonDays, risk_free: riskFree },
    }),
}
