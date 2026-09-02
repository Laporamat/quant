"""api/routers/stats_router.py – Stats computation endpoints."""
from __future__ import annotations
from typing import List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query

from api.schemas.stats_schema import (
    DescriptiveStatsResponse, ReturnSummaryResponse, RiskMetricsResponse,
    CorrelationRequest, CorrelationResponse, RegimeResponse, SeasonalityResponse,
)
from api.dependencies import get_loader
from data.loader import DataLoader
from stats.descriptive import DescriptiveStats
from stats.returns import ReturnStats
from stats.risk_metrics import RiskMetrics
from stats.drawdown import DrawdownAnalysis
from stats.correlation import CorrelationAnalysis
from stats.regime_detection import RegimeDetection
from stats.seasonality import SeasonalityAnalysis
from stats.distribution import DistributionAnalysis
from stats.bubble_detection import BubbleDetection

router = APIRouter(prefix="/stats", tags=["stats"])


def _load_returns(ticker: str, start: Optional[str], end: Optional[str],
                  loader: DataLoader) -> pd.Series:
    df = loader.load(ticker.upper(), start=start, end=end)
    if df.empty:
        raise HTTPException(404, f"No data for {ticker}")
    return df["close"].pct_change().dropna()


@router.get("/descriptive/{ticker}", response_model=DescriptiveStatsResponse)
async def descriptive_stats(
    ticker:     str,
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    rets = _load_returns(ticker, start_date, end_date, loader)
    s    = DescriptiveStats.summary(rets)
    hurst = DescriptiveStats.hurst_exponent(rets)
    return DescriptiveStatsResponse(
        ticker=ticker.upper(),
        count=s["count"], mean=s["mean"], median=s["median"],
        std=s["std"], min=s["min"], max=s["max"],
        skewness=s["skewness"], kurtosis=s["kurtosis"],
        jb_pvalue=s["jb_pvalue"], is_normal=s["is_normal_jb"],
        autocorr_1=s.get("autocorr_1"), hurst=hurst,
    )


@router.get("/returns/{ticker}", response_model=ReturnSummaryResponse)
async def return_stats(
    ticker:     str,
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    df = loader.load(ticker.upper(), start=start_date, end=end_date)
    if df.empty:
        raise HTTPException(404, f"No data for {ticker}")
    prices  = df["close"]
    summary = ReturnStats.return_summary(prices)
    return ReturnSummaryResponse(ticker=ticker.upper(), **summary)


@router.get("/risk/{ticker}", response_model=RiskMetricsResponse)
async def risk_metrics(
    ticker:     str,
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    rets = _load_returns(ticker, start_date, end_date, loader)
    equity = (1 + rets).cumprod()
    da = DistributionAnalysis
    return RiskMetricsResponse(
        ticker=ticker.upper(),
        sharpe=RiskMetrics.sharpe(rets),
        sortino=RiskMetrics.sortino(rets),
        calmar=RiskMetrics.calmar(rets),
        omega=RiskMetrics.omega(rets),
        max_drawdown=DrawdownAnalysis.max_drawdown(equity),
        ann_volatility=float(rets.std() * (252 ** 0.5)),
        var_95=da.var_historical(rets, 0.95),
        cvar_95=da.cvar_historical(rets, 0.95),
        tail_ratio=RiskMetrics.tail_ratio(rets),
        ulcer_index=RiskMetrics.ulcer_index(rets),
    )


@router.get("/drawdown/{ticker}")
async def drawdown_analysis(
    ticker:     str,
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    df = loader.load(ticker.upper(), start=start_date, end=end_date)
    if df.empty:
        raise HTTPException(404, f"No data for {ticker}")
    equity = df["close"] / df["close"].iloc[0]
    return {
        "ticker":  ticker.upper(),
        "summary": DrawdownAnalysis.summary(equity),
        "top_10":  DrawdownAnalysis.top_drawdowns(equity, n=10).to_dict("records"),
    }


@router.post("/correlation", response_model=CorrelationResponse)
async def correlation_matrix(
    req:    CorrelationRequest,
    loader: DataLoader = Depends(get_loader),
):
    panel = loader.load_returns_panel(req.tickers, start=req.start_date, end=req.end_date)
    if panel.empty:
        raise HTTPException(404, "No data for requested tickers")
    corr = CorrelationAnalysis.pairwise(panel, method=req.method)
    return CorrelationResponse(
        tickers=list(corr.columns),
        matrix={col: corr[col].round(4).to_dict() for col in corr.columns},
    )


@router.get("/regime/{ticker}", response_model=RegimeResponse)
async def regime_detection(
    ticker:     str,
    n_states:   int           = Query(3, ge=2, le=4),
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    rets = _load_returns(ticker, start_date, end_date, loader)
    regime_df = RegimeDetection.hmm_regimes(rets, n_states=n_states)
    if regime_df.empty:
        regime_df = pd.DataFrame({"regime": RegimeDetection.ma_regime(
            loader.load(ticker.upper())["close"]
        )})
    stats = RegimeDetection.regime_stats(rets, regime_df.get("regime", regime_df.iloc[:, 0]))
    return RegimeResponse(
        ticker=ticker.upper(),
        regimes=regime_df.tail(252).reset_index().rename(columns={"date": "date"}).to_dict("records"),
        stats=stats.to_dict("records"),
    )


@router.get("/seasonality/{ticker}", response_model=SeasonalityResponse)
async def seasonality(
    ticker:     str,
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    rets = _load_returns(ticker, start_date, end_date, loader)
    sa   = SeasonalityAnalysis
    return SeasonalityResponse(
        ticker=ticker.upper(),
        day_of_week=sa.day_of_week_effect(rets).to_dict("records"),
        month=sa.month_effect(rets).to_dict("records"),
        january_effect=sa.january_effect(rets),
        monday_effect=sa.monday_effect(rets),
    )


@router.get("/distribution/{ticker}")
async def distribution_analysis(
    ticker:     str,
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    rets = _load_returns(ticker, start_date, end_date, loader)
    return {
        "ticker":  ticker.upper(),
        "tail_risk": DistributionAnalysis.tail_risk_report(rets),
        "best_fit":  DistributionAnalysis.fit_best_distribution(rets),
        "t_fit":     DistributionAnalysis.fit_t_distribution(rets),
    }


@router.get("/bubble/{ticker}")
async def bubble_analysis(
    ticker:     str,
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    """
    Detect speculative bubbles using:
    - Log-price acceleration (super-exponential growth)
    - Rolling cumulative return z-score
    - LPPL-inspired growth test
    - Volatility regime spike
    Returns composite bubble score (0-100), individual signals,
    historical crash episodes found in the price series, and
    time-series data for charting.
    """
    df = loader.load(ticker.upper(), start=start_date, end=end_date)
    if df.empty:
        raise HTTPException(404, f"No data for {ticker}")

    prices = df["close"]
    try:
        result = BubbleDetection.analyse(prices, ticker=ticker)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Bubble analysis failed: {e}")

    return {
        "ticker":              result.ticker,
        "start_date":          result.start_date,
        "end_date":            result.end_date,
        "bubble_score":        result.bubble_score,
        "is_bubble":           result.is_bubble,
        "pe_ratio_current":    result.pe_ratio_current,
        "pe_ratio_hist_avg":   result.pe_ratio_hist_avg,
        "pe_zscore":           result.pe_zscore,
        "price_acceleration":  result.price_acceleration,
        "log_return_zscore":   result.log_return_zscore,
        "crash_probability":   result.crash_probability,
        "historical_bubbles":  [
            {
                "peak_date":    b.peak_date,
                "trough_date":  b.trough_date,
                "peak_price":   b.peak_price,
                "trough_price": b.trough_price,
                "drawdown":     b.drawdown,
                "duration_days":b.duration_days,
                "name":         b.name,
            }
            for b in result.historical_bubbles
        ],
        "price_series":  result.price_series,
        "zscore_series": result.zscore_series,
        "signals":       [
            {
                "name":        s.name,
                "triggered":   s.triggered,
                "value":       s.value,
                "threshold":   s.threshold,
                "description": s.description,
            }
            for s in result.signals
        ],
    }


@router.post("/bubble/scan")
async def bubble_scan(
    tickers:    list[str],
    start_date: Optional[str] = Query(None),
    end_date:   Optional[str] = Query(None),
    loader:     DataLoader    = Depends(get_loader),
):
    """Scan a list of tickers and rank them by bubble score."""
    import pandas as pd
    panel_dict = {}
    for t in tickers[:50]:  # cap at 50
        df = loader.load(t.upper(), start=start_date, end=end_date)
        if not df.empty:
            panel_dict[t.upper()] = df["close"]
    if not panel_dict:
        raise HTTPException(404, "No data found for any requested ticker")
    panel = pd.DataFrame(panel_dict)
    summary = BubbleDetection.scan_universe(panel)
    return summary.to_dict("records")
