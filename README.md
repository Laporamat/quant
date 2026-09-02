# 📈 Quant Backend

Comprehensive quantitative trading backend with **20-year historical data analysis**, technical indicators, statistical analytics, and a full **event-driven backtester**.

---

## Architecture

```
quant/
├── config.py                  # Global settings (Pydantic Settings)
├── main.py                    # Entry point (uvicorn server)
│
├── data/
│   ├── downloader.py          # yFinance 20-year OHLCV download
│   ├── loader.py              # Parquet/CSV loader with memory cache
│   ├── cleaner.py             # Missing values, outliers, splits
│   └── universe.py            # SP100, SET50, sector mappings
│
├── indicators/
│   ├── moving_averages.py     # SMA, EMA, WMA, DEMA, TEMA, HMA, KAMA, T3
│   ├── momentum.py            # RSI, Stochastic, MACD, ROC, MFI, CMO
│   ├── volatility.py          # Bollinger, ATR, Keltner, Donchian, HV, GK, YZ
│   ├── trend.py               # ADX, CCI, Aroon, Ichimoku, PSAR, Supertrend
│   ├── volume.py              # OBV, VWAP, CMF, AD Line, Force Index, KVO
│   ├── oscillators.py         # Williams%R, Ultimate Osc, TRIX, StochRSI, KST
│   └── custom.py              # Composite scores, fractal, pivot points
│
├── stats/
│   ├── descriptive.py         # Mean, std, skew, kurtosis, autocorr, Hurst
│   ├── returns.py             # CAGR, monthly table, rolling returns
│   ├── risk_metrics.py        # Sharpe, Sortino, Calmar, Omega, Treynor, IR
│   ├── drawdown.py            # Max DD, duration, underwater curve, top-N DD
│   ├── correlation.py         # Pairwise, rolling, distance corr, beta matrix
│   ├── factor_analysis.py     # Fama-French 3/5 factor loading via OLS
│   ├── regime_detection.py    # Gaussian HMM (bull/bear/sideways) + MA regime
│   ├── seasonality.py         # Day-of-week, month, January, turn-of-month
│   ├── distribution.py        # VaR, CVaR (hist/param/CF), GPD EVT, t-fit
│   └── cointegration.py       # Engle-Granger, Johansen, spread, z-score
│
├── strategies/
│   ├── base_strategy.py       # Abstract base class + Signal dataclass
│   ├── buy_and_hold.py        # Equal-weight benchmark
│   ├── sma_crossover.py       # Golden/death cross trend following
│   ├── momentum_strategy.py   # Cross-sectional & time-series momentum
│   ├── mean_reversion.py      # RSI/Bollinger mean reversion
│   ├── breakout.py            # Donchian + ATR trailing stop breakout
│   ├── pairs_trading.py       # Stat-arb spread z-score
│   ├── multi_factor.py        # Momentum + low-vol + trend factor scoring
│   ├── volatility_targeting.py# Inverse-vol / vol-target allocation
│   ├── trend_following.py     # Dual-momentum (Antonacci) + trend filter
│   └── ml_strategy.py         # Random Forest / XGBoost / LightGBM signals
│
├── backtester/
│   ├── engine.py              # Event-driven backtest loop
│   ├── portfolio.py           # Cash, positions, equity curve, trade log
│   ├── order.py               # Order / Fill data models
│   ├── execution.py           # Market/limit/stop fill + slippage + commission
│   ├── risk_manager.py        # Position sizing (Kelly, vol-target, equal)
│   ├── performance.py         # Full performance report
│   ├── optimizer.py           # Grid search + walk-forward optimisation
│   ├── monte_carlo.py         # Bootstrap / parametric path simulation
│   ├── benchmark.py           # Side-by-side vs benchmark comparison
│   └── report.py              # HTML + JSON report generator
│
├── api/
│   ├── main.py                # FastAPI app factory
│   ├── middleware.py           # CORS, timing, error handling
│   ├── dependencies.py        # Shared FastAPI DI
│   ├── routers/
│   │   ├── data_router.py     # /data/* – download, prices, universe
│   │   ├── stats_router.py    # /stats/* – descriptive, returns, risk
│   │   ├── indicators_router.py # /indicators/* – MA, RSI, BB, ADX …
│   │   ├── strategy_router.py # /strategies/* – list, details
│   │   ├── backtest_router.py # /backtest/* – run, list, report, MC
│   │   └── optimize_router.py # /optimize/* – grid, walk-forward
│   └── schemas/
│       ├── data_schema.py
│       ├── stats_schema.py
│       └── backtest_schema.py
│
├── utils/
│   ├── logger.py              # Structured logging (rotating file)
│   ├── cache.py               # Redis + disk cache
│   ├── date_utils.py          # Business day helpers
│   ├── math_utils.py          # Rolling windows, z-score, IC
│   ├── plotting.py            # Plotly charts (equity, DD, heatmap)
│   └── validators.py          # Input validation
│
├── database/
│   ├── models.py              # SQLAlchemy ORM (Ticker, Price, BacktestRun)
│   ├── session.py             # Async + sync DB sessions
│   ├── crud.py                # CRUD helpers
│   └── migrations/init.sql    # Initial PostgreSQL schema
│
├── jobs/
│   ├── data_refresh.py        # Daily data refresh job
│   └── scheduler.py           # APScheduler setup
│
├── scripts/
│   ├── download_data.py       # CLI: download data
│   ├── run_backtest.py        # CLI: run a backtest
│   ├── run_optimization.py    # CLI: grid search
│   └── generate_report.py     # CLI: HTML report
│
├── tests/
│   ├── conftest.py
│   ├── test_indicators.py
│   ├── test_stats.py
│   ├── test_backtester.py
│   ├── test_strategies.py
│   └── test_api.py
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env as needed (DB URL, Redis URL, etc.)
```

