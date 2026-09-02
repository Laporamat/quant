"""api/routers/data_router.py – Data download, status, universe endpoints."""
from __future__ import annotations
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks

from api.schemas.data_schema import (
    DownloadRequest, DownloadResponse, TickerInfo,
    PriceResponse, OHLCVBar, UniverseResponse, SectorBreakdownResponse,
)
from api.dependencies import get_loader, get_downloader, get_universe_manager
from data.loader import DataLoader
from data.downloader import DataDownloader
from data.universe import UniverseManager

router = APIRouter(prefix="/data", tags=["data"])


@router.post("/download", response_model=DownloadResponse)
async def download_data(
    req: DownloadRequest,
    dl: DataDownloader = Depends(get_downloader),
):
    """Download / refresh historical OHLCV data for a list of tickers."""
    try:
        result = dl.download(req.tickers, force=req.force)
        success = list(result.keys())
        failed  = [t for t in req.tickers if t not in success]
        return DownloadResponse(
            success=success, failed=failed,
            total=len(success),
            message=f"Downloaded {len(success)}/{len(req.tickers)} tickers",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available", response_model=List[TickerInfo])
async def list_available(
    loader: DataLoader = Depends(get_loader),
):
    """List all tickers with data on disk."""
    tickers = loader.available_tickers()
    return [TickerInfo(**loader.describe(t)) for t in tickers]


@router.get("/prices/{ticker}", response_model=PriceResponse)
async def get_prices(
    ticker:     str,
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    freq:       Optional[str] = Query(None, description="Resample freq: W, M, Q"),
    loader:     DataLoader    = Depends(get_loader),
):
    """Return OHLCV data for a ticker."""
    df = loader.load(ticker.upper(), start=start_date, end=end_date, freq=freq)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data for {ticker}")

    bars = [
        OHLCVBar(
            date=str(idx.date()),
            open=float(row.get("open", 0)),
            high=float(row.get("high", 0)),
            low=float(row.get("low", 0)),
            close=float(row["close"]),
            volume=float(row.get("volume", 0)),
        )
        for idx, row in df.iterrows()
    ]
    return PriceResponse(
        ticker=ticker.upper(), data=bars, rows=len(bars),
        start=str(df.index.min().date()), end=str(df.index.max().date()),
    )


@router.get("/status/{ticker}")
async def ticker_status(
    ticker: str,
    loader: DataLoader = Depends(get_loader),
):
    """Return metadata (date range, row count) for a ticker."""
    info = loader.describe(ticker.upper())
    if info.get("rows", 0) == 0:
        raise HTTPException(status_code=404, detail=f"No data for {ticker}")
    return info


@router.get("/universes", response_model=List[str])
async def list_universes(um: UniverseManager = Depends(get_universe_manager)):
    return um.list_universes()


@router.get("/universe/{name}", response_model=UniverseResponse)
async def get_universe(
    name: str,
    um: UniverseManager = Depends(get_universe_manager),
):
    try:
        tickers = um.get_universe(name)
        return UniverseResponse(name=name, tickers=tickers, count=len(tickers))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/universe/{name}/sectors", response_model=SectorBreakdownResponse)
async def sector_breakdown(
    name: str,
    um: UniverseManager = Depends(get_universe_manager),
):
    try:
        sectors = um.sector_breakdown(name)
        return SectorBreakdownResponse(universe=name, sectors=sectors)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
