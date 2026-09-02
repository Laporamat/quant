"""
data/cleaner.py
Clean OHLCV data: handle missing values, outliers, corporate actions,
and ensure data quality before feeding into indicators / backtester.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Cleans a raw OHLCV DataFrame.

    Pipeline (applied in order)
    ---------------------------
    1. Standardise column names & index
    2. Remove duplicated timestamps
    3. Forward-fill short gaps (weekend / holiday) ≤ max_gap days
    4. Drop rows where close is NaN
    5. Clip extreme price outliers (z-score threshold)
    6. Validate OHLCV consistency (high >= low, etc.)
    7. Handle splits & dividends (already adjusted if using auto_adjust=True)
    8. Compute derived columns: returns, log_returns, typical_price
    """

    def __init__(
        self,
        max_gap: int = 3,              # consecutive NaN days to forward-fill
        z_threshold: float = 8.0,      # zscore beyond which close is treated as outlier
        min_price: float = 0.01,       # filter penny stocks / bad data
        min_volume: float = 0.0,       # 0 = allow zero volume
    ) -> None:
        self.max_gap = max_gap
        self.z_threshold = z_threshold
        self.min_price = min_price
        self.min_volume = min_volume

    # ──────────────────────────────────────────
    # Main entry point
    # ──────────────────────────────────────────

    def clean(self, df: pd.DataFrame, ticker: str = "?") -> pd.DataFrame:
        """
        Run the full cleaning pipeline on *df*.

        Parameters
        ----------
        df     : raw OHLCV DataFrame with DatetimeIndex
        ticker : symbol name used in log messages

        Returns
        -------
        Cleaned DataFrame
        """
        if df is None or df.empty:
            logger.warning("[%s] Empty DataFrame – nothing to clean", ticker)
            return pd.DataFrame()

        df = df.copy()
        n_raw = len(df)

        df = self._standardise(df)
        df = self._remove_duplicates(df)
        df = self._fill_gaps(df)
        df = self._drop_null_close(df)
        df = self._remove_outliers(df, ticker)
        df = self._validate_ohlcv(df, ticker)
        df = self._filter_min_price(df)
        df = self._add_derived_columns(df)

        n_clean = len(df)
        logger.info(
            "[%s] Cleaned: %d rows → %d rows (removed %d)",
            ticker, n_raw, n_clean, n_raw - n_clean,
        )
        return df

    def clean_panel(
        self, panel: Dict[str, pd.DataFrame]
    ) -> Dict[str, pd.DataFrame]:
        """Clean a dict of {ticker: df}."""
        return {t: self.clean(df, ticker=t) for t, df in panel.items()}

    # ──────────────────────────────────────────
    # Individual cleaning steps
    # ──────────────────────────────────────────

    @staticmethod
    def _standardise(df: pd.DataFrame) -> pd.DataFrame:
        """Lower-case columns, ensure DatetimeIndex."""
        df.columns = [c.lower().strip() for c in df.columns]
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize(None)  # strip tz
        df.index.name = "date"
        df.sort_index(inplace=True)
        return df

    @staticmethod
    def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
        """Keep last entry for duplicated dates."""
        dup = df.index.duplicated(keep="last")
        if dup.any():
            logger.debug("Removing %d duplicate timestamps", dup.sum())
            df = df[~dup]
        return df

    def _fill_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reindex to a complete calendar range and forward-fill gaps ≤ max_gap.
        Longer gaps (halts, listing gaps) are left as NaN and dropped later.
        """
        full_range = pd.date_range(df.index.min(), df.index.max(), freq="B")
        df = df.reindex(full_range)
        df = df.fillna(method="ffill", limit=self.max_gap)
        return df

    @staticmethod
    def _drop_null_close(df: pd.DataFrame) -> pd.DataFrame:
        return df.dropna(subset=["close"])

    def _remove_outliers(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Replace close prices whose absolute z-score exceeds threshold with NaN,
        then forward-fill.
        """
        close = df["close"]
        log_ret = np.log(close / close.shift(1)).dropna()
        z = (log_ret - log_ret.mean()) / (log_ret.std() + 1e-10)
        outlier_dates = z[z.abs() > self.z_threshold].index
        if len(outlier_dates):
            logger.warning(
                "[%s] %d return outlier(s) detected (|z|>%.1f) – capping",
                ticker, len(outlier_dates), self.z_threshold,
            )
            df.loc[outlier_dates, "close"] = np.nan
            df["close"] = df["close"].fillna(method="ffill")
        return df

    @staticmethod
    def _validate_ohlcv(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """
        Fix OHLCV consistency issues:
        - high < low  → swap
        - open/high/low outside [low, high] range → clip
        """
        if "high" in df.columns and "low" in df.columns:
            bad_hl = df["high"] < df["low"]
            if bad_hl.any():
                logger.debug("[%s] Swapping %d inverted high/low rows", ticker, bad_hl.sum())
                df.loc[bad_hl, ["high", "low"]] = df.loc[bad_hl, ["low", "high"]].values

            for col in ["open", "close"]:
                if col in df.columns:
                    df[col] = df[col].clip(lower=df["low"], upper=df["high"])

        if "volume" in df.columns:
            df["volume"] = df["volume"].clip(lower=0)

        return df

    def _filter_min_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop rows where close is below minimum price threshold."""
        mask = df["close"] >= self.min_price
        removed = (~mask).sum()
        if removed:
            logger.debug("Removed %d rows with close < %.4f", removed, self.min_price)
        return df[mask]

    @staticmethod
    def _add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
        """Add commonly-used derived columns."""
        df = df.copy()
        df["return"] = df["close"].pct_change()
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))

        if all(c in df.columns for c in ["high", "low", "close"]):
            df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3
            df["hl_range"] = df["high"] - df["low"]
            df["hl_pct"] = df["hl_range"] / df["close"]

        return df

    # ──────────────────────────────────────────
    # Quality report
    # ──────────────────────────────────────────

    @staticmethod
    def quality_report(df: pd.DataFrame) -> dict:
        """Return a data quality summary for a DataFrame."""
        if df.empty:
            return {"status": "empty"}
        close = df["close"]
        ret = close.pct_change().dropna()
        return {
            "rows":              len(df),
            "start":             str(df.index.min().date()),
            "end":               str(df.index.max().date()),
            "null_count":        int(df.isnull().sum().sum()),
            "null_pct":          float(df.isnull().mean().mean()),
            "close_min":         float(close.min()),
            "close_max":         float(close.max()),
            "close_mean":        float(close.mean()),
            "return_max":        float(ret.max()),
            "return_min":        float(ret.min()),
            "return_std_daily":  float(ret.std()),
            "zero_volume_days":  int((df.get("volume", pd.Series()) == 0).sum()),
        }
