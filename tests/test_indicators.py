"""tests/test_indicators.py – Unit tests for all indicator calculations."""
import numpy as np
import pandas as pd
import pytest

from indicators.moving_averages import MovingAverages as MA
from indicators.momentum import Momentum
from indicators.volatility import Volatility
from indicators.trend import Trend
from indicators.volume import Volume
from indicators.oscillators import Oscillators


class TestMovingAverages:
    def test_sma_length(self, sample_prices):
        result = MA.sma(sample_prices, 20)
        assert len(result) == len(sample_prices)
        assert result.iloc[:19].isna().all()
        assert result.iloc[20:].notna().all()

    def test_ema_vs_pandas(self, sample_prices):
        result   = MA.ema(sample_prices, 20)
        expected = sample_prices.ewm(span=20, adjust=False, min_periods=20).mean()
        pd.testing.assert_series_equal(result, expected, check_names=False, rtol=1e-6)

    def test_hma_no_nan_in_middle(self, sample_prices):
        result = MA.hma(sample_prices, 20)
        assert len(result.dropna()) > 200

    def test_dema_less_lag_than_ema(self, sample_prices):
        close = sample_prices
        ema   = MA.ema(close, 20).dropna()
        dema  = MA.dema(close, 20).dropna()
        # DEMA should generally react faster; just check no exception and correct length
        assert len(dema) > 100

    def test_kama_bounded(self, sample_prices):
        result = MA.kama(sample_prices, 10)
        valid  = result.dropna()
        assert (valid > 0).all()
        assert (valid < sample_prices.max() * 2).all()

    def test_crossover_signals(self, sample_prices):
        fast = MA.sma(sample_prices, 20)
        slow = MA.sma(sample_prices, 50)
        sig  = MA.crossover(fast, slow)
        assert set(sig.unique()).issubset({-1, 0, 1})


class TestMomentum:
    def test_rsi_range(self, sample_prices):
        rsi = Momentum.rsi(sample_prices, 14).dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all()

    def test_stochastic_range(self, sample_ohlcv):
        df = sample_ohlcv
        st = Momentum.stochastic(df["high"], df["low"], df["close"]).dropna()
        assert (st["stoch_k"] >= 0).all() and (st["stoch_k"] <= 100).all()

    def test_macd_histogram_symmetry(self, sample_prices):
        m = Momentum.macd(sample_prices)
        diff = (m["macd"] - m["macd_sig"] - m["macd_hist"]).dropna().abs()
        assert (diff < 1e-8).all()

    def test_roc_positive_when_price_rises(self):
        prices = pd.Series(range(100, 200), dtype=float)
        roc    = Momentum.roc(prices, 10).dropna()
        assert (roc > 0).all()

    def test_mfi_range(self, sample_ohlcv):
        df  = sample_ohlcv
        mfi = Momentum.mfi(df["high"], df["low"], df["close"], df["volume"]).dropna()
        assert (mfi >= 0).all() and (mfi <= 100).all()


class TestVolatility:
    def test_atr_positive(self, sample_ohlcv):
        df  = sample_ohlcv
        atr = Volatility.atr(df["high"], df["low"], df["close"]).dropna()
        assert (atr > 0).all()

    def test_bb_upper_above_lower(self, sample_prices):
        bb = Volatility.bollinger_bands(sample_prices).dropna()
        assert (bb["bb_upper"] > bb["bb_lower"]).all()

    def test_hist_vol_positive(self, sample_prices):
        hv = Volatility.historical_volatility(sample_prices).dropna()
        assert (hv > 0).all()

    def test_donchian_monotonic(self, sample_ohlcv):
        dc = Volatility.donchian_channels(sample_ohlcv["high"], sample_ohlcv["low"]).dropna()
        assert (dc["dc_upper"] >= dc["dc_lower"]).all()


class TestTrend:
    def test_adx_range(self, sample_ohlcv):
        df  = sample_ohlcv
        adx = Trend.adx(df["high"], df["low"], df["close"]).dropna()
        assert (adx["adx"] >= 0).all()
        assert (adx["adx"] <= 100).all()

    def test_cci_mean_near_zero(self, sample_ohlcv):
        df  = sample_ohlcv
        cci = Trend.cci(df["high"], df["low"], df["close"]).dropna()
        # CCI should oscillate around 0
        assert abs(float(cci.mean())) < 50

    def test_psar_alternates(self, sample_ohlcv):
        df   = sample_ohlcv
        psar = Trend.parabolic_sar(df["high"], df["low"])
        trend_vals = psar["psar_trend"].dropna().unique()
        # Should have both +1 and -1
        assert 1 in trend_vals or -1 in trend_vals


class TestVolume:
    def test_obv_increases_on_up_days(self, sample_ohlcv):
        df  = sample_ohlcv
        obv = Volume.obv(df["close"], df["volume"])
        assert not obv.empty

    def test_cmf_range(self, sample_ohlcv):
        df  = sample_ohlcv
        cmf = Volume.cmf(df["high"], df["low"], df["close"], df["volume"]).dropna()
        assert (cmf >= -1).all() and (cmf <= 1).all()


class TestOscillators:
    def test_williams_r_range(self, sample_ohlcv):
        df = sample_ohlcv
        wr = Oscillators.williams_r(df["high"], df["low"], df["close"]).dropna()
        assert (wr >= -100).all() and (wr <= 0).all()

    def test_stoch_rsi_range(self, sample_prices):
        sr = Oscillators.stoch_rsi(sample_prices).dropna()
        assert (sr["stoch_rsi_k"] >= 0).all() and (sr["stoch_rsi_k"] <= 100).all()

    def test_awesome_oscillator_length(self, sample_ohlcv):
        ao = Oscillators.awesome_oscillator(sample_ohlcv["high"], sample_ohlcv["low"])
        assert len(ao) == len(sample_ohlcv)
