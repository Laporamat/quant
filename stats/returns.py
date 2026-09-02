"""
stats/returns.py
Daily, monthly, annual returns; log returns; excess returns; CAGR.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict

from config import TRADING_DAYS_PER_YEAR


class ReturnStats:
    """Return calculation utilities."""

    # ──────────────────────────────────────────
    # Basic Returns
    # ──────────────────────────────────────────
    @staticmethod
    def daily_returns(prices: pd.Series) -> pd.Series:
        return prices.pct_change().dropna().rename("daily_return")

    @staticmethod
    def log_returns(prices: pd.Series) -> pd.Series:
        return np.log(prices / prices.shift(1)).dropna().rename("log_return")

    @staticmethod
    def cumulative_returns(prices: pd.Series) -> pd.Series:
        daily = ReturnStats.daily_returns(prices)
        return (1 + daily).cumprod().rename("cum_return")

    @staticmethod
    def total_return(prices: pd.Series) -> float:
        """Total return as a fraction."""
        return float(prices.iloc[-1] / prices.iloc[0] - 1) if len(prices) >= 2 else 0.0

    # ──────────────────────────────────────────
    # CAGR
    # ──────────────────────────────────────────
    @staticmethod
    def cagr(prices: pd.Series, trading_days: int = TRADING_DAYS_PER_YEAR) -> float:
        """Compound Annual Growth Rate."""
        if len(prices) < 2:
            return 0.0
        total = ReturnStats.total_return(prices)
        n_years = len(prices) / trading_days
        return float((1 + total) ** (1 / n_years) - 1) if n_years > 0 else 0.0

    # ──────────────────────────────────────────
    # Period returns
    # ──────────────────────────────────────────
    @staticmethod
    def monthly_returns(prices: pd.Series) -> pd.Series:
        """Monthly returns resampled from daily prices."""
        monthly = prices.resample("ME").last()
        return monthly.pct_change().dropna().rename("monthly_return")

    @staticmethod
    def annual_returns(prices: pd.Series) -> pd.Series:
        """Annual returns."""
        annual = prices.resample("YE").last()
        return annual.pct_change().dropna().rename("annual_return")

    @staticmethod
    def quarterly_returns(prices: pd.Series) -> pd.Series:
        quarterly = prices.resample("QE").last()
        return quarterly.pct_change().dropna().rename("quarterly_return")

    @staticmethod
    def weekly_returns(prices: pd.Series) -> pd.Series:
        weekly = prices.resample("W").last()
        return weekly.pct_change().dropna().rename("weekly_return")

    # ──────────────────────────────────────────
    # Excess Returns
    # ──────────────────────────────────────────
    @staticmethod
    def excess_returns(
        returns: pd.Series,
        risk_free_rate: float = 0.02,
        trading_days: int = TRADING_DAYS_PER_YEAR,
    ) -> pd.Series:
        """Returns minus daily risk-free rate."""
        daily_rf = risk_free_rate / trading_days
        return (returns - daily_rf).rename("excess_return")

    @staticmethod
    def active_returns(
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> pd.Series:
        """Active (alpha) returns = portfolio - benchmark."""
        combined = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
        return (combined.iloc[:, 0] - combined.iloc[:, 1]).rename("active_return")

    # ──────────────────────────────────────────
    # Return Aggregation Table
    # ──────────────────────────────────────────
    @staticmethod
    def monthly_return_table(prices: pd.Series) -> pd.DataFrame:
        """
        Returns a year × month table of monthly returns (%).
        Index = year, Columns = Jan..Dec, last col = annual.
        """
        monthly = ReturnStats.monthly_returns(prices)
        df = monthly.to_frame("return")
        df["year"]  = df.index.year
        df["month"] = df.index.month
        pivot = df.pivot(index="year", columns="month", values="return") * 100
        pivot.columns = [
            "Jan","Feb","Mar","Apr","May","Jun",
            "Jul","Aug","Sep","Oct","Nov","Dec",
        ][:len(pivot.columns)]
        # Annual total
        annual = ReturnStats.annual_returns(prices) * 100
        annual.index = annual.index.year
        pivot["Annual"] = annual
        return pivot.round(2)

    # ──────────────────────────────────────────
    # Rolling windows
    # ──────────────────────────────────────────
    @staticmethod
    def rolling_return(
        prices: pd.Series,
        window: int = 252,
    ) -> pd.Series:
        """Rolling n-day total return."""
        return prices.pct_change(window).rename(f"rolling_{window}d_return")

    @staticmethod
    def return_summary(prices: pd.Series) -> Dict[str, float]:
        """Return a dict of common return statistics."""
        daily = ReturnStats.daily_returns(prices)
        monthly = ReturnStats.monthly_returns(prices)
        annual  = ReturnStats.annual_returns(prices)
        return {
            "total_return":      ReturnStats.total_return(prices),
            "cagr":              ReturnStats.cagr(prices),
            "avg_daily_return":  float(daily.mean()),
            "avg_monthly_return":float(monthly.mean()),
            "avg_annual_return": float(annual.mean()),
            "best_day":          float(daily.max()),
            "worst_day":         float(daily.min()),
            "best_month":        float(monthly.max()),
            "worst_month":       float(monthly.min()),
            "best_year":         float(annual.max()),
            "worst_year":        float(annual.min()),
            "pct_positive_days": float((daily > 0).mean()),
            "pct_positive_months": float((monthly > 0).mean()),
        }
