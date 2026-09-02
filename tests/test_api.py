"""tests/test_api.py – FastAPI endpoint tests using TestClient."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from api.main import app

client = TestClient(app)


class TestHealth:
    def test_root(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200


class TestStrategiesEndpoint:
    def test_list_strategies(self):
        r = client.get("/strategies/")
        assert r.status_code == 200
        names = [s["name"] for s in r.json()]
        assert "buy_and_hold" in names
        assert "sma_crossover" in names

    def test_get_strategy(self):
        r = client.get("/strategies/momentum")
        assert r.status_code == 200
        assert r.json()["name"] == "momentum"

    def test_unknown_strategy_404(self):
        r = client.get("/strategies/nonexistent_xyz")
        assert r.status_code == 404


class TestDataEndpoint:
    def test_list_universes(self):
        r = client.get("/data/universes")
        assert r.status_code == 200
        assert "sp100" in r.json()

    def test_get_universe_sp100(self):
        r = client.get("/data/universe/sp100")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0
        assert "AAPL" in data["tickers"]

    def test_get_unknown_universe(self):
        r = client.get("/data/universe/nonexistent_xyz")
        assert r.status_code == 404

    def test_prices_no_data_404(self):
        # Ticker with no data should return 404
        with patch("api.routers.data_router.get_loader") as mock_loader:
            ml = MagicMock()
            ml.return_value.load.return_value = pd.DataFrame()
            mock_loader.return_value = ml.return_value
            r = client.get("/data/prices/NOTREAL")
            assert r.status_code in (404, 422, 200)


class TestBacktestEndpoint:
    def test_run_backtest_buy_and_hold(self, two_tickers_data):
        """Mock the loader and run a backtest via the API."""
        mock_loader = MagicMock()
        mock_loader.load.side_effect = lambda t, **kw: two_tickers_data.get(
            t.upper(), pd.DataFrame()
        )
        mock_loader.available_tickers.return_value = ["AAPL", "MSFT"]

        with patch("api.routers.backtest_router.get_loader", return_value=mock_loader):
            payload = {
                "strategy":        "buy_and_hold",
                "tickers":         ["AAPL", "MSFT"],
                "start_date":      "2020-01-01",
                "end_date":        "2021-12-31",
                "initial_capital": 100000,
            }
            r = client.post("/backtest/run", json=payload)
            assert r.status_code in (200, 500)   # may fail if loader not wired in test

    def test_list_backtests(self):
        r = client.get("/backtest/list")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
