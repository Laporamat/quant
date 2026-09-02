"""
strategies/sma_crossover.py
SMA / EMA golden-cross / death-cross trend-following strategy.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import pandas as pd

from strategies.base_strategy import BaseStrategy, Signal, SignalType
from indicators.moving_averages import MovingAverages as MA


class SMACrossoverStrategy(BaseStrategy):
    """
    Long when fast MA crosses above slow MA, flat otherwise.

    Parameters
    ----------
    fast    : fast MA period (default 50)
    slow    : slow MA period (default 200)
    ma_type : "sma" | "ema" (default "sma")
    tickers : list of tickers (default: all in data)
    """
    name = "sma_crossover"

    def prepare(self, data: Dict[str, pd.DataFrame]) -> None:
        fast    = self.get_param("fast", 50)
        slow    = self.get_param("slow", 200)
        ma_type = self.get_param("ma_type", "sma")
        tickers = self.get_param("tickers") or list(data.keys())

        fn = MA.ema if ma_type == "ema" else MA.sma

        for ticker in tickers:
            df = data.get(ticker)
            if df is None or df.empty:
                continue
            close = df["close"]
            self._indicators[ticker] = pd.DataFrame({
                "fast_ma": fn(close, fast),
                "slow_ma": fn(close, slow),
                "close":   close,
            })
        self._positions: Dict[str, bool] = {t: False for t in tickers}

    def generate_signals(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.DataFrame],
        portfolio_state: Optional[Dict] = None,
    ) -> List[Signal]:
        signals: List[Signal] = []

        for ticker, ind_df in self._indicators.items():
            sliced = ind_df.loc[:date].dropna()
            if len(sliced) < 2:
                continue

            curr = sliced.iloc[-1]
            prev = sliced.iloc[-2]
            in_long = self._positions.get(ticker, False)

            # Golden cross – enter long
            if (curr["fast_ma"] > curr["slow_ma"]) and (prev["fast_ma"] <= prev["slow_ma"]):
                if not in_long:
                    signals.append(Signal(
                        date=date, ticker=ticker,
                        signal=SignalType.BUY,
                        strength=1.0,
                        price=float(curr["close"]),
                        meta={"fast_ma": float(curr["fast_ma"]),
                              "slow_ma": float(curr["slow_ma"])},
                    ))
                    self._positions[ticker] = True

            # Death cross – exit long
            elif (curr["fast_ma"] < curr["slow_ma"]) and (prev["fast_ma"] >= prev["slow_ma"]):
                if in_long:
                    signals.append(Signal(
                        date=date, ticker=ticker,
                        signal=SignalType.SELL,
                        strength=1.0,
                        price=float(curr["close"]),
                        meta={"fast_ma": float(curr["fast_ma"]),
                              "slow_ma": float(curr["slow_ma"])},
                    ))
                    self._positions[ticker] = False

        return signals
