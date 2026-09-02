"""
backtester/portfolio.py
Portfolio state: cash, positions, equity curve, trade log.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from backtester.order import Fill, OrderSide

logger = logging.getLogger(__name__)


@dataclass
class Position:
    ticker:     str
    qty:        float         # positive=long, negative=short
    avg_cost:   float         # average entry price
    entry_date: pd.Timestamp
    market_value: float = 0.0
    unrealised_pnl: float = 0.0

    @property
    def is_long(self) -> bool:
        return self.qty > 0

    @property
    def cost_basis(self) -> float:
        return abs(self.qty) * self.avg_cost

    def update_market_value(self, price: float) -> None:
        self.market_value = self.qty * price
        self.unrealised_pnl = self.qty * (price - self.avg_cost)


class Portfolio:
    """
    Tracks cash, positions, and computes equity at each bar.
    """

    def __init__(
        self,
        initial_capital: float = 1_000_000.0,
    ) -> None:
        self.initial_capital = initial_capital
        self.cash      = initial_capital
        self.positions: Dict[str, Position] = {}
        self.equity_curve: List[Dict] = []
        self.trade_log:    List[Dict] = []
        self._equity_by_date: Dict[pd.Timestamp, float] = {}

    # ──────────────────────────────────────────
    # Fill processing
    # ──────────────────────────────────────────

    def process_fill(self, fill: Fill) -> float:
        """Apply a fill to portfolio state. Returns realised PnL."""
        cost      = fill.qty * fill.net_price
        realised  = 0.0

        if fill.side == OrderSide.BUY:
            self.cash -= cost
            existing = self.positions.get(fill.ticker)
            if existing is None:
                self.positions[fill.ticker] = Position(
                    ticker=fill.ticker,
                    qty=fill.qty,
                    avg_cost=fill.net_price,
                    entry_date=fill.timestamp,
                )
            else:
                # Average in
                total_qty  = existing.qty + fill.qty
                total_cost = existing.qty * existing.avg_cost + fill.qty * fill.net_price
                existing.qty      = total_qty
                existing.avg_cost = total_cost / total_qty if total_qty != 0 else 0
        else:
            # Selling
            existing = self.positions.get(fill.ticker)
            if existing:
                sell_qty = min(abs(fill.qty), abs(existing.qty))
                realised = sell_qty * (fill.net_price - existing.avg_cost)
                existing.qty += fill.qty  # fill.qty is negative for sells
                if abs(existing.qty) < 1e-9:
                    del self.positions[fill.ticker]
            self.cash -= cost  # cost is negative (cash inflow)

        self._log_trade(fill, realised)
        return realised

    # ──────────────────────────────────────────
    # Mark to market
    # ──────────────────────────────────────────

    def mark_to_market(
        self,
        date: pd.Timestamp,
        prices: Dict[str, float],
    ) -> float:
        """Revalue all positions and compute total equity."""
        pos_value = 0.0
        for ticker, pos in self.positions.items():
            price = prices.get(ticker)
            if price is not None:
                pos.update_market_value(price)
                pos_value += pos.market_value

        equity = self.cash + pos_value
        self._equity_by_date[date] = equity
        self.equity_curve.append({
            "date":       date,
            "cash":       self.cash,
            "pos_value":  pos_value,
            "equity":     equity,
            "n_positions": len(self.positions),
        })
        return equity

    # ──────────────────────────────────────────
    # Queries
    # ──────────────────────────────────────────

    @property
    def equity(self) -> float:
        """Latest total equity."""
        if self.equity_curve:
            return self.equity_curve[-1]["equity"]
        return self.cash

    @property
    def total_pnl(self) -> float:
        return self.equity - self.initial_capital

    @property
    def total_return(self) -> float:
        return self.total_pnl / self.initial_capital

    def get_position(self, ticker: str) -> Optional[Position]:
        return self.positions.get(ticker)

    def has_position(self, ticker: str) -> bool:
        return ticker in self.positions

    def position_weight(self, ticker: str) -> float:
        """Position weight as fraction of total equity."""
        pos = self.positions.get(ticker)
        if pos is None or self.equity == 0:
            return 0.0
        return pos.market_value / self.equity

    def get_equity_series(self) -> pd.Series:
        """Return equity curve as pandas Series indexed by date."""
        if not self.equity_curve:
            return pd.Series(dtype=float)
        df = pd.DataFrame(self.equity_curve).set_index("date")
        return df["equity"]

    def get_trade_log(self) -> pd.DataFrame:
        return pd.DataFrame(self.trade_log)

    # ──────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────

    def _log_trade(self, fill: Fill, realised_pnl: float) -> None:
        self.trade_log.append({
            "date":         fill.timestamp,
            "ticker":       fill.ticker,
            "side":         fill.side.value,
            "qty":          fill.qty,
            "price":        fill.price,
            "net_price":    fill.net_price,
            "commission":   fill.commission,
            "slippage":     fill.slippage,
            "realised_pnl": realised_pnl,
        })

    def summary(self) -> dict:
        return {
            "initial_capital":  self.initial_capital,
            "final_equity":     self.equity,
            "total_pnl":        self.total_pnl,
            "total_return_pct": self.total_return * 100,
            "cash":             self.cash,
            "n_open_positions": len(self.positions),
            "n_trades":         len(self.trade_log),
        }
