"""
stats/factor_analysis.py
Fama-French 3/5 factor loading, alpha/beta decomposition via OLS.
Downloads FF factors from Ken French's website via pandas_datareader.
"""
from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class FactorAnalysis:
    """Factor model analysis (Fama-French 3 and 5 factors)."""

    # ──────────────────────────────────────────
    # Data helpers
    # ──────────────────────────────────────────
    @staticmethod
    def load_ff3(start: str = "2004-01-01", end: str = "2024-12-31") -> pd.DataFrame:
        """
        Load Fama-French 3 factors from pandas_datareader.
        Columns: Mkt-RF, SMB, HML, RF
        """
        try:
            import pandas_datareader.data as web
            ff3 = web.DataReader(
                "F-F_Research_Data_Factors_daily",
                "famafrench",
                start=start,
                end=end,
            )[0] / 100  # convert from % to decimal
            ff3.index = pd.to_datetime(ff3.index)
            return ff3
        except Exception as exc:
            logger.error("Could not download FF3 factors: %s", exc)
            return pd.DataFrame()

    @staticmethod
    def load_ff5(start: str = "2004-01-01", end: str = "2024-12-31") -> pd.DataFrame:
        """
        Load Fama-French 5 factors from pandas_datareader.
        Columns: Mkt-RF, SMB, HML, RMW, CMA, RF
        """
        try:
            import pandas_datareader.data as web
            ff5 = web.DataReader(
                "F-F_Research_Data_5_Factors_2x3_daily",
                "famafrench",
                start=start,
                end=end,
            )[0] / 100
            ff5.index = pd.to_datetime(ff5.index)
            return ff5
        except Exception as exc:
            logger.error("Could not download FF5 factors: %s", exc)
            return pd.DataFrame()

    # ──────────────────────────────────────────
    # OLS factor regression
    # ──────────────────────────────────────────
    @staticmethod
    def ols_factor_regression(
        returns: pd.Series,
        factors: pd.DataFrame,
        risk_free_col: str = "RF",
    ) -> Dict[str, float]:
        """
        OLS regression of excess returns on factor returns.

        Parameters
        ----------
        returns    : strategy/stock daily returns
        factors    : DataFrame with factor columns + risk-free column
        risk_free_col : name of risk-free rate column in *factors*

        Returns
        -------
        dict with alpha, betas per factor, R², t-stats
        """
        import statsmodels.api as sm

        rf = factors[risk_free_col] if risk_free_col in factors.columns else 0.0
        y  = (returns - rf).dropna()
        X  = factors.drop(columns=[risk_free_col], errors="ignore")
        aligned = pd.concat([y, X], axis=1).dropna()

        y_clean = aligned.iloc[:, 0]
        X_clean = sm.add_constant(aligned.iloc[:, 1:])
        model   = sm.OLS(y_clean, X_clean).fit()

        result = {"alpha": float(model.params["const"])}
        for col in X.columns:
            result[f"beta_{col.replace('-', '_').lower()}"] = float(model.params[col])
            result[f"tstat_{col.replace('-', '_').lower()}"] = float(model.tvalues[col])

        result.update({
            "alpha_annualised": float(model.params["const"] * 252),
            "alpha_tstat":      float(model.tvalues["const"]),
            "alpha_pvalue":     float(model.pvalues["const"]),
            "r_squared":        float(model.rsquared),
            "adj_r_squared":    float(model.rsquared_adj),
            "n_obs":            int(model.nobs),
        })
        return result

    # ──────────────────────────────────────────
    # Convenience wrappers
    # ──────────────────────────────────────────
    @staticmethod
    def capm_regression(
        returns: pd.Series,
        market_returns: pd.Series,
        risk_free: float = 0.02,
        trading_days: int = 252,
    ) -> Dict[str, float]:
        """Simple CAPM one-factor regression."""
        import statsmodels.api as sm

        daily_rf = risk_free / trading_days
        excess_r = (returns - daily_rf).dropna()
        excess_m = (market_returns - daily_rf).dropna()
        aligned  = pd.concat([excess_r, excess_m], axis=1).dropna()

        y = aligned.iloc[:, 0]
        X = sm.add_constant(aligned.iloc[:, 1])
        model = sm.OLS(y, X).fit()

        return {
            "alpha":          float(model.params["const"]),
            "alpha_annual":   float(model.params["const"] * trading_days),
            "beta":           float(model.params.iloc[1]),
            "alpha_tstat":    float(model.tvalues["const"]),
            "alpha_pvalue":   float(model.pvalues["const"]),
            "r_squared":      float(model.rsquared),
            "n_obs":          int(model.nobs),
        }

    @staticmethod
    def rolling_beta(
        returns: pd.Series,
        benchmark: pd.Series,
        window: int = 252,
    ) -> pd.Series:
        """Rolling CAPM beta."""
        def _beta(s: pd.Series) -> float:
            if len(s) < 2:
                return np.nan
            cov = np.cov(s.values, benchmark.loc[s.index].values)
            return cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else np.nan
        return returns.rolling(window).apply(lambda x: _beta(x), raw=False)

    @staticmethod
    def factor_exposure_table(
        returns_panel: pd.DataFrame,
        factors: pd.DataFrame,
        risk_free_col: str = "RF",
    ) -> pd.DataFrame:
        """Compute factor loadings for each asset in a return panel."""
        rows = []
        for col in returns_panel.columns:
            row = FactorAnalysis.ols_factor_regression(
                returns_panel[col], factors, risk_free_col
            )
            row["ticker"] = col
            rows.append(row)
        return pd.DataFrame(rows).set_index("ticker")
