"""
strategies/multi_factor.py
Multi-factor scoring strategy: value + momentum + quality + low-vol.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from strategies.base_strategy import BaseStrategy, Signal, SignalType


class MultiFactorStrategy(BaseStrategy):
    """
    Rank tickers by composite factor score; long top_k, rebalance monthly.

    Factors
    -------
    momentum : 12-1 month price momentum (weight w_mom)
    low_vol  : negative 21-day realised volatility (weight w_vol)
    trend    : price above 200-day SMA (weight w_trend)

    Parameters
    ----------
    top_k        : number of holdings (default 10)
    w_mom        : momentum weight (default 0.4)
    w_vol        : low-vol weight (default 0.3)
    w_trend      : trend weight (default 0.3)
    mom_lookback : momentum lookback in days (default 252)
    mom_skip     : skip days for momentum (default 21)
    vol_period   : realised vol period (default 21)
    """
    name = "multi_factor"

    def prepare(self, data: Dict[str, pd.DataFrame]) -> None:
        self._tickers    = self.get_param("tickers") or list(data.keys())
        self._top_k      = self.get_param("top_k", 10)
        self._w_mom      = self.get_param("w_mom", 0.4)
        self._w_vol      = self.get_param("w_vol", 0.3)
        self._w_trend    = self.get_param("w_trend", 0.3)
        self._mom_look   = self.get_param("mom_lookback", 252)
        self._mom_skip   = self.get_param("mom_skip", 21)
        self._vol_period = self.get_param("vol_period", 21)
        self._last_rebal: Optional[pd.Timestamp] = None
        self._holdings:   set = set()

        # Build panel
        frames: Dict[str, pd.Series] = {}
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

        closes = self._closes.loc[:date]
        if len(closes) < self._mom_look + 1:
            return []

        scores = self._compute_scores(closes)
        if scores.empty:
            return []

        top = set(scores.nlargest(self._top_k).index.tolist())
        signals: List[Signal] = []
        weight = 1.0 / len(top) if top else 0.0

        for ticker in self._holdings - top:
            df = data.get(ticker)
            if df is None:
                continue
            row = df.loc[:date]
            if row.empty:
                continue
            signals.append(Signal(date=date, ticker=ticker,
                                  signal=SignalType.SELL, strength=1.0,
                                  price=float(row["close"].iloc[-1])))

        for ticker in top - self._holdings:
            df = data.get(ticker)
            if df is None:
                continue
            row = df.loc[:date]
            if row.empty:
                continue
            signals.append(Signal(date=date, ticker=ticker,
                                  signal=SignalType.BUY, strength=weight,
                                  price=float(row["close"].iloc[-1]),
                                  meta={"score": float(scores.get(ticker, 0))}))

        self._holdings = top
        return signals

    def _compute_scores(self, closes: pd.DataFrame) -> pd.Series:
        """Compute cross-sectional factor scores and return a composite rank."""
        # Momentum factor
        curr = closes.iloc[-self._mom_skip - 1]
        past = closes.iloc[-self._mom_look - 1]
        mom  = (curr / past - 1).replace([np.inf, -np.inf], np.nan)

        # Low-vol factor (negative volatility = higher score)
        ret  = closes.pct_change().iloc[-self._vol_period:]
        lvol = -ret.std(ddof=1)

        # Trend factor (1 if above SMA200, 0 otherwise)
        sma200 = closes.tail(200).mean()
        trend  = (closes.iloc[-1] > sma200).astype(float)

        # Cross-sectional z-score each factor
        def zscore(s: pd.Series) -> pd.Series:
            s = s.dropna()
            std = s.std()
            return (s - s.mean()) / std if std > 0 else s * 0

        score = (
            self._w_mom   * zscore(mom) +
            self._w_vol   * zscore(lvol) +
            self._w_trend * zscore(trend)
        )
        return score.dropna()

    def _should_rebalance(self, date: pd.Timestamp) -> bool:
        if self._last_rebal is None:
            return True
        return date.month != self._last_rebal.month
