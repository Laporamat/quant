"""
strategies/trend_following.py
Dual-momentum (absolute + relative) with 200-day trend filter.
Based on Gary Antonacci's Dual Momentum framework.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from strategies.base_strategy import BaseStrategy, Signal, SignalType


class TrendFollowingStrategy(BaseStrategy):
    """
    Dual-momentum trend following:
    1. Absolute momentum: long only when trailing return > risk-free rate
    2. Relative momentum: pick best ticker among universe
    3. Trend filter: price must be above 200-day SMA

    Parameters
    ----------
    lookback        : momentum lookback in days (default 252)
    trend_period    : trend filter SMA period (default 200)
    safe_asset      : defensive asset when absolute momentum is negative (default "TLT")
    risk_free_rate  : annualised risk-free hurdle (default 0.02)
    rebalance_freq  : "M" | "W"
    """
    name = "trend_following"

    def prepare(self, data: Dict[str, pd.DataFrame]) -> None:
        self._tickers    = self.get_param("tickers") or list(data.keys())
        self._lookback   = self.get_param("lookback", 252)
        self._trend_per  = self.get_param("trend_period", 200)
        self._safe       = self.get_param("safe_asset", "TLT")
        self._rfr        = self.get_param("risk_free_rate", 0.02)
        self._freq       = self.get_param("rebalance_freq", "M")
        self._last_rebal: Optional[pd.Timestamp] = None
        self._holding:    Optional[str] = None

        frames: Dict[str, pd.Series] = {}
        for t in self._tickers + ([self._safe] if self._safe else []):
            df = data.get(t)
            if df is not None and not df.empty:
                frames[t] = df["close"]
        self._closes = pd.DataFrame(frames)

    def generate_signals(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.DataFrame],
        portfolio_state: Optional[Dict] = None,
    ) -> List[Signal]:
        if not self._should_rebalance(date):
            return []
        self._last_rebal = date

        closes = self._closes.loc[:date].dropna(how="all")
        if len(closes) < self._lookback + 1:
            return []

        signals: List[Signal] = []
        daily_rf = (1 + self._rfr) ** (1 / 252) - 1

        # ── Compute momentum and trend for each ticker ──
        mom: Dict[str, float] = {}
        in_trend: Dict[str, bool] = {}
        for t in self._tickers:
            if t not in closes.columns:
                continue
            c = closes[t].dropna()
            if len(c) < self._lookback + 1:
                continue
            ret = float(c.iloc[-1] / c.iloc[-self._lookback - 1] - 1)
            mom[t] = ret
            sma = float(c.tail(self._trend_per).mean())
            in_trend[t] = float(c.iloc[-1]) > sma

        # ── Absolute momentum filter: does the best asset beat risk-free? ──
        eligible = {t: m for t, m in mom.items() if in_trend.get(t, False)}
        if not eligible:
            target = self._safe
        else:
            best_t = max(eligible, key=eligible.get)
            annual_mom = eligible[best_t]
            if annual_mom > self._rfr:
                target = best_t
            else:
                target = self._safe

        if target == self._holding:
            return []

        # ── Exit current holding ──
        if self._holding and self._holding != target:
            df = data.get(self._holding)
            if df is not None:
                row = df.loc[:date]
                if not row.empty:
                    signals.append(Signal(
                        date=date, ticker=self._holding,
                        signal=SignalType.SELL, strength=1.0,
                        price=float(row["close"].iloc[-1]),
                        meta={"exit": "rebalance"},
                    ))

        # ── Enter new holding ──
        if target:
            df = data.get(target)
            if df is not None:
                row = df.loc[:date]
                if not row.empty:
                    signals.append(Signal(
                        date=date, ticker=target,
                        signal=SignalType.BUY, strength=1.0,
                        price=float(row["close"].iloc[-1]),
                        meta={"momentum": mom.get(target, 0.0),
                              "trend_filter": in_trend.get(target, False)},
                    ))

        self._holding = target
        return signals

    def _should_rebalance(self, date: pd.Timestamp) -> bool:
        if self._last_rebal is None:
            return True
        if self._freq == "W":
            return date.isocalendar()[1] != self._last_rebal.isocalendar()[1]
        return date.month != self._last_rebal.month
