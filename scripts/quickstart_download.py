#!/usr/bin/env python
"""
scripts/quickstart_download.py
--------------------------------
ดาวน์โหลดข้อมูลขั้นต่ำเพื่อให้ Dashboard ใช้งานได้ทันที

Step 1: Benchmark ETFs (6 ตัว)           ~เร็วมาก
Step 2: Sector ETFs (11 ตัว)             ~1-2 นาที
Step 3: Top 20 SP100 stocks              ~2-3 นาที
Step 4: (Optional) SP100 ทั้งหมด 90 ตัว  ~10-15 นาที

รัน: python scripts/quickstart_download.py
"""
from __future__ import annotations

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("quickstart")

from data.downloader import DataDownloader

# ── Ticker lists ──────────────────────────────────────────────────────────────

BENCHMARKS = ["SPY", "QQQ", "IWM", "GLD", "TLT", "VTI"]

SECTOR_ETFS = ["XLK", "XLV", "XLF", "XLE", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC"]

TOP20_SP100 = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",
    "META", "TSLA", "JPM", "V", "JNJ",
    "PG", "HD", "XOM", "CVX", "MRK",
    "ABBV", "KO", "PEP", "AVGO", "COST",
]

# Full SP100 — run with --full flag
SP100_EXTRA = [
    "BRK-B", "UNH", "MA", "TMO", "WMT", "MCD", "ABT", "ACN",
    "BAC", "NEE", "LIN", "ORCL", "PFE", "TXN", "NKE", "QCOM",
    "DHR", "MDT", "RTX", "HON", "BMY", "UPS", "AMGN", "SBUX",
    "GE", "IBM", "CAT", "GS", "BLK", "AXP", "SPGI", "INTU",
    "ADI", "ISRG", "CVS", "GILD", "LMT", "DE", "MMM", "CI",
    "SYK", "ZTS", "MO", "DUK", "SO", "CL", "CB", "USB",
    "TJX", "PLD", "WFC", "MS", "AMT", "EQIX", "BDX", "ICE",
    "VRTX", "NOW", "REGN", "PANW", "MU", "LRCX", "KLAC",
    "SNPS", "CDNS", "MELI", "ABNB", "DDOG",
]


def download_group(name: str, tickers: list[str], dl: DataDownloader) -> int:
    log.info("=" * 55)
    log.info("Downloading: %s (%d tickers)", name, len(tickers))
    log.info("=" * 55)
    result = dl.download(tickers)
    ok  = len(result)
    log.info("Done: %d/%d tickers saved ✓", ok, len(tickers))
    return ok


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--full",  action="store_true", help="Download full SP100 (~15 min)")
    parser.add_argument("--force", action="store_true", help="Re-download even if data exists")
    parser.add_argument("--start", default="2004-01-01", help="Start date (default 2004-01-01)")
    args = parser.parse_args()

    dl = DataDownloader(start_date=args.start, fmt="parquet")

    total = 0
    total += download_group("Benchmark ETFs",  BENCHMARKS,   dl)
    total += download_group("Sector ETFs",     SECTOR_ETFS,  dl)
    total += download_group("Top 20 SP100",    TOP20_SP100,  dl)

    if args.full:
        total += download_group("SP100 Extended", SP100_EXTRA, dl)

    log.info("")
    log.info("★  Quickstart download complete!  %d tickers saved to data/raw/", total)
    log.info("")
    log.info("Next steps:")
    log.info("  1. Make sure FastAPI is running:  python main.py")
    log.info("  2. Open the frontend:             http://localhost:5173")
    log.info("  3. Download full SP100 later:     python scripts/quickstart_download.py --full")


if __name__ == "__main__":
    main()
