"""
strategies/buy_and_hold.py
Buy and hold all tickers with equal weight on first available bar.
Used as a benchmark.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import pandas as pd

from strategies.base_strategy import BaseStrategy, Signal, SignalType


class BuyAndHoldStrategy(BaseStrategy):
    """
    Buy equal-weight positions on the first bar, never sell.

    Parameters
    ----------
    tickers : list of ticker symbols to buy (default: all in data)
    weight  : fraction of capital per ticker (default: 1/n)
    """
    name = "buy_and_hold"

    def __init__(self, params: Optional[Dict] = None) -> None:
        super().__init__(params)
        self._entered: set = set()

    def prepare(self, data: Dict[str, pd.DataFrame]) -> None:
        self._tickers = self.get_param("tickers") or list(data.keys())
        self._entered.clear()

    def generate_signals(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.DataFrame],
        portfolio_state: Optional[Dict] = None,
    ) -> List[Signal]:
        signals: List[Signal] = []
        n = len(self._tickers)
        weight = self.get_param("weight") or (1.0 / n if n > 0 else 1.0)

        for ticker in self._tickers:
            if ticker in self._entered:
                continue
            df = data.get(ticker)
            if df is None:
                continue
            bar = self._latest_bar(df, date)
            if bar is None:
                continue
            signals.append(Signal(
                date=date,
                ticker=ticker,
                signal=SignalType.BUY,
                strength=weight,
                price=float(bar["close"]),
                meta={"strategy": self.name},
            ))
            self._entered.add(ticker)

        return signals