### 3. Download historical data
```bash
python scripts/download_data.py --universe sp100 --start 2004-01-01
```

### 4. Run a backtest (CLI)
```bash
python scripts/run_backtest.py \
  --strategy sma_crossover \
  --tickers AAPL,MSFT,GOOGL,AMZN,NVDA \
  --start 2010-01-01 --end 2024-12-31
```

### 5. Start the API server
```bash
python main.py
# Or: uvicorn api.main:app --reload
```
Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/data/universe/{name}` | List tickers in a universe |
| GET | `/data/prices/{ticker}` | OHLCV data for a ticker |
| POST | `/data/download` | Download / refresh data |
| GET | `/stats/descriptive/{ticker}` | Descriptive stats |
| GET | `/stats/returns/{ticker}` | Return summary |
| GET | `/stats/risk/{ticker}` | Risk metrics (Sharpe, VaR…) |
| GET | `/stats/drawdown/{ticker}` | Drawdown analysis |
| POST | `/stats/correlation` | Correlation matrix |
| GET | `/stats/regime/{ticker}` | HMM regime detection |
| GET | `/stats/seasonality/{ticker}` | Seasonality effects |
| GET | `/indicators/all/{ticker}` | All technical indicators |
| GET | `/indicators/rsi/{ticker}` | RSI |
| GET | `/indicators/macd/{ticker}` | MACD |
| GET | `/indicators/bollinger/{ticker}` | Bollinger Bands |
| GET | `/strategies/` | List all strategies |
| POST | `/backtest/run` | Run a backtest |
| GET | `/backtest/list` | List past backtests |
| GET | `/backtest/{id}/report` | HTML report for a run |
| POST | `/backtest/monte-carlo` | Monte Carlo simulation |
| POST | `/optimize/grid` | Grid search optimisation |
| POST | `/optimize/walk-forward` | Walk-forward analysis |

---

## Available Strategies

| Name | Description |
|------|-------------|
| `buy_and_hold` | Equal-weight benchmark |
| `sma_crossover` | Golden/death-cross MA |
| `momentum` | Cross-sectional & time-series momentum |
| `mean_reversion` | RSI + Bollinger Band reversion |
| `breakout` | Donchian Channel + ATR stop |
| `pairs_trading` | Spread z-score stat-arb |
| `multi_factor` | Momentum + low-vol + trend |
| `volatility_targeting` | Inverse-vol / risk-parity |
| `trend_following` | Antonacci dual-momentum |
| `ml` | Random Forest / XGBoost / LightGBM |

---

## Docker

```bash
cd docker
docker-compose up --build
```

Services: PostgreSQL (5432), Redis (6379), API (8000).

---

## Run Tests

```bash
pytest tests/ -v --tb=short
```

---

## Data Sources

- **Equities**: Yahoo Finance via `yfinance` (20-year daily OHLCV, auto-adjusted)
- **Universe**: S&P 100 (90 tickers), SET50 Thailand, custom universes
- **Benchmark**: SPY (S&P 500 ETF)

---

*Built with FastAPI · pandas · yfinance · scikit-learn · XGBoost · SQLAlchemy · APScheduler · Plotly*
