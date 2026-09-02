"""api/routers/indicators_router.py – Compute technical indicators for a symbol."""
from __future__ import annotations
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_loader
from data.loader import DataLoader
from indicators.moving_averages import MovingAverages as MA
from indicators.momentum import Momentum
from indicators.volatility import Volatility
from indicators.trend import Trend
from indicators.volume import Volume
from indicators.oscillators import Oscillators
from indicators.custom import CustomIndicators

router = APIRouter(prefix="/indicators", tags=["indicators"])


def _get_ohlcv(ticker: str, start: Optional[str], end: Optional[str],
               loader: DataLoader) -> pd.DataFrame:
    df = loader.load(ticker.upper(), start=start, end=end)
    if df.empty:
        raise HTTPException(404, f"No data for {ticker}")
    return df


def _to_records(df: pd.DataFrame, tail: int = 500) -> list:
    out = df.tail(tail).copy()
    out.index = out.index.astype(str)
    return out.reset_index().rename(columns={"index": "date"}).to_dict("records")


# ── Moving Averages ──────────────────────────────────────────────────────────

@router.get("/ma/{ticker}")
async def moving_averages(
    ticker:     str,
    periods:    str           = Query("20,50,200", description="Comma-separated periods"),
    ma_type:    str           = Query("sma", description="sma|ema|wma|hma|tema"),
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    df = _get_ohlcv(ticker, start_date, end_date, loader)
    close = df["close"]
    result = {"date": [str(d.date()) for d in close.index]}
    fn_map = {"sma": MA.sma, "ema": MA.ema, "wma": MA.wma,
              "hma": MA.hma, "tema": MA.tema, "dema": MA.dema}
    fn = fn_map.get(ma_type, MA.sma)
    for p in [int(x) for x in periods.split(",")]:
        result[f"{ma_type}_{p}"] = fn(close, p).round(4).tolist()
    return result


# ── Momentum ─────────────────────────────────────────────────────────────────

@router.get("/rsi/{ticker}")
async def rsi(
    ticker:     str,
    period:     int           = Query(14),
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    df    = _get_ohlcv(ticker, start_date, end_date, loader)
    rsi_s = Momentum.rsi(df["close"], period)
    return {"date": [str(d.date()) for d in rsi_s.index],
            "rsi":  rsi_s.round(2).tolist()}


@router.get("/macd/{ticker}")
async def macd(
    ticker:     str,
    fast:       int           = Query(12),
    slow:       int           = Query(26),
    signal:     int           = Query(9),
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    df      = _get_ohlcv(ticker, start_date, end_date, loader)
    macd_df = Momentum.macd(df["close"], fast, slow, signal)
    return _to_records(macd_df)


# ── Volatility ───────────────────────────────────────────────────────────────

@router.get("/bollinger/{ticker}")
async def bollinger_bands(
    ticker:     str,
    period:     int           = Query(20),
    std_dev:    float         = Query(2.0),
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    df = _get_ohlcv(ticker, start_date, end_date, loader)
    bb = Volatility.bollinger_bands(df["close"], period, std_dev)
    return _to_records(bb)


@router.get("/atr/{ticker}")
async def atr(
    ticker:     str,
    period:     int           = Query(14),
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    df  = _get_ohlcv(ticker, start_date, end_date, loader)
    atr_s = Volatility.atr(df["high"], df["low"], df["close"], period)
    return {"date": [str(d.date()) for d in atr_s.index], "atr": atr_s.round(4).tolist()}


# ── Trend ────────────────────────────────────────────────────────────────────

@router.get("/adx/{ticker}")
async def adx(
    ticker:     str,
    period:     int           = Query(14),
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    df = _get_ohlcv(ticker, start_date, end_date, loader)
    return _to_records(Trend.adx(df["high"], df["low"], df["close"], period))


@router.get("/ichimoku/{ticker}")
async def ichimoku(
    ticker:     str,
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    df = _get_ohlcv(ticker, start_date, end_date, loader)
    return _to_records(Trend.ichimoku(df["high"], df["low"], df["close"]))


# ── Volume ───────────────────────────────────────────────────────────────────

@router.get("/volume/{ticker}")
async def volume_indicators(
    ticker:     str,
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    df = _get_ohlcv(ticker, start_date, end_date, loader)
    return _to_records(Volume.all_volume(df["high"], df["low"], df["close"], df["volume"]))


# ── All indicators ───────────────────────────────────────────────────────────

@router.get("/all/{ticker}")
async def all_indicators(
    ticker:     str,
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    tail:       int           = Query(100),
    loader:     DataLoader    = Depends(get_loader),
):
    df = _get_ohlcv(ticker, start_date, end_date, loader)
    frames = [
        MA.all_mas(df["close"]),
        Momentum.all_momentum(df["high"], df["low"], df["close"], df["volume"]),
        Volatility.all_volatility(df["open"], df["high"], df["low"], df["close"]),
        Trend.all_trend(df["high"], df["low"], df["close"]),
        Volume.all_volume(df["high"], df["low"], df["close"], df["volume"]),
        Oscillators.all_oscillators(df["open"], df["high"], df["low"], df["close"]),
    ]
    import pandas as pd
    combined = pd.concat(frames, axis=1)
    return _to_records(combined, tail=tail)
