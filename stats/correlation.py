"""
stats/correlation.py
Pairwise correlation, rolling correlation, beta matrix, distance matrix.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Optional


class CorrelationAnalysis:
    """Correlation metrics for multi-asset portfolios."""

    # ──────────────────────────────────────────
    # Static correlation
    # ──────────────────────────────────────────
    @staticmethod
    def pairwise(
        returns: pd.DataFrame,
        method: str = "pearson",
    ) -> pd.DataFrame:
        """Pearson / Spearman / Kendall pairwise correlation matrix."""
        return returns.corr(method=method)

    @staticmethod
    def pairwise_returns(
        prices: pd.DataFrame,
        method: str = "pearson",
    ) -> pd.DataFrame:
        rets = prices.pct_change().dropna()
        return CorrelationAnalysis.pairwise(rets, method)

    # ──────────────────────────────────────────
    # Rolling correlation
    # ──────────────────────────────────────────
    @staticmethod
    def rolling_corr(
        s1: pd.Series,
        s2: pd.Series,
        window: int = 63,
    ) -> pd.Series:
        """Rolling Pearson correlation between two return series."""
        return s1.rolling(window).corr(s2).rename("rolling_corr")

    @staticmethod
    def rolling_corr_matrix(
        returns: pd.DataFrame,
        window: int = 63,
    ) -> Dict[str, pd.DataFrame]:
        """
        Rolling correlation matrix over *window* days.
        Returns dict of {date: corr_matrix}.
        (Sparse – computed every 5 days for performance.)
        """
        dates = returns.index[window - 1::5]
        result: Dict[str, pd.DataFrame] = {}
        for d in dates:
            subset = returns.loc[:d].tail(window)
            result[str(d.date())] = subset.corr()
        return result

    # ──────────────────────────────────────────
    # Beta matrix
    # ──────────────────────────────────────────
    @staticmethod
    def beta_matrix(
        returns: pd.DataFrame,
        benchmark: pd.Series,
    ) -> pd.Series:
        """Compute beta of each asset vs benchmark."""
        aligned = pd.concat([returns, benchmark.rename("bench")], axis=1).dropna()
        bench_var = aligned["bench"].var()
        betas = {}
        for col in returns.columns:
            cov_val = aligned[col].cov(aligned["bench"])
            betas[col] = cov_val / bench_var if bench_var != 0 else np.nan
        return pd.Series(betas, name="beta")

    # ──────────────────────────────────────────
    # Distance correlation
    # ──────────────────────────────────────────
    @staticmethod
    def distance_corr(s1: pd.Series, s2: pd.Series) -> float:
        """
        Distance correlation (detects non-linear dependence).
        dcor = 0 ↔ independence, dcor = 1 ↔ perfect dependence.
        """
        a = s1.dropna().values.astype(float)
        b = s2.dropna().values.astype(float)
        n = min(len(a), len(b))
        a, b = a[:n], b[:n]

        def _dcov(x: np.ndarray, y: np.ndarray) -> float:
            n_ = len(x)
            A  = np.abs(x[:, None] - x[None, :])
            B  = np.abs(y[:, None] - y[None, :])
            A  = A - A.mean(axis=0) - A.mean(axis=1)[:, None] + A.mean()
            B  = B - B.mean(axis=0) - B.mean(axis=1)[:, None] + B.mean()
            return float(np.sqrt(np.maximum((A * B).mean(), 0)))

        dco  = _dcov(a, b)
        dva  = _dcov(a, a)
        dvb  = _dcov(b, b)
        denom = np.sqrt(dva * dvb)
        return float(dco / denom) if denom > 0 else 0.0

    # ──────────────────────────────────────────
    # Cluster analysis helper
    # ──────────────────────────────────────────
    @staticmethod
    def correlation_clusters(
        returns: pd.DataFrame,
        n_clusters: int = 5,
    ) -> Dict[str, int]:
        """Assign tickers to correlation-based clusters using k-means."""
        from sklearn.cluster import KMeans
        corr = returns.corr().fillna(0).values
        dist = 1 - corr
        km   = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(dist)
        return dict(zip(returns.columns, labels.tolist()))

    # ──────────────────────────────────────────
    # Avg correlation (portfolio concentration)
    # ──────────────────────────────────────────
    @staticmethod
    def average_correlation(returns: pd.DataFrame) -> float:
        """Average pairwise Pearson correlation (excluding diagonal)."""
        corr = returns.corr()
        n    = len(corr)
        if n < 2:
            return np.nan
        total = corr.values.sum() - np.trace(corr.values)
        return float(total / (n * (n - 1)))
