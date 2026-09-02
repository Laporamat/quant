"""
jobs/data_refresh.py
Scheduled job to refresh daily OHLCV data for configured universes.
"""
from __future__ import annotations
import logging
from datetime import date

from config import settings, SP100_TICKERS, SET50_TICKERS
from data.downloader import DataDownloader
from data.cleaner import DataCleaner

logger = logging.getLogger(__name__)


def refresh_universe(universe: str = "sp100") -> dict:
    """Refresh price data for a given universe. Returns summary."""
    dl      = DataDownloader()
    cleaner = DataCleaner()

    tickers_map = {"sp100": SP100_TICKERS, "set50": SET50_TICKERS}
    tickers = tickers_map.get(universe.lower(), SP100_TICKERS)

    logger.info("Starting data refresh for universe '%s' (%d tickers)", universe, len(tickers))
    results = dl.update(tickers)

    updated, failed = [], []
    for ticker, df in results.items():
        if df is not None and not df.empty:
            updated.append(ticker)
        else:
            failed.append(ticker)

    summary = {
        "date":     str(date.today()),
        "universe": universe,
        "updated":  len(updated),
        "failed":   len(failed),
        "failed_tickers": failed,
    }
    logger.info(
        "Data refresh complete: %d updated, %d failed",
        len(updated), len(failed),
    )
    return summary


def refresh_all() -> dict:
    """Refresh SP100 + SET50."""
    r1 = refresh_universe("sp100")
    r2 = refresh_universe("set50")
    return {"sp100": r1, "set50": r2}


if __name__ == "__main__":
    import sys
    logging.basicConfig(level="INFO")
    universe = sys.argv[1] if len(sys.argv) > 1 else "sp100"
    result = refresh_universe(universe)
    print(result)
