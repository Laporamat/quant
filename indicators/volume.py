"""
indicators/volume.py
OBV, VWAP, CMF, Accumulation/Distribution Line, Force Index,
Volume Profile, MFI (volume-based), PVT, VROC
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.moving_averages import MovingAverages as MA


class Volume:
    """Volume-based indicators."""

    # ──────────────────────────────────────────
    # On-Balance Volume
    # ──────────────────────────────────────────
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume."""
        direction = np.sign(close.diff()).fillna(0)
        obv_vals = (direction * volume).cumsum()
        return obv_vals.rename("obv")

    # ──────────────────────────────────────────
    # Volume-Weighted Average Price (rolling)
    # ──────────────────────────────────────────
    @staticmethod
    def vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Rolling VWAP over *period* bars."""
        tp = (high + low + close) / 3
        pv = tp * volume
        vwap_vals = (
            pv.rolling(period).sum() / volume.rolling(period).sum()
        )
        return vwap_vals.rename("vwap")

    # ──────────────────────────────────────────
    # Chaikin Money Flow
    # ──────────────────────────────────────────
    @staticmethod
    def cmf(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        period: int = 20,
    ) -> pd.Series:
        """Chaikin Money Flow."""
        hl_range = (high - low).replace(0, np.nan)
        clv = ((close - low) - (high - close)) / hl_range
        mfv = clv * volume
        cmf_vals = mfv.rolling(period).sum() / volume.rolling(period).sum()
        return cmf_vals.rename("cmf")

    # ──────────────────────────────────────────
    # Accumulation/Distribution Line
    # ──────────────────────────────────────────
    @staticmethod
    def ad_line(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
    ) -> pd.Series:
        """Chaikin Accumulation/Distribution Line."""
        hl_range = (high - low).replace(0, np.nan)
        clv = ((close - low) - (high - close)) / hl_range
        return (clv * volume).cumsum().rename("ad_line")

    # ──────────────────────────────────────────
    # Force Index
    # ──────────────────────────────────────────
    @staticmethod
    def force_index(
        close: pd.Series,
        volume: pd.Series,
        period: int = 13,
    ) -> pd.Series:
        """Elder's Force Index (EMA smoothed)."""
        fi = close.diff() * volume
        return MA.ema(fi, period).rename("force_index")

    # ──────────────────────────────────────────
    # Ease of Movement
    # ──────────────────────────────────────────
    @staticmethod
    def eom(
        high: pd.Series,
        low: pd.Series,
        volume: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Ease of Movement."""
        midpoint_move = ((high + low) / 2) - ((high.shift(1) + low.shift(1)) / 2)
        box_ratio = (volume / 1e8) / (high - low + 1e-10)
        raw_eom = midpoint_move / box_ratio
        return MA.sma(raw_eom, period).rename("eom")

    # ──────────────────────────────────────────
    # Price-Volume Trend
    # ──────────────────────────────────────────
    @staticmethod
    def pvt(close: pd.Series, volume: pd.Series) -> pd.Series:
        """Price Volume Trend (cumulative)."""
        ret = close.pct_change().fillna(0)
        return (ret * volume).cumsum().rename("pvt")

    # ──────────────────────────────────────────
    # Volume Rate of Change
    # ──────────────────────────────────────────
    @staticmethod
    def vroc(volume: pd.Series, period: int = 25) -> pd.Series:
        """Volume Rate of Change."""
        return ((volume - volume.shift(period)) / volume.shift(period) * 100).rename("vroc")

    # ──────────────────────────────────────────
    # Negative Volume Index / Positive Volume Index
    # ──────────────────────────────────────────
    @staticmethod
    def nvi_pvi(close: pd.Series, volume: pd.Series) -> pd.DataFrame:
        """Negative Volume Index and Positive Volume Index."""
        ret = close.pct_change().fillna(0)
        vol_change = volume.diff()
        nvi = pd.Series(1000.0, index=close.index)
        pvi = pd.Series(1000.0, index=close.index)

        for i in range(1, len(close)):
            if vol_change.iloc[i] < 0:
                nvi.iloc[i] = nvi.iloc[i - 1] * (1 + ret.iloc[i])
                pvi.iloc[i] = pvi.iloc[i - 1]
            else:
                pvi.iloc[i] = pvi.iloc[i - 1] * (1 + ret.iloc[i])
                nvi.iloc[i] = nvi.iloc[i - 1]

        return pd.DataFrame({"nvi": nvi, "pvi": pvi})

    # ──────────────────────────────────────────
    # Volume SMA for comparison
    # ──────────────────────────────────────────
    @staticmethod
    def volume_sma(volume: pd.Series, period: int = 20) -> pd.Series:
        """Simple moving average of volume."""
        return MA.sma(volume, period).rename("volume_sma")

    @staticmethod
    def relative_volume(volume: pd.Series, period: int = 20) -> pd.Series:
        """Volume relative to its SMA (RVOL)."""
        return (volume / (MA.sma(volume, period) + 1e-10)).rename("rvol")

    # ──────────────────────────────────────────
    # Klinger Volume Oscillator
    # ──────────────────────────────────────────
    @staticmethod
    def kvo(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        fast: int = 34,
        slow: int = 55,
        signal: int = 13,
    ) -> pd.DataFrame:
        """Klinger Volume Oscillator."""
        tp = (high + low + close) / 3
        trend = np.where(tp > tp.shift(1), 1, -1)
        dm = high - low
        cm = np.where(
            pd.Series(trend, index=high.index) == pd.Series(trend, index=high.index).shift(1),
            dm.shift(1) + dm,
            dm.shift(1) + dm,
        )
        sv = pd.Series(
            volume.values * np.abs(2 * dm.values / (cm + 1e-10) - 1) * trend,
            index=high.index,
        )
        kvo_val = MA.ema(sv, fast) - MA.ema(sv, slow)
        kvo_sig = MA.ema(kvo_val, signal)
        return pd.DataFrame({"kvo": kvo_val, "kvo_signal": kvo_sig})

    # ──────────────────────────────────────────
    # Batch
    # ──────────────────────────────────────────
    @staticmethod
    def all_volume(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
    ) -> pd.DataFrame:
        v = Volume
        return pd.concat([
            v.obv(close, volume).to_frame(),
            v.vwap(high, low, close, volume).to_frame(),
            v.cmf(high, low, close, volume).to_frame(),
            v.ad_line(high, low, close, volume).to_frame(),
            v.force_index(close, volume).to_frame(),
            v.eom(high, low, volume).to_frame(),
            v.pvt(close, volume).to_frame(),
            v.vroc(volume).to_frame(),
            v.volume_sma(volume).to_frame(),
            v.relative_volume(volume).to_frame(),
        ], axis=1)
