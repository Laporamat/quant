"""
data/universe.py
Stock universe definitions and sector/country mappings.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

import pandas as pd

from config import (
    SET50_TICKERS,
    SP100_TICKERS,
    BENCHMARK_TICKERS,
    SECTOR_ETFS,
    UNIVERSE_MAP,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Sector mappings  (ticker → sector)
# ──────────────────────────────────────────────

SP100_SECTOR_MAP: Dict[str, str] = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Communication",
    "AMZN": "Consumer Disc.", "NVDA": "Technology", "META": "Communication",
    "TSLA": "Consumer Disc.", "BRK-B": "Financials", "UNH": "Healthcare",
    "JNJ": "Healthcare", "XOM": "Energy", "JPM": "Financials",
    "V": "Financials", "PG": "Consumer Staples", "MA": "Financials",
    "HD": "Consumer Disc.", "CVX": "Energy", "MRK": "Healthcare",
    "ABBV": "Healthcare", "PEP": "Consumer Staples", "KO": "Consumer Staples",
    "AVGO": "Technology", "COST": "Consumer Staples", "TMO": "Healthcare",
    "WMT": "Consumer Staples", "MCD": "Consumer Disc.", "ABT": "Healthcare",
    "ACN": "Technology", "BAC": "Financials", "NEE": "Utilities",
    "LIN": "Materials", "ORCL": "Technology", "PFE": "Healthcare",
    "TXN": "Technology", "NKE": "Consumer Disc.", "QCOM": "Technology",
    "DHR": "Healthcare", "MDT": "Healthcare", "RTX": "Industrials",
    "HON": "Industrials", "BMY": "Healthcare", "UPS": "Industrials",
    "AMGN": "Healthcare", "SBUX": "Consumer Disc.", "GE": "Industrials",
    "IBM": "Technology", "CAT": "Industrials", "GS": "Financials",
    "BLK": "Financials", "AXP": "Financials",
    "SPY": "ETF", "QQQ": "ETF", "IWM": "ETF",
    "VTI": "ETF", "GLD": "Commodities", "TLT": "Fixed Income",
    "HYG": "Fixed Income", "LQD": "Fixed Income",
    "EEM": "ETF", "VEA": "ETF",
}

SET50_SECTOR_MAP: Dict[str, str] = {
    "PTT.BK":    "Energy", "PTTEP.BK":  "Energy",
    "PTTGC.BK":  "Energy", "IRPC.BK":   "Energy", "TOP.BK": "Energy",
    "SCB.BK":    "Financials", "KBANK.BK": "Financials",
    "BBL.BK":    "Financials", "KTB.BK":   "Financials", "BAY.BK": "Financials",
    "AOT.BK":    "Industrials", "THAI.BK":  "Industrials",
    "BEM.BK":    "Industrials", "BTS.BK":   "Industrials",
    "ADVANC.BK": "Communication", "DTAC.BK": "Communication",
    "TRUE.BK":   "Communication", "INTUCH.BK": "Communication",
    "CPALL.BK":  "Consumer Staples", "MAKRO.BK": "Consumer Staples",
    "BJC.BK":    "Consumer Disc.", "BIGC.BK":  "Consumer Disc.",
    "SCC.BK":    "Materials", "SCCC.BK":   "Materials",
    "TUF.BK":    "Consumer Staples", "CPF.BK":   "Consumer Staples",
    "MINT.BK":   "Consumer Disc.", "ERW.BK":   "Consumer Disc.",
    "CENTEL.BK": "Consumer Disc.", "DELTA.BK": "Technology",
    "KCE.BK":    "Technology", "HANA.BK":   "Technology",
    "CPN.BK":    "Real Estate", "LH.BK":    "Real Estate",
    "PS.BK":     "Real Estate", "QH.BK":    "Real Estate",
    "AP.BK":     "Real Estate", "SPALI.BK": "Real Estate",
    "SIRI.BK":   "Real Estate",
    "EGCO.BK":   "Utilities", "RATCH.BK":  "Utilities",
    "GULF.BK":   "Utilities", "GPSC.BK":   "Utilities",
    "BANPU.BK":  "Energy",
}

FULL_SECTOR_MAP: Dict[str, str] = {**SP100_SECTOR_MAP, **SET50_SECTOR_MAP}

# Country mapping
COUNTRY_MAP: Dict[str, str] = {
    **{t: "US" for t in SP100_TICKERS},
    **{t: "TH" for t in SET50_TICKERS},
}


class UniverseManager:
    """
    Manages stock universes, sector filters, and metadata.

    Usage
    -----
    um = UniverseManager()
    tickers = um.get_universe("sp100")
    tech = um.filter_by_sector("sp100", "Technology")
    """

    BUILTIN_UNIVERSES: Dict[str, List[str]] = {
        "set50":     SET50_TICKERS,
        "sp100":     SP100_TICKERS,
        "benchmark": BENCHMARK_TICKERS,
        "all":       list(set(SET50_TICKERS + SP100_TICKERS)),
    }

    def __init__(self) -> None:
        self._custom: Dict[str, List[str]] = {}

    # ──────────────────────────────────────────
    # Universe access
    # ──────────────────────────────────────────

    def get_universe(self, name: str) -> List[str]:
        """Return tickers for a named universe."""
        name = name.lower()
        if name in self._custom:
            return self._custom[name]
        if name in self.BUILTIN_UNIVERSES:
            return self.BUILTIN_UNIVERSES[name]
        raise ValueError(
            f"Unknown universe '{name}'. "
            f"Available: {list(self.BUILTIN_UNIVERSES.keys()) + list(self._custom.keys())}"
        )

    def list_universes(self) -> List[str]:
        return list(self.BUILTIN_UNIVERSES.keys()) + list(self._custom.keys())

    def register_universe(self, name: str, tickers: List[str]) -> None:
        """Register a custom universe."""
        self._custom[name.lower()] = tickers
        logger.info("Registered universe '%s' with %d tickers", name, len(tickers))

    # ──────────────────────────────────────────
    # Sector / country filters
    # ──────────────────────────────────────────

    def get_sector(self, ticker: str) -> str:
        """Return sector for *ticker* (or 'Unknown')."""
        return FULL_SECTOR_MAP.get(ticker, "Unknown")

    def get_country(self, ticker: str) -> str:
        """Return country code for *ticker* (or 'Unknown')."""
        return COUNTRY_MAP.get(ticker, "Unknown")

    def filter_by_sector(
        self,
        universe: str,
        sector: str,
    ) -> List[str]:
        """Return tickers in *universe* belonging to *sector*."""
        tickers = self.get_universe(universe)
        return [t for t in tickers if FULL_SECTOR_MAP.get(t) == sector]

    def filter_by_country(self, universe: str, country: str) -> List[str]:
        """Return tickers in *universe* from *country* ('US' | 'TH')."""
        tickers = self.get_universe(universe)
        return [t for t in tickers if COUNTRY_MAP.get(t) == country]

    def sector_breakdown(self, universe: str) -> Dict[str, List[str]]:
        """Return dict of {sector: [tickers]}."""
        tickers = self.get_universe(universe)
        breakdown: Dict[str, List[str]] = {}
        for t in tickers:
            sector = FULL_SECTOR_MAP.get(t, "Unknown")
            breakdown.setdefault(sector, []).append(t)
        return dict(sorted(breakdown.items()))

    # ──────────────────────────────────────────
    # DataFrame helpers
    # ──────────────────────────────────────────

    def universe_to_df(self, universe: str) -> pd.DataFrame:
        """Return a DataFrame with ticker metadata."""
        tickers = self.get_universe(universe)
        rows = [
            {
                "ticker":  t,
                "sector":  FULL_SECTOR_MAP.get(t, "Unknown"),
                "country": COUNTRY_MAP.get(t, "Unknown"),
            }
            for t in tickers
        ]
        return pd.DataFrame(rows)

    @staticmethod
    def get_sector_etfs() -> Dict[str, str]:
        return SECTOR_ETFS
