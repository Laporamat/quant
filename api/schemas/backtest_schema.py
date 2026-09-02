"""api/schemas/backtest_schema.py – Pydantic models for backtest endpoints."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    strategy:         str                  = Field(..., description="Strategy name from STRATEGY_REGISTRY")
    tickers:          List[str]
    start_date:       str                  = "2004-01-01"
    end_date:         str                  = "2024-12-31"
    initial_capital:  float                = 1_000_000.0
    commission_pct:   float                = 0.0015
    slippage_pct:     float                = 0.0005
    max_position_pct: float                = 0.10
    position_sizing:  str                  = "equal"
    benchmark_ticker: str                  = "SPY"
    strategy_params:  Dict[str, Any]       = {}


class BacktestResponse(BaseModel):
    run_id:         str
    strategy:       str
    start_date:     str
    end_date:       str
    initial_capital:float
    performance:    Dict[str, Any]
    equity_curve:   Dict[str, float]       # date → equity
    n_trades:       int
    run_time_s:     float


class BacktestListItem(BaseModel):
    run_id:   str
    strategy: str
    created:  str
    sharpe:   Optional[float]
    cagr:     Optional[float]


class OptimizeRequest(BaseModel):
    strategy:    str
    tickers:     List[str]
    start_date:  str         = "2004-01-01"
    end_date:    str         = "2024-12-31"
    param_grid:  Dict[str, List[Any]]
    metric:      str         = "sharpe"
    maximize:    bool        = True
    n_jobs:      int         = -1


class OptimizeResponse(BaseModel):
    strategy:     str
    metric:       str
    best_params:  Dict[str, Any]
    best_value:   float
    all_results:  List[Dict[str, Any]]


class MonteCarloRequest(BaseModel):
    ticker:     str
    start_date: Optional[str] = None
    end_date:   Optional[str] = None
    n_sims:     int           = 1000
    horizon:    int           = 252
    method:     str           = "bootstrap"   # "bootstrap" | "parametric"


class MonteCarloResponse(BaseModel):
    ticker:       str
    n_sims:       int
    horizon_days: int
    stats:        Dict[str, float]
    percentile_paths: Dict[str, List[float]]   # {"p5": [...], "p50": [...], "p95": [...]}
