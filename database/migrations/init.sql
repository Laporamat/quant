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

-- ── Auth tables (added for full auth system) ──────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(320) UNIQUE NOT NULL,
    username        VARCHAR(64)  UNIQUE NOT NULL,
    display_name    VARCHAR(128),
    hashed_password TEXT         NOT NULL,
    role            VARCHAR(20)  NOT NULL DEFAULT 'viewer',  -- viewer|analyst|admin
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    is_verified     BOOLEAN      NOT NULL DEFAULT FALSE,
    avatar_url      TEXT,
    -- 2FA
    totp_secret     TEXT,
    totp_enabled    BOOLEAN      NOT NULL DEFAULT FALSE,
    -- Security tracking
    failed_logins   SMALLINT     NOT NULL DEFAULT 0,
    locked_until    TIMESTAMP,
    last_login_at   TIMESTAMP,
    last_login_ip   VARCHAR(45),
    password_changed_at TIMESTAMP DEFAULT NOW(),
    -- Timestamps
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_users_email    ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);

-- Refresh token store (one row per active session)
CREATE TABLE IF NOT EXISTS user_sessions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token   TEXT        UNIQUE NOT NULL,   -- SHA-256 hash of actual token
    device_info     TEXT,                          -- browser/OS from user-agent
    ip_address      VARCHAR(45),
    is_revoked      BOOLEAN     NOT NULL DEFAULT FALSE,
    expires_at      TIMESTAMP   NOT NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    last_used_at    TIMESTAMP   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_sessions_user    ON user_sessions (user_id);
CREATE INDEX IF NOT EXISTS ix_sessions_token   ON user_sessions (refresh_token);
CREATE INDEX IF NOT EXISTS ix_sessions_expires ON user_sessions (expires_at);

-- Full audit log — every auth event
CREATE TABLE IF NOT EXISTS audit_logs (
    id          BIGSERIAL   PRIMARY KEY,
    user_id     UUID        REFERENCES users(id) ON DELETE SET NULL,
    event       VARCHAR(64) NOT NULL,   -- login_success|login_failed|logout|register|...
    ip_address  VARCHAR(45),
    user_agent  TEXT,
    details     JSONB,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_audit_user  ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_audit_event ON audit_logs (event);
CREATE INDEX IF NOT EXISTS ix_audit_ts    ON audit_logs (created_at);

-- Email verification tokens
CREATE TABLE IF NOT EXISTS verification_tokens (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  TEXT        UNIQUE NOT NULL,
    purpose     VARCHAR(32) NOT NULL,  -- email_verify|password_reset
    expires_at  TIMESTAMP   NOT NULL,
    used_at     TIMESTAMP,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_vtoken_hash ON verification_tokens (token_hash);
