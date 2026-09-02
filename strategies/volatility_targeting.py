"""
strategies/volatility_targeting.py
Volatility-targeting and risk-parity portfolio allocation.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from strategies.base_strategy import BaseStrategy, Signal, SignalType


class VolatilityTargetingStrategy(BaseStrategy):
    """
    Scales position sizes so each ticker contributes equal annualised vol,
    and the portfolio targets a specified total vol level.

    Parameters
    ----------
    target_vol      : annual portfolio volatility target (default 0.10 = 10%)
    vol_lookback    : days for realised vol estimation (default 63)
    rebalance_freq  : "M" monthly | "W" weekly | "D" daily
    max_leverage    : max sum of weights (default 1.0 = no leverage)
    min_weight      : floor per ticker (default 0.0)
    max_weight      : cap per ticker (default 0.4)
    """
    name = "volatility_targeting"

    def prepare(self, data: Dict[str, pd.DataFrame]) -> None:
        self._tickers     = self.get_param("tickers") or list(data.keys())
        self._target_vol  = self.get_param("target_vol", 0.10)
        self._vol_look    = self.get_param("vol_lookback", 63)
        self._freq        = self.get_param("rebalance_freq", "M")
        self._max_lev     = self.get_param("max_leverage", 1.0)
        self._min_w       = self.get_param("min_weight", 0.0)
        self._max_w       = self.get_param("max_weight", 0.40)
        self._last_rebal: Optional[pd.Timestamp] = None
        self._weights:    Dict[str, float] = {}

        frames: Dict[str, pd.Series] = {}
        for t in self._tickers:
            df = data.get(t)
            if df is not None and not df.empty:
                frames[t] = df["close"].pct_change()
        self._returns = pd.DataFrame(frames)

    def generate_signals(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.DataFrame],
        portfolio_state: Optional[Dict] = None,
    ) -> List[Signal]:
        if not self._should_rebalance(date):
            return []
        self._last_rebal = date

        rets = self._returns.loc[:date].tail(self._vol_look).dropna(how="all")
        if len(rets) < 10:
            return []

        new_weights = self._compute_weights(rets)
        if not new_weights:
            return []

        signals: List[Signal] = []
        for ticker, w in new_weights.items():
            df = data.get(ticker)
            if df is None:
                continue
            row = df.loc[:date]
            if row.empty:
                continue
            price = float(row["close"].iloc[-1])
            old_w = self._weights.get(ticker, 0.0)

            if w > 0 and old_w == 0:
                signals.append(Signal(date=date, ticker=ticker, signal=SignalType.BUY,
                                      strength=w, price=price,
                                      meta={"weight": w, "type": "vol_target"}))
            elif w == 0 and old_w > 0:
                signals.append(Signal(date=date, ticker=ticker, signal=SignalType.SELL,
                                      strength=1.0, price=price))
            elif abs(w - old_w) > 0.01:   # rebalance if drift > 1%
                signals.append(Signal(date=date, ticker=ticker, signal=SignalType.BUY,
                                      strength=w, price=price,
                                      meta={"weight": w, "rebalance": True}))

        self._weights = new_weights
        return signals

    def _compute_weights(self, rets: pd.DataFrame) -> Dict[str, float]:
        """Inverse-volatility weights scaled to target portfolio vol."""
        ann = np.sqrt(252)
        vols = rets.std(ddof=1) * ann
        vols = vols.replace(0, np.nan).dropna()
        if vols.empty:
            return {}

        inv_vol = 1.0 / vols
        raw_w   = inv_vol / inv_vol.sum()

        # Scale to target portfolio vol (diagonal covariance approx.)
        port_vol = float(np.sqrt((raw_w**2 * vols**2).sum()))
        scale    = self._target_vol / port_vol if port_vol > 0 else 1.0
        scale    = min(scale, self._max_lev / raw_w.sum())

        weights = (raw_w * scale).clip(lower=self._min_w, upper=self._max_w)
        # Normalise to sum ≤ max_leverage
        if weights.sum() > self._max_lev:
            weights = weights / weights.sum() * self._max_lev

        return {t: float(w) for t, w in weights.items()}

    def _should_rebalance(self, date: pd.Timestamp) -> bool:
        if self._last_rebal is None:
            return True
        if self._freq == "D":
            return True
        if self._freq == "W":
            return date.isocalendar()[1] != self._last_rebal.isocalendar()[1]
        return date.month != self._last_rebal.month
