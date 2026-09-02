"""
backtester/engine.py
Core event-driven backtesting engine.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from backtester.portfolio import Portfolio
from backtester.execution import ExecutionModel
from backtester.risk_manager import RiskManager
from backtester.order import Order, OrderSide, OrderType
from strategies.base_strategy import BaseStrategy, Signal

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for a single backtest run."""
    start_date:       str
    end_date:         str
    initial_capital:  float = 1_000_000.0
    commission_pct:   float = 0.0015
    slippage_pct:     float = 0.0005
    max_position_pct: float = 0.10
    position_sizing:  str   = "equal"
    max_drawdown_halt:float  = 0.25
    stop_loss_pct:    Optional[float] = None
    benchmark_ticker: str   = "SPY"
    meta:             dict  = field(default_factory=dict)


@dataclass
class BacktestResult:
    """Container for backtest output."""
    config:        BacktestConfig
    strategy_name: str
    equity_curve:  pd.Series
    returns:       pd.Series
    trade_log:     pd.DataFrame
    performance:   dict
    signals_log:   List[dict] = field(default_factory=list)
    run_time_s:    float = 0.0


class BacktestEngine:
    """
    Event-driven backtesting engine.

    Loop
    ----
    For each trading day:
      1. Call strategy.on_bar()
      2. Call strategy.generate_signals()
      3. RiskManager converts signals → Orders
      4. ExecutionModel fills Orders
      5. Portfolio.process_fill() updates state
      6. Portfolio.mark_to_market() records equity
    """

    def __init__(
        self,
        strategy:  BaseStrategy,
        data:      Dict[str, pd.DataFrame],   # {ticker: ohlcv_df}
        config:    Optional[BacktestConfig] = None,
    ) -> None:
        self.strategy = strategy
        self.data     = data
        self.config   = config or BacktestConfig(
            start_date="2004-01-01",
            end_date="2024-12-31",
        )

    def run(self) -> BacktestResult:
        """Execute the full backtest and return results."""
        t0 = time.perf_counter()
        cfg = self.config

        logger.info(
            "Starting backtest: %s | %s → %s | capital=%.0f",
            self.strategy.name, cfg.start_date, cfg.end_date, cfg.initial_capital,
        )

        # ── Setup ─────────────────────────────
        portfolio = Portfolio(cfg.initial_capital)
        execution = ExecutionModel(
            commission_pct=cfg.commission_pct,
            slippage_pct=cfg.slippage_pct,
        )
        risk_mgr = RiskManager(
            initial_capital=cfg.initial_capital,
            max_position_pct=cfg.max_position_pct,
            position_sizing=cfg.position_sizing,
            max_drawdown_halt=cfg.max_drawdown_halt,
            stop_loss_pct=cfg.stop_loss_pct,
        )

        # ── Prepare strategy ──────────────────
        # Slice data to [start, end] for strategy.prepare
        sliced_data = self._slice_data(cfg.start_date, cfg.end_date)
        self.strategy.prepare(sliced_data)

        # ── Build trading calendar ─────────────
        all_dates = self._build_calendar(cfg.start_date, cfg.end_date)

        # Pre-build returns history for vol-target sizing
        returns_history = self._build_returns_panel()

        signals_log: List[dict] = []
        pending_orders: List[Order] = []

        # ── Main loop ─────────────────────────
        for date in all_dates:
            # Get current prices
            prices = self._current_prices(date)
            if not prices:
                continue

            # Fill any pending orders from previous bar
            fills = []
            for order in pending_orders:
                ticker = order.ticker
                bar = self._get_bar(ticker, date)
                if bar is None:
                    continue
                fill = execution.fill_order(order, bar, date)
                if fill:
                    pnl = portfolio.process_fill(fill)
                    fills.append(fill)
            pending_orders = []

            # Mark to market
            portfolio.mark_to_market(date, prices)
            risk_mgr.update_peak_equity(portfolio.equity)

            # Strategy on_bar hook
            self.strategy.on_bar(date, sliced_data)

            # Generate signals
            portfolio_state = {
                "cash":      portfolio.cash,
                "equity":    portfolio.equity,
                "positions": portfolio.positions,
            }
            signals: List[Signal] = self.strategy.generate_signals(
                date, sliced_data, portfolio_state
            )

            if signals:
                for s in signals:
                    signals_log.append({
                        "date":   date,
                        "ticker": s.ticker,
                        "signal": s.signal.value,
                        "strength": s.strength,
                        "price": s.price,
                    })

                # Size orders via risk manager
                rets_to_date = returns_history.loc[:date] if returns_history is not None else None
                orders = risk_mgr.size_orders(
                    signals, portfolio.equity, portfolio.positions,
                    prices, rets_to_date,
                )
                pending_orders.extend(orders)

        # ── Close any remaining positions ──────
        final_date = all_dates[-1] if len(all_dates) > 0 else None
        if final_date:
            for ticker, pos in list(portfolio.positions.items()):
                bar = self._get_bar(ticker, final_date)
                if bar is None:
                    continue
                close_order = Order(
                    ticker=ticker,
                    side=OrderSide.SELL,
                    qty=-abs(pos.qty),
                    order_type=OrderType.MARKET,
                    created_at=final_date,
                )
                fill = execution.fill_order(close_order, bar, final_date)
                if fill:
                    portfolio.process_fill(fill)

        # ── Compute performance ────────────────
        from backtester.performance import PerformanceAnalytics
        equity_series = portfolio.get_equity_series()
        returns       = equity_series.pct_change().dropna()
        performance   = PerformanceAnalytics.full_report(
            equity_series, returns,
            benchmark_ticker=cfg.benchmark_ticker,
        )

        run_time = time.perf_counter() - t0
        logger.info(
            "Backtest complete in %.2fs | Final equity: %.0f (%.1f%%)",
            run_time, portfolio.equity, portfolio.total_return * 100,
        )

        return BacktestResult(
            config=cfg,
            strategy_name=self.strategy.name,
            equity_curve=equity_series,
            returns=returns,
            trade_log=portfolio.get_trade_log(),
            performance=performance,
            signals_log=signals_log,
            run_time_s=run_time,
        )

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _slice_data(self, start: str, end: str) -> Dict[str, pd.DataFrame]:
        return {
            t: df.loc[start:end]
            for t, df in self.data.items()
            if not df.loc[start:end].empty
        }

    def _build_calendar(self, start: str, end: str) -> pd.DatetimeIndex:
        """Union of all dates present in data files within [start, end]."""
        dates = set()
        for df in self.data.values():
            sliced = df.loc[start:end]
            dates.update(sliced.index.tolist())
        return pd.DatetimeIndex(sorted(dates))

    def _build_returns_panel(self) -> Optional[pd.DataFrame]:
        frames: Dict[str, pd.Series] = {}
        for t, df in self.data.items():
            if "close" in df.columns:
                frames[t] = df["close"].pct_change()
        if not frames:
            return None
        return pd.DataFrame(frames)

    def _current_prices(self, date: pd.Timestamp) -> Dict[str, float]:
        prices = {}
        for ticker, df in self.data.items():
            sliced = df.loc[:date]
            if not sliced.empty and "close" in sliced.columns:
                prices[ticker] = float(sliced["close"].iloc[-1])
        return prices

    def _get_bar(
        self, ticker: str, date: pd.Timestamp
    ) -> Optional[pd.Series]:
        df = self.data.get(ticker)
        if df is None:
            return None
        sliced = df.loc[:date]
        return sliced.iloc[-1] if not sliced.empty else None
