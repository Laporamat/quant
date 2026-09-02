"""
stats/distribution.py
Return distribution fitting, VaR, CVaR, tail risk metrics.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from typing import Dict, Optional


class DistributionAnalysis:
    """Distribution fitting and tail risk analysis."""

    # ──────────────────────────────────────────
    # VaR methods
    # ──────────────────────────────────────────
    @staticmethod
    def var_historical(returns: pd.Series, confidence: float = 0.95) -> float:
        """Historical VaR at *confidence* level (positive value = loss)."""
        return float(-returns.dropna().quantile(1 - confidence))

    @staticmethod
    def var_parametric(
        returns: pd.Series,
        confidence: float = 0.95,
    ) -> float:
        """Parametric (Gaussian) VaR."""
        mu  = returns.mean()
        sig = returns.std(ddof=1)
        z   = scipy_stats.norm.ppf(1 - confidence)
        return float(-(mu + z * sig))

    @staticmethod
    def var_cornish_fisher(
        returns: pd.Series,
        confidence: float = 0.95,
    ) -> float:
        """Cornish-Fisher VaR (accounts for skewness and excess kurtosis)."""
        mu   = returns.mean()
        sig  = returns.std(ddof=1)
        s    = scipy_stats.skew(returns.dropna())
        k    = scipy_stats.kurtosis(returns.dropna(), fisher=True)   # excess
        z    = scipy_stats.norm.ppf(1 - confidence)
        zc   = (
            z
            + (z**2 - 1) * s / 6
            + (z**3 - 3 * z) * k / 24
            - (2 * z**3 - 5 * z) * s**2 / 36
        )
        return float(-(mu + zc * sig))

    # ──────────────────────────────────────────
    # CVaR / Expected Shortfall
    # ──────────────────────────────────────────
    @staticmethod
    def cvar_historical(returns: pd.Series, confidence: float = 0.95) -> float:
        """Historical CVaR (Expected Shortfall) – mean of losses beyond VaR."""
        var = DistributionAnalysis.var_historical(returns, confidence)
        tail = returns[returns <= -var]
        return float(-tail.mean()) if not tail.empty else var

    @staticmethod
    def cvar_parametric(
        returns: pd.Series,
        confidence: float = 0.95,
    ) -> float:
        """Parametric (Gaussian) CVaR."""
        mu   = returns.mean()
        sig  = returns.std(ddof=1)
        z    = scipy_stats.norm.ppf(1 - confidence)
        es   = -(mu - sig * scipy_stats.norm.pdf(z) / (1 - confidence))
        return float(es)

    # ──────────────────────────────────────────
    # Distribution fitting
    # ──────────────────────────────────────────
    @staticmethod
    def fit_best_distribution(
        returns: pd.Series,
        candidates: list[str] | None = None,
    ) -> Dict:
        """
        Fit multiple distributions and select best by KS test.
        Returns: {name, params, ks_stat, ks_pvalue}
        """
        if candidates is None:
            candidates = ["norm", "t", "laplace", "logistic", "gennorm"]

        clean = returns.dropna().values
        best = {"name": None, "ks_stat": np.inf, "ks_pvalue": 0.0, "params": None}

        for name in candidates:
            try:
                dist = getattr(scipy_stats, name)
                params = dist.fit(clean)
                ks_stat, ks_p = scipy_stats.kstest(
                    clean, name, args=params
                )
                if ks_stat < best["ks_stat"]:
                    best = {
                        "name":      name,
                        "ks_stat":   float(ks_stat),
                        "ks_pvalue": float(ks_p),
                        "params":    [float(p) for p in params],
                    }
            except Exception:
                continue

        return best

    @staticmethod
    def fit_t_distribution(returns: pd.Series) -> Dict:
        """Fit Student-t distribution and return degrees of freedom, loc, scale."""
        clean = returns.dropna().values
        df, loc, scale = scipy_stats.t.fit(clean)
        return {
            "df":    float(df),
            "loc":   float(loc),
            "scale": float(scale),
            "implied_kurtosis": 6.0 / (df - 4) if df > 4 else np.inf,
        }

    # ──────────────────────────────────────────
    # Extreme Value Theory – GPD tail fit
    # ──────────────────────────────────────────
    @staticmethod
    def gpd_tail(
        returns: pd.Series,
        confidence: float = 0.95,
    ) -> Dict:
        """
        Fit Generalised Pareto Distribution (GPD) to the left tail.
        Used for EVT-based VaR beyond historical range.
        """
        threshold = float(returns.quantile(1 - confidence))
        tail = -(returns[returns < threshold])  # positive losses
        if len(tail) < 10:
            return {"error": "insufficient tail data"}

        try:
            xi, loc, beta = scipy_stats.genpareto.fit(tail, floc=0)
        except Exception as e:
            return {"error": str(e)}

        # EVT VaR
        n  = len(returns)
        nu = len(tail)
        p  = 1 - confidence
        evt_var = threshold + beta / xi * ((n / nu * p) ** (-xi) - 1) if xi != 0 else \
                  threshold - beta * np.log(n / nu * p)

        return {
            "gpd_xi":    float(xi),
            "gpd_beta":  float(beta),
            "gpd_loc":   float(loc),
            "n_tail":    int(nu),
            "threshold": float(threshold),
            "evt_var":   float(evt_var),
        }

    # ──────────────────────────────────────────
    # Full Tail Risk Report
    # ──────────────────────────────────────────
    @staticmethod
    def tail_risk_report(
        returns: pd.Series,
        confidences: list[float] | None = None,
    ) -> Dict:
        """Compute VaR and CVaR at multiple confidence levels."""
        if confidences is None:
            confidences = [0.90, 0.95, 0.99]
        da = DistributionAnalysis
        report: Dict = {}
        for c in confidences:
            clabel = f"{int(c*100)}"
            report[f"var_hist_{clabel}"]  = da.var_historical(returns, c)
            report[f"var_param_{clabel}"] = da.var_parametric(returns, c)
            report[f"var_cf_{clabel}"]    = da.var_cornish_fisher(returns, c)
            report[f"cvar_hist_{clabel}"] = da.cvar_historical(returns, c)
            report[f"cvar_param_{clabel}"]= da.cvar_parametric(returns, c)

        report["best_fit"]     = da.fit_best_distribution(returns)
        report["t_dist_fit"]   = da.fit_t_distribution(returns)
        report["gpd_tail_95"]  = da.gpd_tail(returns, 0.95)
        return report
