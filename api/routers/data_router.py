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


# ── Quick-start background download ──────────────────────────────────────────

_QUICKSTART_TICKERS = [
    # Benchmarks
    "SPY", "QQQ", "IWM", "GLD", "TLT", "VTI",
    # Sector ETFs
    "XLK", "XLV", "XLF", "XLE", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE", "XLC",
    # Top 20 SP100
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "JNJ",
    "PG", "HD", "XOM", "CVX", "MRK", "ABBV", "KO", "PEP", "AVGO", "COST",
]

_download_status: dict = {"running": False, "done": 0, "total": 0, "errors": []}


def _run_quickstart(dl: DataDownloader) -> None:
    global _download_status
    _download_status["running"] = True
    _download_status["total"]   = len(_QUICKSTART_TICKERS)
    _download_status["done"]    = 0
    _download_status["errors"]  = []
    try:
        result = dl.download(_QUICKSTART_TICKERS)
        _download_status["done"] = len(result)
        missing = [t for t in _QUICKSTART_TICKERS if t not in result]
        _download_status["errors"] = missing
    finally:
        _download_status["running"] = False


@router.post("/quickstart", tags=["data"])
async def quickstart_download(
    background_tasks: BackgroundTasks,
    dl: DataDownloader = Depends(get_downloader),
):
    """Trigger a background download of benchmarks + sector ETFs + top 20 SP100."""
    if _download_status["running"]:
        return {"status": "already_running", **_download_status}
    background_tasks.add_task(_run_quickstart, dl)
    return {"status": "started", "tickers": len(_QUICKSTART_TICKERS)}


@router.get("/quickstart/status", tags=["data"])
async def quickstart_status():
    """Poll the status of a running quickstart download."""
    return {
        "running": _download_status["running"],
        "done":    _download_status["done"],
        "total":   _download_status["total"],
        "errors":  _download_status["errors"],
        "pct":     round(_download_status["done"] / max(_download_status["total"], 1) * 100),
    }
