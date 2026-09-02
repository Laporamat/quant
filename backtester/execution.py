"""
backtester/execution.py
Execution model: slippage, commission, order fill simulation.
"""
from __future__ import annotations

import logging
from typing import Optional
import numpy as np
import pandas as pd

from backtester.order import Order, OrderType, OrderSide, OrderStatus, Fill

logger = logging.getLogger(__name__)


class ExecutionModel:
    """
    Simulates realistic order execution with:
    - Fixed or percentage commission
    - Fixed, percentage, or volume-based slippage
    - Market impact model (optional)
    - Next-open execution (avoids lookahead bias)

    Parameters
    ----------
    commission_pct  : commission as fraction of trade value (default 0.0015)
    commission_fixed: fixed cost per trade in $ (default 0.0)
    slippage_pct    : slippage as fraction of price (default 0.0005)
    slippage_model  : "fixed" | "percentage" | "sqrt" (market impact)
    execute_on      : "open" (next bar open) | "close" (current bar close)
    """

    def __init__(
        self,
        commission_pct:   float = 0.0015,
        commission_fixed: float = 0.0,
        slippage_pct:     float = 0.0005,
        slippage_model:   str   = "percentage",
        execute_on:       str   = "open",
    ) -> None:
        self.commission_pct   = commission_pct
        self.commission_fixed = commission_fixed
        self.slippage_pct     = slippage_pct
        self.slippage_model   = slippage_model
        self.execute_on       = execute_on

    def fill_order(
        self,
        order: Order,
        bar: pd.Series,   # current OHLCV bar
        timestamp: pd.Timestamp,
        volume_fraction: float = 0.05,  # max fraction of bar volume we can trade
    ) -> Optional[Fill]:
        """
        Attempt to fill *order* using *bar* data.

        Returns a Fill if successful, None if the order cannot be filled.
        """
        # Choose execution price
        exec_price = self._execution_price(order, bar)
        if exec_price is None or exec_price <= 0:
            return None

        # Limit order check
        if order.order_type == OrderType.LIMIT:
            if order.is_buy  and exec_price > order.limit_price:
                return None
            if order.is_sell and exec_price < order.limit_price:
                return None

        # Stop order check
        if order.order_type in (OrderType.STOP, OrderType.STOP_LIMIT):
            if order.is_buy  and exec_price < order.stop_price:
                return None
            if order.is_sell and exec_price > order.stop_price:
                return None

        # Volume / liquidity constraint
        max_qty  = volume_fraction * float(bar.get("volume", 1e9))
        fill_qty = min(abs(order.qty), max_qty) if max_qty > 0 else abs(order.qty)
        if fill_qty < 1e-6:
            return None

        signed_qty = fill_qty if order.is_buy else -fill_qty

        # Slippage
        slippage = self._compute_slippage(exec_price, fill_qty, bar)

        # Commission
        commission = self._compute_commission(exec_price, fill_qty)

        # Net execution price (slippage direction depends on side)
        if order.is_buy:
            net_price = exec_price + slippage
        else:
            net_price = exec_price - slippage

        fill = Fill(
            order_id=order.order_id,
            ticker=order.ticker,
            side=order.side,
            qty=signed_qty,
            price=exec_price,
            commission=commission,
            slippage=slippage,
            timestamp=timestamp,
        )
        fill.net_price = net_price  # override dataclass default

        order.fill(net_price, signed_qty)
        logger.debug(
            "Filled %s %s %.2f @ %.4f (slip=%.4f comm=%.2f)",
            order.side.value, order.ticker, fill_qty,
            exec_price, slippage, commission,
        )
        return fill

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _execution_price(self, order: Order, bar: pd.Series) -> Optional[float]:
        """Determine raw execution price from bar data."""
        if self.execute_on == "open" and "open" in bar:
            return float(bar["open"])
        return float(bar["close"]) if "close" in bar else None

    def _compute_slippage(
        self,
        price: float,
        qty: float,
        bar: pd.Series,
    ) -> float:
        """Compute slippage in price units."""
        if self.slippage_model == "fixed":
            return self.slippage_pct   # treat as fixed $ amount

        if self.slippage_model == "sqrt":
            # Square-root market impact: σ * sqrt(qty / ADV)
            volume = float(bar.get("volume", 1e6)) or 1e6
            sigma  = price * 0.01     # rough daily vol proxy
            impact = sigma * np.sqrt(qty / volume)
            return impact

        # Default: percentage
        return price * self.slippage_pct

    def _compute_commission(self, price: float, qty: float) -> float:
        return self.commission_fixed + price * qty * self.commission_pct
