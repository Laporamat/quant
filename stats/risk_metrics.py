"""
stats/risk_metrics.py
Sharpe, Sortino, Calmar, Omega, Treynor, Information Ratio,
Beta, Alpha, Tail Ratio, Gain-to-Pain, Martin Ratio, Ulcer Index
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Optional

from config import TRADING_DAYS_PER_YEAR
from stats.drawdown import DrawdownAnalysis


class RiskMetrics:
    """Performance and risk-adjusted return metrics."""

    # ──────────────────────────────────────────
    # Sharpe Ratio
    # ──────────────────────────────────────────
    @staticmethod
    def sharpe(
        returns: pd.Series,
        risk_free: float = 0.02,
        trading_days: int = TRADING_DAYS_PER_YEAR,
    ) -> float:
        """Annualised Sharpe ratio."""
        daily_rf = risk_free / trading_days
        excess   = returns - daily_rf
        if excess.std() == 0:
            return 0.0
        return float(excess.mean() / excess.std(ddof=1) * np.sqrt(trading_days))

    # ──────────────────────────────────────────
    # Sortino Ratio
    # ──────────────────────────────────────────
    @staticmethod
    def sortino(
        returns: pd.Series,
        risk_free: float = 0.02,
        trading_days: int = TRADING_DAYS_PER_YEAR,
        target: float = 0.0,
    ) -> float:
        """Sortino ratio (penalises only downside volatility)."""
        daily_rf    = risk_free / trading_days
        excess      = returns - daily_rf
        downside    = excess[excess < target]
        downside_std = np.sqrt((downside ** 2).mean())
        if downside_std == 0:
            return 0.0
        return float(excess.mean() / downside_std * np.sqrt(trading_days))

    # ──────────────────────────────────────────
    # Calmar Ratio
    # ──────────────────────────────────────────
    @staticmethod
    def calmar(
        returns: pd.Series,
        trading_days: int = TRADING_DAYS_PER_YEAR,
    ) -> float:
        """Calmar ratio = CAGR / |Max Drawdown|."""
        equity = (1 + returns).cumprod()
        mdd    = DrawdownAnalysis.max_drawdown(equity)
        if mdd == 0:
            return 0.0
        ann_return = float(returns.mean() * trading_days)
        return float(ann_return / abs(mdd))

    # ──────────────────────────────────────────
    # Omega Ratio
    # ──────────────────────────────────────────
    @staticmethod
    def omega(
        returns: pd.Series,
        threshold: float = 0.0,
        risk_free: float = 0.02,
        trading_days: int = TRADING_DAYS_PER_YEAR,
    ) -> float:
        """Omega ratio = sum(gains above threshold) / sum(losses below threshold)."""
        daily_threshold = threshold + risk_free / trading_days
        gains  = (returns[returns > daily_threshold] - daily_threshold).sum()
        losses = (daily_threshold - returns[returns <= daily_threshold]).sum()
        return float(gains / losses) if losses > 0 else np.inf

    # ──────────────────────────────────────────
    # Treynor Ratio
    # ──────────────────────────────────────────
    @staticmethod
    def treynor(
        returns: pd.Series,
        benchmark_returns: pd.Series,
        risk_free: float = 0.02,
        trading_days: int = TRADING_DAYS_PER_YEAR,
    ) -> float:
        """Treynor ratio = excess return / beta."""
        beta = RiskMetrics.beta(returns, benchmark_returns)
        if beta == 0:
            return 0.0
        ann_return = float(returns.mean() * trading_days)
        return float((ann_return - risk_free) / beta)

    # ──────────────────────────────────────────
    # Information Ratio
    # ──────────────────────────────────────────
    @staticmethod
    def information_ratio(
        returns: pd.Series,
        benchmark_returns: pd.Series,
        trading_days: int = TRADING_DAYS_PER_YEAR,
    ) -> float:
        """Information ratio = active return / tracking error."""
        aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
        active  = aligned.iloc[:, 0] - aligned.iloc[:, 1]
        te      = active.std(ddof=1)
        if te == 0:
            return 0.0
        return float(active.mean() / te * np.sqrt(trading_days))

    # ──────────────────────────────────────────
    # Beta & Alpha
    # ──────────────────────────────────────────
    @staticmethod
    def beta(returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """CAPM beta."""
        aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(aligned) < 2:
            return np.nan
        cov  = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
        var  = cov[1, 1]
        return float(cov[0, 1] / var) if var != 0 else np.nan

    @staticmethod
    def alpha(
        returns: pd.Series,
        benchmark_returns: pd.Series,
        risk_free: float = 0.02,
        trading_days: int = TRADING_DAYS_PER_YEAR,
    ) -> float:
        """CAPM Jensen's alpha (annualised)."""
        beta  = RiskMetrics.beta(returns, benchmark_returns)
        ann_r = float(returns.mean() * trading_days)
        ann_b = float(benchmark_returns.mean() * trading_days)
        return float(ann_r - (risk_free + beta * (ann_b - risk_free)))

    # ──────────────────────────────────────────
    # Tail / Downside Metrics
    # ──────────────────────────────────────────
    @staticmethod
    def tail_ratio(returns: pd.Series, pct: float = 0.05) -> float:
        """Tail ratio: 95th percentile / abs(5th percentile)."""
        up   = returns.quantile(1 - pct)
        down = abs(returns.quantile(pct))
        return float(up / down) if down != 0 else np.inf

    @staticmethod
    def downside_deviation(
        returns: pd.Series,
        mar: float = 0.0,
        trading_days: int = TRADING_DAYS_PER_YEAR,
    ) -> float:
        """Annualised downside deviation below MAR."""
        below = returns[returns < mar]
        return float(np.sqrt((below ** 2).mean()) * np.sqrt(trading_days))

    @staticmethod
    def upside_potential_ratio(
        returns: pd.Series,
        mar: float = 0.0,
        trading_days: int = TRADING_DAYS_PER_YEAR,
    ) -> float:
        """Upside Potential Ratio = upside mean / downside deviation."""
        above = returns[returns > mar].mean()
        dd    = RiskMetrics.downside_deviation(returns, mar, trading_days) / np.sqrt(trading_days)
        return float(above / dd) if dd != 0 else np.inf

    # ──────────────────────────────────────────
    # Ulcer Index & Martin Ratio
    # ──────────────────────────────────────────
    @staticmethod
    def ulcer_index(returns: pd.Series) -> float:
        """Ulcer Index = RMS of percentage drawdowns."""
        equity = (1 + returns).cumprod()
        roll_max = equity.cummax()
        dd_pct = (equity - roll_max) / roll_max * 100
        return float(np.sqrt((dd_pct ** 2).mean()))

    @staticmethod
    def martin_ratio(
        returns: pd.Series,
        risk_free: float = 0.02,
        trading_days: int = TRADING_DAYS_PER_YEAR,
    ) -> float:
        """Martin Ratio = excess annual return / Ulcer Index."""
        ui = RiskMetrics.ulcer_index(returns)
        ann_r = float(returns.mean() * trading_days)
        return float((ann_r - risk_free) / ui) if ui != 0 else 0.0

    # ──────────────────────────────────────────
    # Gain-to-Pain Ratio
    # ──────────────────────────────────────────
    @staticmethod
    def gain_to_pain(returns: pd.Series) -> float:
        """Gain-to-Pain = sum(positive) / |sum(negative)|."""
        gains  = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())
        return float(gains / losses) if losses > 0 else np.inf

    # ──────────────────────────────────────────
    # Full Report
    # ──────────────────────────────────────────
    @staticmethod
    def full_report(
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        risk_free: float = 0.02,
        trading_days: int = TRADING_DAYS_PER_YEAR,
    ) -> Dict[str, float]:
        """Compute all risk metrics and return as a dict."""
        rm = RiskMetrics
        equity = (1 + returns).cumprod()
        mdd    = DrawdownAnalysis.max_drawdown(equity)

        report: Dict[str, float] = {
            "sharpe":            rm.sharpe(returns, risk_free, trading_days),
            "sortino":           rm.sortino(returns, risk_free, trading_days),
            "calmar":            rm.calmar(returns, trading_days),
            "omega":             rm.omega(returns, risk_free=risk_free),
            "tail_ratio":        rm.tail_ratio(returns),
            "downside_dev":      rm.downside_deviation(returns),
            "ulcer_index":       rm.ulcer_index(returns),
            "martin_ratio":      rm.martin_ratio(returns, risk_free, trading_days),
            "gain_to_pain":      rm.gain_to_pain(returns),
            "max_drawdown":      mdd,
            "ann_return":        float(returns.mean() * trading_days),
            "ann_volatility":    float(returns.std(ddof=1) * np.sqrt(trading_days)),
            "upside_potential":  rm.upside_potential_ratio(returns),
        }

        if benchmark_returns is not None:
            report.update({
                "beta":              rm.beta(returns, benchmark_returns),
                "alpha":             rm.alpha(returns, benchmark_returns, risk_free, trading_days),
                "treynor":           rm.treynor(returns, benchmark_returns, risk_free, trading_days),
                "information_ratio": rm.information_ratio(returns, benchmark_returns, trading_days),
            })

        return report
