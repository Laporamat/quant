"""
backtester/order.py
Order data model: market, limit, stop-limit orders.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import pandas as pd


class OrderType(str, Enum):
    MARKET      = "MARKET"
    LIMIT       = "LIMIT"
    STOP        = "STOP"
    STOP_LIMIT  = "STOP_LIMIT"


class OrderSide(str, Enum):
    BUY  = "BUY"
    SELL = "SELL"


class OrderStatus(str, Enum):
    PENDING   = "PENDING"
    FILLED    = "FILLED"
    PARTIAL   = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED  = "REJECTED"


@dataclass
class Order:
    """Represents a trading order."""
    ticker:      str
    side:        OrderSide
    qty:         float                    # signed (negative = short/sell)
    order_type:  OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price:  Optional[float] = None
    created_at:  Optional[pd.Timestamp] = None
    filled_at:   Optional[pd.Timestamp] = None
    fill_price:  Optional[float] = None
    fill_qty:    float = 0.0
    status:      OrderStatus = OrderStatus.PENDING
    order_id:    str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    meta:        dict = field(default_factory=dict)

    @property
    def is_buy(self) -> bool:
        return self.side == OrderSide.BUY

    @property
    def is_sell(self) -> bool:
        return self.side == OrderSide.SELL

    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED

    @property
    def notional(self) -> Optional[float]:
        if self.fill_price is not None:
            return self.fill_qty * self.fill_price
        return None

    def fill(self, price: float, qty: Optional[float] = None) -> None:
        self.fill_price = price
        self.fill_qty   = qty if qty is not None else self.qty
        self.status     = OrderStatus.FILLED

    def cancel(self) -> None:
        self.status = OrderStatus.CANCELLED

    def __repr__(self) -> str:
        return (
            f"Order({self.order_id} {self.side.value} {self.qty:.2f} "
            f"{self.ticker} @ {self.order_type.value} "
            f"status={self.status.value})"
        )


@dataclass
class Fill:
    """Represents an executed order fill."""
    order_id:   str
    ticker:     str
    side:       OrderSide
    qty:        float
    price:      float
    commission: float
    slippage:   float
    timestamp:  pd.Timestamp
    net_price:  float = field(init=False)

    def __post_init__(self) -> None:
        self.net_price = self.price + self.slippage + (
            self.commission / self.qty if self.qty != 0 else 0
        )
