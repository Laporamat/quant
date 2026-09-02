"""
stats/drawdown.py
Max drawdown, drawdown duration, underwater curve, drawdown statistics.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List


class DrawdownAnalysis:
    """Drawdown-related metrics for an equity curve."""

    # ──────────────────────────────────────────
    # Underwater Curve
    # ──────────────────────────────────────────
    @staticmethod
    def underwater(equity: pd.Series) -> pd.Series:
        """Drawdown (percentage below running peak) at each timestep."""
        roll_max = equity.cummax()
        return ((equity - roll_max) / roll_max).rename("drawdown")

    # ──────────────────────────────────────────
    # Max Drawdown
    # ──────────────────────────────────────────
    @staticmethod
    def max_drawdown(equity: pd.Series) -> float:
        """Maximum percentage drawdown (negative number)."""
        uw = DrawdownAnalysis.underwater(equity)
        return float(uw.min())

    # ──────────────────────────────────────────
    # Drawdown Duration
    # ──────────────────────────────────────────
    @staticmethod
    def max_drawdown_duration(equity: pd.Series) -> int:
        """Maximum drawdown duration in trading days."""
        uw = DrawdownAnalysis.underwater(equity)
        in_dd = uw < 0
        duration = 0
        max_duration = 0
        for val in in_dd:
            if val:
                duration += 1
                max_duration = max(max_duration, duration)
            else:
                duration = 0
        return max_duration

    # ──────────────────────────────────────────
    # All Drawdown Periods
    # ──────────────────────────────────────────
    @staticmethod
    def drawdown_periods(equity: pd.Series) -> List[Dict]:
        """
        Return a list of all drawdown periods with:
        start, end, trough, duration, drawdown_pct.
        """
        uw = DrawdownAnalysis.underwater(equity)
        periods: List[Dict] = []
        start    = None
        trough   = 0.0
        trough_d = None

        for date, val in uw.items():
            if val < 0 and start is None:
                start = date
                trough = val
                trough_d = date
            elif val < 0 and start is not None:
                if val < trough:
                    trough = val
                    trough_d = date
            elif val == 0 and start is not None:
                periods.append({
                    "start":          start,
                    "trough":         trough_d,
                    "end":            date,
                    "duration_days":  (date - start).days,
                    "drawdown_pct":   round(trough * 100, 4),
                    "recovery_days":  (date - trough_d).days,
                })
                start    = None
                trough   = 0.0
                trough_d = None

        # Open-ended drawdown at end of series
        if start is not None:
            periods.append({
                "start":          start,
                "trough":         trough_d,
                "end":            None,
                "duration_days":  (uw.index[-1] - start).days,
                "drawdown_pct":   round(trough * 100, 4),
                "recovery_days":  None,
            })

        return periods

    # ──────────────────────────────────────────
    # Top N Drawdowns
    # ──────────────────────────────────────────
    @staticmethod
    def top_drawdowns(equity: pd.Series, n: int = 10) -> pd.DataFrame:
        """Return the n worst drawdown periods sorted by magnitude."""
        periods = DrawdownAnalysis.drawdown_periods(equity)
        df = pd.DataFrame(periods)
        if df.empty:
            return df
        return df.nsmallest(n, "drawdown_pct").reset_index(drop=True)

    # ──────────────────────────────────────────
    # Recovery Statistics
    # ──────────────────────────────────────────
    @staticmethod
    def recovery_factor(equity: pd.Series) -> float:
        """Total return divided by maximum drawdown (absolute)."""
        total = float(equity.iloc[-1] / equity.iloc[0] - 1)
        mdd   = abs(DrawdownAnalysis.max_drawdown(equity))
        return float(total / mdd) if mdd > 0 else np.inf

    # ──────────────────────────────────────────
    # Average Drawdown
    # ──────────────────────────────────────────
    @staticmethod
    def average_drawdown(equity: pd.Series) -> float:
        """Mean drawdown across all drawdown periods."""
        periods = DrawdownAnalysis.drawdown_periods(equity)
        if not periods:
            return 0.0
        return float(np.mean([p["drawdown_pct"] for p in periods]) / 100)

    # ──────────────────────────────────────────
    # Full Summary
    # ──────────────────────────────────────────
    @staticmethod
    def summary(equity: pd.Series) -> Dict:
        """Return a comprehensive drawdown summary dict."""
        periods = DrawdownAnalysis.drawdown_periods(equity)
        completed = [p for p in periods if p["end"] is not None]

        avg_duration    = np.mean([p["duration_days"]  for p in completed]) if completed else 0
        avg_recovery    = np.mean([p["recovery_days"]  for p in completed]) if completed else 0

        return {
            "max_drawdown":           DrawdownAnalysis.max_drawdown(equity),
            "max_drawdown_duration":  DrawdownAnalysis.max_drawdown_duration(equity),
            "average_drawdown":       DrawdownAnalysis.average_drawdown(equity),
            "recovery_factor":        DrawdownAnalysis.recovery_factor(equity),
            "num_drawdown_periods":   len(periods),
            "avg_dd_duration_days":   float(avg_duration),
            "avg_recovery_days":      float(avg_recovery),
        }
