"""
stats/cointegration.py
Engle-Granger and Johansen cointegration tests for pairs trading.
Spread construction, z-score, and signal generation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple


class CointegrationTests:
    """Statistical tests and utilities for pairs/spread trading."""

    # ──────────────────────────────────────────
    # Engle-Granger Test
    # ──────────────────────────────────────────
    @staticmethod
    def engle_granger(
        y: pd.Series,
        x: pd.Series,
    ) -> Dict:
        """
        Engle-Granger two-step cointegration test.
        Returns: {'cointegrated': bool, 'hedge_ratio': float, 'adf_stat': float, 'pvalue': float}
        """
        from statsmodels.tsa.stattools import coint
        import statsmodels.api as sm

        aligned = pd.concat([y, x], axis=1).dropna()
        y_c, x_c = aligned.iloc[:, 0], aligned.iloc[:, 1]

        # OLS hedge ratio
        X = sm.add_constant(x_c.values)
        model = sm.OLS(y_c.values, X).fit()
        hedge_ratio = float(model.params[1])
        intercept   = float(model.params[0])
        spread      = y_c - hedge_ratio * x_c - intercept

        # Engle-Granger test
        t_stat, p_value, critical_values = coint(y_c, x_c)

        return {
            "cointegrated":   float(p_value) < 0.05,
            "adf_stat":       float(t_stat),
            "pvalue":         float(p_value),
            "critical_1pct":  float(critical_values[0]),
            "critical_5pct":  float(critical_values[1]),
            "critical_10pct": float(critical_values[2]),
            "hedge_ratio":    hedge_ratio,
            "intercept":      intercept,
            "spread_mean":    float(spread.mean()),
            "spread_std":     float(spread.std()),
            "half_life":      CointegrationTests.half_life(spread),
        }

    # ──────────────────────────────────────────
    # Johansen Test
    # ──────────────────────────────────────────
    @staticmethod
    def johansen(
        prices: pd.DataFrame,
        det_order: int = 0,
        k_ar_diff: int = 1,
    ) -> Dict:
        """
        Johansen cointegration test for multiple series.

        Parameters
        ----------
        prices     : DataFrame, one column per asset
        det_order  : -1 no constant, 0 constant, 1 linear trend
        k_ar_diff  : number of lags

        Returns dict with trace and max eigenvalue statistics.
        """
        from statsmodels.tsa.vector_ar.vecm import coint_johansen

        clean = prices.dropna()
        result = coint_johansen(clean, det_order, k_ar_diff)

        n = prices.shape[1]
        trace_stats  = result.lr1.tolist()
        max_ev_stats = result.lr2.tolist()
        # Critical values at 90/95/99%
        trace_cv  = result.cvt.tolist()
        max_ev_cv = result.cvm.tolist()

        n_cointegrating = sum(
            trace_stats[i] > trace_cv[i][1]   # 95% level
            for i in range(len(trace_stats))
        )

        return {
            "n_cointegrating_95pct": n_cointegrating,
            "trace_stats":           trace_stats,
            "max_eigenvalue_stats":  max_ev_stats,
            "trace_cv_95pct":        [cv[1] for cv in trace_cv],
            "max_ev_cv_95pct":       [cv[1] for cv in max_ev_cv],
            "eigenvectors":          result.evec.tolist(),
        }

    # ──────────────────────────────────────────
    # Half-Life of Mean Reversion
    # ──────────────────────────────────────────
    @staticmethod
    def half_life(spread: pd.Series) -> float:
        """
        Estimate the half-life of mean reversion using OLS on ΔS = λS[-1].
        Half-life = -ln(2)/λ
        """
        import statsmodels.api as sm
        s    = spread.dropna()
        ds   = s.diff().dropna()
        s_lag = s.shift(1).dropna()
        aligned = pd.concat([ds, s_lag], axis=1).dropna()

        X = sm.add_constant(aligned.iloc[:, 1])
        model = sm.OLS(aligned.iloc[:, 0], X).fit()
        lam = model.params.iloc[1]
        if lam >= 0:
            return np.inf          # no mean reversion
        return float(-np.log(2) / lam)

    # ──────────────────────────────────────────
    # Spread Construction
    # ──────────────────────────────────────────
    @staticmethod
    def spread(
        y: pd.Series,
        x: pd.Series,
        hedge_ratio: Optional[float] = None,
    ) -> pd.Series:
        """
        Construct spread S = Y - β * X.
        If hedge_ratio is None, it is estimated via OLS.
        """
        if hedge_ratio is None:
            import statsmodels.api as sm
            aligned = pd.concat([y, x], axis=1).dropna()
            model   = sm.OLS(aligned.iloc[:, 0], sm.add_constant(aligned.iloc[:, 1])).fit()
            hedge_ratio = float(model.params.iloc[1])
        return (y - hedge_ratio * x).rename("spread")

    @staticmethod
    def zscore(spread: pd.Series, window: int = 63) -> pd.Series:
        """Rolling z-score of the spread."""
        roll_mean = spread.rolling(window).mean()
        roll_std  = spread.rolling(window).std(ddof=1)
        return ((spread - roll_mean) / (roll_std + 1e-10)).rename("zscore")

    # ──────────────────────────────────────────
    # Pair Scanner
    # ──────────────────────────────────────────
    @staticmethod
    def scan_pairs(
        prices: pd.DataFrame,
        min_history: int = 252,
        pvalue_threshold: float = 0.05,
    ) -> pd.DataFrame:
        """
        Test all pairs for cointegration and return results sorted by p-value.
        """
        tickers = prices.columns.tolist()
        results = []
        for i in range(len(tickers)):
            for j in range(i + 1, len(tickers)):
                t1, t2 = tickers[i], tickers[j]
                pair_prices = prices[[t1, t2]].dropna()
                if len(pair_prices) < min_history:
                    continue
                try:
                    res = CointegrationTests.engle_granger(
                        pair_prices[t1], pair_prices[t2]
                    )
                    if res["pvalue"] <= pvalue_threshold:
                        results.append({
                            "asset1":       t1,
                            "asset2":       t2,
                            "pvalue":       res["pvalue"],
                            "adf_stat":     res["adf_stat"],
                            "hedge_ratio":  res["hedge_ratio"],
                            "half_life":    res["half_life"],
                            "cointegrated": res["cointegrated"],
                        })
                except Exception:
                    continue

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values("pvalue").reset_index(drop=True)
        return df
