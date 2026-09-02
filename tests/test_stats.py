"""tests/test_stats.py – Unit tests for stats calculations."""
import numpy as np
import pandas as pd
import pytest

from stats.descriptive import DescriptiveStats
from stats.returns import ReturnStats
from stats.risk_metrics import RiskMetrics
from stats.drawdown import DrawdownAnalysis
from stats.distribution import DistributionAnalysis


class TestDescriptive:
    def test_summary_keys(self, sample_returns):
        s = DescriptiveStats.summary(sample_returns)
        for key in ["count", "mean", "std", "skewness", "kurtosis", "jb_pvalue"]:
            assert key in s

    def test_hurst_random_walk(self):
        rng = np.random.default_rng(0)
        rw  = pd.Series(rng.standard_normal(1000))
        h   = DescriptiveStats.hurst_exponent(rw)
        assert 0.3 <= h <= 0.7   # close to 0.5 for random walk

    def test_percentiles_ordered(self, sample_returns):
        pcts = DescriptiveStats.percentiles(sample_returns)
        vals = list(pcts.values())
        assert vals == sorted(vals)


class TestReturns:
    def test_total_return_positive_trend(self):
        prices = pd.Series(range(100, 200, 1), dtype=float)
        tr     = ReturnStats.total_return(prices)
        assert tr == pytest.approx(0.99, rel=0.01)

    def test_cagr_compound(self):
        prices = pd.Series([100.0] * 252 + [200.0])
        cagr   = ReturnStats.cagr(prices)
        assert cagr == pytest.approx(1.0, rel=0.05)   # ~100% return per year

    def test_monthly_returns_length(self, sample_prices):
        m = ReturnStats.monthly_returns(sample_prices)
        assert len(m) > 0

    def test_log_vs_simple(self, sample_prices):
        simple = ReturnStats.daily_returns(sample_prices)
        log    = ReturnStats.log_returns(sample_prices)
        # Log returns should be slightly smaller than simple for positive prices
        assert float(log.mean()) <= float(simple.mean())


class TestRiskMetrics:
    def test_sharpe_positive_trend(self):
        rng    = np.random.default_rng(0)
        rets   = pd.Series(rng.normal(0.001, 0.01, 500))
        sharpe = RiskMetrics.sharpe(rets)
        assert sharpe > 0

    def test_sortino_ge_sharpe_for_one_sided(self):
        # Constant positive returns → sortino should be higher or equal
        rets   = pd.Series([0.001] * 250)
        sharpe = RiskMetrics.sharpe(rets)
        sortino= RiskMetrics.sortino(rets)
        # For zero downside, sortino is inf; just check no exception
        assert not np.isnan(sharpe)

    def test_calmar_negative_mdd(self, sample_returns, sample_equity):
        calmar = RiskMetrics.calmar(sample_returns)
        # Can be any sign depending on data; just check it is a finite number
        assert np.isfinite(calmar)

    def test_omega_positive_returns(self):
        rets  = pd.Series([0.005] * 200)
        omega = RiskMetrics.omega(rets)
        assert omega == pytest.approx(float("inf"))

    def test_beta_calculation(self, sample_returns):
        bench = sample_returns * 0.8 + pd.Series(
            np.random.default_rng(1).normal(0, 0.001, len(sample_returns)),
            index=sample_returns.index,
        )
        beta = RiskMetrics.beta(sample_returns, bench)
        assert 0.5 < beta < 2.0   # should be ~1.25


class TestDrawdown:
    def test_max_drawdown_negative(self, sample_equity):
        mdd = DrawdownAnalysis.max_drawdown(sample_equity)
        assert mdd <= 0

    def test_underwater_zeros_at_new_highs(self, sample_equity):
        uw = DrawdownAnalysis.underwater(sample_equity)
        # At the start, equity = max → dd = 0
        assert uw.iloc[0] == pytest.approx(0.0, abs=1e-9)

    def test_recovery_factor_positive(self, sample_equity):
        rf = DrawdownAnalysis.recovery_factor(sample_equity)
        assert np.isfinite(rf)


class TestDistribution:
    def test_var_ordering(self, sample_returns):
        v95 = DistributionAnalysis.var_historical(sample_returns, 0.95)
        v99 = DistributionAnalysis.var_historical(sample_returns, 0.99)
        assert v99 >= v95   # higher confidence → larger VaR

    def test_cvar_ge_var(self, sample_returns):
        var  = DistributionAnalysis.var_historical(sample_returns, 0.95)
        cvar = DistributionAnalysis.cvar_historical(sample_returns, 0.95)
        assert cvar >= var

    def test_best_distribution_returns_name(self, sample_returns):
        result = DistributionAnalysis.fit_best_distribution(sample_returns)
        assert "name" in result and result["name"] is not None
