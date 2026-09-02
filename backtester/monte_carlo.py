"""
backtester/monte_carlo.py
Monte Carlo simulation on return paths for risk estimation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple


class MonteCarlo:
    """Monte Carlo simulation utilities for backtesting."""

    # ──────────────────────────────────────────
    # Bootstrap simulation
    # ──────────────────────────────────────────
    @staticmethod
    def bootstrap_equity(
        returns: pd.Series,
        n_sims:  int = 1000,
        n_days:  Optional[int] = None,
        block_size: int = 20,
        seed:    int = 42,
    ) -> pd.DataFrame:
        """
        Block-bootstrap equity paths (preserves autocorrelation structure).

        Parameters
        ----------
        returns    : historical daily returns
        n_sims     : number of simulated paths
        n_days     : simulation horizon (default = len(returns))
        block_size : block length for bootstrap
        seed       : random seed

        Returns
        -------
        DataFrame of shape (n_days, n_sims) – simulated equity paths
        """
        rng    = np.random.default_rng(seed)
        clean  = returns.dropna().values
        n_days = n_days or len(clean)

        # Build block array
        n_blocks = int(np.ceil(n_days / block_size))
        paths    = np.ones((n_days + 1, n_sims))

        for sim in range(n_sims):
            sampled = []
            while len(sampled) < n_days:
                start = rng.integers(0, len(clean) - block_size + 1)
                sampled.extend(clean[start: start + block_size].tolist())
            sampled = np.array(sampled[:n_days])
            paths[1:, sim] = np.cumprod(1 + sampled)

        return pd.DataFrame(paths, columns=[f"sim_{i}" for i in range(n_sims)])

    # ──────────────────────────────────────────
    # Parametric (Normal) simulation
    # ──────────────────────────────────────────
    @staticmethod
    def parametric_equity(
        returns:  pd.Series,
        n_sims:   int = 1000,
        n_days:   Optional[int] = None,
        seed:     int = 42,
    ) -> pd.DataFrame:
        """
        Simulate equity paths assuming normally distributed returns.
        """
        rng    = np.random.default_rng(seed)
        clean  = returns.dropna()
        mu     = float(clean.mean())
        sigma  = float(clean.std(ddof=1))
        n_days = n_days or len(clean)

        draws  = rng.normal(mu, sigma, (n_days, n_sims))
        paths  = np.vstack([np.ones(n_sims), np.cumprod(1 + draws, axis=0)])
        return pd.DataFrame(paths, columns=[f"sim_{i}" for i in range(n_sims)])

    # ──────────────────────────────────────────
    # Summary statistics across paths
    # ──────────────────────────────────────────
    @staticmethod
    def path_statistics(
        paths: pd.DataFrame,
        percentiles: List[float] | None = None,
        trading_days: int = 252,
    ) -> Dict:
        """
        Compute summary statistics across all simulated paths.

        Parameters
        ----------
        paths       : DataFrame of equity paths (rows=days, cols=simulations)
        percentiles : list of percentile levels (default [5,25,50,75,95])
        """
        if percentiles is None:
            percentiles = [5, 10, 25, 50, 75, 90, 95]

        final = paths.iloc[-1]   # terminal equity values

        # Annualised returns per path
        n_years = (len(paths) - 1) / trading_days
        ann_ret = (final ** (1 / n_years) - 1) if n_years > 0 else final

        # Max drawdown per path
        def _mdd(col: np.ndarray) -> float:
            peak = np.maximum.accumulate(col)
            return float(np.min((col - peak) / peak))

        mdds = paths.apply(lambda c: _mdd(c.values), axis=0)

        stats = {
            "n_sims":            len(final),
            "n_days":            len(paths) - 1,
            "mean_terminal":     float(final.mean()),
            "median_terminal":   float(final.median()),
            "std_terminal":      float(final.std()),
            "mean_ann_return":   float(ann_ret.mean()),
            "prob_positive":     float((final > 1.0).mean()),
            "prob_double":       float((final > 2.0).mean()),
            "mean_max_drawdown": float(mdds.mean()),
            "worst_max_drawdown":float(mdds.min()),
        }
        for p in percentiles:
            stats[f"p{p}_terminal"] = float(np.percentile(final, p))
            stats[f"p{p}_ann_ret"]  = float(np.percentile(ann_ret, p))
            stats[f"p{p}_mdd"]      = float(np.percentile(mdds, p))

        return stats

    # ──────────────────────────────────────────
    # VaR / CVaR via simulation
    # ──────────────────────────────────────────
    @staticmethod
    def mc_var_cvar(
        returns: pd.Series,
        horizon: int = 21,
        n_sims:  int = 10_000,
        confidence: float = 0.95,
        seed: int = 42,
    ) -> Dict[str, float]:
        """
        Monte Carlo VaR and CVaR for a *horizon*-day holding period.
        """
        paths = MonteCarlo.parametric_equity(returns, n_sims, horizon, seed)
        terminal_rets = paths.iloc[-1] - 1  # fraction
        var  = float(-np.percentile(terminal_rets, (1 - confidence) * 100))
        cvar = float(-terminal_rets[terminal_rets < -var].mean())
        return {
            "horizon":    horizon,
            "confidence": confidence,
            "var":        var,
            "cvar":       cvar,
        }
