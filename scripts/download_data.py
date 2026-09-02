#!/usr/bin/env python
"""scripts/download_data.py – CLI to download historical data."""
import sys
import typer
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SP100_TICKERS, SET50_TICKERS, UNIVERSE_MAP
from data.downloader import DataDownloader

app = typer.Typer(help="Download historical OHLCV data from Yahoo Finance.")


@app.command()
def download(
    universe: str = typer.Option("sp100", help="Universe: sp100|set50|all"),
    tickers:  str = typer.Option(None,    help="Comma-separated tickers (overrides universe)"),
    start:    str = typer.Option("2004-01-01"),
    end:      str = typer.Option(None),
    force:    bool= typer.Option(False,   help="Re-download even if data exists"),
    fmt:      str = typer.Option("parquet", help="Format: parquet|csv"),
):
    """Download 20-year OHLCV data for a universe or custom ticker list."""
    logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s %(message)s")

    if tickers:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
    else:
        ticker_list = UNIVERSE_MAP.get(universe.lower(), SP100_TICKERS)

    typer.echo(f"Downloading {len(ticker_list)} tickers ({start} → {end or 'today'}) ...")
    dl = DataDownloader(start_date=start, end_date=end or "", fmt=fmt)
    result = dl.download(ticker_list, force=force)
    typer.echo(f"✅  Downloaded {len(result)}/{len(ticker_list)} tickers.")


if __name__ == "__main__":
    app()
