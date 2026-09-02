"""
strategies/mean_reversion.py
RSI and Bollinger Band mean-reversion strategy.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import pandas as pd

from strategies.base_strategy import BaseStrategy, Signal, SignalType
from indicators.momentum import Momentum
from indicators.volatility import Volatility


class MeanReversionStrategy(BaseStrategy):
    """
    Mean reversion using RSI and/or Bollinger Bands.

    Parameters
    ----------
    mode         : "rsi" | "bollinger" | "combined"
    rsi_period   : RSI period (default 14)
    rsi_oversold : RSI buy threshold (default 30)
    rsi_overbought: RSI sell threshold (default 70)
    bb_period    : Bollinger period (default 20)
    bb_std       : Bollinger std (default 2.0)
    hold_days    : max hold period in days (default 10)
    """
    name = "mean_reversion"

    def prepare(self, data: Dict[str, pd.DataFrame]) -> None:
        tickers         = self.get_param("tickers") or list(data.keys())
        rsi_period      = self.get_param("rsi_period", 14)
        rsi_oversold    = self.get_param("rsi_oversold", 30)
        rsi_overbought  = self.get_param("rsi_overbought", 70)
        bb_period       = self.get_param("bb_period", 20)
        bb_std          = self.get_param("bb_std", 2.0)
        self._mode      = self.get_param("mode", "combined")
        self._hold_days = self.get_param("hold_days", 10)
        self._thresholds = {"rsi_oversold": rsi_oversold, "rsi_overbought": rsi_overbought}

        for ticker in tickers:
            df = data.get(ticker)
            if df is None or df.empty:
                continue
            rsi = Momentum.rsi(df["close"], rsi_period)
            bb  = Volatility.bollinger_bands(df["close"], bb_period, bb_std)
            self._indicators[ticker] = pd.concat([rsi, bb, df["close"]], axis=1)

        self._entry_dates: Dict[str, pd.Timestamp] = {}
        self._positions:   Dict[str, str] = {}     # ticker -> "long" | "short"

    def generate_signals(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.DataFrame],
        portfolio_state: Optional[Dict] = None,
    ) -> List[Signal]:
        signals: List[Signal] = []

        for ticker, ind_df in self._indicators.items():
            sliced = ind_df.loc[:date].dropna()
            if sliced.empty:
                continue
            curr = sliced.iloc[-1]
            close    = float(curr["close"])
            rsi      = float(curr["rsi"])
            bb_upper = float(curr["bb_upper"])
            bb_lower = float(curr["bb_lower"])
            in_pos   = self._positions.get(ticker)

            # ── Exit by hold-days rule ─────────────
            if in_pos and ticker in self._entry_dates:
                entry = self._entry_dates[ticker]
                if (date - entry).days >= self._hold_days:
                    sig_type = SignalType.SELL if in_pos == "long" else SignalType.COVER
                    signals.append(Signal(
                        date=date, ticker=ticker,
                        signal=sig_type, strength=1.0, price=close,
                        meta={"exit": "hold_days"},
                    ))
                    self._positions.pop(ticker, None)
                    self._entry_dates.pop(ticker, None)
                    continue

            # ── Entry signals ──────────────────────
            buy_rsi  = rsi < self._thresholds["rsi_oversold"]
            sell_rsi = rsi > self._thresholds["rsi_overbought"]
            buy_bb   = close < bb_lower
            sell_bb  = close > bb_upper

            if self._mode == "rsi":
                go_long  = buy_rsi
                go_short = sell_rsi
            elif self._mode == "bollinger":
                go_long  = buy_bb
                go_short = sell_bb
            else:  # combined
                go_long  = buy_rsi and buy_bb
                go_short = sell_rsi and sell_bb

            if go_long and in_pos != "long":
                if in_pos == "short":
                    signals.append(Signal(date=date, ticker=ticker,
                                          signal=SignalType.COVER, strength=1.0, price=close))
                signals.append(Signal(
                    date=date, ticker=ticker,
                    signal=SignalType.BUY, strength=1.0, price=close,
                    meta={"rsi": rsi, "bb_lower": bb_lower},
                ))
                self._positions[ticker]   = "long"
                self._entry_dates[ticker] = date

            elif go_short and in_pos != "short":
                if in_pos == "long":
                    signals.append(Signal(date=date, ticker=ticker,
                                          signal=SignalType.SELL, strength=1.0, price=close))
                signals.append(Signal(
                    date=date, ticker=ticker,
                    signal=SignalType.SHORT, strength=1.0, price=close,
                    meta={"rsi": rsi, "bb_upper": bb_upper},
                ))
                self._positions[ticker]   = "short"
                self._entry_dates[ticker] = date

        return signals
