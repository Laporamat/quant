"""api/schemas/stats_schema.py – Pydantic models for stats endpoints."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StatsRequest(BaseModel):
    ticker:     str
    start_date: Optional[str] = None
    end_date:   Optional[str] = None


class DescriptiveStatsResponse(BaseModel):
    ticker:     str
    count:      int
    mean:       float
    median:     float
    std:        float
    min:        float
    max:        float
    skewness:   float
    kurtosis:   float
    jb_pvalue:  float
    is_normal:  bool
    autocorr_1: Optional[float]
    hurst:      Optional[float]


class ReturnSummaryResponse(BaseModel):
    ticker:            str
    total_return:      float
    cagr:              float
    avg_daily_return:  float
    avg_monthly_return:float
    best_day:          float
    worst_day:         float
    pct_positive_days: float


class RiskMetricsResponse(BaseModel):
    ticker:        str
    sharpe:        float
    sortino:       float
    calmar:        float
    omega:         float
    max_drawdown:  float
    ann_volatility:float
    var_95:        float
    cvar_95:       float
    tail_ratio:    float
    ulcer_index:   float


class CorrelationRequest(BaseModel):
    tickers:    List[str]
    start_date: Optional[str] = None
    end_date:   Optional[str] = None
    method:     str = "pearson"


class CorrelationResponse(BaseModel):
    tickers: List[str]
    matrix:  Dict[str, Dict[str, float]]


class RegimeResponse(BaseModel):
    ticker:  str
    regimes: List[Dict[str, Any]]
    stats:   List[Dict[str, Any]]


class SeasonalityResponse(BaseModel):
    ticker:          str
    day_of_week:     List[Dict]
    month:           List[Dict]
    january_effect:  Dict
    monday_effect:   Dict
