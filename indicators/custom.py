"""
indicators/custom.py
Composite indicators and signal aggregators:
- TrendScore, MomentumScore, VolatilityRegime, CompositeSignal
- SignalAggregator: combines multiple indicator signals into one
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.moving_averages import MovingAverages as MA
from indicators.momentum import Momentum
from indicators.volatility import Volatility
from indicators.trend import Trend
from indicators.volume import Volume


class CustomIndicators:
    """Composite and custom indicators built on top of base indicators."""

    # ──────────────────────────────────────────
    # Trend Strength Score  (0–100)
    # ──────────────────────────────────────────
    @staticmethod
    def trend_score(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
    ) -> pd.Series:
        """
        Composite trend strength score (0-100).
        Combines ADX, price vs SMA200, and golden-cross alignment.
        """
        adx_df   = Trend.adx(high, low, close, 14)
        adx_norm = adx_df["adx"].clip(0, 50) / 50 * 100   # 0–100

        sma200   = MA.sma(close, 200)
        above200 = (close > sma200).astype(float) * 100

        sma50    = MA.sma(close, 50)
        sma20    = MA.sma(close, 20)
        alignment = ((sma20 > sma50) & (sma50 > sma200)).astype(float) * 100

        score = (adx_norm * 0.4 + above200 * 0.3 + alignment * 0.3)
        return score.rename("trend_score")

    # ──────────────────────────────────────────
    # Momentum Score  (-100 to +100)
    # ──────────────────────────────────────────
    @staticmethod
    def momentum_score(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
    ) -> pd.Series:
        """
        Composite momentum score (-100 to +100).
        Combines RSI, MACD, and MFI.
        """
        rsi   = Momentum.rsi(close, 14)
        rsi_c = (rsi - 50) * 2         # scaled to -100/+100

        macd_df  = Momentum.macd(close)
        macd_c   = np.sign(macd_df["macd_hist"]) * 100

        mfi   = Momentum.mfi(high, low, close, volume, 14)
        mfi_c = (mfi - 50) * 2

        score = (rsi_c * 0.4 + macd_c * 0.3 + mfi_c * 0.3)
        return score.rename("momentum_score")

    # ──────────────────────────────────────────
    # Volatility Regime  (0=low, 1=normal, 2=high)
    # ──────────────────────────────────────────
    @staticmethod
    def volatility_regime(
        close: pd.Series,
        period: int = 21,
        low_pct: float = 0.25,
        high_pct: float = 0.75,
    ) -> pd.Series:
        """
        Classify current HV percentile into:
        0 = low vol  (< 25th percentile over rolling 252 days)
        1 = normal vol
        2 = high vol (> 75th percentile)
        """
        hv = Volatility.historical_volatility(close, period)
        roll_low  = hv.rolling(252, min_periods=63).quantile(low_pct)
        roll_high = hv.rolling(252, min_periods=63).quantile(high_pct)
        regime = pd.Series(1, index=close.index)
        regime[hv < roll_low]  = 0
        regime[hv > roll_high] = 2
        return regime.rename("vol_regime")

    # ──────────────────────────────────────────
    # Composite Signal  (-1 / 0 / +1)
    # ──────────────────────────────────────────
    @staticmethod
    def composite_signal(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        trend_threshold: float = 50.0,
        momentum_threshold: float = 20.0,
    ) -> pd.Series:
        """
        Overall composite signal:
        +1 = strong buy (trend + momentum both positive)
        -1 = strong sell
         0 = neutral
        """
        ts = CustomIndicators.trend_score(high, low, close)
        ms = CustomIndicators.momentum_score(high, low, close, volume)

        long_cond  = (ts >= trend_threshold) & (ms >= momentum_threshold)
        short_cond = (ts <= (100 - trend_threshold)) & (ms <= -momentum_threshold)

        signal = pd.Series(0, index=close.index)
        signal[long_cond]  = 1
        signal[short_cond] = -1
        return signal.rename("composite_signal")

    # ──────────────────────────────────────────
    # Price-Relative Strength vs benchmark
    # ──────────────────────────────────────────
    @staticmethod
    def relative_strength(
        close: pd.Series,
        benchmark_close: pd.Series,
        period: int = 63,
    ) -> pd.Series:
        """
        Relative strength of stock vs benchmark over *period* bars.
        RS = (stock_return / benchmark_return) on a rolling basis.
        """
        stock_ret = close / close.shift(period)
        bench_ret = benchmark_close / benchmark_close.shift(period)
        return (stock_ret / bench_ret.replace(0, np.nan)).rename("relative_strength")

    # ──────────────────────────────────────────
    # Fractal Indicator (Bill Williams)
    # ──────────────────────────────────────────
    @staticmethod
    def fractals(high: pd.Series, low: pd.Series, n: int = 2) -> pd.DataFrame:
        """
        Fractal highs (high[i] is highest of 2n+1 bars centred on i)
        and fractal lows.
        """
        frac_high = pd.Series(np.nan, index=high.index)
        frac_low  = pd.Series(np.nan, index=low.index)

        for i in range(n, len(high) - n):
            window_h = high.iloc[i - n: i + n + 1]
            window_l = low.iloc[i - n: i + n + 1]
            if high.iloc[i] == window_h.max():
                frac_high.iloc[i] = high.iloc[i]
            if low.iloc[i] == window_l.min():
                frac_low.iloc[i] = low.iloc[i]

        return pd.DataFrame({"fractal_high": frac_high, "fractal_low": frac_low})

    # ──────────────────────────────────────────
    # Pivot Points (Classic)
    # ──────────────────────────────────────────
    @staticmethod
    def pivot_points(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
    ) -> pd.DataFrame:
        """Classic daily pivot points (PP, R1-R3, S1-S3)."""
        pp = (high.shift(1) + low.shift(1) + close.shift(1)) / 3
        r1 = 2 * pp - low.shift(1)
        r2 = pp + (high.shift(1) - low.shift(1))
        r3 = high.shift(1) + 2 * (pp - low.shift(1))
        s1 = 2 * pp - high.shift(1)
        s2 = pp - (high.shift(1) - low.shift(1))
        s3 = low.shift(1) - 2 * (high.shift(1) - pp)
        return pd.DataFrame({"pp": pp, "r1": r1, "r2": r2, "r3": r3,
                              "s1": s1, "s2": s2, "s3": s3})

    # ──────────────────────────────────────────
    # Signal Aggregator
    # ──────────────────────────────────────────
    @staticmethod
    def aggregate_signals(signals: pd.DataFrame, weights: dict | None = None) -> pd.Series:
        """
        Combine multiple signal columns (-1/0/+1) into a weighted score.

        Parameters
        ----------
        signals : DataFrame where each column is a signal (-1, 0, 1)
        weights : dict of {column: weight}; equal weights if None

        Returns
        -------
        Series of aggregate scores in [-1, +1]
        """
        if weights is None:
            weights = {col: 1.0 for col in signals.columns}
        total_weight = sum(abs(w) for w in weights.values()) or 1.0
        score = sum(
            signals[col] * w
            for col, w in weights.items()
            if col in signals.columns
        ) / total_weight
        return score.rename("agg_signal")

    # ──────────────────────────────────────────
    # Full compute
    # ──────────────────────────────────────────
    @staticmethod
    def all_custom(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        benchmark_close: pd.Series | None = None,
    ) -> pd.DataFrame:
        c = CustomIndicators
        frames: list[pd.Series | pd.DataFrame] = [
            c.trend_score(high, low, close).to_frame(),
            c.momentum_score(high, low, close, volume).to_frame(),
            c.volatility_regime(close).to_frame(),
            c.composite_signal(high, low, close, volume).to_frame(),
            c.fractals(high, low),
            c.pivot_points(high, low, close),
        ]
        if benchmark_close is not None:
            frames.append(c.relative_strength(close, benchmark_close).to_frame())
        return pd.concat(frames, axis=1)
