"""
indicators/momentum.py
RSI, Stochastic, ROC, MFI, CMO, MACD, PPO, DPO, Elder Ray, Momentum
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.moving_averages import MovingAverages as MA


class Momentum:
    """Momentum and oscillator indicators."""

    # ──────────────────────────────────────────
    # RSI  (Relative Strength Index)
    # ──────────────────────────────────────────
    @staticmethod
    def rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """RSI using Wilder's smoothing (RMA)."""
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = MA.rma(gain, period)
        avg_loss = MA.rma(loss, period)
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        return rsi.rename("rsi")

    # ──────────────────────────────────────────
    # Stochastic Oscillator
    # ──────────────────────────────────────────
    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
        smooth_k: int = 3,
    ) -> pd.DataFrame:
        """Stochastic %K and %D."""
        lowest_low   = low.rolling(k_period).min()
        highest_high = high.rolling(k_period).max()
        raw_k = 100 * (close - lowest_low) / (highest_high - lowest_low + 1e-10)
        pct_k = MA.sma(raw_k, smooth_k)
        pct_d = MA.sma(pct_k, d_period)
        return pd.DataFrame({"stoch_k": pct_k, "stoch_d": pct_d})

    # ──────────────────────────────────────────
    # Rate of Change
    # ──────────────────────────────────────────
    @staticmethod
    def roc(close: pd.Series, period: int = 14) -> pd.Series:
        """Price Rate of Change as a percentage."""
        return ((close - close.shift(period)) / close.shift(period) * 100).rename("roc")

    # ──────────────────────────────────────────
    # Money Flow Index
    # ──────────────────────────────────────────
    @staticmethod
    def mfi(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Money Flow Index (volume-weighted RSI)."""
        tp = (high + low + close) / 3
        raw_mf = tp * volume
        pos_mf = raw_mf.where(tp > tp.shift(1), 0.0)
        neg_mf = raw_mf.where(tp < tp.shift(1), 0.0)
        pos_sum = pos_mf.rolling(period).sum()
        neg_sum = neg_mf.rolling(period).sum()
        mfr = pos_sum / neg_sum.replace(0, np.nan)
        return (100 - 100 / (1 + mfr)).rename("mfi")

    # ──────────────────────────────────────────
    # Chande Momentum Oscillator
    # ──────────────────────────────────────────
    @staticmethod
    def cmo(close: pd.Series, period: int = 14) -> pd.Series:
        """Chande Momentum Oscillator."""
        delta = close.diff()
        up = delta.clip(lower=0).rolling(period).sum()
        dn = (-delta.clip(upper=0)).rolling(period).sum()
        return (100 * (up - dn) / (up + dn + 1e-10)).rename("cmo")

    # ──────────────────────────────────────────
    # MACD
    # ──────────────────────────────────────────
    @staticmethod
    def macd(
        close: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> pd.DataFrame:
        """MACD line, signal line, and histogram."""
        ema_fast   = MA.ema(close, fast)
        ema_slow   = MA.ema(close, slow)
        macd_line  = ema_fast - ema_slow
        signal_line = MA.ema(macd_line, signal)
        histogram  = macd_line - signal_line
        return pd.DataFrame({
            "macd":      macd_line,
            "macd_sig":  signal_line,
            "macd_hist": histogram,
        })

    # ──────────────────────────────────────────
    # PPO (Percentage Price Oscillator)
    # ──────────────────────────────────────────
    @staticmethod
    def ppo(
        close: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> pd.DataFrame:
        """Percentage Price Oscillator (MACD normalised by slow EMA)."""
        ema_fast = MA.ema(close, fast)
        ema_slow = MA.ema(close, slow)
        ppo_line = (ema_fast - ema_slow) / ema_slow * 100
        ppo_sig  = MA.ema(ppo_line, signal)
        ppo_hist = ppo_line - ppo_sig
        return pd.DataFrame({
            "ppo":      ppo_line,
            "ppo_sig":  ppo_sig,
            "ppo_hist": ppo_hist,
        })

    # ──────────────────────────────────────────
    # Momentum
    # ──────────────────────────────────────────
    @staticmethod
    def momentum(close: pd.Series, period: int = 10) -> pd.Series:
        """Raw price momentum: close - close[n]."""
        return (close - close.shift(period)).rename("momentum")

    # ──────────────────────────────────────────
    # Elder Ray
    # ──────────────────────────────────────────
    @staticmethod
    def elder_ray(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 13,
    ) -> pd.DataFrame:
        """Elder Ray Bull and Bear Power."""
        ema = MA.ema(close, period)
        bull = high - ema
        bear = low - ema
        return pd.DataFrame({"bull_power": bull, "bear_power": bear})

    # ──────────────────────────────────────────
    # True Strength Index
    # ──────────────────────────────────────────
    @staticmethod
    def tsi(close: pd.Series, r: int = 25, s: int = 13) -> pd.Series:
        """True Strength Index."""
        m = close.diff()
        m2 = m.ewm(span=r, adjust=False).mean().ewm(span=s, adjust=False).mean()
        abs_m2 = m.abs().ewm(span=r, adjust=False).mean().ewm(span=s, adjust=False).mean()
        return (100 * m2 / abs_m2.replace(0, np.nan)).rename("tsi")

    # ──────────────────────────────────────────
    # Relative Vigor Index
    # ──────────────────────────────────────────
    @staticmethod
    def rvi(
        open_: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 10,
    ) -> pd.DataFrame:
        """Relative Vigor Index."""
        num = close - open_
        denom = high - low
        weights = np.array([1, 2, 2, 1], dtype=float) / 6.0

        def _sym_avg(s: pd.Series) -> pd.Series:
            r = (s + 2 * s.shift(1) + 2 * s.shift(2) + s.shift(3)) / 6
            return r

        numerator   = _sym_avg(num).rolling(period).mean()
        denominator = _sym_avg(denom).rolling(period).mean()
        rvi_val     = numerator / denominator.replace(0, np.nan)
        sig         = _sym_avg(rvi_val)
        return pd.DataFrame({"rvi": rvi_val, "rvi_signal": sig})

    # ──────────────────────────────────────────
    # Batch
    # ──────────────────────────────────────────
    @staticmethod
    def all_momentum(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
    ) -> pd.DataFrame:
        """Compute all momentum indicators."""
        m = Momentum
        frames = [
            m.rsi(close),
            m.stochastic(high, low, close),
            m.roc(close),
            m.mfi(high, low, close, volume),
            m.cmo(close),
            m.macd(close),
            m.ppo(close),
            m.momentum(close),
            m.elder_ray(high, low, close),
            m.tsi(close),
        ]
        return pd.concat(frames, axis=1)
