"""tests/conftest.py – Shared pytest fixtures."""
from __future__ import annotations
import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_prices() -> pd.Series:
    """250 days of synthetic price data starting at 100."""
    rng = np.random.default_rng(42)
    n   = 500
    ret = rng.normal(0.0005, 0.015, n)
    prices = pd.Series(
        100 * np.cumprod(1 + ret),
        index=pd.bdate_range("2020-01-01", periods=n),
        name="close",
    )
    return prices


@pytest.fixture
def sample_ohlcv(sample_prices) -> pd.DataFrame:
    """OHLCV DataFrame built from sample prices."""
    close  = sample_prices
    spread = close * 0.005
    rng    = np.random.default_rng(1)
    return pd.DataFrame({
        "open":   close * (1 + rng.uniform(-0.003, 0.003, len(close))),
        "high":   close + spread,
        "low":    close - spread,
        "close":  close,
        "volume": np.abs(rng.normal(1_000_000, 200_000, len(close))),
    }, index=close.index)


@pytest.fixture
def sample_returns(sample_prices) -> pd.Series:
    return sample_prices.pct_change().dropna()


@pytest.fixture
def sample_equity(sample_returns) -> pd.Series:
    return (1 + sample_returns).cumprod() * 100_000


@pytest.fixture
def two_tickers_data(sample_ohlcv) -> dict:
    """Two tickers for pairs / multi-asset tests."""
    rng = np.random.default_rng(99)
    df2 = sample_ohlcv.copy()
    df2["close"] = sample_ohlcv["close"] * (1 + rng.normal(0, 0.01, len(sample_ohlcv)))
    return {"AAPL": sample_ohlcv, "MSFT": df2}
