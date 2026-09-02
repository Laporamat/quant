"""
strategies/momentum_strategy.py
Cross-sectional & time-series momentum strategy.

- Cross-sectional: rank tickers by trailing n-month return, long top-k
- Time-series: each ticker is long only when its 12-1 return is positive
"""
from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from strategies.base_strategy import BaseStrategy, Signal, SignalType


class MomentumStrategy(BaseStrategy):
    """
    Momentum strategy with monthly rebalancing.

    Parameters
    ----------
    lookback      : momentum lookback in trading days (default 252)
    skip          : skip last n days to avoid reversal (default 21)
    top_k         : number of top tickers to hold (default 10)
    mode          : "cross_sectional" | "time_series" | "combined"
    rebalance_freq: "M" = monthly, "W" = weekly, "D" = daily
    """
    name = "momentum"

    def prepare(self, data: Dict[str, pd.DataFrame]) -> None:
        self._tickers   = self.get_param("tickers") or list(data.keys())
        self._lookback  = self.get_param("lookback", 252)
        self._skip      = self.get_param("skip", 21)
        self._top_k     = self.get_param("top_k", 10)
        self._mode      = self.get_param("mode", "cross_sectional")
        self._freq      = self.get_param("rebalance_freq", "M")
        self._last_rebal: Optional[pd.Timestamp] = None
        self._holdings:  set = set()

        # Build close-price panel
        frames = {}
        for t in self._tickers:
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
        signals: List[Signal] = []
        closes_to_date = self._closes.loc[:date].dropna(how="all")

        if len(closes_to_date) < self._lookback + self._skip + 1:
            return []

        # Compute momentum score: return from -lookback to -skip days ago
        curr_prices   = closes_to_date.iloc[-self._skip - 1]
        past_prices   = closes_to_date.iloc[-self._lookback - 1]
        mom_scores    = (curr_prices / past_prices) - 1

        if self._mode in ("cross_sectional", "combined"):
            top_tickers = mom_scores.nlargest(self._top_k).index.tolist()
        else:
            top_tickers = mom_scores[mom_scores > 0].index.tolist()

        new_holdings = set(top_tickers)

        # Exit positions no longer in top
        for ticker in self._holdings - new_holdings:
            bar = data.get(ticker)
            if bar is None:
                continue
            row = bar.loc[:date]
            if row.empty:
                continue
            signals.append(Signal(
                date=date, ticker=ticker,
                signal=SignalType.SELL, strength=1.0,
                price=float(row["close"].iloc[-1]),
                meta={"momentum_score": float(mom_scores.get(ticker, 0))},
            ))

        # Enter new top-k positions
        weight = 1.0 / len(new_holdings) if new_holdings else 0.0
        for ticker in new_holdings - self._holdings:
            bar = data.get(ticker)
            if bar is None:
                continue
            row = bar.loc[:date]
            if row.empty:
                continue
            signals.append(Signal(
                date=date, ticker=ticker,
                signal=SignalType.BUY, strength=weight,
                price=float(row["close"].iloc[-1]),
                meta={"momentum_score": float(mom_scores.get(ticker, 0))},
            ))

        self._holdings = new_holdings
        return signals

    def _should_rebalance(self, date: pd.Timestamp) -> bool:
        if self._last_rebal is None:
            return True
        if self._freq == "D":
            return True
        if self._freq == "W":
            return date.isocalendar()[1] != self._last_rebal.isocalendar()[1]
        if self._freq == "M":
            return date.month != self._last_rebal.month
        return False
