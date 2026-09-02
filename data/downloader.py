"""
data/downloader.py
Download 20-year OHLCV + Adjusted data from Yahoo Finance via yfinance.
Supports batch downloads, retries, rate-limiting, and persistent caching.
"""
from __future__ import annotations

import time
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import settings, DATA_DIR

logger = logging.getLogger(__name__)


class DataDownloader:
    """
    Downloads historical OHLCV data for a list of tickers via yfinance.

    Features
    --------
    - 20-year window (configurable via settings)
    - Chunk-based parallel batch download
    - Auto-retry with exponential back-off
    - Saves to parquet or CSV on disk
    - Incremental updates (only fetch missing dates)
    """

    def __init__(
        self,
        data_dir: Path = DATA_DIR,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fmt: str = "parquet",
    ) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.start_date = start_date or settings.start_date
        self.end_date = end_date or settings.end_date
        self.fmt = fmt  # "parquet" | "csv"
        self.chunk_size = settings.yfinance_chunk_size

    # ──────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────

    def download(self, tickers: List[str], force: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Download data for *tickers* and persist to disk.

        Parameters
        ----------
        tickers : list of ticker symbols
        force   : re-download even if data exists on disk

        Returns
        -------
        dict mapping ticker -> DataFrame(OHLCV + Adj Close)
        """
        results: Dict[str, pd.DataFrame] = {}
        tickers_to_fetch: List[str] = []

        for ticker in tickers:
            path = self._ticker_path(ticker)
            if not force and path.exists():
                df = self._read(path)
                if df is not None and not df.empty:
                    results[ticker] = df
                    logger.debug("Loaded %s from cache (%d rows)", ticker, len(df))
                    continue
            tickers_to_fetch.append(ticker)

        if tickers_to_fetch:
            fetched = self._batch_download(tickers_to_fetch)
            for ticker, df in fetched.items():
                if df is not None and not df.empty:
                    self._write(df, self._ticker_path(ticker))
                    results[ticker] = df

        logger.info(
            "Download complete: %d/%d tickers retrieved",
            len(results),
            len(tickers),
        )
        return results

    def update(self, tickers: List[str]) -> Dict[str, pd.DataFrame]:
        """Incremental update: only download data newer than what is on disk."""
        results: Dict[str, pd.DataFrame] = {}
        for ticker in tickers:
            path = self._ticker_path(ticker)
            if path.exists():
                existing = self._read(path)
                if existing is not None and not existing.empty:
                    last_date = existing.index.max()
                    new_start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
                    if new_start >= self.end_date:
                        results[ticker] = existing
                        continue
                    fresh = self._fetch_single(ticker, new_start, self.end_date)
                    if fresh is not None and not fresh.empty:
                        combined = pd.concat([existing, fresh])
                        combined = combined[~combined.index.duplicated(keep="last")]
                        combined.sort_index(inplace=True)
                        self._write(combined, path)
                        results[ticker] = combined
                        logger.info("Updated %s: +%d rows", ticker, len(fresh))
                    else:
                        results[ticker] = existing
                    continue
            # No existing data – full download
            fetched = self._batch_download([ticker])
            if ticker in fetched and fetched[ticker] is not None:
                self._write(fetched[ticker], path)
                results[ticker] = fetched[ticker]
        return results

    def download_single(self, ticker: str, force: bool = False) -> Optional[pd.DataFrame]:
        """Convenience wrapper for a single ticker."""
        result = self.download([ticker], force=force)
        return result.get(ticker)

    def get_info(self, ticker: str) -> dict:
        """Return yfinance info dict for a ticker."""
        try:
            return yf.Ticker(ticker).info
        except Exception as exc:
            logger.warning("Could not fetch info for %s: %s", ticker, exc)
            return {}

    def get_dividends(self, ticker: str) -> pd.Series:
        """Return historical dividends for a ticker."""
        try:
            return yf.Ticker(ticker).dividends
        except Exception as exc:
            logger.warning("Dividends fetch failed for %s: %s", ticker, exc)
            return pd.Series(dtype=float)

    def get_splits(self, ticker: str) -> pd.Series:
        """Return historical stock splits for a ticker."""
        try:
            return yf.Ticker(ticker).splits
        except Exception as exc:
            logger.warning("Splits fetch failed for %s: %s", ticker, exc)
            return pd.Series(dtype=float)

    # ──────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────

    def _batch_download(self, tickers: List[str]) -> Dict[str, pd.DataFrame]:
        """Download tickers in chunks to respect rate limits."""
        results: Dict[str, pd.DataFrame] = {}
        chunks = [
            tickers[i : i + self.chunk_size]
            for i in range(0, len(tickers), self.chunk_size)
        ]
        for idx, chunk in enumerate(chunks):
            logger.info(
                "Downloading chunk %d/%d (%d tickers): %s…",
                idx + 1, len(chunks), len(chunk), chunk[:3],
            )
            chunk_data = self._fetch_batch(chunk)
            results.update(chunk_data)
            if idx < len(chunks) - 1:
                time.sleep(settings.yfinance_retry_delay)
        return results

    @retry(
        stop=stop_after_attempt(settings.yfinance_max_retries),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        reraise=False,
    )
    def _fetch_batch(self, tickers: List[str]) -> Dict[str, pd.DataFrame]:
        """Fetch a batch of tickers using yfinance.download."""
        raw = yf.download(
            tickers=tickers,
            start=self.start_date,
            end=self.end_date,
            auto_adjust=True,          # prices adjusted for splits & dividends
            progress=False,
            threads=True,
            group_by="ticker",
        )
        result: Dict[str, pd.DataFrame] = {}
        if len(tickers) == 1:
            ticker = tickers[0]
            if not raw.empty:
                df = raw.copy()
                df.columns = [c.lower() for c in df.columns]
                df.index.name = "date"
                df = self._validate_ohlcv(df)
                result[ticker] = df
        else:
            for ticker in tickers:
                try:
                    df = raw[ticker].copy()
                    if df.empty:
                        logger.warning("No data for %s", ticker)
                        continue
                    df.columns = [c.lower() for c in df.columns]
                    df.index.name = "date"
                    df = self._validate_ohlcv(df)
                    result[ticker] = df
                except KeyError:
                    logger.warning("Ticker %s not found in batch response", ticker)
        return result

    @retry(
        stop=stop_after_attempt(settings.yfinance_max_retries),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        reraise=False,
    )
    def _fetch_single(
        self,
        ticker: str,
        start: str,
        end: str,
    ) -> Optional[pd.DataFrame]:
        """Fetch a single ticker for a date range."""
        raw = yf.download(
            tickers=ticker,
            start=start,
            end=end,
            auto_adjust=True,
            progress=False,
        )
        if raw.empty:
            return None
        raw.columns = [c.lower() for c in raw.columns]
        raw.index.name = "date"
        return self._validate_ohlcv(raw)

    @staticmethod
    def _validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
        """Ensure standard OHLCV columns and remove bad rows."""
        required = {"open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing OHLCV columns: {missing}")
        df = df[list(required)].copy()
        df.sort_index(inplace=True)
        df.dropna(subset=["close"], inplace=True)
        # Remove zero/negative prices
        df = df[(df["close"] > 0) & (df["open"] > 0)]
        return df

    def _ticker_path(self, ticker: str) -> Path:
        """Sanitise ticker name for use as filename."""
        safe = ticker.replace("/", "_").replace(".", "_").replace("-", "_")
        ext = "parquet" if self.fmt == "parquet" else "csv"
        return self.data_dir / f"{safe}.{ext}"

    def _write(self, df: pd.DataFrame, path: Path) -> None:
        """Persist DataFrame to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        if self.fmt == "parquet":
            df.to_parquet(path, engine="pyarrow")
        else:
            df.to_csv(path)
        logger.debug("Saved %s (%d rows)", path.name, len(df))

    def _read(self, path: Path) -> Optional[pd.DataFrame]:
        """Read DataFrame from disk."""
        try:
            if path.suffix == ".parquet":
                return pd.read_parquet(path, engine="pyarrow")
            else:
                return pd.read_csv(path, index_col=0, parse_dates=True)
        except Exception as exc:
            logger.warning("Failed to read %s: %s", path, exc)
            return None

    # ──────────────────────────────────────────
    # Listing helpers
    # ──────────────────────────────────────────

    def list_downloaded(self) -> List[str]:
        """Return list of tickers already downloaded to disk."""
        ext = "parquet" if self.fmt == "parquet" else "csv"
        return [p.stem.replace("_", ".") for p in self.data_dir.glob(f"*.{ext}")]

    def get_date_range(self, ticker: str) -> Optional[tuple]:
        """Return (start_date, end_date) for downloaded ticker data."""
        path = self._ticker_path(ticker)
        if not path.exists():
            return None
        df = self._read(path)
        if df is None or df.empty:
            return None
        return df.index.min().date(), df.index.max().date()
