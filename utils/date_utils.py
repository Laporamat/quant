"""
utils/date_utils.py
Trading calendar and business day helpers.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import List, Optional


TRADING_DAYS_PER_YEAR = 252


def is_business_day(dt: date) -> bool:
    """Return True if *dt* is Mon–Fri."""
    return dt.weekday() < 5


def next_business_day(dt: date) -> date:
    """Return next business day after *dt*."""
    d = dt + timedelta(days=1)
    while not is_business_day(d):
        d += timedelta(days=1)
    return d


def prev_business_day(dt: date) -> date:
    """Return previous business day before *dt*."""
    d = dt - timedelta(days=1)
    while not is_business_day(d):
        d -= timedelta(days=1)
    return d


def business_days_between(start: date, end: date) -> int:
    """Count business days between two dates (inclusive start, exclusive end)."""
    return int(np.busday_count(start, end))


def date_range_business(start: str, end: str) -> pd.DatetimeIndex:
    """Return a DatetimeIndex of business days between start and end."""
    return pd.bdate_range(start, end)


def years_ago(n: int) -> str:
    """Return ISO date string n years before today."""
    return (date.today() - timedelta(days=365 * n)).strftime("%Y-%m-%d")


def parse_date(s: Optional[str]) -> Optional[pd.Timestamp]:
    if s is None:
        return None
    return pd.Timestamp(s)


def trading_year_fraction(start: str, end: str) -> float:
    """Fraction of trading year between two dates."""
    days = business_days_between(
        pd.Timestamp(start).date(),
        pd.Timestamp(end).date()
    )
    return days / TRADING_DAYS_PER_YEAR


def monthly_rebalance_dates(start: str, end: str) -> List[pd.Timestamp]:
    """Return month-end business dates between start and end."""
    return pd.bdate_range(start, end, freq="BM").tolist()


def quarterly_rebalance_dates(start: str, end: str) -> List[pd.Timestamp]:
    return pd.bdate_range(start, end, freq="BQ").tolist()


def year_month_to_date(year: int, month: int) -> pd.Timestamp:
    return pd.Timestamp(f"{year}-{month:02d}-01")


def split_train_test(
    index: pd.DatetimeIndex,
    test_pct: float = 0.2,
) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    """Split a DatetimeIndex into train / test by percentage."""
    split = int(len(index) * (1 - test_pct))
    return index[:split], index[split:]
