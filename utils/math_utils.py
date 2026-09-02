"""
utils/math_utils.py
Rolling window helpers and fast numerical utilities.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Callable, Optional


def rolling_apply(
    series: pd.Series,
    window: int,
    fn: Callable[[np.ndarray], float],
    min_periods: Optional[int] = None,
) -> pd.Series:
    """Apply an arbitrary function over a rolling window."""
    return series.rolling(window, min_periods=min_periods or window).apply(fn, raw=True)


def zscore_series(series: pd.Series, window: Optional[int] = None) -> pd.Series:
    """Rolling or expanding z-score."""
    if window:
        mu  = series.rolling(window).mean()
        sig = series.rolling(window).std(ddof=1)
    else:
        mu  = series.expanding().mean()
        sig = series.expanding().std(ddof=1)
    return ((series - mu) / (sig + 1e-10)).rename("zscore")


def rank_series(series: pd.Series, pct: bool = True) -> pd.Series:
    """Cross-sectional rank (or percentile rank) of a series."""
    return series.rank(pct=pct)


def ewma_vol(returns: pd.Series, halflife: int = 21) -> pd.Series:
    """EWMA volatility (annualised)."""
    return returns.ewm(halflife=halflife).std() * np.sqrt(252)


def information_coefficient(
    predictions: pd.Series,
    forward_returns: pd.Series,
) -> float:
    """Rank IC (Spearman correlation) between predictions and next-period returns."""
    from scipy.stats import spearmanr
    aligned = pd.concat([predictions, forward_returns], axis=1).dropna()
    if len(aligned) < 5:
        return float("nan")
    corr, _ = spearmanr(aligned.iloc[:, 0], aligned.iloc[:, 1])
    return float(corr)


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    return a / b if b != 0 else default


def winsorise(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    """Winsorise a series to [lower, upper] quantile."""
    lo = series.quantile(lower)
    hi = series.quantile(upper)
    return series.clip(lower=lo, upper=hi)


def annualise_return(daily_return: float, trading_days: int = 252) -> float:
    return (1 + daily_return) ** trading_days - 1


def annualise_vol(daily_vol: float, trading_days: int = 252) -> float:
    return daily_vol * np.sqrt(trading_days)


def portfolio_return(
    weights: pd.Series,
    returns: pd.DataFrame,
) -> pd.Series:
    """Weighted portfolio return series."""
    aligned = returns[weights.index.tolist()].dropna()
    w = weights.reindex(aligned.columns).fillna(0)
    return aligned.dot(w)


def correlation_to_covariance(
    corr: pd.DataFrame,
    vols: pd.Series,
) -> pd.DataFrame:
    """Convert correlation matrix + vol vector to covariance matrix."""
    D = np.diag(vols.values)
    cov = D @ corr.values @ D
    return pd.DataFrame(cov, index=corr.index, columns=corr.columns)
