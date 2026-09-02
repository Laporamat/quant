"""
indicators/volatility.py
Bollinger Bands, ATR, Keltner Channels, Donchian Channels,
Historical Volatility, Garman-Klass, Parkinson, Yang-Zhang
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.moving_averages import MovingAverages as MA


class Volatility:
    """Volatility indicators and channel overlays."""

    # ──────────────────────────────────────────
    # True Range & ATR
    # ──────────────────────────────────────────
    @staticmethod
    def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """True Range."""
        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low  - prev_close).abs(),
        ], axis=1).max(axis=1)
        return tr.rename("true_range")

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range using Wilder's smoothing."""
        tr = Volatility.true_range(high, low, close)
        return MA.rma(tr, period).rename("atr")

    # ──────────────────────────────────────────
    # Bollinger Bands
    # ──────────────────────────────────────────
    @staticmethod
    def bollinger_bands(
        close: pd.Series,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> pd.DataFrame:
        """Bollinger Bands: upper, middle (SMA), lower."""
        mid = MA.sma(close, period)
        std = close.rolling(period).std(ddof=0)
        upper = mid + std_dev * std
        lower = mid - std_dev * std
        width = (upper - lower) / mid
        pct_b = (close - lower) / (upper - lower + 1e-10)
        return pd.DataFrame({
            "bb_upper":  upper,
            "bb_mid":    mid,
            "bb_lower":  lower,
            "bb_width":  width,
            "bb_pct_b":  pct_b,
        })

    # ──────────────────────────────────────────
    # Keltner Channels
    # ──────────────────────────────────────────
    @staticmethod
    def keltner_channels(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        ema_period: int = 20,
        atr_period: int = 10,
        multiplier: float = 2.0,
    ) -> pd.DataFrame:
        """Keltner Channels based on EMA ± multiplier × ATR."""
        mid   = MA.ema(close, ema_period)
        atr   = Volatility.atr(high, low, close, atr_period)
        upper = mid + multiplier * atr
        lower = mid - multiplier * atr
        return pd.DataFrame({
            "kc_upper": upper,
            "kc_mid":   mid,
            "kc_lower": lower,
        })

    # ──────────────────────────────────────────
    # Donchian Channels
    # ──────────────────────────────────────────
    @staticmethod
    def donchian_channels(
        high: pd.Series,
        low: pd.Series,
        period: int = 20,
    ) -> pd.DataFrame:
        """Donchian Channels: highest high and lowest low over n periods."""
        upper = high.rolling(period).max()
        lower = low.rolling(period).min()
        mid   = (upper + lower) / 2
        return pd.DataFrame({
            "dc_upper": upper,
            "dc_mid":   mid,
            "dc_lower": lower,
        })

    # ──────────────────────────────────────────
    # Historical (Close-to-Close) Volatility
    # ──────────────────────────────────────────
    @staticmethod
    def historical_volatility(
        close: pd.Series,
        period: int = 21,
        annualise: bool = True,
        trading_days: int = 252,
    ) -> pd.Series:
        """Annualised standard deviation of log returns."""
        log_ret = np.log(close / close.shift(1))
        hv = log_ret.rolling(period).std(ddof=1)
        if annualise:
            hv = hv * np.sqrt(trading_days)
        return hv.rename("hist_vol")

    # ──────────────────────────────────────────
    # Garman-Klass Volatility Estimator
    # ──────────────────────────────────────────
    @staticmethod
    def garman_klass(
        open_: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 21,
        trading_days: int = 252,
    ) -> pd.Series:
        """Garman-Klass volatility estimator (uses OHLC)."""
        log_hl = (np.log(high / low)) ** 2
        log_co = np.log(close / open_) ** 2
        daily_var = 0.5 * log_hl - (2 * np.log(2) - 1) * log_co
        gk_var = daily_var.rolling(period).mean()
        return (np.sqrt(gk_var * trading_days)).rename("gk_vol")

    # ──────────────────────────────────────────
    # Parkinson Volatility Estimator
    # ──────────────────────────────────────────
    @staticmethod
    def parkinson(
        high: pd.Series,
        low: pd.Series,
        period: int = 21,
        trading_days: int = 252,
    ) -> pd.Series:
        """Parkinson high-low volatility estimator."""
        log_hl2 = (np.log(high / low)) ** 2
        factor = 1.0 / (4 * np.log(2))
        var = factor * log_hl2.rolling(period).mean()
        return (np.sqrt(var * trading_days)).rename("park_vol")

    # ──────────────────────────────────────────
    # Yang-Zhang Volatility Estimator
    # ──────────────────────────────────────────
    @staticmethod
    def yang_zhang(
        open_: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 21,
        trading_days: int = 252,
    ) -> pd.Series:
        """Yang-Zhang volatility estimator (combines overnight and open-to-close)."""
        k = 0.34 / (1.34 + (period + 1) / (period - 1))
        log_oc = np.log(open_ / close.shift(1))
        log_co = np.log(close / open_)
        log_hl = np.log(high / low)

        overnight_var = log_oc.rolling(period).var(ddof=1)
        oc_var        = log_co.rolling(period).var(ddof=1)
        rs_var        = ((log_hl ** 2) * (2 * np.log(2) - 1)).rolling(period).mean()  # Rogers-Satchell

        yz_var = overnight_var + k * oc_var + (1 - k) * rs_var
        return (np.sqrt(yz_var * trading_days)).rename("yz_vol")

    # ──────────────────────────────────────────
    # Volatility Squeeze
    # ──────────────────────────────────────────
    @staticmethod
    def squeeze(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        bb_period: int = 20,
        bb_std: float = 2.0,
        kc_period: int = 20,
        kc_mult: float = 1.5,
    ) -> pd.DataFrame:
        """
        Bollinger Band / Keltner Channel squeeze indicator.
        squeeze_on=1 when BB is inside KC.
        """
        bb = Volatility.bollinger_bands(close, bb_period, bb_std)
        kc = Volatility.keltner_channels(high, low, close, kc_period, kc_period, kc_mult)
        squeeze_on = (
            (bb["bb_lower"] > kc["kc_lower"]) & (bb["bb_upper"] < kc["kc_upper"])
        ).astype(int)
        return pd.DataFrame({
            "squeeze_on": squeeze_on,
            "bb_width":   bb["bb_width"],
        })

    # ──────────────────────────────────────────
    # Batch
    # ──────────────────────────────────────────
    @staticmethod
    def all_volatility(
        open_: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
    ) -> pd.DataFrame:
        v = Volatility
        return pd.concat([
            v.bollinger_bands(close),
            v.keltner_channels(high, low, close),
            v.donchian_channels(high, low),
            v.atr(high, low, close),
            v.historical_volatility(close),
            v.garman_klass(open_, high, low, close),
            v.parkinson(high, low),
            v.yang_zhang(open_, high, low, close),
        ], axis=1)
