"""
stats/descriptive.py
Descriptive statistics for price/return series.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from typing import Dict, Any


class DescriptiveStats:
    """Descriptive statistics for a price or return series."""

    @staticmethod
    def summary(series: pd.Series) -> Dict[str, Any]:
        """Full descriptive stats dictionary."""
        clean = series.dropna()
        if clean.empty:
            return {}

        n = len(clean)
        mean   = float(clean.mean())
        median = float(clean.median())
        std    = float(clean.std(ddof=1))
        skew   = float(scipy_stats.skew(clean))
        kurt   = float(scipy_stats.kurtosis(clean, fisher=True))  # excess kurtosis
        mn     = float(clean.min())
        mx     = float(clean.max())
        q25    = float(clean.quantile(0.25))
        q75    = float(clean.quantile(0.75))
        iqr    = q75 - q25

        # Jarque-Bera normality test
        jb_stat, jb_p = scipy_stats.jarque_bera(clean)

        # Shapiro-Wilk (capped at 5000 samples for performance)
        sample = clean.values[:5000]
        sw_stat, sw_p = scipy_stats.shapiro(sample)

        # Autocorrelation lag-1 and lag-5
        ac1 = float(clean.autocorr(1)) if n > 1 else np.nan
        ac5 = float(clean.autocorr(5)) if n > 5 else np.nan

        return {
            "count":       n,
            "mean":        mean,
            "median":      median,
            "std":         std,
            "min":         mn,
            "max":         mx,
            "q25":         q25,
            "q75":         q75,
            "iqr":         iqr,
            "skewness":    skew,
            "kurtosis":    kurt,      # excess (normal=0)
            "is_leptokurtic": kurt > 0,
            "jb_stat":     float(jb_stat),
            "jb_pvalue":   float(jb_p),
            "is_normal_jb": jb_p > 0.05,
            "sw_stat":     float(sw_stat),
            "sw_pvalue":   float(sw_p),
            "autocorr_1":  ac1,
            "autocorr_5":  ac5,
        }

    @staticmethod
    def percentiles(
        series: pd.Series,
        pcts: list[float] | None = None,
    ) -> Dict[str, float]:
        """Return percentile values."""
        if pcts is None:
            pcts = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        clean = series.dropna()
        return {f"p{int(p)}": float(clean.quantile(p / 100)) for p in pcts}

    @staticmethod
    def rolling_stats(
        series: pd.Series,
        period: int = 63,
    ) -> pd.DataFrame:
        """Rolling mean, std, skew, kurtosis."""
        return pd.DataFrame({
            "roll_mean":  series.rolling(period).mean(),
            "roll_std":   series.rolling(period).std(),
            "roll_skew":  series.rolling(period).skew(),
            "roll_kurt":  series.rolling(period).kurt(),
        })

    @staticmethod
    def autocorrelation(series: pd.Series, max_lag: int = 20) -> pd.Series:
        """Return autocorrelation values for lags 1..max_lag."""
        return pd.Series(
            {lag: float(series.dropna().autocorr(lag)) for lag in range(1, max_lag + 1)},
            name="autocorr",
        )

    @staticmethod
    def ljung_box(series: pd.Series, lags: int = 10) -> Dict[str, float]:
        """Ljung-Box test for autocorrelation."""
        from statsmodels.stats.diagnostic import acorr_ljungbox
        result = acorr_ljungbox(series.dropna(), lags=[lags], return_df=True)
        return {
            "lb_stat":    float(result["lb_stat"].iloc[-1]),
            "lb_pvalue":  float(result["lb_pvalue"].iloc[-1]),
            "significant": float(result["lb_pvalue"].iloc[-1]) < 0.05,
        }

    @staticmethod
    def adf_test(series: pd.Series) -> Dict[str, Any]:
        """Augmented Dickey-Fuller test for stationarity."""
        from statsmodels.tsa.stattools import adfuller
        result = adfuller(series.dropna(), autolag="AIC")
        return {
            "adf_stat":    float(result[0]),
            "pvalue":      float(result[1]),
            "n_lags":      int(result[2]),
            "n_obs":       int(result[3]),
            "critical_1":  float(result[4]["1%"]),
            "critical_5":  float(result[4]["5%"]),
            "critical_10": float(result[4]["10%"]),
            "is_stationary": float(result[1]) < 0.05,
        }

    @staticmethod
    def hurst_exponent(series: pd.Series, max_lag: int = 100) -> float:
        """
        Hurst exponent via R/S analysis.
        H < 0.5 = mean-reverting
        H = 0.5 = random walk
        H > 0.5 = trending
        """
        lags = range(2, min(max_lag, len(series) // 2))
        tau  = []
        for lag in lags:
            rs_values = []
            sub = series.dropna().values
            for i in range(0, len(sub) - lag, lag):
                segment = sub[i: i + lag]
                if len(segment) < 2:
                    continue
                mean_s = np.mean(segment)
                dev    = np.cumsum(segment - mean_s)
                r      = np.max(dev) - np.min(dev)
                s      = np.std(segment, ddof=1)
                if s > 0:
                    rs_values.append(r / s)
            if rs_values:
                tau.append((lag, np.mean(rs_values)))

        if len(tau) < 2:
            return np.nan

        lags_v = np.log([t[0] for t in tau])
        rs_v   = np.log([t[1] for t in tau])
        hurst, _ = np.polyfit(lags_v, rs_v, 1)
        return float(hurst)
