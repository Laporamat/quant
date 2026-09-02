"""
backtester/risk_manager.py
Position sizing (Kelly, fixed-fraction, vol-target) and risk controls.
"""
from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional

from backtester.order import Order, OrderSide, OrderType
from strategies.base_strategy import Signal, SignalType

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Converts strategy signals into sized orders and applies risk controls.

    Parameters
    ----------
    initial_capital     : portfolio starting value
    max_position_pct    : max single position as fraction of equity (default 0.10)
    max_portfolio_risk  : max total notional / equity (default 1.0 = no leverage)
    position_sizing     : "equal" | "vol_target" | "kelly" | "fixed_fraction"
    target_vol          : per-position annual vol target (for vol_target sizing)
    kelly_fraction      : fraction of Kelly criterion to use (default 0.25)
    max_drawdown_halt   : halt trading if drawdown exceeds this (default 0.25)
    stop_loss_pct       : automatic stop-loss per trade (default None)
    """

    def __init__(
        self,
        initial_capital:    float = 1_000_000.0,
        max_position_pct:   float = 0.10,
        max_portfolio_risk: float = 1.0,
        position_sizing:    str   = "equal",
        target_vol:         float = 0.15,
        kelly_fraction:     float = 0.25,
        max_drawdown_halt:  float = 0.25,
        stop_loss_pct:      Optional[float] = None,
    ) -> None:
        self.initial_capital    = initial_capital
        self.max_pos_pct        = max_position_pct
        self.max_portfolio_risk = max_portfolio_risk
        self.position_sizing    = position_sizing
        self.target_vol         = target_vol
        self.kelly_fraction     = kelly_fraction
        self.max_dd_halt        = max_drawdown_halt
        self.stop_loss_pct      = stop_loss_pct
        self._peak_equity       = initial_capital

    def size_orders(
        self,
        signals: List[Signal],
        portfolio_equity: float,
        positions: Dict,
        prices: Dict[str, float],
        returns_history: Optional[pd.DataFrame] = None,
    ) -> List[Order]:
        """
        Convert signals to sized Orders.

        Parameters
        ----------
        signals          : list of signals from strategy
        portfolio_equity : current total equity
        positions        : current open positions {ticker: Position}
        prices           : current prices {ticker: price}
        returns_history  : DataFrame of recent returns (for vol-target sizing)

        Returns
        -------
        List of Order objects
        """
        # ── Circuit breaker ──────────────────
        drawdown = (self.initial_capital - portfolio_equity) / self.initial_capital
        if drawdown > self.max_dd_halt:
            logger.warning(
                "Max drawdown halt triggered (%.1f%% > %.1f%%)",
                drawdown * 100, self.max_dd_halt * 100,
            )
            return []

        orders: List[Order] = []
        for sig in signals:
            order = self._signal_to_order(
                sig, portfolio_equity, positions, prices, returns_history
            )
            if order is not None:
                orders.append(order)
        return orders

    def _signal_to_order(
        self,
        sig: Signal,
        equity: float,
        positions: Dict,
        prices: Dict[str, float],
        returns_history: Optional[pd.DataFrame],
    ) -> Optional[Order]:
        price = prices.get(sig.ticker) or sig.price
        if price is None or price <= 0:
            return None

        # Exit signals → sell entire position
        if sig.signal in (SignalType.SELL, SignalType.COVER):
            pos = positions.get(sig.ticker)
            if pos is None:
                return None
            qty = abs(pos.qty)
            return Order(
                ticker=sig.ticker,
                side=OrderSide.SELL,
                qty=-qty,
                order_type=OrderType.MARKET,
                created_at=sig.date,
            )

        # Entry signals → compute position size
        dollar_size = self._compute_dollar_size(
            sig, equity, price, returns_history
        )
        if dollar_size <= 0:
            return None

        qty = dollar_size / price
        side = OrderSide.BUY if sig.signal in (SignalType.BUY,) else OrderSide.SELL

        stop = None
        if self.stop_loss_pct and sig.signal == SignalType.BUY:
            stop = price * (1 - self.stop_loss_pct)

        return Order(
            ticker=sig.ticker,
            side=side,
            qty=qty if side == OrderSide.BUY else -qty,
            order_type=OrderType.MARKET,
            created_at=sig.date,
            stop_price=stop,
            meta={"signal_strength": sig.strength},
        )

    def _compute_dollar_size(
        self,
        sig: Signal,
        equity: float,
        price: float,
        returns_history: Optional[pd.DataFrame],
    ) -> float:
        """Compute position size in dollars."""
        cap = equity * self.max_pos_pct

        if self.position_sizing == "equal":
            raw = equity * sig.strength
        elif self.position_sizing == "vol_target" and returns_history is not None:
            ticker = sig.ticker
            if ticker in returns_history.columns:
                ann_vol = float(returns_history[ticker].dropna().tail(63).std() * np.sqrt(252))
                raw = equity * (self.target_vol / ann_vol) if ann_vol > 0 else equity * 0.01
            else:
                raw = equity * sig.strength
        elif self.position_sizing == "kelly":
            # Simplified Kelly: use signal strength as win probability proxy
            win_p  = max(0.5 + sig.strength * 0.1, 0.51)
            win_r  = 0.02   # expected win size
            loss_r = 0.01   # expected loss size
            kelly  = win_p / loss_r - (1 - win_p) / win_r
            kelly  = max(0, kelly) * self.kelly_fraction
            raw    = equity * kelly
        else:  # fixed_fraction
            raw = equity * self.get_param_or_default("fixed_fraction", 0.02)

        return min(raw, cap)

    @staticmethod
    def get_param_or_default(param: str, default: float) -> float:
        return default

    # ──────────────────────────────────────────
    # Kelly criterion utility
    # ──────────────────────────────────────────
    @staticmethod
    def kelly_criterion(
        win_rate: float,
        avg_win: float,
        avg_loss: float,
    ) -> float:
        """
        Full Kelly fraction.
        f* = (win_rate * avg_win - (1-win_rate) * avg_loss) / avg_win
        """
        if avg_win == 0:
            return 0.0
        return (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

    def update_peak_equity(self, equity: float) -> None:
        self._peak_equity = max(self._peak_equity, equity)

    @property
    def current_drawdown(self) -> float:
        return (self._peak_equity - self.initial_capital) / self.initial_capital
