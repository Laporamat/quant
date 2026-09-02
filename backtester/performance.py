"""
backtester/performance.py
Full performance analytics report from a backtest equity curve.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Optional

from config import TRADING_DAYS_PER_YEAR
from stats.risk_metrics import RiskMetrics
from stats.drawdown import DrawdownAnalysis
from stats.returns import ReturnStats


class PerformanceAnalytics:
    """Compute comprehensive performance metrics from equity curve + returns."""

    @staticmethod
    def full_report(
        equity: pd.Series,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        risk_free: float = 0.02,
        trading_days: int = TRADING_DAYS_PER_YEAR,
        benchmark_ticker: str = "SPY",
    ) -> Dict:
        """
        Generate a comprehensive performance report.

        Parameters
        ----------
        equity            : portfolio equity curve
        returns           : daily portfolio returns
        benchmark_returns : optional benchmark return series
        risk_free         : annual risk-free rate
        trading_days      : trading days per year

        Returns
        -------
        dict of performance metrics
        """
        if returns.empty or equity.empty:
            return {"error": "empty returns/equity"}

        rm    = RiskMetrics
        da    = DrawdownAnalysis
        rs    = ReturnStats

        # ── Return metrics ────────────────────
        total_return = float(equity.iloc[-1] / equity.iloc[0] - 1)
        n_years      = len(returns) / trading_days
        cagr         = float((1 + total_return) ** (1 / n_years) - 1) if n_years > 0 else 0.0
        ann_vol      = float(returns.std(ddof=1) * np.sqrt(trading_days))

        # ── Risk-adjusted ────────────────────
        sharpe  = rm.sharpe(returns, risk_free, trading_days)
        sortino = rm.sortino(returns, risk_free, trading_days)
        calmar  = rm.calmar(returns, trading_days)
        omega   = rm.omega(returns)

        # ── Drawdown ─────────────────────────
        mdd      = da.max_drawdown(equity)
        mdd_dur  = da.max_drawdown_duration(equity)
        avg_dd   = da.average_drawdown(equity)
        rec_fac  = da.recovery_factor(equity)

        # ── Win/Loss stats ───────────────────
        pos_days  = (returns > 0).sum()
        neg_days  = (returns < 0).sum()
        win_rate  = pos_days / len(returns) if len(returns) > 0 else 0.0
        avg_win   = float(returns[returns > 0].mean()) if pos_days > 0 else 0.0
        avg_loss  = float(returns[returns < 0].mean()) if neg_days > 0 else 0.0
        payoff    = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0

        # ── Monthly table ────────────────────
        try:
            monthly_tbl = rs.monthly_return_table(equity).to_dict()
        except Exception:
            monthly_tbl = {}

        # ── VaR / CVaR ───────────────────────
        from stats.distribution import DistributionAnalysis
        var_95  = DistributionAnalysis.var_historical(returns, 0.95)
        cvar_95 = DistributionAnalysis.cvar_historical(returns, 0.95)
        var_99  = DistributionAnalysis.var_historical(returns, 0.99)

        report = {
            # Core
            "start_date":       str(equity.index[0].date()),
            "end_date":         str(equity.index[-1].date()),
            "n_days":           len(returns),
            "n_years":          round(n_years, 2),
            "initial_capital":  float(equity.iloc[0]),
            "final_equity":     float(equity.iloc[-1]),

            # Returns
            "total_return":     round(total_return, 6),
            "cagr":             round(cagr, 6),
            "ann_volatility":   round(ann_vol, 6),
            "avg_daily_return": round(float(returns.mean()), 6),

            # Risk-adjusted
            "sharpe":           round(sharpe, 4),
            "sortino":          round(sortino, 4),
            "calmar":           round(calmar, 4),
            "omega":            round(omega, 4),
            "ulcer_index":      round(rm.ulcer_index(returns), 4),
            "martin_ratio":     round(rm.martin_ratio(returns, risk_free, trading_days), 4),
            "gain_to_pain":     round(rm.gain_to_pain(returns), 4),
            "tail_ratio":       round(rm.tail_ratio(returns), 4),

            # Drawdown
            "max_drawdown":           round(mdd, 6),
            "max_drawdown_duration":  int(mdd_dur),
            "avg_drawdown":           round(avg_dd, 6),
            "recovery_factor":        round(rec_fac, 4),

            # Trade stats
            "win_rate":         round(win_rate, 4),
            "avg_win":          round(avg_win, 6),
            "avg_loss":         round(avg_loss, 6),
            "payoff_ratio":     round(payoff, 4),
            "positive_days":    int(pos_days),
            "negative_days":    int(neg_days),

            # Risk
            "var_95":           round(var_95, 6),
            "cvar_95":          round(cvar_95, 6),
            "var_99":           round(var_99, 6),

            # Calendar
            "monthly_returns":  monthly_tbl,
        }

        # ── vs Benchmark ─────────────────────
        if benchmark_returns is not None:
            aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
            if len(aligned) > 5:
                strat_r = aligned.iloc[:, 0]
                bench_r = aligned.iloc[:, 1]
                report.update({
                    "benchmark":         benchmark_ticker,
                    "beta":              round(rm.beta(strat_r, bench_r), 4),
                    "alpha_annual":      round(rm.alpha(strat_r, bench_r, risk_free, trading_days), 4),
                    "information_ratio": round(rm.information_ratio(strat_r, bench_r, trading_days), 4),
                    "treynor":           round(rm.treynor(strat_r, bench_r, risk_free, trading_days), 4),
                })

        return report
