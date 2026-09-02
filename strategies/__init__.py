"""Strategies package."""
from strategies.base_strategy import BaseStrategy, Signal, SignalType
from strategies.buy_and_hold import BuyAndHoldStrategy
from strategies.sma_crossover import SMACrossoverStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.breakout import BreakoutStrategy
from strategies.pairs_trading import PairsTradingStrategy
from strategies.multi_factor import MultiFactorStrategy
from strategies.volatility_targeting import VolatilityTargetingStrategy
from strategies.trend_following import TrendFollowingStrategy
from strategies.ml_strategy import MLStrategy

STRATEGY_REGISTRY = {
    "buy_and_hold":        BuyAndHoldStrategy,
    "sma_crossover":       SMACrossoverStrategy,
    "momentum":            MomentumStrategy,
    "mean_reversion":      MeanReversionStrategy,
    "breakout":            BreakoutStrategy,
    "pairs_trading":       PairsTradingStrategy,
    "multi_factor":        MultiFactorStrategy,
    "volatility_targeting":VolatilityTargetingStrategy,
    "trend_following":     TrendFollowingStrategy,
    "ml":                  MLStrategy,
}

__all__ = list(STRATEGY_REGISTRY.keys()) + ["BaseStrategy", "Signal", "SignalType", "STRATEGY_REGISTRY"]
