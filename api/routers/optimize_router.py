"""api/routers/optimize_router.py – Strategy parameter optimisation endpoints."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Depends
from api.schemas.backtest_schema import OptimizeRequest, OptimizeResponse
from api.dependencies import get_loader
from data.loader import DataLoader
from backtester.engine import BacktestConfig
from backtester.optimizer import StrategyOptimizer
from strategies import STRATEGY_REGISTRY

router = APIRouter(prefix="/optimize", tags=["optimize"])


@router.post("/grid", response_model=OptimizeResponse)
async def grid_search(
    req:    OptimizeRequest,
    loader: DataLoader = Depends(get_loader),
):
    """Grid search over strategy parameters. Returns best params and all results."""
    if req.strategy not in STRATEGY_REGISTRY:
        raise HTTPException(400, f"Unknown strategy '{req.strategy}'")

    data = {}
    for t in req.tickers:
        df = loader.load(t, start=req.start_date, end=req.end_date)
        if not df.empty:
            data[t] = df
    if not data:
        raise HTTPException(404, "No data found for requested tickers")

    config = BacktestConfig(
        start_date=req.start_date,
        end_date=req.end_date,
    )

    optimizer = StrategyOptimizer(
        strategy_class=STRATEGY_REGISTRY[req.strategy],
        data=data,
        config=config,
        n_jobs=req.n_jobs,
    )
    try:
        result = optimizer.grid_search(
            param_grid=req.param_grid,
            metric=req.metric,
            maximize=req.maximize,
        )
    except Exception as e:
        raise HTTPException(500, f"Optimisation failed: {e}")

    return OptimizeResponse(
        strategy=req.strategy,
        metric=req.metric,
        best_params=result.best_params,
        best_value=result.best_metric,
        all_results=result.all_results.head(50).to_dict("records"),
    )


@router.post("/walk-forward")
async def walk_forward(
    req:         OptimizeRequest,
    train_years: int = 3,
    test_years:  int = 1,
    loader:      DataLoader = Depends(get_loader),
):
    """Walk-forward optimisation. Returns per-fold OOS performance."""
    if req.strategy not in STRATEGY_REGISTRY:
        raise HTTPException(400, f"Unknown strategy '{req.strategy}'")

    data = {
        t: loader.load(t, start=req.start_date, end=req.end_date)
        for t in req.tickers
    }
    data = {t: df for t, df in data.items() if not df.empty}

    config = BacktestConfig(start_date=req.start_date, end_date=req.end_date)
    optimizer = StrategyOptimizer(
        STRATEGY_REGISTRY[req.strategy], data, config, req.n_jobs
    )
    try:
        df = optimizer.walk_forward(
            param_grid=req.param_grid,
            metric=req.metric,
            train_years=train_years,
            test_years=test_years,
        )
    except Exception as e:
        raise HTTPException(500, f"Walk-forward failed: {e}")

    return df.to_dict("records")
