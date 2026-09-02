"""
strategies/breakout.py
Donchian Channel and ATR-based breakout strategy.
"""
from __future__ import annotations

from typing import Dict, List, Optional
import pandas as pd

from strategies.base_strategy import BaseStrategy, Signal, SignalType
from indicators.volatility import Volatility


class BreakoutStrategy(BaseStrategy):
    """
    Long when price breaks above the Donchian upper band.
    Stop-loss at entry - ATR multiplier × ATR.

    Parameters
    ----------
    donchian_period : lookback for Donchian channels (default 20)
    atr_period      : ATR period (default 14)
    atr_stop_mult   : stop-loss = entry - mult × ATR (default 2.0)
    exit_period     : exit on break below short-period Donchian (default 10)
    """
    name = "breakout"

    def prepare(self, data: Dict[str, pd.DataFrame]) -> None:
        tickers       = self.get_param("tickers") or list(data.keys())
        don_period    = self.get_param("donchian_period", 20)
        atr_period    = self.get_param("atr_period", 14)
        exit_period   = self.get_param("exit_period", 10)

        for ticker in tickers:
            df = data.get(ticker)
            if df is None or df.empty:
                continue
            dc = Volatility.donchian_channels(df["high"], df["low"], don_period)
            dc_exit = Volatility.donchian_channels(df["high"], df["low"], exit_period)
            atr = Volatility.atr(df["high"], df["low"], df["close"], atr_period)
            self._indicators[ticker] = pd.concat([
                dc.rename(columns={"dc_upper": "dc_upper", "dc_lower": "dc_lower", "dc_mid": "dc_mid"}),
                dc_exit[["dc_lower"]].rename(columns={"dc_lower": "dc_lower_exit"}),
                atr.rename("atr"),
                df["close"],
                df["high"],
                df["low"],
            ], axis=1)

        self._positions: Dict[str, float] = {}   # ticker -> stop_price

    def generate_signals(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.DataFrame],
        portfolio_state: Optional[Dict] = None,
    ) -> List[Signal]:
        signals: List[Signal] = []
        atr_mult = self.get_param("atr_stop_mult", 2.0)

        for ticker, ind_df in self._indicators.items():
            sliced = ind_df.loc[:date].dropna()
            if len(sliced) < 2:
                continue

            curr = sliced.iloc[-1]
            prev = sliced.iloc[-2]
            close = float(curr["close"])
            atr   = float(curr["atr"]) if not pd.isna(curr["atr"]) else 0.0
            in_pos = ticker in self._positions

            # ── Stop-loss hit ──────────────────────
            if in_pos and close <= self._positions[ticker]:
                signals.append(Signal(
                    date=date, ticker=ticker,
                    signal=SignalType.SELL, strength=1.0, price=close,
                    meta={"exit": "stop_loss", "stop": self._positions[ticker]},
                ))
                del self._positions[ticker]
                continue

            # ── Donchian exit (short-period lower break) ──
            if in_pos and close < float(curr.get("dc_lower_exit", -1e9)):
                signals.append(Signal(
                    date=date, ticker=ticker,
                    signal=SignalType.SELL, strength=1.0, price=close,
                    meta={"exit": "donchian_exit"},
                ))
                del self._positions[ticker]
                continue

            # ── Entry: close breaks above previous Donchian upper ──
            if (not in_pos
                    and close > float(prev["dc_upper"])
                    and not pd.isna(prev["dc_upper"])):
                stop = close - atr_mult * atr
                self._positions[ticker] = stop
                signals.append(Signal(
                    date=date, ticker=ticker,
                    signal=SignalType.BUY, strength=1.0, price=close,
                    stop_loss=stop,
                    meta={"dc_upper": float(prev["dc_upper"]), "atr": atr},
                ))

            # ── Trailing stop update ──
            elif in_pos:
                new_stop = close - atr_mult * atr
                if new_stop > self._positions[ticker]:
                    self._positions[ticker] = new_stop

        return signals
