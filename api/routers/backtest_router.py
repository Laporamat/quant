"""api/routers/backtest_router.py – Run, list, and retrieve backtest results."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from api.schemas.backtest_schema import (
    BacktestRequest, BacktestResponse, BacktestListItem,
    MonteCarloRequest, MonteCarloResponse,
)
from api.dependencies import get_loader
from data.loader import DataLoader
from backtester.engine import BacktestEngine, BacktestConfig
from backtester.report import BacktestReport
from backtester.monte_carlo import MonteCarlo
from strategies import STRATEGY_REGISTRY

router = APIRouter(prefix="/backtest", tags=["backtest"])

# In-memory store (replace with DB in production)
_backtest_store: Dict[str, dict] = {}


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    req:    BacktestRequest,
    loader: DataLoader = Depends(get_loader),
):
    """Run a backtest and return results immediately."""
    if req.strategy not in STRATEGY_REGISTRY:
        raise HTTPException(400, f"Unknown strategy '{req.strategy}'")

    # Load data
    params = {**req.strategy_params, "tickers": req.tickers}
    data   = {}
    for t in req.tickers:
        df = loader.load(t, start=req.start_date, end=req.end_date)
        if not df.empty:
            data[t] = df
    if not data:
        raise HTTPException(404, "No price data found for requested tickers")

    # Also load benchmark
    bench_df = loader.load(req.benchmark_ticker, start=req.start_date, end=req.end_date)
    if not bench_df.empty:
        data[req.benchmark_ticker] = bench_df

    config = BacktestConfig(
        start_date=req.start_date,
        end_date=req.end_date,
        initial_capital=req.initial_capital,
        commission_pct=req.commission_pct,
        slippage_pct=req.slippage_pct,
        max_position_pct=req.max_position_pct,
        position_sizing=req.position_sizing,
        benchmark_ticker=req.benchmark_ticker,
    )

    strategy = STRATEGY_REGISTRY[req.strategy](params=params)
    engine   = BacktestEngine(strategy, data, config)

    try:
        result = engine.run()
    except Exception as e:
        raise HTTPException(500, f"Backtest failed: {e}")

    run_id = str(uuid.uuid4())[:8]
    _backtest_store[run_id] = {
        "result":  result,
        "created": datetime.utcnow().isoformat(),
        "request": req.model_dump(),
    }

    # Equity curve (sampled – last 1000 bars for response size)
    eq = result.equity_curve.tail(1000)
    eq_dict = {str(k.date()): round(v, 2) for k, v in eq.items()}

    return BacktestResponse(
        run_id=run_id,
        strategy=req.strategy,
        start_date=req.start_date,
        end_date=req.end_date,
        initial_capital=req.initial_capital,
        performance=result.performance,
        equity_curve=eq_dict,
        n_trades=len(result.trade_log),
        run_time_s=result.run_time_s,
    )


@router.get("/list", response_model=List[BacktestListItem])
async def list_backtests():
    """List all stored backtest runs."""
    items = []
    for run_id, entry in _backtest_store.items():
        perf = entry["result"].performance
        items.append(BacktestListItem(
            run_id=run_id,
            strategy=entry["result"].strategy_name,
            created=entry["created"],
            sharpe=perf.get("sharpe"),
            cagr=perf.get("cagr"),
        ))
    return sorted(items, key=lambda x: x.created, reverse=True)


@router.get("/{run_id}")
async def get_backtest(run_id: str):
    """Retrieve a stored backtest result by ID."""
    entry = _backtest_store.get(run_id)
    if not entry:
        raise HTTPException(404, f"Backtest {run_id} not found")
    result = entry["result"]
    # Sample equity curve (last 1000 bars) — same as /run response
    eq = result.equity_curve.tail(1000)
    eq_dict = {str(k.date()): round(v, 2) for k, v in eq.items()}
    return {
        "run_id":       run_id,
        "strategy":     result.strategy_name,
        "performance":  result.performance,
        "equity_curve": eq_dict,
        "trade_log":    result.trade_log.tail(100).to_dict("records"),
        "created":      entry["created"],
    }


@router.get("/{run_id}/report")
async def get_report(run_id: str):
    """Generate and return HTML report for a backtest run."""
    entry = _backtest_store.get(run_id)
    if not entry:
        raise HTTPException(404, f"Backtest {run_id} not found")
    report = BacktestReport(entry["result"])
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=report.to_html())


@router.post("/monte-carlo", response_model=MonteCarloResponse)
async def monte_carlo(
    req:    MonteCarloRequest,
    loader: DataLoader = Depends(get_loader),
):
    """Run Monte Carlo simulation on historical returns."""
    rets = loader.load_returns(req.ticker, start=req.start_date, end=req.end_date)
    if rets.empty:
        raise HTTPException(404, f"No data for {req.ticker}")

    if req.method == "bootstrap":
        paths = MonteCarlo.bootstrap_equity(rets, n_sims=req.n_sims, n_days=req.horizon)
    else:
        paths = MonteCarlo.parametric_equity(rets, n_sims=req.n_sims, n_days=req.horizon)

    stats = MonteCarlo.path_statistics(paths)
    pcts  = {
        "p5":  paths.quantile(0.05, axis=1).round(4).tolist(),
        "p25": paths.quantile(0.25, axis=1).round(4).tolist(),
        "p50": paths.quantile(0.50, axis=1).round(4).tolist(),
        "p75": paths.quantile(0.75, axis=1).round(4).tolist(),
        "p95": paths.quantile(0.95, axis=1).round(4).tolist(),
    }
    return MonteCarloResponse(
        ticker=req.ticker.upper(),
        n_sims=req.n_sims,
        horizon_days=req.horizon,
        stats={k: round(v, 6) for k, v in stats.items() if isinstance(v, float)},
        percentile_paths=pcts,
    )
