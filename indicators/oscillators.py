"""
indicators/oscillators.py
Williams %R, Ultimate Oscillator, DPO, TRIX, Stochastic RSI,
Know Sure Thing (KST), Awesome Oscillator, DEMA Oscillator
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.moving_averages import MovingAverages as MA


class Oscillators:
    """Oscillator indicators not covered in momentum.py."""

    # ──────────────────────────────────────────
    # Williams %R
    # ──────────────────────────────────────────
    @staticmethod
    def williams_r(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Williams %R (-100 to 0)."""
        highest_high = high.rolling(period).max()
        lowest_low   = low.rolling(period).min()
        wr = -100 * (highest_high - close) / (highest_high - lowest_low + 1e-10)
        return wr.rename("williams_r")

    # ──────────────────────────────────────────
    # Ultimate Oscillator
    # ──────────────────────────────────────────
    @staticmethod
    def ultimate_oscillator(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        p1: int = 7,
        p2: int = 14,
        p3: int = 28,
        w1: float = 4.0,
        w2: float = 2.0,
        w3: float = 1.0,
    ) -> pd.Series:
        """Williams Ultimate Oscillator."""
        prev_close = close.shift(1)
        bp = close - pd.concat([low, prev_close], axis=1).min(axis=1)
        tr = pd.concat([high, prev_close], axis=1).max(axis=1) - \
             pd.concat([low,  prev_close], axis=1).min(axis=1)

        avg1 = bp.rolling(p1).sum() / (tr.rolling(p1).sum() + 1e-10)
        avg2 = bp.rolling(p2).sum() / (tr.rolling(p2).sum() + 1e-10)
        avg3 = bp.rolling(p3).sum() / (tr.rolling(p3).sum() + 1e-10)
        uo = 100 * (w1 * avg1 + w2 * avg2 + w3 * avg3) / (w1 + w2 + w3)
        return uo.rename("ultimate_osc")

    # ──────────────────────────────────────────
    # DPO (Detrended Price Oscillator)
    # ──────────────────────────────────────────
    @staticmethod
    def dpo(close: pd.Series, period: int = 20) -> pd.Series:
        """Detrended Price Oscillator."""
        shift = period // 2 + 1
        sma = MA.sma(close, period)
        return (close.shift(shift) - sma).rename("dpo")

    # ──────────────────────────────────────────
    # TRIX
    # ──────────────────────────────────────────
    @staticmethod
    def trix(close: pd.Series, period: int = 15, signal: int = 9) -> pd.DataFrame:
        """TRIX: 1-period % ROC of a triple-smoothed EMA."""
        e1 = MA.ema(close, period)
        e2 = MA.ema(e1, period)
        e3 = MA.ema(e2, period)
        trix_line = e3.pct_change() * 100
        trix_sig  = MA.ema(trix_line, signal)
        return pd.DataFrame({"trix": trix_line, "trix_signal": trix_sig})

    # ──────────────────────────────────────────
    # Stochastic RSI
    # ──────────────────────────────────────────
    @staticmethod
    def stoch_rsi(
        close: pd.Series,
        rsi_period: int = 14,
        stoch_period: int = 14,
        k_period: int = 3,
        d_period: int = 3,
    ) -> pd.DataFrame:
        """Stochastic RSI %K and %D."""
        from indicators.momentum import Momentum
        rsi = Momentum.rsi(close, rsi_period)
        rsi_min = rsi.rolling(stoch_period).min()
        rsi_max = rsi.rolling(stoch_period).max()
        stoch_k = 100 * (rsi - rsi_min) / (rsi_max - rsi_min + 1e-10)
        k = MA.sma(stoch_k, k_period)
        d = MA.sma(k, d_period)
        return pd.DataFrame({"stoch_rsi_k": k, "stoch_rsi_d": d})

    # ──────────────────────────────────────────
    # Know Sure Thing (KST)
    # ──────────────────────────────────────────
    @staticmethod
    def kst(
        close: pd.Series,
        r1: int = 10, r2: int = 13, r3: int = 14, r4: int = 15,
        n1: int = 10, n2: int = 13, n3: int = 14, n4: int = 15,
        signal: int = 9,
    ) -> pd.DataFrame:
        """Know Sure Thing (KST) oscillator."""
        def roc(s: pd.Series, n: int) -> pd.Series:
            return (s - s.shift(n)) / s.shift(n) * 100

        rc1 = MA.sma(roc(close, r1), n1)
        rc2 = MA.sma(roc(close, r2), n2)
        rc3 = MA.sma(roc(close, r3), n3)
        rc4 = MA.sma(roc(close, r4), n4)
        kst_line = rc1 + 2 * rc2 + 3 * rc3 + 4 * rc4
        kst_sig  = MA.sma(kst_line, signal)
        return pd.DataFrame({"kst": kst_line, "kst_signal": kst_sig})

    # ──────────────────────────────────────────
    # Awesome Oscillator
    # ──────────────────────────────────────────
    @staticmethod
    def awesome_oscillator(
        high: pd.Series,
        low: pd.Series,
        fast: int = 5,
        slow: int = 34,
    ) -> pd.Series:
        """Awesome Oscillator by Bill Williams."""
        midpoint = (high + low) / 2
        ao = MA.sma(midpoint, fast) - MA.sma(midpoint, slow)
        return ao.rename("awesome_osc")

    # ──────────────────────────────────────────
    # Balance of Power
    # ──────────────────────────────────────────
    @staticmethod
    def balance_of_power(
        open_: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Balance of Power."""
        bop = (close - open_) / (high - low + 1e-10)
        return MA.sma(bop, period).rename("bop")

    # ──────────────────────────────────────────
    # Chande Forecast Oscillator
    # ──────────────────────────────────────────
    @staticmethod
    def cfo(close: pd.Series, period: int = 14) -> pd.Series:
        """Chande Forecast Oscillator."""
        linreg = close.rolling(period).apply(
            lambda x: np.polyval(np.polyfit(range(len(x)), x, 1), len(x) - 1),
            raw=True,
        )
        return (100 * (close - linreg) / (close + 1e-10)).rename("cfo")

    # ──────────────────────────────────────────
    # Batch
    # ──────────────────────────────────────────
    @staticmethod
    def all_oscillators(
        open_: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
    ) -> pd.DataFrame:
        o = Oscillators
        return pd.concat([
            o.williams_r(high, low, close).to_frame(),
            o.ultimate_oscillator(high, low, close).to_frame(),
            o.dpo(close).to_frame(),
            o.trix(close),
            o.stoch_rsi(close),
            o.kst(close),
            o.awesome_oscillator(high, low).to_frame(),
            o.balance_of_power(open_, high, low, close).to_frame(),
            o.cfo(close).to_frame(),
        ], axis=1)
