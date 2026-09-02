"""
strategies/ml_strategy.py
Machine-learning signal generation using Random Forest / XGBoost.
Features: technical indicators, rolling stats, calendar features.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from strategies.base_strategy import BaseStrategy, Signal, SignalType
from indicators.moving_averages import MovingAverages as MA
from indicators.momentum import Momentum
from indicators.volatility import Volatility

logger = logging.getLogger(__name__)


class MLStrategy(BaseStrategy):
    """
    ML-based strategy that trains on historical features and generates
    BUY/SELL signals when predicted return > threshold.

    Parameters
    ----------
    model_type      : "rf" (Random Forest) | "xgb" (XGBoost) | "lgbm"
    lookahead       : forward return horizon to predict (default 5 days)
    feature_window  : training history lookback (default 504 days)
    retrain_freq    : days between retraining (default 63)
    threshold       : min predicted return to generate signal (default 0.005)
    top_k           : number of top ranked tickers to hold (default 5)
    """
    name = "ml"

    def prepare(self, data: Dict[str, pd.DataFrame]) -> None:
        self._tickers      = self.get_param("tickers") or list(data.keys())
        self._model_type   = self.get_param("model_type", "rf")
        self._lookahead    = self.get_param("lookahead", 5)
        self._feat_window  = self.get_param("feature_window", 504)
        self._retrain_freq = self.get_param("retrain_freq", 63)
        self._threshold    = self.get_param("threshold", 0.005)
        self._top_k        = self.get_param("top_k", 5)

        self._models:    Dict[str, object] = {}
        self._last_train:Dict[str, Optional[pd.Timestamp]] = {t: None for t in self._tickers}
        self._holdings:  set = set()

        # Pre-compute features for all tickers
        self._features: Dict[str, pd.DataFrame] = {}
        for ticker in self._tickers:
            df = data.get(ticker)
            if df is None or df.empty:
                continue
            try:
                self._features[ticker] = self._build_features(df)
            except Exception as e:
                logger.warning("Feature build failed for %s: %s", ticker, e)

    def generate_signals(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.DataFrame],
        portfolio_state: Optional[Dict] = None,
    ) -> List[Signal]:
        predictions: Dict[str, float] = {}

        for ticker in self._tickers:
            feat_df = self._features.get(ticker)
            if feat_df is None:
                continue

            df = data.get(ticker)
            if df is None:
                continue

            # Retrain if needed
            if self._needs_retrain(ticker, date):
                self._train(ticker, feat_df.loc[:date], df)
                self._last_train[ticker] = date

            model = self._models.get(ticker)
            if model is None:
                continue

            # Predict on current bar
            row = feat_df.loc[:date].dropna()
            if row.empty:
                continue
            X = row.iloc[[-1]].values
            try:
                pred = float(model.predict(X)[0])
                predictions[ticker] = pred
            except Exception:
                continue

        if not predictions:
            return []

        # Rank and select top-k
        sorted_pred = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
        new_holdings = {t for t, p in sorted_pred[:self._top_k] if p > self._threshold}

        signals: List[Signal] = []
        weight = 1.0 / len(new_holdings) if new_holdings else 0.0

        for ticker in self._holdings - new_holdings:
            df = data.get(ticker)
            if df is None:
                continue
            row = df.loc[:date]
            if row.empty:
                continue
            signals.append(Signal(
                date=date, ticker=ticker, signal=SignalType.SELL,
                strength=1.0, price=float(row["close"].iloc[-1]),
            ))

        for ticker in new_holdings - self._holdings:
            df = data.get(ticker)
            if df is None:
                continue
            row = df.loc[:date]
            if row.empty:
                continue
            signals.append(Signal(
                date=date, ticker=ticker, signal=SignalType.BUY,
                strength=weight, price=float(row["close"].iloc[-1]),
                meta={"pred_return": predictions.get(ticker, 0.0)},
            ))

        self._holdings = new_holdings
        return signals

    # ──────────────────────────────────────────
    # Feature Engineering
    # ──────────────────────────────────────────

    @staticmethod
    def _build_features(df: pd.DataFrame) -> pd.DataFrame:
        """Build feature matrix from OHLCV data."""
        close = df["close"]
        high  = df["high"]
        low   = df["low"]
        vol   = df["volume"]

        feat = pd.DataFrame(index=df.index)

        # Price-based
        for p in [5, 10, 21, 63, 126, 252]:
            feat[f"ret_{p}d"] = close.pct_change(p)

        # Moving averages ratios
        for p in [10, 20, 50, 200]:
            feat[f"price_sma{p}_ratio"] = close / MA.sma(close, p) - 1

        # RSI
        feat["rsi_14"] = Momentum.rsi(close, 14)
        feat["rsi_28"] = Momentum.rsi(close, 28)

        # Volatility
        feat["hvol_21"]  = Volatility.historical_volatility(close, 21, True)
        feat["hvol_63"]  = Volatility.historical_volatility(close, 63, True)
        feat["atr_norm"] = Volatility.atr(high, low, close, 14) / close

        # MACD
        macd = Momentum.macd(close)
        feat["macd_hist"] = macd["macd_hist"] / (close + 1e-10)

        # Volume
        feat["vol_ratio"] = vol / (vol.rolling(21).mean() + 1e-10)

        # Calendar
        feat["month"]      = df.index.month
        feat["day_of_week"] = df.index.dayofweek
        feat["is_jan"]     = (df.index.month == 1).astype(int)

        return feat.dropna()

    # ──────────────────────────────────────────
    # Model Training
    # ──────────────────────────────────────────

    def _train(
        self,
        ticker: str,
        feat_df: pd.DataFrame,
        price_df: pd.DataFrame,
    ) -> None:
        """Train the ML model for *ticker* on available features."""
        window = self._feat_window
        feat   = feat_df.tail(window).copy()
        close  = price_df["close"].reindex(feat.index)

        # Forward return as label
        fwd_ret = close.pct_change(self._lookahead).shift(-self._lookahead)
        aligned = pd.concat([feat, fwd_ret.rename("label")], axis=1).dropna()

        if len(aligned) < 50:
            logger.debug("Not enough data to train %s", ticker)
            return

        X = aligned.drop(columns=["label"]).values
        y = aligned["label"].values

        try:
            model = self._build_model()
            model.fit(X, y)
            self._models[ticker] = model
        except Exception as e:
            logger.error("Training failed for %s: %s", ticker, e)

    def _build_model(self):
        if self._model_type == "xgb":
            from xgboost import XGBRegressor
            return XGBRegressor(
                n_estimators=100, max_depth=4, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                random_state=42, verbosity=0,
            )
        elif self._model_type == "lgbm":
            from lightgbm import LGBMRegressor
            return LGBMRegressor(
                n_estimators=100, max_depth=4, learning_rate=0.05,
                random_state=42, verbose=-1,
            )
        else:  # Random Forest
            from sklearn.ensemble import RandomForestRegressor
            return RandomForestRegressor(
                n_estimators=100, max_depth=6, min_samples_leaf=5,
                random_state=42, n_jobs=-1,
            )

    def _needs_retrain(self, ticker: str, date: pd.Timestamp) -> bool:
        last = self._last_train.get(ticker)
        if last is None:
            return True
        return (date - last).days >= self._retrain_freq
