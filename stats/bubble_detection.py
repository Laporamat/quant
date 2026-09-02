"""
stats/bubble_detection.py
Historical bubble & crash detection using:
  1. Log-price acceleration (2nd derivative of log price)
  2. Rolling cumulative-return z-score (price divergence from historical norm)
  3. Shiller PE-proxy via trailing 12-month earnings growth (heuristic)
  4. LPPL-inspired super-exponential growth test
  5. Historical bubble catalogue (known episodes matched by signature)

No external ML models required — pure numpy / pandas / scipy.
"""
from __future__ import annotations

import math
import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

warnings.filterwarnings("ignore")


# ── Known historical bubble episodes (approximate) ──────────────────────────
KNOWN_BUBBLES: List[Dict] = [
    {
        "name":         "Dot-com Bubble",
        "peak_date":    "2000-03-10",
        "trough_date":  "2002-10-09",
        "ticker_hint":  ["QQQ", "MSFT", "CSCO", "INTC", "AAPL"],
        "min_drawdown": 0.40,
    },
    {
        "name":         "US Housing / GFC",
        "peak_date":    "2007-10-09",
        "trough_date":  "2009-03-09",
        "ticker_hint":  ["SPY", "XLF", "JPM", "BAC", "GS"],
        "min_drawdown": 0.50,
    },
    {
        "name":         "China A-share Bubble",
        "peak_date":    "2015-06-12",
        "trough_date":  "2016-01-26",
        "ticker_hint":  ["FXI", "KWEB"],
        "min_drawdown": 0.40,
    },
    {
        "name":         "COVID Crash",
        "peak_date":    "2020-02-19",
        "trough_date":  "2020-03-23",
        "ticker_hint":  ["SPY", "QQQ", "IWM"],
        "min_drawdown": 0.30,
    },
    {
        "name":         "Crypto Bubble 2021",
        "peak_date":    "2021-11-10",
        "trough_date":  "2022-11-21",
        "ticker_hint":  ["COIN", "MARA", "RIOT"],
        "min_drawdown": 0.70,
    },
    {
        "name":         "Growth/Tech Bubble 2021-22",
        "peak_date":    "2021-11-19",
        "trough_date":  "2022-12-28",
        "ticker_hint":  ["QQQ", "ARKK", "NVDA", "META", "NFLX"],
        "min_drawdown": 0.30,
    },
]


@dataclass
class BubbleSignal:
    name:        str
    triggered:   bool
    value:       float
    threshold:   float
    description: str


@dataclass
class BubbleEvent:
    peak_date:    str
    trough_date:  str
    peak_price:   float
    trough_price: float
    drawdown:     float
    duration_days: int
    name:         str


@dataclass
class BubbleResult:
    ticker:              str
    start_date:          str
    end_date:            str
    bubble_score:        float          # 0–100 composite
    is_bubble:           bool
    pe_ratio_current:    Optional[float]
    pe_ratio_hist_avg:   Optional[float]
    pe_zscore:           Optional[float]
    price_acceleration:  float
    log_return_zscore:   float
    crash_probability:   float
    historical_bubbles:  List[BubbleEvent]
    price_series:        List[Dict]
    zscore_series:       List[Dict]
    signals:             List[BubbleSignal]


