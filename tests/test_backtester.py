"""tests/test_backtester.py – Integration tests for the backtesting engine."""
import pandas as pd
import numpy as np
import pytest

from backtester.engine import BacktestEngine, BacktestConfig
from backtester.portfolio import Portfolio
from backtester.order import Order, OrderSide, OrderType, Fill
from backtester.execution import ExecutionModel
from backtester.performance import PerformanceAnalytics
from backtester.monte_carlo import MonteCarlo
from strategies.buy_and_hold import BuyAndHoldStrategy
from strategies.sma_crossover import SMACrossoverStrategy


class TestPortfolio:
    def test_initial_state(self):
        p = Portfolio(100_000)
        assert p.cash == 100_000
        assert p.equity == 100_000
        assert len(p.positions) == 0

    def test_buy_fill_reduces_cash(self):
        p = Portfolio(100_000)
        fill = Fill("o1", "AAPL", OrderSide.BUY, qty=10, price=150.0,
                    commission=1.0, slippage=0.05, timestamp=pd.Timestamp("2024-01-02"))
        fill.net_price = 150.05
        p.process_fill(fill)
        assert p.cash < 100_000
        assert "AAPL" in p.positions

    def test_sell_fill_increases_cash(self):
        p = Portfolio(100_000)
        buy = Fill("o1", "AAPL", OrderSide.BUY, qty=10, price=150.0,
                   commission=0.0, slippage=0.0, timestamp=pd.Timestamp("2024-01-02"))
        buy.net_price = 150.0
        p.process_fill(buy)
        sell = Fill("o2", "AAPL", OrderSide.SELL, qty=-10, price=160.0,
                    commission=0.0, slippage=0.0, timestamp=pd.Timestamp("2024-01-10"))
        sell.net_price = 160.0
        pnl = p.process_fill(sell)
        assert pnl == pytest.approx(100.0, abs=0.1)
        assert "AAPL" not in p.positions


class TestExecution:
    def test_market_order_fills(self, sample_ohlcv):
        bar = sample_ohlcv.iloc[10]
        ex  = ExecutionModel()
        order = Order("AAPL", OrderSide.BUY, qty=10, order_type=OrderType.MARKET)
        fill  = ex.fill_order(order, bar, pd.Timestamp("2024-01-10"))
        assert fill is not None
        assert fill.qty == pytest.approx(10, abs=0.01)

    def test_limit_order_not_filled_above_price(self, sample_ohlcv):
        bar = sample_ohlcv.iloc[10]
        ex  = ExecutionModel()
        order = Order("AAPL", OrderSide.BUY, qty=10,
                      order_type=OrderType.LIMIT, limit_price=1.0)  # way below market
        fill  = ex.fill_order(order, bar, pd.Timestamp("2024-01-10"))
        assert fill is None


class TestBacktestEngine:
    def test_buy_and_hold_runs(self, two_tickers_data):
        strategy = BuyAndHoldStrategy(params={"tickers": ["AAPL", "MSFT"]})
        config   = BacktestConfig(
            start_date="2020-01-01",
            end_date="2021-12-31",
            initial_capital=100_000,
        )
        engine = BacktestEngine(strategy, two_tickers_data, config)
        result = engine.run()
        assert result.equity_curve is not None
        assert len(result.equity_curve) > 0
        assert "sharpe" in result.performance

    def test_equity_never_negative(self, two_tickers_data):
        strategy = BuyAndHoldStrategy(params={"tickers": ["AAPL"]})
        config   = BacktestConfig(start_date="2020-01-01", end_date="2021-12-31")
        engine   = BacktestEngine(strategy, {"AAPL": two_tickers_data["AAPL"]}, config)
        result   = engine.run()
        assert (result.equity_curve > 0).all()

    def test_sma_crossover_trades(self, two_tickers_data):
        strategy = SMACrossoverStrategy(params={
            "tickers": ["AAPL"], "fast": 5, "slow": 20
        })
        config = BacktestConfig(start_date="2020-01-01", end_date="2021-12-31")
        engine = BacktestEngine(strategy, {"AAPL": two_tickers_data["AAPL"]}, config)
        result = engine.run()
        # May or may not have trades; just confirm it runs cleanly
        assert result.performance is not None


class TestMonteCarlo:
    def test_bootstrap_shape(self, sample_returns):
        paths = MonteCarlo.bootstrap_equity(sample_returns, n_sims=100, n_days=50)
        assert paths.shape == (51, 100)

    def test_all_paths_start_at_one(self, sample_returns):
        paths = MonteCarlo.bootstrap_equity(sample_returns, n_sims=50, n_days=30)
        assert (paths.iloc[0] == pytest.approx(1.0)).all()

    def test_stats_returns_dict(self, sample_returns):
        paths = MonteCarlo.parametric_equity(sample_returns, n_sims=100, n_days=50)
        stats = MonteCarlo.path_statistics(paths)
        assert "mean_terminal" in stats
        assert "prob_positive" in stats
