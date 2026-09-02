"""utils/validators.py – Input validation helpers."""
from __future__ import annotations
import re
from datetime import date, datetime
from typing import List


def validate_ticker(ticker: str) -> str:
    """Normalise and validate a ticker symbol."""
    t = ticker.upper().strip()
    if not re.match(r'^[A-Z0-9.\-]{1,12}$', t):
        raise ValueError(f"Invalid ticker: '{ticker}'")
    return t


def validate_date(s: str) -> str:
    """Validate ISO date string YYYY-MM-DD."""
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date: '{s}' (expected YYYY-MM-DD)")
    return s


def validate_date_range(start: str, end: str) -> None:
    validate_date(start)
    validate_date(end)
    if start > end:
        raise ValueError(f"start_date ({start}) must be <= end_date ({end})")


def validate_tickers(tickers: List[str]) -> List[str]:
    return [validate_ticker(t) for t in tickers]


def validate_positive(value: float, name: str = "value") -> float:
    if value <= 0:
        raise ValueError(f"{name} must be positive (got {value})")
    return value


def validate_fraction(value: float, name: str = "value") -> float:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be in [0, 1] (got {value})")
    return value
