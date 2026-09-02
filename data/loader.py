"""
data/loader.py
Load, validate, and serve OHLCV DataFrames with in-memory and disk caching.
"""
from __future__ import annotations

import hashlib
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from config import settings, DATA_DIR, CACHE_DIR

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Central data-access layer.  Reads from disk (parquet/csv), caches in memory,
    and exposes sliced / resampled views of the data.

    Usage
    -----
    loader = DataLoader()
    df = loader.load("AAPL")
    panel = loader.load_panel(["AAPL","MSFT"], "2020-01-01", "2024-12-31")
    """

    def __init__(
        self,
        data_dir: Path = DATA_DIR,
        cache_dir: Path = CACHE_DIR,
        fmt: str = "parquet",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.fmt = fmt
        self._mem_cache: Dict[str, pd.DataFrame] = {}

    # ──────────────────────────────────────────
    # Single-ticker access
    # ──────────────────────────────────────────

    def load(
        self,
        ticker: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        columns: Optional[List[str]] = None,
        freq: Optional[str] = None,   # e.g. "W", "M", "Q"
    ) -> pd.DataFrame:
        """
        Load OHLCV data for *ticker*, optionally sliced and resampled.

        Parameters
        ----------
        ticker  : symbol, e.g. "AAPL"
        start   : "YYYY-MM-DD" start filter (inclusive)
        end     : "YYYY-MM-DD" end filter (inclusive)
        columns : subset of columns to return
        freq    : pandas resample frequency string

        Returns
        -------
        DataFrame with DatetimeIndex
        """
        df = self._get_or_load(ticker)
        if df.empty:
            logger.warning("No data available for %s", ticker)
            return df

        # Date slice
        if start:
            df = df.loc[start:]
        if end:
            df = df.loc[:end]

        # Resample
        if freq:
            df = self._resample(df, freq)

        # Column filter
        if columns:
            available = [c for c in columns if c in df.columns]
            df = df[available]

        return df.copy()

    def load_close(
        self,
        ticker: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> pd.Series:
        """Return close price series for *ticker*."""
        df = self.load(ticker, start=start, end=end, columns=["close"])
        return df["close"] if "close" in df.columns else pd.Series(dtype=float)

    def load_returns(
        self,
        ticker: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        log_returns: bool = False,
    ) -> pd.Series:
        """Return daily simple or log returns for *ticker*."""
        close = self.load_close(ticker, start=start, end=end)
        if close.empty:
            return pd.Series(dtype=float)
        if log_returns:
            import numpy as np
            return (np.log(close / close.shift(1))).dropna()
        return close.pct_change().dropna()

    # ──────────────────────────────────────────
    # Multi-ticker (panel) access
    # ──────────────────────────────────────────

    def load_panel(
        self,
        tickers: List[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        column: str = "close",
        freq: Optional[str] = None,
        min_history_days: int = 252,
    ) -> pd.DataFrame:
        """
        Build a wide panel of *column* values, one ticker per column.
        Tickers with insufficient history are dropped and logged.
        """
        frames: Dict[str, pd.Series] = {}
        for ticker in tickers:
            df = self.load(ticker, start=start, end=end, freq=freq)
            if df.empty or column not in df.columns:
                logger.debug("Skipping %s – no %s column", ticker, column)
                continue
            series = df[column]
            if len(series) < min_history_days:
                logger.debug(
                    "Skipping %s – only %d days (< %d)",
                    ticker, len(series), min_history_days,
                )
                continue
            frames[ticker] = series

        if not frames:
            return pd.DataFrame()

        panel = pd.DataFrame(frames)
        panel.sort_index(inplace=True)
        return panel

    def load_returns_panel(
        self,
        tickers: List[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        log_returns: bool = False,
    ) -> pd.DataFrame:
        """Return a panel of daily returns, one ticker per column."""
        panel = self.load_panel(tickers, start=start, end=end, column="close")
        if panel.empty:
            return panel
        if log_returns:
            import numpy as np
            return (np.log(panel / panel.shift(1))).dropna(how="all")
        return panel.pct_change().dropna(how="all")

    # ──────────────────────────────────────────
    # Metadata helpers
    # ──────────────────────────────────────────

    def available_tickers(self) -> List[str]:
        """List tickers that have data files on disk."""
        ext = "parquet" if self.fmt == "parquet" else "csv"
        return sorted(
            p.stem.replace("_", ".", 1) for p in self.data_dir.glob(f"*.{ext}")
        )

    def date_range(self, ticker: str) -> Optional[Tuple[pd.Timestamp, pd.Timestamp]]:
        """Return (first_date, last_date) for a ticker."""
        df = self._get_or_load(ticker)
        if df.empty:
            return None
        return df.index.min(), df.index.max()

    def num_rows(self, ticker: str) -> int:
        """Return row count for a ticker."""
        df = self._get_or_load(ticker)
        return len(df)

    def describe(self, ticker: str) -> dict:
        """Return summary dict for a ticker."""
        df = self._get_or_load(ticker)
        if df.empty:
            return {"ticker": ticker, "rows": 0}
        dr = self.date_range(ticker)
        return {
            "ticker":     ticker,
            "rows":       len(df),
            "start":      str(dr[0].date()),
            "end":        str(dr[1].date()),
            "columns":    list(df.columns),
            "close_last": float(df["close"].iloc[-1]) if "close" in df.columns else None,
        }

    # ──────────────────────────────────────────
    # Cache management
    # ──────────────────────────────────────────

    def clear_memory_cache(self) -> None:
        self._mem_cache.clear()
        logger.debug("In-memory cache cleared")

    def preload(self, tickers: List[str]) -> None:
        """Eagerly load tickers into memory cache."""
        for t in tickers:
            self._get_or_load(t)
        logger.info("Preloaded %d tickers into memory cache", len(tickers))

    # ──────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────

    def _get_or_load(self, ticker: str) -> pd.DataFrame:
        if ticker in self._mem_cache:
            return self._mem_cache[ticker]
        df = self._read_from_disk(ticker)
        if df is not None and not df.empty:
            self._mem_cache[ticker] = df
            return df
        return pd.DataFrame()

    def _read_from_disk(self, ticker: str) -> Optional[pd.DataFrame]:
        """Try parquet first, then csv."""
        safe = ticker.replace("/", "_").replace(".", "_").replace("-", "_")
        for ext in ("parquet", "csv"):
            path = self.data_dir / f"{safe}.{ext}"
            if path.exists():
                try:
                    if ext == "parquet":
                        df = pd.read_parquet(path, engine="pyarrow")
                    else:
                        df = pd.read_csv(path, index_col=0, parse_dates=True)
                    df.index = pd.to_datetime(df.index, utc=False)
                    df.index.name = "date"
                    df.columns = [c.lower() for c in df.columns]
                    logger.debug("Read %s from %s (%d rows)", ticker, path.name, len(df))
                    return df
                except Exception as exc:
                    logger.error("Error reading %s: %s", path, exc)
        logger.debug("No disk data found for %s", ticker)
        return None

    @staticmethod
    def _resample(df: pd.DataFrame, freq: str) -> pd.DataFrame:
        """Resample OHLCV to a lower frequency."""
        agg = {
            "open":   "first",
            "high":   "max",
            "low":    "min",
            "close":  "last",
            "volume": "sum",
        }
        cols = {k: v for k, v in agg.items() if k in df.columns}
        return df.resample(freq).agg(cols).dropna(subset=["close"])

    @staticmethod
    def _cache_key(*args) -> str:
        raw = "|".join(str(a) for a in args)
        return hashlib.md5(raw.encode()).hexdigest()
