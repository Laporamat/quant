"""api/routers/strategy_router.py – Strategy listing and configuration."""
from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException

from strategies import STRATEGY_REGISTRY

router = APIRouter(prefix="/strategies", tags=["strategies"])

# Strategy metadata catalogue
STRATEGY_META: Dict[str, Dict[str, Any]] = {
    "buy_and_hold": {
        "description": "Long equal-weight positions held forever. Benchmark strategy.",
        "params": {"tickers": "list", "weight": "float (optional)"},
        "suitable_for": ["benchmark", "long_only"],
    },
    "sma_crossover": {
        "description": "Golden/death-cross SMA or EMA trend following.",
        "params": {"fast": "int (default 50)", "slow": "int (default 200)",
                   "ma_type": "sma|ema"},
        "suitable_for": ["trend", "long_only"],
    },
    "momentum": {
        "description": "Cross-sectional or time-series price momentum with monthly rebalancing.",
        "params": {"lookback": "int (days, default 252)", "skip": "int (default 21)",
                   "top_k": "int (default 10)", "mode": "cross_sectional|time_series|combined"},
        "suitable_for": ["momentum", "long_only"],
    },
    "mean_reversion": {
        "description": "RSI/Bollinger Band mean-reversion with configurable hold period.",
        "params": {"mode": "rsi|bollinger|combined", "rsi_oversold": "int (default 30)",
                   "rsi_overbought": "int (default 70)", "hold_days": "int (default 10)"},
        "suitable_for": ["mean_reversion", "long_short"],
    },
    "breakout": {
        "description": "Donchian Channel breakout with ATR trailing stop.",
        "params": {"donchian_period": "int (default 20)", "atr_period": "int (default 14)",
                   "atr_stop_mult": "float (default 2.0)"},
        "suitable_for": ["breakout", "long_only"],
    },
    "pairs_trading": {
        "description": "Statistical arbitrage pairs trading on spread z-score.",
        "params": {"asset1": "str", "asset2": "str", "entry_z": "float (default 2.0)",
                   "exit_z": "float (default 0.5)", "lookback": "int (default 63)"},
        "suitable_for": ["stat_arb", "market_neutral"],
    },
    "multi_factor": {
        "description": "Multi-factor ranking: momentum + low-vol + trend filter.",
        "params": {"top_k": "int (default 10)", "w_mom": "float (default 0.4)",
                   "w_vol": "float (default 0.3)", "w_trend": "float (default 0.3)"},
        "suitable_for": ["factor", "long_only"],
    },
    "volatility_targeting": {
        "description": "Inverse-volatility weighting scaled to target portfolio vol.",
        "params": {"target_vol": "float (default 0.10)", "vol_lookback": "int (default 63)"},
        "suitable_for": ["risk_parity", "long_only"],
    },
    "trend_following": {
        "description": "Antonacci dual-momentum with 200-day trend filter.",
        "params": {"lookback": "int (default 252)", "safe_asset": "str (default TLT)"},
        "suitable_for": ["trend", "long_only"],
    },
    "ml": {
        "description": "ML-based signal generation (Random Forest / XGBoost / LightGBM).",
        "params": {"model_type": "rf|xgb|lgbm", "lookahead": "int (default 5)",
                   "top_k": "int (default 5)", "retrain_freq": "int (default 63)"},
        "suitable_for": ["ml", "long_only"],
    },
}


@router.get("/", response_model=List[Dict])
async def list_strategies():
    """List all available strategies with metadata."""
    return [
        {"name": name, **meta}
        for name, meta in STRATEGY_META.items()
        if name in STRATEGY_REGISTRY
    ]


@router.get("/{name}")
async def get_strategy(name: str):
    """Get details for a specific strategy."""
    if name not in STRATEGY_REGISTRY:
        raise HTTPException(404, f"Strategy '{name}' not found")
    return {"name": name, **STRATEGY_META.get(name, {})}
