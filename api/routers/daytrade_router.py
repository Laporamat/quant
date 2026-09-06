"""
api/routers/daytrade_router.py
──────────────────────────────
Day-trading quantitative analysis powered by the OCaml probability engine.

Endpoints:
  POST /daytrade/option        — Black-Scholes price + Greeks + implied vol
  POST /daytrade/bond          — Bond price, duration, convexity, DV01
  POST /daytrade/probability   — GBM probability cone + target probabilities
  POST /daytrade/risk          — VaR, CVaR, Kelly criterion, Sharpe
  POST /daytrade/regime        — Bayesian bull/bear probability
  POST /daytrade/chain         — Full option chain (multi-strike)
  POST /daytrade/full          — Combined: cone + risk + regime (one call)
  GET  /daytrade/realtime/{ticker}  — Live intraday analysis from stored prices
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

# Add ocaml_engine to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ocaml_engine"))
from quant_probability import compute_daytrade, prob_cone, bayesian_regime_prob  # type: ignore

from api.dependencies import get_loader
from data.loader import DataLoader

router = APIRouter(prefix="/daytrade", tags=["daytrade"])


# ── Pydantic request models ───────────────────────────────────────────────────

class OptionRequest(BaseModel):
    spot:            float = Field(..., gt=0,  description="Current underlying price")
    strike:          float = Field(..., gt=0,  description="Option strike price")
    volatility:      float = Field(..., gt=0,  description="Implied/historical volatility (annualised)")
    time_to_expiry:  float = Field(..., gt=0,  description="Time to expiry in years (e.g. 0.0833 = 1 month)")
    risk_free:       float = Field(0.05,       description="Risk-free rate (annual)")
    option_type:     str   = Field("call",     description="'call' or 'put'")
    use_binomial:    bool  = Field(True,       description="Also price via CRR binomial tree (200 steps)")

class BondRequest(BaseModel):
    face_value:   float = Field(1000.0, description="Face/par value")
    coupon_rate:  float = Field(...,    description="Annual coupon rate (e.g. 0.05 = 5%)")
    ytm:          float = Field(...,    description="Yield to maturity (annual, e.g. 0.04)")
    frequency:    int   = Field(2,      description="Coupon payments per year")
    periods:      int   = Field(20,     description="Total number of coupon periods")

class ProbabilityRequest(BaseModel):
    spot:            float       = Field(...,    gt=0)
    volatility:      float       = Field(...,    gt=0,  description="Annualised vol (e.g. 0.25)")
    drift:           float       = Field(0.10,          description="Expected annual drift (e.g. 0.10 = 10%)")
    horizon_days:    int         = Field(30,            description="Forecast horizon in trading days")
    confidence:      float       = Field(0.95,          description="Confidence level for cone")
    targets:         List[float] = Field(default_factory=list, description="Target prices to compute P(reach)")

class RiskRequest(BaseModel):
    daily_sigma:      float = Field(..., gt=0, description="Daily return std dev (e.g. 0.015)")
    daily_mu:         float = Field(0.0,       description="Daily expected return")
    confidence:       float = Field(0.95,      description="VaR confidence level")
    win_probability:  float = Field(0.55,      description="Historical win rate for Kelly")
    win_loss_ratio:   float = Field(1.5,       description="Avg win / avg loss for Kelly")

class RegimeRequest(BaseModel):
    recent_returns: List[float] = Field(..., min_length=5,
                                        description="Last N daily returns (e.g. 20 days)")
    prior_bull:     float = Field(0.6, description="Prior P(bull market)")
    bull_params:    Dict[str, float] = Field(
        default={"mu": 0.0006, "sigma": 0.008},
        description="Bull regime: daily mu and sigma"
    )
    bear_params:    Dict[str, float] = Field(
        default={"mu": -0.001, "sigma": 0.018},
        description="Bear regime: daily mu and sigma"
    )

class ChainRequest(BaseModel):
    spot:           float       = Field(...,    gt=0)
    volatility:     float       = Field(...,    gt=0)
    time_to_expiry: float       = Field(...,    gt=0)
    risk_free:      float       = Field(0.05)
    strikes:        List[float] = Field(default_factory=list,
                                        description="Leave empty for auto ATM±10 strikes")

class FullRequest(BaseModel):
    spot:            float       = Field(..., gt=0)
    volatility:      float       = Field(..., gt=0, description="Annualised vol")
    drift:           float       = Field(0.10)
    risk_free:       float       = Field(0.05)
    horizon_days:    int         = Field(5, description="1-5 for day-trading")
    recent_returns:  List[float] = Field(default_factory=list)
    win_probability: float       = Field(0.55)
    win_loss_ratio:  float       = Field(1.5)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe(v: Any) -> Any:
    """Convert NaN/Inf to None for JSON serialisation."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v

def _clean(d: Any) -> Any:
    if isinstance(d, dict):
        return {k: _clean(v) for k, v in d.items()}
    if isinstance(d, list):
        return [_clean(x) for x in d]
    return _safe(d)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/option")
async def price_option(req: OptionRequest):
    """
    Black-Scholes + CRR binomial option pricing with full Greeks.
    Engine: OCaml (if binary present) or Python port.
    """
    result = compute_daytrade({
        "mode":           "option",
        "spot":           req.spot,
        "strike":         req.strike,
        "risk_free":      req.risk_free,
        "volatility":     req.volatility,
        "time_to_expiry": req.time_to_expiry,
        "option_type":    req.option_type,
    })
    return _clean(result)


