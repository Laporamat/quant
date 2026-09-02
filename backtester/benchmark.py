"""
backtester/benchmark.py
Compare strategy vs a benchmark (SPY, SET50 proxy, etc.)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, Optional

from stats.risk_metrics import RiskMetrics
from stats.drawdown import DrawdownAnalysis


class BenchmarkComparison:
    """Side-by-side performance comparison of strategy vs benchmark."""

    @staticmethod
    def compare(
        strategy_equity:   pd.Series,
        benchmark_prices:  pd.Series,
        strategy_name:     str = "Strategy",
        benchmark_name:    str = "Benchmark",
        risk_free:         float = 0.02,
        trading_days:      int = 252,
    ) -> Dict:
        """
        Comprehensive side-by-side comparison.

        Parameters
        ----------
        strategy_equity  : strategy total equity curve
        benchmark_prices : benchmark close prices (same index)
        """
        # Align
        aligned = pd.concat(
            [strategy_equity.rename("strategy"), benchmark_prices.rename("bench")],
            axis=1,
        ).dropna()

        if len(aligned) < 5:
            return {"error": "insufficient aligned data"}

        strat_eq = aligned["strategy"]
        bench_eq = aligned["bench"]

        # Rebase to 1.0
        strat_rebased = strat_eq / strat_eq.iloc[0]
        bench_rebased = bench_eq / bench_eq.iloc[0]

        strat_ret = strat_rebased.pct_change().dropna()
        bench_ret = bench_rebased.pct_change().dropna()

        rm = RiskMetrics
        da = DrawdownAnalysis

        def _metrics(eq: pd.Series, ret: pd.Series, name: str) -> Dict:
            n_years = len(ret) / trading_days
            total   = float(eq.iloc[-1] / eq.iloc[0] - 1)
            cagr    = float((1 + total) ** (1 / n_years) - 1) if n_years > 0 else 0.0
            return {
                f"{name}_total_return":  round(total, 4),
                f"{name}_cagr":          round(cagr, 4),
                f"{name}_ann_vol":       round(float(ret.std(ddof=1) * np.sqrt(trading_days)), 4),
                f"{name}_sharpe":        round(rm.sharpe(ret, risk_free, trading_days), 4),
                f"{name}_sortino":       round(rm.sortino(ret, risk_free, trading_days), 4),
                f"{name}_calmar":        round(rm.calmar(ret, trading_days), 4),
                f"{name}_max_drawdown":  round(da.max_drawdown(eq), 4),
                f"{name}_mdd_duration":  da.max_drawdown_duration(eq),
            }

        result = {}
        result.update(_metrics(strat_rebased, strat_ret, strategy_name))
        result.update(_metrics(bench_rebased, bench_ret, benchmark_name))

        # Relative metrics
        result.update({
            "beta":              round(rm.beta(strat_ret, bench_ret), 4),
            "alpha_annual":      round(rm.alpha(strat_ret, bench_ret, risk_free, trading_days), 4),
            "information_ratio": round(rm.information_ratio(strat_ret, bench_ret, trading_days), 4),
            "correlation":       round(float(strat_ret.corr(bench_ret)), 4),
            "excess_return":     round(
                result.get(f"{strategy_name}_cagr", 0) - result.get(f"{benchmark_name}_cagr", 0), 4
            ),
        })

        return result

    @staticmethod
    def relative_strength_chart(
        strategy_equity: pd.Series,
        benchmark_prices: pd.Series,
    ) -> pd.DataFrame:
        """Return a DataFrame with both curves rebased to 1.0 and relative strength."""
        aligned = pd.concat(
            [strategy_equity, benchmark_prices],
            axis=1, keys=["strategy", "benchmark"],
        ).dropna()
        rebased = aligned / aligned.iloc[0]
        rebased["relative_strength"] = rebased["strategy"] / rebased["benchmark"]
        return rebased

    @staticmethod
    def rolling_comparison(
        strategy_returns:  pd.Series,
        benchmark_returns: pd.Series,
        window:            int = 63,
        trading_days:      int = 252,
    ) -> pd.DataFrame:
        """Rolling Sharpe, beta, alpha, and correlation vs benchmark."""
        rm = RiskMetrics
        result = pd.DataFrame(index=strategy_returns.index)
        result["rolling_sharpe"] = strategy_returns.rolling(window).apply(
            lambda x: rm.sharpe(pd.Series(x), trading_days=trading_days), raw=False
        )
        result["rolling_beta"] = strategy_returns.rolling(window).apply(
            lambda x: rm.beta(pd.Series(x), benchmark_returns.reindex(
                strategy_returns.index[
                    strategy_returns.index.get_loc(x.index[-1]) - window + 1:
                    strategy_returns.index.get_loc(x.index[-1]) + 1
                ]
            )) if len(x) == window else np.nan,
            raw=False,
        )
        result["rolling_corr"] = strategy_returns.rolling(window).corr(benchmark_returns)
        return result
