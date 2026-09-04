"""
stats/seasonality.py
Day-of-week, month-of-year, quarter, holiday effects analysis.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict
from scipy import stats as scipy_stats


class SeasonalityAnalysis:
    """Calendar and seasonal effects on returns."""

    # ──────────────────────────────────────────
    # Day of Week
    # ──────────────────────────────────────────
    @staticmethod
    def day_of_week_effect(returns: pd.Series) -> pd.DataFrame:
        """Average return by day of week (0=Mon .. 4=Fri)."""
        df = returns.to_frame("return")
        df["day"]  = returns.index.dayofweek
        df["name"] = returns.index.day_name()
        stats = (
            df.groupby(["day", "name"])["return"]
            .agg(["mean", "std", "count"])
            .reset_index()
        )
        stats.columns = ["day_num", "day_name", "mean_return", "std", "count"]
        stats["t_stat"] = stats["mean_return"] / (stats["std"] / np.sqrt(stats["count"]))
        stats["annualised"] = stats["mean_return"] * 252
        return stats.sort_values("day_num").reset_index(drop=True)

    # ──────────────────────────────────────────
    # Month of Year
    # ──────────────────────────────────────────
    @staticmethod
    def month_effect(returns: pd.Series) -> pd.DataFrame:
        """Average return by calendar month."""
        df = returns.to_frame("return")
        df["month"] = returns.index.month
        df["name"]  = returns.index.month_name()
        stats = (
            df.groupby(["month", "name"])["return"]
            .agg(["mean", "std", "count"])
            .reset_index()
        )
        stats.columns = ["month_num", "month_name", "mean_return", "std", "count"]
        stats["t_stat"] = stats["mean_return"] / (stats["std"] / np.sqrt(stats["count"]))
        stats["annualised_contrib"] = stats["mean_return"] * 21  # ~21 trading days/month
        return stats.sort_values("month_num").reset_index(drop=True)

    # ──────────────────────────────────────────
    # Quarter
    # ──────────────────────────────────────────
    @staticmethod
    def quarter_effect(returns: pd.Series) -> pd.DataFrame:
        """Average return by calendar quarter."""
        df = returns.to_frame("return")
        df["quarter"] = returns.index.quarter
        stats = (
            df.groupby("quarter")["return"]
            .agg(["mean", "std", "count"])
            .reset_index()
        )
        stats.columns = ["quarter", "mean_return", "std", "count"]
        stats["quarter_label"] = ["Q1", "Q2", "Q3", "Q4"][:len(stats)]
        stats["t_stat"] = stats["mean_return"] / (stats["std"] / np.sqrt(stats["count"]))
        return stats

    # ──────────────────────────────────────────
    # Turn-of-Month Effect
    # ──────────────────────────────────────────
    @staticmethod
    def turn_of_month_effect(
        returns: pd.Series,
        tom_days: int = 3,
    ) -> Dict[str, float]:
        """
        Compare returns on the last N and first N trading days of each month
        vs all other days (Turn of Month anomaly).
        """
        df   = returns.to_frame("return")
        # Business day position within month
        df["bdom"] = df.groupby([df.index.year, df.index.month]).cumcount() + 1
        grp = df.groupby([df.index.year, df.index.month])
        df["bdom_from_end"] = grp["bdom"].transform("max") - df["bdom"] + 1

        tom_mask = (df["bdom"] <= tom_days) | (df["bdom_from_end"] <= tom_days)
        tom_ret  = returns[tom_mask]
        other_ret = returns[~tom_mask]

        ttest = scipy_stats.ttest_ind(tom_ret.dropna(), other_ret.dropna())
        return {
            "tom_mean_daily":   float(tom_ret.mean()),
            "other_mean_daily": float(other_ret.mean()),
            "tom_annualised":   float(tom_ret.mean() * 252),
            "other_annualised": float(other_ret.mean() * 252),
            "t_stat":           float(ttest.statistic),
            "p_value":          float(ttest.pvalue),
            "significant":      float(ttest.pvalue) < 0.05,
        }

    # ──────────────────────────────────────────
    # January Effect
    # ──────────────────────────────────────────
    @staticmethod
    def january_effect(returns: pd.Series) -> Dict:
        """Test if January returns differ from other months."""
        jan  = returns[returns.index.month == 1]
        rest = returns[returns.index.month != 1]
        ttest = scipy_stats.ttest_ind(jan.dropna(), rest.dropna())
        detected = bool(float(ttest.pvalue) < 0.05 and float(jan.mean()) > float(rest.mean()))
        return {
            "detected":  detected,
            "p_value":   float(ttest.pvalue),
            "avg_jan":   float(jan.mean()),
            "avg_other": float(rest.mean()),
            "t_stat":    float(ttest.statistic),
            "effect":    float(jan.mean() - rest.mean()),
        }

    # ──────────────────────────────────────────
    # Monday Effect
    # ──────────────────────────────────────────
    @staticmethod
    def monday_effect(returns: pd.Series) -> Dict:
        """Test if Monday returns differ from other weekdays."""
        mon  = returns[returns.index.dayofweek == 0]
        rest = returns[returns.index.dayofweek != 0]
        ttest = scipy_stats.ttest_ind(mon.dropna(), rest.dropna())
        detected = bool(float(ttest.pvalue) < 0.05 and float(mon.mean()) < float(rest.mean()))
        return {
            "detected":  detected,
            "p_value":   float(ttest.pvalue),
            "avg_mon":   float(mon.mean()),
            "avg_other": float(rest.mean()),
            "t_stat":    float(ttest.statistic),
        }

    # ──────────────────────────────────────────
    # Full seasonality report
    # ──────────────────────────────────────────
    @staticmethod
    def full_report(returns: pd.Series) -> Dict:
        s = SeasonalityAnalysis
        return {
            "day_of_week":        s.day_of_week_effect(returns).to_dict("records"),
            "month":              s.month_effect(returns).to_dict("records"),
            "quarter":            s.quarter_effect(returns).to_dict("records"),
            "turn_of_month":      s.turn_of_month_effect(returns),
            "january_effect":     s.january_effect(returns),
            "monday_effect":      s.monday_effect(returns),
        }
