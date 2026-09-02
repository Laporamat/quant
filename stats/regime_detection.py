"""
stats/regime_detection.py
Hidden Markov Model (HMM) based market regime detection.
Bull (0), Bear (1), Sideways (2) – with 2- or 3-state HMM.
"""
from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RegimeDetection:
    """Market regime detection using Gaussian HMM and heuristic methods."""

    # ──────────────────────────────────────────
    # HMM Regime Detection
    # ──────────────────────────────────────────
    @staticmethod
    def hmm_regimes(
        returns: pd.Series,
        n_states: int = 3,
        n_iter: int = 200,
        covariance_type: str = "full",
        random_state: int = 42,
    ) -> pd.DataFrame:
        """
        Fit a Gaussian HMM to daily returns and label regimes.

        Returns DataFrame with columns:
        - regime (0/1/2) labeled as bull/sideways/bear by mean return
        - regime_label ("Bull"/"Sideways"/"Bear")
        - regime_prob_0, regime_prob_1, ... (state probabilities)
        """
        try:
            from hmmlearn.hmm import GaussianHMM
        except ImportError:
            logger.error("hmmlearn not installed: pip install hmmlearn")
            return pd.DataFrame()

        clean = returns.dropna()
        X = clean.values.reshape(-1, 1)

        model = GaussianHMM(
            n_components=n_states,
            covariance_type=covariance_type,
            n_iter=n_iter,
            random_state=random_state,
        )
        model.fit(X)
        states = model.predict(X)
        probs  = model.predict_proba(X)

        # Sort states by mean return: highest = bull, lowest = bear
        means  = model.means_.flatten()
        order  = np.argsort(means)[::-1]  # descending
        rank_map = {orig: new for new, orig in enumerate(order)}
        remapped  = np.vectorize(rank_map.get)(states)

        labels = ["Bull", "Sideways", "Bear"][:n_states]
        label_map = {i: labels[i] for i in range(n_states)}

        result = pd.DataFrame(index=clean.index)
        result["regime"] = remapped
        result["regime_label"] = result["regime"].map(label_map)
        for i in range(n_states):
            result[f"regime_prob_{i}"] = probs[:, order[i]]

        return result

    # ──────────────────────────────────────────
    # Heuristic Regime (moving-average based)
    # ──────────────────────────────────────────
    @staticmethod
    def ma_regime(
        close: pd.Series,
        fast: int = 50,
        slow: int = 200,
    ) -> pd.Series:
        """
        Simple MA-based regime:
        Bull  (1) = price > slow MA and fast > slow
        Bear (-1) = price < slow MA and fast < slow
        Neutral (0) = mixed signals
        """
        sma_fast = close.rolling(fast).mean()
        sma_slow = close.rolling(slow).mean()
        bull = (close > sma_slow) & (sma_fast > sma_slow)
        bear = (close < sma_slow) & (sma_fast < sma_slow)
        regime = pd.Series(0, index=close.index, name="ma_regime")
        regime[bull] = 1
        regime[bear] = -1
        return regime

    # ──────────────────────────────────────────
    # Volatility Regime
    # ──────────────────────────────────────────
    @staticmethod
    def volatility_regime(
        returns: pd.Series,
        low_pct: float = 0.33,
        high_pct: float = 0.67,
        window: int = 21,
        lookback: int = 252,
    ) -> pd.Series:
        """
        Volatility-based regime:
        0 = low vol, 1 = mid vol, 2 = high vol
        """
        hv = returns.rolling(window).std() * np.sqrt(252)
        lo = hv.rolling(lookback).quantile(low_pct)
        hi = hv.rolling(lookback).quantile(high_pct)
        regime = pd.Series(1, index=returns.index, name="vol_regime")
        regime[hv <= lo] = 0
        regime[hv >= hi] = 2
        return regime

    # ──────────────────────────────────────────
    # Regime Statistics
    # ──────────────────────────────────────────
    @staticmethod
    def regime_stats(returns: pd.Series, regime: pd.Series) -> pd.DataFrame:
        """
        Compute return statistics per regime label.

        Returns DataFrame with mean/std/count per regime.
        """
        combined = pd.concat([returns, regime], axis=1).dropna()
        combined.columns = ["return", "regime"]

        rows = []
        for lbl, grp in combined.groupby("regime"):
            rows.append({
                "regime":      lbl,
                "count":       len(grp),
                "pct_days":    len(grp) / len(combined) * 100,
                "mean_return": float(grp["return"].mean() * 252),
                "volatility":  float(grp["return"].std() * np.sqrt(252)),
                "sharpe":      float(
                    grp["return"].mean() / grp["return"].std() * np.sqrt(252)
                ) if grp["return"].std() > 0 else 0.0,
            })
        return pd.DataFrame(rows)

    # ──────────────────────────────────────────
    # Regime Transition Matrix
    # ──────────────────────────────────────────
    @staticmethod
    def transition_matrix(regime: pd.Series) -> pd.DataFrame:
        """Empirical regime transition probability matrix."""
        states  = sorted(regime.dropna().unique())
        matrix  = pd.DataFrame(0, index=states, columns=states, dtype=float)
        for s1, s2 in zip(regime[:-1], regime[1:]):
            if pd.notna(s1) and pd.notna(s2):
                matrix.loc[s1, s2] += 1
        row_sums = matrix.sum(axis=1)
        return matrix.divide(row_sums, axis=0).fillna(0)
