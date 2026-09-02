"""
indicators/trend.py
ADX, CCI, Aroon, Ichimoku Cloud, Parabolic SAR, Supertrend, PSAR
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.moving_averages import MovingAverages as MA
from indicators.volatility import Volatility


class Trend:
    """Trend-following indicators."""

    # ──────────────────────────────────────────
    # ADX / DMI
    # ──────────────────────────────────────────
    @staticmethod
    def adx(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.DataFrame:
        """ADX with +DI and -DI."""
        tr   = Volatility.true_range(high, low, close)
        plus_dm  = high.diff().clip(lower=0)
        minus_dm = (-low.diff()).clip(lower=0)
        # Zero where the other DM is larger
        cond = plus_dm < minus_dm
        plus_dm  = plus_dm.where(~cond, 0.0)
        minus_dm = minus_dm.where(cond, 0.0)

        atr  = MA.rma(tr, period)
        pdi  = 100 * MA.rma(plus_dm, period)  / (atr + 1e-10)
        mdi  = 100 * MA.rma(minus_dm, period) / (atr + 1e-10)
        dx   = 100 * (pdi - mdi).abs() / (pdi + mdi + 1e-10)
        adx  = MA.rma(dx, period)
        return pd.DataFrame({"adx": adx, "pdi": pdi, "mdi": mdi, "dx": dx})

    # ──────────────────────────────────────────
    # CCI  (Commodity Channel Index)
    # ──────────────────────────────────────────
    @staticmethod
    def cci(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 20,
        constant: float = 0.015,
    ) -> pd.Series:
        """Commodity Channel Index."""
        tp = (high + low + close) / 3
        sma_tp = MA.sma(tp, period)
        mad    = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
        return ((tp - sma_tp) / (constant * mad + 1e-10)).rename("cci")

    # ──────────────────────────────────────────
    # Aroon
    # ──────────────────────────────────────────
    @staticmethod
    def aroon(
        high: pd.Series,
        low: pd.Series,
        period: int = 25,
    ) -> pd.DataFrame:
        """Aroon Up, Down, and Oscillator."""
        def periods_since_max(s: pd.Series) -> pd.Series:
            return s.rolling(period + 1).apply(
                lambda x: period - np.argmax(x), raw=True
            )

        def periods_since_min(s: pd.Series) -> pd.Series:
            return s.rolling(period + 1).apply(
                lambda x: period - np.argmin(x), raw=True
            )

        aroon_up   = 100 * (period - periods_since_max(high)) / period
        aroon_down = 100 * (period - periods_since_min(low))  / period
        aroon_osc  = aroon_up - aroon_down
        return pd.DataFrame({
            "aroon_up":   aroon_up,
            "aroon_down": aroon_down,
            "aroon_osc":  aroon_osc,
        })

    # ──────────────────────────────────────────
    # Ichimoku Cloud
    # ──────────────────────────────────────────
    @staticmethod
    def ichimoku(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        tenkan: int = 9,
        kijun: int = 26,
        senkou_b: int = 52,
        chikou: int = 26,
    ) -> pd.DataFrame:
        """Ichimoku Kinko Hyo Cloud."""
        def mid(h: pd.Series, l: pd.Series, n: int) -> pd.Series:
            return (h.rolling(n).max() + l.rolling(n).min()) / 2

        tenkan_sen  = mid(high, low, tenkan)
        kijun_sen   = mid(high, low, kijun)
        senkou_a    = ((tenkan_sen + kijun_sen) / 2).shift(kijun)
        senkou_b_s  = mid(high, low, senkou_b).shift(kijun)
        chikou_span = close.shift(-chikou)

        cloud_top    = pd.concat([senkou_a, senkou_b_s], axis=1).max(axis=1)
        cloud_bottom = pd.concat([senkou_a, senkou_b_s], axis=1).min(axis=1)
        cloud_bullish = (senkou_a > senkou_b_s).astype(int)

        return pd.DataFrame({
            "tenkan":        tenkan_sen,
            "kijun":         kijun_sen,
            "senkou_a":      senkou_a,
            "senkou_b":      senkou_b_s,
            "chikou":        chikou_span,
            "cloud_top":     cloud_top,
            "cloud_bottom":  cloud_bottom,
            "cloud_bullish": cloud_bullish,
        })

    # ──────────────────────────────────────────
    # Parabolic SAR
    # ──────────────────────────────────────────
    @staticmethod
    def parabolic_sar(
        high: pd.Series,
        low: pd.Series,
        af_start: float = 0.02,
        af_step:  float = 0.02,
        af_max:   float = 0.20,
    ) -> pd.DataFrame:
        """Parabolic SAR (pure Python loop – accurate reference implementation)."""
        highs  = high.values
        lows   = low.values
        n      = len(highs)
        sar    = np.full(n, np.nan)
        trend  = np.full(n, 0, dtype=int)   # 1=bull, -1=bear

        # Initialise
        bull   = True
        af     = af_start
        ep     = highs[0]
        sar[0] = lows[0]

        for i in range(1, n):
            prev_sar = sar[i - 1]

            if bull:
                new_sar = prev_sar + af * (ep - prev_sar)
                new_sar = min(new_sar, lows[i - 1], lows[max(i - 2, 0)])
                if lows[i] < new_sar:          # reversal to bear
                    bull = False
                    new_sar = ep
                    ep = lows[i]
                    af = af_start
                else:
                    if highs[i] > ep:
                        ep = highs[i]
                        af = min(af + af_step, af_max)
            else:
                new_sar = prev_sar + af * (ep - prev_sar)
                new_sar = max(new_sar, highs[i - 1], highs[max(i - 2, 0)])
                if highs[i] > new_sar:         # reversal to bull
                    bull = True
                    new_sar = ep
                    ep = highs[i]
                    af = af_start
                else:
                    if lows[i] < ep:
                        ep = lows[i]
                        af = min(af + af_step, af_max)

            sar[i]   = new_sar
            trend[i] = 1 if bull else -1

        return pd.DataFrame(
            {"psar": sar, "psar_trend": trend},
            index=high.index,
        )

    # ──────────────────────────────────────────
    # Supertrend
    # ──────────────────────────────────────────
    @staticmethod
    def supertrend(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 10,
        multiplier: float = 3.0,
    ) -> pd.DataFrame:
        """Supertrend indicator."""
        atr  = Volatility.atr(high, low, close, period)
        hl2  = (high + low) / 2
        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr

        supertrend = pd.Series(np.nan, index=close.index)
        direction  = pd.Series(0, index=close.index)
        in_uptrend = True

        for i in range(1, len(close)):
            ub_prev = upper_band.iloc[i - 1]
            lb_prev = lower_band.iloc[i - 1]
            st_prev = supertrend.iloc[i - 1]

            # Adjust bands
            if upper_band.iloc[i] > ub_prev or close.iloc[i - 1] > ub_prev:
                upper_band.iloc[i] = upper_band.iloc[i]
            else:
                upper_band.iloc[i] = ub_prev

            if lower_band.iloc[i] < lb_prev or close.iloc[i - 1] < lb_prev:
                lower_band.iloc[i] = lower_band.iloc[i]
            else:
                lower_band.iloc[i] = lb_prev

            if in_uptrend:
                if close.iloc[i] < lower_band.iloc[i]:
                    in_uptrend = False
            else:
                if close.iloc[i] > upper_band.iloc[i]:
                    in_uptrend = True

            if in_uptrend:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i]  = 1
            else:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i]  = -1

        return pd.DataFrame({"supertrend": supertrend, "st_direction": direction})

    # ──────────────────────────────────────────
    # Vortex Indicator
    # ──────────────────────────────────────────
    @staticmethod
    def vortex(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.DataFrame:
        """Vortex Indicator VI+ and VI-."""
        tr  = Volatility.true_range(high, low, close)
        vmp = (high - low.shift(1)).abs()
        vmm = (low  - high.shift(1)).abs()
        tr_sum  = tr.rolling(period).sum()
        vip = vmp.rolling(period).sum() / (tr_sum + 1e-10)
        vim = vmm.rolling(period).sum() / (tr_sum + 1e-10)
        return pd.DataFrame({"vi_plus": vip, "vi_minus": vim})

    # ──────────────────────────────────────────
    # Batch
    # ──────────────────────────────────────────
    @staticmethod
    def all_trend(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
    ) -> pd.DataFrame:
        t = Trend
        return pd.concat([
            t.adx(high, low, close),
            t.cci(high, low, close),
            t.aroon(high, low),
            t.ichimoku(high, low, close),
            t.parabolic_sar(high, low),
            t.supertrend(high, low, close),
            t.vortex(high, low, close),
        ], axis=1)
