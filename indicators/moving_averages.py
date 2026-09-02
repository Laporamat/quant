"""
indicators/moving_averages.py
SMA, EMA, WMA, DEMA, TEMA, HMA, VWMA, KAMA, ZLEMA, T3, JMA
All functions accept a pandas Series and return a pandas Series.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class MovingAverages:
    """Static factory for all moving-average variants."""

    # ──────────────────────────────────────────
    # Simple Moving Average
    # ──────────────────────────────────────────
    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average."""
        return series.rolling(window=period, min_periods=period).mean()

    # ──────────────────────────────────────────
    # Exponential Moving Average
    # ──────────────────────────────────────────
    @staticmethod
    def ema(series: pd.Series, period: int, adjust: bool = False) -> pd.Series:
        """Exponential Moving Average (Wilder / standard EMA)."""
        return series.ewm(span=period, adjust=adjust, min_periods=period).mean()

    # ──────────────────────────────────────────
    # Weighted Moving Average
    # ──────────────────────────────────────────
    @staticmethod
    def wma(series: pd.Series, period: int) -> pd.Series:
        """Linearly Weighted Moving Average."""
        weights = np.arange(1, period + 1, dtype=float)

        def _wma(x: np.ndarray) -> float:
            return float(np.dot(x, weights) / weights.sum())

        return series.rolling(window=period, min_periods=period).apply(_wma, raw=True)

    # ──────────────────────────────────────────
    # Double EMA
    # ──────────────────────────────────────────
    @staticmethod
    def dema(series: pd.Series, period: int) -> pd.Series:
        """Double Exponential Moving Average: 2*EMA - EMA(EMA)."""
        e = MovingAverages.ema(series, period)
        return 2 * e - MovingAverages.ema(e, period)

    # ──────────────────────────────────────────
    # Triple EMA
    # ──────────────────────────────────────────
    @staticmethod
    def tema(series: pd.Series, period: int) -> pd.Series:
        """Triple Exponential Moving Average: 3*EMA - 3*EMA(EMA) + EMA(EMA(EMA))."""
        e1 = MovingAverages.ema(series, period)
        e2 = MovingAverages.ema(e1, period)
        e3 = MovingAverages.ema(e2, period)
        return 3 * e1 - 3 * e2 + e3

    # ──────────────────────────────────────────
    # Hull Moving Average
    # ──────────────────────────────────────────
    @staticmethod
    def hma(series: pd.Series, period: int) -> pd.Series:
        """Hull Moving Average: WMA(2*WMA(n/2) - WMA(n), sqrt(n))."""
        half = max(int(period / 2), 1)
        sqrt_n = max(int(np.sqrt(period)), 1)
        raw = 2 * MovingAverages.wma(series, half) - MovingAverages.wma(series, period)
        return MovingAverages.wma(raw, sqrt_n)

    # ──────────────────────────────────────────
    # Volume-Weighted MA
    # ──────────────────────────────────────────
    @staticmethod
    def vwma(close: pd.Series, volume: pd.Series, period: int) -> pd.Series:
        """Volume-Weighted Moving Average."""
        pv = close * volume
        return pv.rolling(window=period, min_periods=period).sum() / \
               volume.rolling(window=period, min_periods=period).sum()

    # ──────────────────────────────────────────
    # Kaufman Adaptive MA
    # ──────────────────────────────────────────
    @staticmethod
    def kama(series: pd.Series, period: int = 10, fast: int = 2, slow: int = 30) -> pd.Series:
        """
        Kaufman Adaptive Moving Average.
        Adjusts its speed based on the efficiency ratio of price movement.
        """
        fast_sc = 2 / (fast + 1)
        slow_sc = 2 / (slow + 1)
        close = series.values.astype(float)
        kama_vals = np.full(len(close), np.nan)

        # seed with first valid value
        start = period - 1
        kama_vals[start] = close[start]

        for i in range(start + 1, len(close)):
            direction = abs(close[i] - close[i - period])
            volatility = np.sum(np.abs(np.diff(close[i - period: i + 1])))
            er = direction / volatility if volatility != 0 else 0.0
            sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
            kama_vals[i] = kama_vals[i - 1] + sc * (close[i] - kama_vals[i - 1])

        return pd.Series(kama_vals, index=series.index, name="kama")

    # ──────────────────────────────────────────
    # Zero-Lag EMA
    # ──────────────────────────────────────────
    @staticmethod
    def zlema(series: pd.Series, period: int) -> pd.Series:
        """Zero-Lag EMA: EMA applied to (close + (close - close[lag]))."""
        lag = (period - 1) // 2
        adjusted = series + (series - series.shift(lag))
        return MovingAverages.ema(adjusted, period)

    # ──────────────────────────────────────────
    # T3 Moving Average (Tillson)
    # ──────────────────────────────────────────
    @staticmethod
    def t3(series: pd.Series, period: int = 5, vfactor: float = 0.7) -> pd.Series:
        """
        T3 Moving Average by Tim Tillson.
        Uses a series of 6 EMAs for a smooth, low-lag result.
        """
        c1 = -(vfactor ** 3)
        c2 = 3 * vfactor ** 2 + 3 * vfactor ** 3
        c3 = -6 * vfactor ** 2 - 3 * vfactor - 3 * vfactor ** 3
        c4 = 1 + 3 * vfactor + vfactor ** 3 + 3 * vfactor ** 2

        e1 = MovingAverages.ema(series, period)
        e2 = MovingAverages.ema(e1, period)
        e3 = MovingAverages.ema(e2, period)
        e4 = MovingAverages.ema(e3, period)
        e5 = MovingAverages.ema(e4, period)
        e6 = MovingAverages.ema(e5, period)
        return c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3

    # ──────────────────────────────────────────
    # Wilder Smoothed MA
    # ──────────────────────────────────────────
    @staticmethod
    def rma(series: pd.Series, period: int) -> pd.Series:
        """Wilder's smoothed moving average (RMA), used in RSI/ATR."""
        alpha = 1.0 / period
        return series.ewm(alpha=alpha, adjust=False, min_periods=period).mean()

    # ──────────────────────────────────────────
    # Crossover signal helpers
    # ──────────────────────────────────────────
    @staticmethod
    def crossover(fast: pd.Series, slow: pd.Series) -> pd.Series:
        """Return +1 when fast crosses above slow, -1 when below, 0 otherwise."""
        diff = fast - slow
        signal = np.where(
            (diff > 0) & (diff.shift(1) <= 0), 1,
            np.where((diff < 0) & (diff.shift(1) >= 0), -1, 0)
        )
        return pd.Series(signal, index=fast.index, name="crossover")

    @staticmethod
    def golden_cross(close: pd.Series, fast: int = 50, slow: int = 200) -> pd.Series:
        """Return 1 on golden cross (fast SMA crosses above slow SMA), -1 on death cross."""
        sma_fast = MovingAverages.sma(close, fast)
        sma_slow = MovingAverages.sma(close, slow)
        return MovingAverages.crossover(sma_fast, sma_slow)

    # ──────────────────────────────────────────
    # Batch compute
    # ──────────────────────────────────────────
    @staticmethod
    def all_mas(close: pd.Series) -> pd.DataFrame:
        """Compute all MAs and return as a DataFrame."""
        ma = MovingAverages
        return pd.DataFrame({
            "sma_20":   ma.sma(close, 20),
            "sma_50":   ma.sma(close, 50),
            "sma_200":  ma.sma(close, 200),
            "ema_12":   ma.ema(close, 12),
            "ema_26":   ma.ema(close, 26),
            "ema_50":   ma.ema(close, 50),
            "wma_20":   ma.wma(close, 20),
            "dema_20":  ma.dema(close, 20),
            "tema_20":  ma.tema(close, 20),
            "hma_20":   ma.hma(close, 20),
            "kama_10":  ma.kama(close, 10),
            "zlema_20": ma.zlema(close, 20),
            "t3_5":     ma.t3(close, 5),
        })
