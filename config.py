"""
config.py - Global configuration for the Quant Backend
All settings are loaded from environment variables with sensible defaults.
"""
from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "raw"
CACHE_DIR = BASE_DIR / "data" / "cache"
REPORTS_DIR = BASE_DIR / "reports"

for _d in (DATA_DIR, CACHE_DIR, REPORTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────
# Settings model
# ──────────────────────────────────────────────
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────
    app_name: str = "Quant Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "changeme-secret-key-in-production"

    # ── Server ───────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False

    # ── Database ─────────────────────────────
    database_url: str = "postgresql+asyncpg://quant:quant@localhost:5432/quantdb"
    database_url_sync: str = "postgresql+psycopg2://quant:quant@localhost:5432/quantdb"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    # ── Redis ────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600          # 1 hour default
    cache_price_ttl: int = 86400           # 24 h for price data
    cache_stats_ttl: int = 7200            # 2 h for computed stats

    # ── Data ─────────────────────────────────
    data_dir: Path = DATA_DIR
    cache_dir: Path = CACHE_DIR
    reports_dir: Path = REPORTS_DIR
    data_format: str = "parquet"           # "parquet" | "csv"
    history_years: int = 20
    start_date: str = (date.today() - timedelta(days=365 * 20)).strftime("%Y-%m-%d")
    end_date: str = date.today().strftime("%Y-%m-%d")

    # ── yFinance ─────────────────────────────
    yfinance_chunk_size: int = 50          # tickers per batch request
    yfinance_max_retries: int = 3
    yfinance_retry_delay: float = 2.0

    # ── Backtesting ──────────────────────────
    default_initial_capital: float = 1_000_000.0
    default_commission_pct: float = 0.0015    # 0.15%
    default_slippage_pct: float = 0.0005      # 0.05%
    max_position_size_pct: float = 0.10       # max 10% per position
    default_risk_free_rate: float = 0.02      # 2% annual

    # ── ML ───────────────────────────────────
    ml_random_state: int = 42
    ml_cv_folds: int = 5
    ml_test_size: float = 0.2
    ml_feature_lookback: int = 60

    # ── Scheduler ────────────────────────────
    scheduler_timezone: str = "Asia/Bangkok"
    data_refresh_cron: str = "0 18 * * 1-5"   # weekdays 18:00

    # ── Logging ──────────────────────────────
    log_json: bool = True
    log_file: str = "logs/quant.log"


settings = Settings()


# ──────────────────────────────────────────────
# Stock Universes
# ──────────────────────────────────────────────

# SET50 Thailand – top 50 constituent-like symbols (approximation)
SET50_TICKERS: List[str] = [
    "PTT.BK", "PTTEP.BK", "PTTGC.BK", "IRPC.BK", "TOP.BK",
    "SCB.BK", "KBANK.BK", "BBL.BK", "KTB.BK", "BAY.BK",
    "AOT.BK", "THAI.BK", "BEM.BK", "BTS.BK", "BMCL.BK",
    "ADVANC.BK", "DTAC.BK", "TRUE.BK", "INTUCH.BK", "JAS.BK",
    "CPALL.BK", "MAKRO.BK", "BJC.BK", "BIGC.BK", "ROBINS.BK",
    "SCC.BK", "SCCC.BK", "TPIPL.BK", "TUF.BK", "CPF.BK",
    "MINT.BK", "ERW.BK", "CENTEL.BK", "DELTA.BK", "KCE.BK",
    "HANA.BK", "STEC.BK", "ITD.BK", "CPN.BK", "LH.BK",
    "PS.BK", "QH.BK", "AP.BK", "SPALI.BK", "SIRI.BK",
    "EGCO.BK", "RATCH.BK", "GULF.BK", "GPSC.BK", "BANPU.BK",
]

# US Large Cap (S&P 100 subset)
SP100_TICKERS: List[str] = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "UNH", "JNJ", "XOM", "JPM", "V", "PG", "MA", "HD",
    "CVX", "MRK", "ABBV", "PEP", "KO", "AVGO", "COST", "TMO",
    "WMT", "MCD", "ABT", "ACN", "BAC", "NEE", "LIN", "ORCL",
    "PFE", "TXN", "NKE", "QCOM", "DHR", "MDT", "RTX", "HON",
    "BMY", "UPS", "AMGN", "SBUX", "GE", "IBM", "CAT", "GS",
    "BLK", "AXP", "SPGI", "INTU", "ADI", "ISRG", "CVS", "GILD",
    "LMT", "DE", "MMM", "CI", "SYK", "ZTS", "MO", "DUK",
    "SO", "CL", "CB", "USB", "TJX", "PLD", "WFC", "MS",
    "AMT", "EQIX", "BDX", "ICE", "VRTX", "NOW", "REGN", "PANW",
    "MU", "LRCX", "KLAC", "SNPS", "CDNS", "MELI", "ABNB", "DDOG",
    "SPY", "QQQ", "IWM", "VTI", "GLD", "TLT", "HYG", "LQD",
    "EEM", "VEA",
]

# ETF benchmarks
BENCHMARK_TICKERS: List[str] = [
    "SPY",   # S&P 500
    "QQQ",   # Nasdaq-100
    "IWM",   # Russell 2000
    "GLD",   # Gold
    "TLT",   # 20Y Treasury
    "VTI",   # Total US Market
]

# Sector ETFs
SECTOR_ETFS: dict = {
    "Technology":       "XLK",
    "Healthcare":       "XLV",
    "Financials":       "XLF",
    "Energy":           "XLE",
    "Consumer Disc.":   "XLY",
    "Consumer Staples": "XLP",
    "Industrials":      "XLI",
    "Materials":        "XLB",
    "Utilities":        "XLU",
    "Real Estate":      "XLRE",
    "Communication":    "XLC",
}

# Default universe used when none is specified
DEFAULT_UNIVERSE: str = "sp100"
UNIVERSE_MAP: dict = {
    "set50":      SET50_TICKERS,
    "sp100":      SP100_TICKERS,
    "benchmark":  BENCHMARK_TICKERS,
}


# ──────────────────────────────────────────────
# Technical indicator defaults
# ──────────────────────────────────────────────
INDICATOR_DEFAULTS: dict = {
    "sma_fast":        20,
    "sma_slow":        50,
    "sma_trend":       200,
    "ema_fast":        12,
    "ema_slow":        26,
    "ema_signal":      9,
    "rsi_period":      14,
    "bb_period":       20,
    "bb_std":          2.0,
    "atr_period":      14,
    "adx_period":      14,
    "stoch_k":         14,
    "stoch_d":         3,
    "macd_fast":       12,
    "macd_slow":       26,
    "macd_signal":     9,
    "donchian_period": 20,
    "williams_period": 14,
    "cci_period":      20,
    "mfi_period":      14,
    "obv_ema":         21,
    "vwap_period":     14,
}

# Trading calendar info
TRADING_DAYS_PER_YEAR: int = 252
TRADING_MONTHS_PER_YEAR: int = 12
TRADING_WEEKS_PER_YEAR: int = 52
