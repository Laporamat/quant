"""
api/routers/trade_signal_router.py
────────────────────────────────────
Statistical edge trading signals — กำไรน้อยแต่ต่อเนื่อง ขาดทุนน้อยที่สุด

Philosophy:
  - ใช้ข้อมูลอดีต 20 ปีคำนวณ edge ทางสถิติของแต่ละหุ้น
  - เลือก setup ที่มี Expected Value > 0 และ Max Drawdown ต่ำ
  - Kelly Criterion คำนวณขนาด position ที่ optimal
  - Mean Reversion + Momentum + Regime filter

Endpoints:
  GET  /trade/signals/{ticker}   — สัญญาณเทรดปัจจุบันพร้อม probability
  POST /trade/scan               — สแกนหลายหุ้นหาโอกาส
  GET  /trade/setup/{ticker}     — วิเคราะห์ setup เต็มรูปแบบ
  GET  /trade/edge/{ticker}      — Statistical edge จากข้อมูลอดีต
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ocaml_engine"))
from quant_probability import (  # type: ignore
    norm_cdf, norm_inv, bayesian_regime_prob,
    kelly_criterion, var_parametric, cvar_parametric,
    prob_reach_target, prob_cone,
)

from api.dependencies import get_loader
from data.loader import DataLoader

router = APIRouter(prefix="/trade", tags=["trade-signals"])


# ────────────────────────────────────────────────────────────────────────────
# Core statistical edge functions
# ────────────────────────────────────────────────────────────────────────────

def _compute_rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff().dropna()
    gain  = delta.clip(lower=0).rolling(period).mean().iloc[-1]
    loss  = (-delta.clip(upper=0)).rolling(period).mean().iloc[-1]
    if loss == 0:
        return 100.0
    rs = gain / loss
    return 100 - 100 / (1 + rs)

def _compute_bb_position(prices: pd.Series, period: int = 20, n_std: float = 2.0) -> float:
    """Position within Bollinger Bands: -1=lower, 0=middle, +1=upper."""
    ma  = prices.rolling(period).mean().iloc[-1]
    std = prices.rolling(period).std().iloc[-1]
    if std == 0:
        return 0.0
    upper = ma + n_std * std
    lower = ma - n_std * std
    curr  = prices.iloc[-1]
    return (curr - ma) / (upper - ma) if curr > ma else (curr - ma) / (ma - lower)

def _compute_zscore(prices: pd.Series, window: int = 20) -> float:
    """Z-score of current price relative to rolling window."""
    mu  = prices.rolling(window).mean().iloc[-1]
    std = prices.rolling(window).std().iloc[-1]
    if std == 0:
        return 0.0
    return (prices.iloc[-1] - mu) / std

def _compute_momentum(returns: pd.Series, periods: List[int] = [5, 10, 21]) -> dict:
    """Multi-period momentum."""
    result = {}
    for p in periods:
        if len(returns) >= p:
            cum = float((1 + returns.tail(p)).prod() - 1)
            result[f"mom_{p}d"] = round(cum * 100, 3)
    return result

def _historical_win_rates(returns: pd.Series, holding_days: int = 5) -> dict:
    """
    Backtest: for each past entry, what % of times was exit > entry after N days?
    Simulates every day as a potential entry.
    """
    r = returns.values
    n = len(r)
    wins, losses, neutral = 0, 0, 0
    total_pnl = 0.0
    win_pnl, loss_pnl = [], []

    for i in range(n - holding_days):
        pnl = float(np.prod(1 + r[i:i + holding_days]) - 1)
        total_pnl += pnl
        if pnl > 0.001:
            wins += 1
            win_pnl.append(pnl)
        elif pnl < -0.001:
            losses += 1
            loss_pnl.append(pnl)
        else:
            neutral += 1

    total = wins + losses + neutral
    win_rate  = wins / total if total > 0 else 0
    avg_win   = float(np.mean(win_pnl))  if win_pnl  else 0
    avg_loss  = float(np.mean(loss_pnl)) if loss_pnl else -0.001
    wlr       = abs(avg_win / avg_loss)  if avg_loss != 0 else 1.0
    ev        = win_rate * avg_win + (1 - win_rate) * avg_loss if loss_pnl else win_rate * avg_win
    kelly     = kelly_criterion(win_rate, wlr) if wlr > 0 else 0

    return {
        "win_rate":   round(win_rate, 4),
        "avg_win":    round(avg_win * 100, 3),
        "avg_loss":   round(avg_loss * 100, 3),
        "wl_ratio":   round(wlr, 3),
        "expected_value": round(ev * 100, 4),
        "kelly_pct":  round(max(0.0, kelly) * 100, 2),
        "half_kelly": round(max(0.0, kelly) * 50, 2),
        "total_trades": total,
    }

def _mean_reversion_signal(prices: pd.Series, returns: pd.Series) -> dict:
    """
    Mean reversion edge:
    - Z-score of price vs 20-day MA
    - Bollinger band position
    - Historical probability of reversion within 5 days
    """
    zscore = _compute_zscore(prices, 20)
    bb_pos = _compute_bb_position(prices, 20, 2.0)
    rsi    = _compute_rsi(prices, 14)

    # Signal direction
    if zscore < -1.5 and rsi < 35:
        direction = "LONG"
        strength  = min(1.0, abs(zscore) / 3.0)
    elif zscore > 1.5 and rsi > 65:
        direction = "SHORT"
        strength  = min(1.0, abs(zscore) / 3.0)
    else:
        direction = "NEUTRAL"
        strength  = 0.0

    # Historical probability: when z < -1.5, what % rebounded in 5d?
    hist_probs = {}
    for threshold, label in [(-1.5, "z<-1.5"), (-2.0, "z<-2.0"), (-2.5, "z<-2.5")]:
        z_series = prices.rolling(20).apply(
            lambda x: (x[-1] - x[:-1].mean()) / (x[:-1].std() + 1e-10), raw=True
        )
        entry_mask = z_series < threshold
        count, rev_count = 0, 0
        for i in range(len(entry_mask) - 5):
            if entry_mask.iloc[i]:
                count += 1
                if prices.iloc[i + 5] > prices.iloc[i]:
                    rev_count += 1
        hist_probs[label] = round(rev_count / count, 3) if count > 10 else None

    return {
        "type":      "mean_reversion",
        "direction": direction,
        "strength":  round(strength, 3),
        "z_score":   round(zscore, 3),
        "bb_position": round(bb_pos, 3),
        "rsi":       round(rsi, 2),
        "hist_reversion_probs": hist_probs,
    }

def _momentum_signal(returns: pd.Series, prices: pd.Series) -> dict:
    """
    Trend/momentum edge:
    - Cross-sectional momentum (price vs MA20/MA50/MA200)
    - Historical win rate of momentum continuation
    """
    close = prices
    ma20  = close.rolling(20).mean().iloc[-1]
    ma50  = close.rolling(50).mean().iloc[-1]
    ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else close.mean()
    curr  = close.iloc[-1]

    above_ma20  = curr > ma20
    above_ma50  = curr > ma50
    above_ma200 = curr > ma200
    momentum_score = sum([above_ma20, above_ma50, above_ma200]) / 3

    # 5-day momentum
    ret_5d  = float((1 + returns.tail(5)).prod() - 1)
    ret_21d = float((1 + returns.tail(21)).prod() - 1)

    direction = "LONG" if momentum_score > 0.5 and ret_5d > 0 else \
                "SHORT" if momentum_score < 0.5 and ret_5d < 0 else "NEUTRAL"

    return {
        "type":       "momentum",
        "direction":  direction,
        "score":      round(momentum_score, 3),
        "above_ma20": above_ma20,
        "above_ma50": above_ma50,
        "above_ma200":above_ma200,
        "ret_5d_pct": round(ret_5d * 100, 3),
        "ret_21d_pct":round(ret_21d * 100, 3),
    }

def _compute_edge_score(
    ev: float, win_rate: float, kelly: float,
    var_1d: float, sharpe: float, regime_prob: float,
) -> float:
    """
    Composite edge score 0-100:
    - Expected value (หุ้นน้อยแต่ต่อเนื่อง)
    - Win rate สูง
    - Kelly > 0 (มี edge จริง)
    - VaR ต่ำ (ความเสี่ยงน้อย)
    - Sharpe > 0
    - Regime เป็น bull
    """
    score = 0.0
    # EV component (max 30 pts) — ต้องการ EV > 0 แต่ไม่ต้องสูงมาก
    if ev > 0:
        score += min(30, ev * 1000)
    # Win rate (max 25 pts) — อยากได้ > 55%
    score += min(25, max(0, (win_rate - 0.45) * 250))
    # Kelly (max 20 pts) — แค่มี positive edge
    if kelly > 0:
        score += min(20, kelly * 100)
    # VaR penalty (max -15 if VaR high)
    score -= max(0, (var_1d - 0.01) * 300)
    # Sharpe (max 15 pts)
    score += min(15, max(0, sharpe * 5))
    # Regime (max 10 pts)
    score += regime_prob * 10
    return round(max(0, min(100, score)), 1)


# ────────────────────────────────────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────────────────────────────────────

@router.get("/signals/{ticker}")
async def get_signals(
    ticker:       str,
    holding_days: int   = Query(5,    ge=1, le=21),
    risk_free:    float = Query(0.05),
    loader: DataLoader  = Depends(get_loader),
):
    """
    วิเคราะห์สัญญาณเทรดสำหรับหุ้นหนึ่งตัว
    ใช้ข้อมูลอดีต 20 ปีคำนวณ probability และ edge
    """
    df = loader.load(ticker.upper())
    if df.empty or len(df) < 60:
        raise HTTPException(404, f"Insufficient data for {ticker}")

    prices  = df["close"]
    returns = prices.pct_change().dropna()

    # ── Stats ──────────────────────────────────────────────────────────────
    d_sigma = float(returns.std())
    d_mu    = float(returns.mean())
    ann_vol = d_sigma * math.sqrt(252)
    ann_mu  = d_mu * 252
    spot    = float(prices.iloc[-1])

    # ── Historical edge (from all 20 years) ────────────────────────────────
    edge    = _historical_win_rates(returns, holding_days)

    # ── Signals ────────────────────────────────────────────────────────────
    mr_sig  = _mean_reversion_signal(prices, returns)
    mom_sig = _momentum_signal(returns, prices)

    # ── Bayesian regime ────────────────────────────────────────────────────
    recent  = returns.tail(20).tolist()
    regime_p = bayesian_regime_prob(0.6, 0.0006, 0.008, -0.001, 0.018, recent) if recent else 0.6

    # ── Risk metrics ───────────────────────────────────────────────────────
    var_1d  = var_parametric(d_mu, d_sigma, 0.95)
    cvar_1d = cvar_parametric(d_mu, d_sigma, 0.95)
    sharpe_r = (d_mu - risk_free / 252) / d_sigma * math.sqrt(252)

    # ── Momentum (multi-period) ────────────────────────────────────────────
    momentum = _compute_momentum(returns)

    # ── Probability targets ────────────────────────────────────────────────
    tp1 = spot * 1.01   # +1%
    tp2 = spot * 1.02   # +2%
    sl1 = spot * 0.99   # -1%

    p_tp1 = prob_reach_target(spot, tp1, ann_mu, ann_vol, holding_days)
    p_tp2 = prob_reach_target(spot, tp2, ann_mu, ann_vol, holding_days)
    p_sl1 = prob_reach_target(spot, sl1, ann_mu, ann_vol, holding_days)

    # ── Composite edge score ────────────────────────────────────────────────
    edge_score = _compute_edge_score(
        edge["expected_value"] / 100,
        edge["win_rate"],
        edge["kelly_pct"] / 100,
        var_1d,
        sharpe_r,
        regime_p,
    )

    # ── Recommended setup ───────────────────────────────────────────────────
    # Pick the strongest signal
    mr_dir  = mr_sig["direction"]
    mom_dir = mom_sig["direction"]
    if mr_dir == mom_dir and mr_dir != "NEUTRAL":
        combined = mr_dir
        signal_confidence = 0.7 + mr_sig["strength"] * 0.2
    elif mr_dir != "NEUTRAL":
        combined = mr_dir
        signal_confidence = 0.5 + mr_sig["strength"] * 0.15
    elif mom_dir != "NEUTRAL":
        combined = mom_dir
        signal_confidence = 0.45
    else:
        combined = "NEUTRAL"
        signal_confidence = 0.0

    # ── Position sizing ─────────────────────────────────────────────────────
    # Use Half-Kelly for safety (ลดความเสี่ยงลง 50%)
    position_pct = edge["half_kelly"]   # % of capital

    return {
        "ticker":       ticker.upper(),
        "spot":         round(spot, 4),
        "signal":       combined,
        "signal_confidence": round(signal_confidence, 3),
        "edge_score":   edge_score,
        "regime":       "bull" if regime_p > 0.5 else "bear",
        "regime_prob":  round(regime_p, 4),
        "holding_days": holding_days,
        # Risk
        "ann_volatility": round(ann_vol * 100, 2),
        "var_1day_pct":   round(var_1d * 100, 3),
        "cvar_1day_pct":  round(cvar_1d * 100, 3),
        "sharpe":         round(sharpe_r, 4),
        # Historical edge
        "historical_edge": edge,
        "position_pct":    round(position_pct, 2),
        # Probability targets
        "probabilities": {
            f"p_+1pct_{holding_days}d":  round(p_tp1, 4),
            f"p_+2pct_{holding_days}d":  round(p_tp2, 4),
            f"p_-1pct_{holding_days}d":  round(p_sl1, 4),
            "tp1": round(tp1, 2),
            "tp2": round(tp2, 2),
            "sl1": round(sl1, 2),
        },
        # Sub-signals
        "mean_reversion": mr_sig,
        "momentum":       {**mom_sig, **momentum},
    }


class ScanRequest(BaseModel):
    tickers:      List[str]
    holding_days: int   = 5
    min_edge_score: float = 40.0
    max_var_pct:    float = 3.0    # max 1-day VaR %

@router.post("/scan")
async def scan_signals(
    req: ScanRequest,
    loader: DataLoader = Depends(get_loader),
):
    """
    สแกนหลายหุ้นพร้อมกัน หาเฉพาะที่มี edge score สูงและ VaR ต่ำ
    เรียงตาม edge_score จากมากไปน้อย
    """
    results = []
    for t in req.tickers[:60]:
        try:
            df = loader.load(t.upper())
            if df.empty or len(df) < 60:
                continue
            prices  = df["close"]
            returns = prices.pct_change().dropna()
            d_sigma = float(returns.std())
            d_mu    = float(returns.mean())
            spot    = float(prices.iloc[-1])
            var_1d  = var_parametric(d_mu, d_sigma, 0.95)

            if var_1d * 100 > req.max_var_pct:
                continue

            edge     = _historical_win_rates(returns, req.holding_days)
            recent   = returns.tail(20).tolist()
            regime_p = bayesian_regime_prob(0.6, 0.0006, 0.008, -0.001, 0.018, recent)
            sharpe_r = (d_mu - 0.05/252) / d_sigma * math.sqrt(252)
            mr       = _mean_reversion_signal(prices, returns)
            mom      = _momentum_signal(returns, prices)

            edge_score = _compute_edge_score(
                edge["expected_value"] / 100,
                edge["win_rate"],
                edge["kelly_pct"] / 100,
                var_1d, sharpe_r, regime_p,
            )
            if edge_score < req.min_edge_score:
                continue

            # Combined signal
            if mr["direction"] == mom["direction"] != "NEUTRAL":
                sig = mr["direction"]
            elif mr["direction"] != "NEUTRAL":
                sig = mr["direction"]
            else:
                sig = mom["direction"]

            results.append({
                "ticker":       t.upper(),
                "spot":         round(spot, 2),
                "signal":       sig,
                "edge_score":   edge_score,
                "win_rate":     edge["win_rate"],
                "expected_value": edge["expected_value"],
                "half_kelly":   edge["half_kelly"],
                "var_1day_pct": round(var_1d * 100, 3),
                "sharpe":       round(sharpe_r, 3),
                "regime":       "bull" if regime_p > 0.5 else "bear",
                "mr_signal":    mr["direction"],
                "mom_signal":   mom["direction"],
                "rsi":          round(mr["rsi"], 1),
                "z_score":      round(mr["z_score"], 2),
            })
        except Exception:
            continue

    results.sort(key=lambda x: x["edge_score"], reverse=True)
    return {"results": results, "count": len(results), "scanned": len(req.tickers)}


@router.get("/edge/{ticker}")
async def statistical_edge(
    ticker:  str,
    loader:  DataLoader = Depends(get_loader),
):
    """
    Deep statistical edge analysis จากข้อมูลอดีตทั้งหมด
    แยกตาม holding period, regime, seasonality
    """
    df = loader.load(ticker.upper())
    if df.empty or len(df) < 252:
        raise HTTPException(404, f"Need ≥1 year of data for {ticker}")

    prices  = df["close"]
    returns = prices.pct_change().dropna()

    # ── Edge by holding period ─────────────────────────────────────────────
    by_period = {}
    for h in [1, 3, 5, 10, 21]:
        e = _historical_win_rates(returns, h)
        by_period[f"{h}d"] = e

    # ── Edge by regime (bull vs bear days) ─────────────────────────────────
    ma200     = prices.rolling(200).mean()
    bull_mask = prices > ma200
    edge_bull = _historical_win_rates(returns[bull_mask.shift(1).fillna(False)], 5)
    edge_bear = _historical_win_rates(returns[~bull_mask.shift(1).fillna(True)], 5)

    # ── Edge by day of week ────────────────────────────────────────────────
    dow_edge = {}
    for dow, label in enumerate(["Mon","Tue","Wed","Thu","Fri"]):
        mask = returns.index.dayofweek == dow
        sub  = returns[mask]
        if len(sub) > 50:
            wr = float((sub > 0).mean())
            avg = float(sub.mean() * 100)
            dow_edge[label] = {"win_rate": round(wr, 3), "avg_return_pct": round(avg, 4)}

    # ── Edge by month ──────────────────────────────────────────────────────
    month_edge = {}
    for m in range(1, 13):
        mask = returns.index.month == m
        sub  = returns[mask]
        if len(sub) > 20:
            wr   = float((sub > 0).mean())
            avg  = float(sub.mean() * 100)
            month_edge[str(m)] = {"win_rate": round(wr, 3), "avg_return_pct": round(avg, 4)}

    # ── Best entry conditions (from historical data) ────────────────────────
    best_z_edges = {}
    for z_thresh, label in [(-3,-3), (-2,-2), (-1,-1), (1,1), (2,2)]:
        z_series = prices.rolling(20).apply(
            lambda x: (x[-1] - x[:-1].mean()) / (x[:-1].std() + 1e-10), raw=True
        ).dropna()
        aligned = returns.reindex(z_series.index)
        if z_thresh < 0:
            mask = z_series < z_thresh
        else:
            mask = z_series > z_thresh
        subset = aligned.shift(-5)[mask].dropna()
        if len(subset) > 10:
            wr = float((subset > 0).mean())
            best_z_edges[f"z{'+' if z_thresh > 0 else ''}{z_thresh}"] = {
                "win_rate_5d": round(wr, 3),
                "n_signals": int(mask.sum()),
            }

    # ── Drawdown analysis ──────────────────────────────────────────────────
    cum_ret    = (1 + returns).cumprod()
    peak       = cum_ret.cummax()
    drawdown   = (cum_ret / peak - 1)
    max_dd     = float(drawdown.min())
    avg_dd     = float(drawdown[drawdown < 0].mean()) if (drawdown < 0).any() else 0.0
    recovery_days = []
    in_dd = False
    dd_start = 0
    for i, (val, p) in enumerate(zip(cum_ret.values, peak.values)):
        if val < p and not in_dd:
            in_dd = True
            dd_start = i
        elif val >= p and in_dd:
            recovery_days.append(i - dd_start)
            in_dd = False
    avg_recovery = float(np.mean(recovery_days)) if recovery_days else 0

    return {
        "ticker": ticker.upper(),
        "total_days": len(returns),
        "by_holding_period": by_period,
        "by_regime": {
            "bull_market": edge_bull,
            "bear_market": edge_bear,
        },
        "by_day_of_week": dow_edge,
        "by_month": month_edge,
        "entry_by_zscore": best_z_edges,
        "drawdown_stats": {
            "max_drawdown_pct":  round(max_dd * 100, 2),
            "avg_drawdown_pct":  round(avg_dd * 100, 2),
            "avg_recovery_days": round(avg_recovery, 1),
        },
    }


@router.get("/setup/{ticker}")
async def trade_setup(
    ticker:       str,
    capital:      float = Query(100_000),
    max_risk_pct: float = Query(1.0,  description="Max % of capital to risk per trade"),
    loader: DataLoader  = Depends(get_loader),
):
    """
    สร้าง trade setup ที่สมบูรณ์:
    - Entry price
    - Stop-loss (ตาม VaR 95%)
    - Take-profit 1 & 2
    - Position size (ตาม Kelly + Max Risk)
    - Expected PnL distribution
    """
    df = loader.load(ticker.upper())
    if df.empty or len(df) < 60:
        raise HTTPException(404, f"No data for {ticker}")

    prices  = df["close"]
    returns = prices.pct_change().dropna()
    d_sigma = float(returns.std())
    d_mu    = float(returns.mean())
    spot    = float(prices.iloc[-1])
    ann_vol = d_sigma * math.sqrt(252)
    ann_mu  = d_mu * 252

    # ── Historical edge ─────────────────────────────────────────────────────
    edge_5d  = _historical_win_rates(returns, 5)
    win_rate = edge_5d["win_rate"]
    wlr      = edge_5d["wl_ratio"]

    # ── Kelly + position sizing ─────────────────────────────────────────────
    kelly_f    = kelly_criterion(win_rate, wlr)
    half_kelly = max(0.0, kelly_f * 0.5)

    # Position size: min(half-kelly, max_risk_pct / var_1d)
    var_1d     = var_parametric(d_mu, d_sigma, 0.95)
    risk_based = (max_risk_pct / 100) / var_1d if var_1d > 0 else 0
    pos_frac   = min(half_kelly, risk_based)
    pos_value  = capital * pos_frac
    shares     = int(pos_value / spot) if spot > 0 else 0

    # ── Stop-loss / Take-profit ─────────────────────────────────────────────
    # Stop: 2x daily VaR (tight stop to minimise loss)
    stop_dist  = var_1d * 2
    stop_price = round(spot * (1 - stop_dist), 4)
    stop_pct   = round(-stop_dist * 100, 3)

    # TP1: risk/reward 1.5:1 (กำไรน้อยแต่มีโอกาสสูง)
    tp1_dist   = stop_dist * 1.5
    tp1_price  = round(spot * (1 + tp1_dist), 4)
    tp1_pct    = round(tp1_dist * 100, 3)

    # TP2: risk/reward 2.5:1
    tp2_dist   = stop_dist * 2.5
    tp2_price  = round(spot * (1 + tp2_dist), 4)
    tp2_pct    = round(tp2_dist * 100, 3)

    # ── Probability of each outcome ─────────────────────────────────────────
    p_stop = prob_reach_target(spot, stop_price, ann_mu, ann_vol, 5)
    p_tp1  = prob_reach_target(spot, tp1_price,  ann_mu, ann_vol, 5)
    p_tp2  = prob_reach_target(spot, tp2_price,  ann_mu, ann_vol, 5)

    # ── Expected PnL ────────────────────────────────────────────────────────
    # Scenario: P(TP1) × TP1_gain + P(stop) × stop_loss + rest × 0
    p_neutral = max(0, 1 - p_tp1 - p_stop)
    ev_trade  = (p_tp1 * tp1_pct + (1 - p_tp1) * stop_pct) / 100  # expected return
    ev_dollar = ev_trade * pos_value

    # ── Max loss ────────────────────────────────────────────────────────────
    max_loss_dollar = abs(stop_pct / 100) * pos_value
    max_loss_cap    = max_loss_dollar / capital * 100

    # ── Cone ───────────────────────────────────────────────────────────────
    cone = prob_cone(spot, ann_mu, ann_vol, 5, 0.95)

    # ── Regime ─────────────────────────────────────────────────────────────
    recent   = returns.tail(20).tolist()
    regime_p = bayesian_regime_prob(0.6, 0.0006, 0.008, -0.001, 0.018, recent)

    # ── Signals ────────────────────────────────────────────────────────────
    mr  = _mean_reversion_signal(prices, returns)
    mom = _momentum_signal(returns, prices)

    return {
        "ticker":      ticker.upper(),
        "spot":        round(spot, 4),
        "capital":     capital,
        # Setup
        "entry":       round(spot, 4),
        "stop_price":  stop_price,
        "stop_pct":    stop_pct,
        "tp1_price":   tp1_price,
        "tp1_pct":     tp1_pct,
        "tp2_price":   tp2_price,
        "tp2_pct":     tp2_pct,
        # Position sizing
        "position_size_pct": round(pos_frac * 100, 2),
        "position_value":    round(pos_value, 2),
        "shares":            shares,
        "max_loss_dollar":   round(max_loss_dollar, 2),
        "max_loss_cap_pct":  round(max_loss_cap, 3),
        # Probabilities
        "p_stop":    round(p_stop, 4),
        "p_tp1":     round(p_tp1,  4),
        "p_tp2":     round(p_tp2,  4),
        "p_neutral": round(p_neutral, 4),
        "ev_trade_pct":    round(ev_trade * 100, 4),
        "ev_dollar":       round(ev_dollar, 2),
        # Context
        "regime":          "bull" if regime_p > 0.5 else "bear",
        "regime_prob":     round(regime_p, 4),
        "win_rate":        edge_5d["win_rate"],
        "kelly_pct":       round(kelly_f * 100, 2),
        "half_kelly_pct":  round(half_kelly * 100, 2),
        "wl_ratio":        edge_5d["wl_ratio"],
        "sharpe":          round((d_mu - 0.05/252) / d_sigma * math.sqrt(252), 4),
        "var_1day_pct":    round(var_1d * 100, 3),
        # Chart data
        "cone":            cone,
        "signals": {
            "mean_reversion": mr,
            "momentum":       mom,
        },
    }