class BubbleDetection:
    """Detect speculative bubbles and historical crash episodes."""

    BUBBLE_SCORE_THRESHOLD = 60.0   # out of 100
    ZSCORE_BUBBLE          = 2.0    # 2-sigma above rolling mean
    ACCEL_THRESHOLD        = 0.30   # annualised log-price acceleration
    DRAWDOWN_BUBBLE        = 0.20   # ≥20% drawdown defines an episode

    # ── Main entry point ─────────────────────────────────────────────────────
    @classmethod
    def analyse(
        cls,
        prices:     pd.Series,    # DatetimeIndex, daily close
        ticker:     str = "TICKER",
    ) -> BubbleResult:
        prices = prices.dropna().sort_index()
        if len(prices) < 63:
            raise ValueError("Need at least 63 trading days of data")

        log_p  = np.log(prices)
        rets   = prices.pct_change().dropna()

        # ── 1. Rolling cumulative return z-score ─────────────────────────────
        rolling_252 = rets.rolling(252)
        roll_cum    = (1 + rets).rolling(252).apply(lambda x: x.prod() - 1, raw=True)
        roll_mean   = roll_cum.rolling(252 * 3).mean()
        roll_std    = roll_cum.rolling(252 * 3).std()
        zscore_ser  = ((roll_cum - roll_mean) / (roll_std + 1e-10)).fillna(0.0)
        current_z   = float(zscore_ser.iloc[-1])

        # ── 2. Log-price acceleration (2nd derivative) ────────────────────────
        # Fit OLS to last 252 days: log_p = a + b*t + c*t² → c = acceleration
        tail        = log_p.iloc[-252:]
        t           = np.arange(len(tail))
        if len(tail) >= 30:
            coeffs  = np.polyfit(t, tail.values, 2)
            accel   = float(coeffs[0]) * 252          # annualised
        else:
            accel   = 0.0

        # ── 3. Super-exponential growth test (LPPL heuristic) ─────────────────
        # If cumulative log return over last year exceeds mean + 2.5 std → flag
        log_ret_1y  = float(log_p.iloc[-1] - log_p.iloc[max(0, len(log_p) - 252)])
        all_yr_rets = [
            float(log_p.iloc[min(i + 252, len(log_p) - 1)] - log_p.iloc[i])
            for i in range(0, len(log_p) - 252, 21)
        ]
        yr_mean     = float(np.mean(all_yr_rets)) if all_yr_rets else 0.0
        yr_std      = float(np.std(all_yr_rets))  if all_yr_rets else 1.0
        lppl_z      = (log_ret_1y - yr_mean) / (yr_std + 1e-10)

        # ── 4. Volatility regime (elevated vol = late-stage bubble) ──────────
        vol_now    = float(rets.iloc[-63:].std() * math.sqrt(252))
        vol_hist   = float(rets.std() * math.sqrt(252))
        vol_ratio  = vol_now / (vol_hist + 1e-10)

        # ── 5. Composite bubble score ─────────────────────────────────────────
        scores: Dict[str, float] = {}
        # z-score component (max 30 points at z≥3)
        scores["zscore"]      = min(30.0, max(0.0, (current_z / 3.0) * 30.0))
        # acceleration component (max 25 points at accel≥0.5)
        scores["accel"]       = min(25.0, max(0.0, (accel / 0.50) * 25.0))
        # LPPL z-score (max 25 points at z≥3)
        scores["lppl"]        = min(25.0, max(0.0, (lppl_z / 3.0) * 25.0))
        # Vol spike (max 20 points at ratio≥2.5)
        scores["vol_spike"]   = min(20.0, max(0.0, ((vol_ratio - 1.0) / 1.5) * 20.0))
        bubble_score          = sum(scores.values())

        # ── 6. Crash probability (empirical from score) ───────────────────────
        crash_prob = min(0.99, max(0.01, bubble_score / 100.0))

        # ── 7. Signals ───────────────────────────────────────────────────────
        signals = [
            BubbleSignal(
                name        = "Return Z-Score",
                triggered   = current_z >= cls.ZSCORE_BUBBLE,
                value       = round(current_z, 4),
                threshold   = cls.ZSCORE_BUBBLE,
                description = "Rolling 1Y cumulative return is significantly above its long-run mean",
            ),
            BubbleSignal(
                name        = "Price Acceleration",
                triggered   = accel >= cls.ACCEL_THRESHOLD,
                value       = round(accel, 4),
                threshold   = cls.ACCEL_THRESHOLD,
                description = "Log-price is growing at a super-exponential (accelerating) rate",
            ),
            BubbleSignal(
                name        = "LPPL Super-Exponential",
                triggered   = lppl_z >= 2.5,
                value       = round(lppl_z, 4),
                threshold   = 2.5,
                description = "1-year log return exceeds historical norm by 2.5σ — LPPL-type growth",
            ),
            BubbleSignal(
                name        = "Volatility Spike",
                triggered   = vol_ratio >= 1.5,
                value       = round(vol_ratio, 4),
                threshold   = 1.5,
                description = "Recent 63-day volatility is ≥1.5× long-run average — instability signal",
            ),
        ]

        # ── 8. Historical bubble episodes in this price series ───────────────
        hist_bubbles = cls._find_historical_bubbles(prices, ticker)

        # ── 9. Build output series (downsample to max 1000 points) ───────────
        step = max(1, len(prices) // 1000)
        price_series = [
            {
                "date":      str(prices.index[i].date()),
                "close":     round(float(prices.iloc[i]), 4),
                "log_price": round(float(log_p.iloc[i]), 6),
            }
            for i in range(0, len(prices), step)
        ]
        zscore_series = [
            {
                "date":   str(zscore_ser.index[i].date()),
                "zscore": round(float(zscore_ser.iloc[i]), 4),
            }
            for i in range(0, len(zscore_ser), step)
        ]

        return BubbleResult(
            ticker             = ticker.upper(),
            start_date         = str(prices.index[0].date()),
            end_date           = str(prices.index[-1].date()),
            bubble_score       = round(bubble_score, 2),
            is_bubble          = bubble_score >= cls.BUBBLE_SCORE_THRESHOLD,
            pe_ratio_current   = None,   # would need earnings data
            pe_ratio_hist_avg  = None,
            pe_zscore          = None,
            price_acceleration = round(accel, 6),
            log_return_zscore  = round(current_z, 6),
            crash_probability  = round(crash_prob, 4),
            historical_bubbles = hist_bubbles,
            price_series       = price_series,
            zscore_series      = zscore_series,
            signals            = signals,
        )

    # ── Historical episode detector ──────────────────────────────────────────
    @classmethod
    def _find_historical_bubbles(
        cls,
        prices: pd.Series,
        ticker: str,
    ) -> List[BubbleEvent]:
        """Find all drawdown episodes ≥ DRAWDOWN_BUBBLE threshold."""
        events: List[BubbleEvent] = []
        equity = prices / prices.iloc[0]
        peak   = equity.iloc[0]
        peak_date = prices.index[0]

        for date, val in equity.items():
            if val > peak:
                peak      = val
                peak_date = date
            dd = (val / peak) - 1.0
            if dd <= -cls.DRAWDOWN_BUBBLE:
                # Check if we already captured this episode
                # (allow 252-day gap between episodes)
                if events and (date - pd.Timestamp(events[-1].trough_date)).days < 252:
                    # Update trough if this is deeper
                    if dd < -events[-1].drawdown:
                        events[-1] = BubbleEvent(
                            peak_date    = events[-1].peak_date,
                            trough_date  = str(date.date()),
                            peak_price   = events[-1].peak_price,
                            trough_price = round(float(prices[date]), 4),
                            drawdown     = round(abs(dd), 4),
                            duration_days= (date - pd.Timestamp(events[-1].peak_date)).days,
                            name         = events[-1].name,
                        )
                else:
                    # Try to match to a known bubble by overlapping date range
                    name = cls._match_known_bubble(peak_date, date, ticker)
                    events.append(BubbleEvent(
                        peak_date    = str(peak_date.date()),
                        trough_date  = str(date.date()),
                        peak_price   = round(float(prices[peak_date]), 4),
                        trough_price = round(float(prices[date]), 4),
                        drawdown     = round(abs(dd), 4),
                        duration_days= (date - peak_date).days,
                        name         = name,
                    ))

        return events[:15]   # cap at 15 episodes

    @staticmethod
    def _match_known_bubble(peak: pd.Timestamp, trough: pd.Timestamp, ticker: str) -> str:
        """Return the name of a matching known bubble episode, or generic label."""
        for kb in KNOWN_BUBBLES:
            kb_peak   = pd.Timestamp(kb["peak_date"])
            kb_trough = pd.Timestamp(kb["trough_date"])
            # Overlap if within ±180 days of known peak
            if abs((peak - kb_peak).days) <= 180:
                hints = kb.get("ticker_hint", [])
                if not hints or any(h in ticker.upper() for h in hints):
                    return kb["name"]
        yr = str(peak.year)
        return f"Market Decline {yr}"

    # ── Multi-asset bubble scan ───────────────────────────────────────────────
    @classmethod
    def scan_universe(
        cls,
        price_panel: pd.DataFrame,  # columns = tickers, index = DatetimeIndex
    ) -> pd.DataFrame:
        """Run bubble analysis on every column and return a summary DataFrame."""
        rows = []
        for ticker in price_panel.columns:
            prices = price_panel[ticker].dropna()
            if len(prices) < 63:
                continue
            try:
                res = cls.analyse(prices, ticker=ticker)
                rows.append({
                    "ticker":         ticker,
                    "bubble_score":   res.bubble_score,
                    "is_bubble":      res.is_bubble,
                    "z_score":        res.log_return_zscore,
                    "acceleration":   res.price_acceleration,
                    "crash_prob":     res.crash_probability,
                    "n_bubbles":      len(res.historical_bubbles),
                })
            except Exception:
                pass
        return pd.DataFrame(rows).sort_values("bubble_score", ascending=False)
