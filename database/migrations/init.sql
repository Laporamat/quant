-- database/migrations/init.sql
-- Initial schema – run once against the target PostgreSQL database.

CREATE TABLE IF NOT EXISTS tickers (
    id          SERIAL PRIMARY KEY,
    symbol      VARCHAR(16)  UNIQUE NOT NULL,
    name        VARCHAR(256),
    exchange    VARCHAR(32),
    sector      VARCHAR(64),
    country     VARCHAR(8),
    currency    VARCHAR(8),
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prices (
    id      BIGSERIAL PRIMARY KEY,
    ticker  VARCHAR(16) NOT NULL REFERENCES tickers(symbol) ON DELETE CASCADE,
    date    VARCHAR(12) NOT NULL,
    open    DOUBLE PRECISION,
    high    DOUBLE PRECISION,
    low     DOUBLE PRECISION,
    close   DOUBLE PRECISION NOT NULL,
    volume  DOUBLE PRECISION,
    CONSTRAINT uq_price_ticker_date UNIQUE (ticker, date)
);
CREATE INDEX IF NOT EXISTS ix_price_ticker_date ON prices (ticker, date);

CREATE TABLE IF NOT EXISTS backtest_runs (
    id               VARCHAR(36)  PRIMARY KEY,
    strategy_name    VARCHAR(64)  NOT NULL,
    start_date       VARCHAR(12),
    end_date         VARCHAR(12),
    initial_capital  DOUBLE PRECISION,
    commission_pct   DOUBLE PRECISION DEFAULT 0.0015,
    slippage_pct     DOUBLE PRECISION DEFAULT 0.0005,
    tickers          TEXT,
    strategy_params  TEXT,
    performance      TEXT,
    status           VARCHAR(20)  DEFAULT 'completed',
    sharpe           DOUBLE PRECISION,
    cagr             DOUBLE PRECISION,
    max_drawdown     DOUBLE PRECISION,
    n_trades         INTEGER,
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS optimisation_results (
    id           SERIAL PRIMARY KEY,
    strategy     VARCHAR(64),
    metric       VARCHAR(32),
    best_params  TEXT,
    best_value   DOUBLE PRECISION,
    all_results  TEXT,
    created_at   TIMESTAMP DEFAULT NOW()
);