@router.post("/bond")
async def price_bond(req: BondRequest):
    """Bond dirty price, modified duration, convexity and DV01."""
    result = compute_daytrade({
        "mode":        "bond",
        "face_value":  req.face_value,
        "coupon_rate": req.coupon_rate,
        "ytm":         req.ytm,
        "frequency":   req.frequency,
        "periods":     req.periods,
    })
    return _clean(result)


@router.post("/probability")
async def probability_analysis(req: ProbabilityRequest):
    """
    GBM probability cone + target price probabilities.
    Returns daily lower/expected/upper bands for charting.
    """
    result = compute_daytrade({
        "mode":          "probability",
        "spot":          req.spot,
        "drift":         req.drift,
        "volatility":    req.volatility,
        "horizon_days":  req.horizon_days,
        "confidence":    req.confidence,
        "targets":       req.targets,
    })
    return _clean(result)


@router.post("/risk")
async def risk_metrics(req: RiskRequest):
    """VaR, CVaR, Kelly criterion, Sharpe ratio."""
    result = compute_daytrade({
        "mode":             "risk",
        "daily_mu":         req.daily_mu,
        "daily_sigma":      req.daily_sigma,
        "confidence":       req.confidence,
        "win_probability":  req.win_probability,
        "win_loss_ratio":   req.win_loss_ratio,
    })
    return _clean(result)


@router.post("/regime")
async def regime_probability(req: RegimeRequest):
    """Bayesian bull/bear regime probability from recent returns."""
    result = compute_daytrade({
        "mode":            "regime",
        "prior_bull":      req.prior_bull,
        "bull_params":     req.bull_params,
        "bear_params":     req.bear_params,
        "recent_returns":  req.recent_returns,
    })
    return _clean(result)


@router.post("/chain")
async def option_chain(req: ChainRequest):
    """Full option chain: call+put price, delta, gamma, theta, vega for multiple strikes."""
    result = compute_daytrade({
        "mode":           "chain",
        "spot":           req.spot,
        "risk_free":      req.risk_free,
        "volatility":     req.volatility,
        "time_to_expiry": req.time_to_expiry,
        "strikes":        req.strikes,
    })
    return _clean(result)


@router.post("/full")
async def full_analysis(req: FullRequest):
    """
    Combined day-trading analysis in a single call:
    - Probability cone (GBM, 5-day horizon)
    - Bayesian regime probability
    - VaR / CVaR
    - ATM straddle price (cost of uncertainty)
    - Break-even prices
    """
    result = compute_daytrade({
        "mode":             "daytrade_full",
        "spot":             req.spot,
        "volatility":       req.volatility,
        "drift":            req.drift,
        "risk_free":        req.risk_free,
        "horizon_days":     req.horizon_days,
        "recent_returns":   req.recent_returns,
        "win_probability":  req.win_probability,
        "win_loss_ratio":   req.win_loss_ratio,
    })
    return _clean(result)


@router.get("/realtime/{ticker}")
async def realtime_analysis(
    ticker:         str,
    horizon_days:   int   = Query(5,    ge=1, le=60),
    confidence:     float = Query(0.95, ge=0.5, le=0.999),
    risk_free:      float = Query(0.05),
    loader:         DataLoader = Depends(get_loader),
):
    """
    Live intraday day-trading analysis using stored price data.
    Computes volatility from recent 30-day history, then runs full analysis.
    """
    import pandas as pd

    df = loader.load(ticker.upper())
    if df.empty:
        raise HTTPException(404, f"No data for {ticker}")

    # Compute stats from last 252 days
    hist   = df["close"].tail(252)
    rets   = hist.pct_change().dropna()
    sigma  = float(rets.std() * (252 ** 0.5))          # annualised vol
    mu     = float(rets.mean() * 252)                   # annualised drift
    spot   = float(hist.iloc[-1])
    recent = rets.tail(20).tolist()                     # last 20 returns for Bayesian

    # Daily stats
    d_sigma = float(rets.std())
    d_mu    = float(rets.mean())

    # Full OCaml/Python analysis
    result = compute_daytrade({
        "mode":            "daytrade_full",
        "spot":            spot,
        "volatility":      sigma,
        "drift":           mu,
        "risk_free":       risk_free,
        "horizon_days":    horizon_days,
        "recent_returns":  recent,
    })

    # Enrich with historical context
    result["ticker"]          = ticker.upper()
    result["spot"]            = round(spot, 4)
    result["ann_volatility"]  = round(sigma * 100, 2)
    result["ann_drift"]       = round(mu * 100, 2)
    result["daily_sigma_pct"] = round(d_sigma * 100, 3)

    # Win rate from historical data (up days)
    win_rate = float((rets > 0).mean())
    avg_win  = float(rets[rets > 0].mean()) if (rets > 0).any() else 0
    avg_loss = float(abs(rets[rets < 0].mean())) if (rets < 0).any() else 1e-6
    wlr      = avg_win / avg_loss if avg_loss > 0 else 1.0

    from quant_probability import kelly_criterion, var_parametric, cvar_parametric, sharpe
    result["win_rate"]    = round(win_rate, 4)
    result["kelly_pct"]   = round(max(0.0, kelly_criterion(win_rate, wlr)) * 100, 2)
    result["sharpe"]      = round(sharpe(d_mu, d_sigma), 4)

    # Option chain: ATM ± 5% strikes, 30-day expiry
    t_exp   = 30 / 252.0
    strikes = [round(spot * (1 + i * 0.01), 2) for i in range(-5, 6)]
    from quant_probability import option_chain
    result["option_chain"] = option_chain(spot, risk_free, sigma, t_exp, strikes)

    return _clean(result)
