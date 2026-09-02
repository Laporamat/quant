"""
strategies/pairs_trading.py
Statistical arbitrage pairs trading using spread z-score.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from strategies.base_strategy import BaseStrategy, Signal, SignalType
from stats.cointegration import CointegrationTests


class PairsTradingStrategy(BaseStrategy):
    """
    Pairs trading on a pre-specified pair (asset1, asset2).

    Entry rules
    -----------
    z > entry_z  → short asset1, long asset2
    z < -entry_z → long asset1, short asset2
    |z| < exit_z → close both legs

    Parameters
    ----------
    asset1       : first ticker
    asset2       : second ticker
    lookback     : rolling window for spread z-score (default 63)
    entry_z      : z-score threshold to enter (default 2.0)
    exit_z       : z-score threshold to exit (default 0.5)
    hedge_ratio  : fixed hedge ratio; None = rolling OLS (default None)
    """
    name = "pairs_trading"

    def prepare(self, data: Dict[str, pd.DataFrame]) -> None:
        self._a1      = self.get_param("asset1")
        self._a2      = self.get_param("asset2")
        self._lookback = self.get_param("lookback", 63)
        self._entry_z  = self.get_param("entry_z", 2.0)
        self._exit_z   = self.get_param("exit_z", 0.5)
        self._hr       = self.get_param("hedge_ratio")   # may be None
        self._position: Optional[str] = None  # "long_a1" | "short_a1" | None

        if not self._a1 or not self._a2:
            raise ValueError("pairs_trading requires 'asset1' and 'asset2' params")

        # Pre-compute spread
        df1 = data.get(self._a1)
        df2 = data.get(self._a2)
        if df1 is None or df2 is None:
            self._spread = pd.Series(dtype=float)
            return

        aligned = pd.concat([df1["close"], df2["close"]], axis=1, keys=[self._a1, self._a2]).dropna()
        if self._hr is None:
            # Rolling OLS hedge ratio
            hedge = aligned[self._a1].rolling(self._lookback).apply(
                lambda y: self._ols_beta(y, aligned[self._a2].loc[y.index]),
                raw=False,
            )
        else:
            hedge = pd.Series(float(self._hr), index=aligned.index)

        self._spread = aligned[self._a1] - hedge * aligned[self._a2]
        self._hedge  = hedge
        self._prices = aligned

    def generate_signals(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.DataFrame],
        portfolio_state: Optional[Dict] = None,
    ) -> List[Signal]:
        if self._spread.empty:
            return []

        spr = self._spread.loc[:date].dropna()
        if len(spr) < self._lookback:
            return []

        roll_mean = spr.rolling(self._lookback).mean().iloc[-1]
        roll_std  = spr.rolling(self._lookback).std(ddof=1).iloc[-1]
        if pd.isna(roll_std) or roll_std == 0:
            return []

        z = (spr.iloc[-1] - roll_mean) / roll_std
        p1 = float(self._prices[self._a1].loc[:date].iloc[-1])
        p2 = float(self._prices[self._a2].loc[:date].iloc[-1])
        signals: List[Signal] = []

        if self._position is None:
            if z > self._entry_z:          # spread too high → mean-revert down
                signals += [
                    Signal(date=date, ticker=self._a1, signal=SignalType.SHORT, strength=0.5,
                           price=p1, meta={"z": float(z)}),
                    Signal(date=date, ticker=self._a2, signal=SignalType.BUY,   strength=0.5,
                           price=p2, meta={"z": float(z)}),
                ]
                self._position = "short_a1"
            elif z < -self._entry_z:       # spread too low → mean-revert up
                signals += [
                    Signal(date=date, ticker=self._a1, signal=SignalType.BUY,   strength=0.5,
                           price=p1, meta={"z": float(z)}),
                    Signal(date=date, ticker=self._a2, signal=SignalType.SHORT, strength=0.5,
                           price=p2, meta={"z": float(z)}),
                ]
                self._position = "long_a1"
        else:
            if abs(z) < self._exit_z:      # spread mean-reverted → close
                if self._position == "short_a1":
                    signals += [
                        Signal(date=date, ticker=self._a1, signal=SignalType.COVER, strength=0.5, price=p1),
                        Signal(date=date, ticker=self._a2, signal=SignalType.SELL,  strength=0.5, price=p2),
                    ]
                else:
                    signals += [
                        Signal(date=date, ticker=self._a1, signal=SignalType.SELL,  strength=0.5, price=p1),
                        Signal(date=date, ticker=self._a2, signal=SignalType.COVER, strength=0.5, price=p2),
                    ]
                self._position = None

        return signals

    @staticmethod
    def _ols_beta(y: pd.Series, x: pd.Series) -> float:
        aligned = pd.concat([y, x], axis=1).dropna()
        if len(aligned) < 2:
            return 1.0
        cov = np.cov(aligned.values.T)
        return float(cov[0, 1] / cov[1, 1]) if cov[1, 1] != 0 else 1.0
