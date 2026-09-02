"""
database/models.py
SQLAlchemy ORM models for tickers, prices, backtests, and indicators.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey,
    Index, Integer, JSON, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── Ticker master ──────────────────────────────────────────────────────────────

class Ticker(Base):
    __tablename__ = "tickers"

    id:         Mapped[int]          = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol:     Mapped[str]          = mapped_column(String(16), unique=True, nullable=False, index=True)
    name:       Mapped[Optional[str]]= mapped_column(String(256))
    exchange:   Mapped[Optional[str]]= mapped_column(String(32))
    sector:     Mapped[Optional[str]]= mapped_column(String(64))
    country:    Mapped[Optional[str]]= mapped_column(String(8))
    currency:   Mapped[Optional[str]]= mapped_column(String(8))
    is_active:  Mapped[bool]         = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]     = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime]     = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    prices:     list["Price"]        = relationship("Price", back_populates="ticker_rel",
                                                     cascade="all, delete-orphan")


# ── OHLCV price data ───────────────────────────────────────────────────────────

class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_price_ticker_date"),
        Index("ix_price_ticker_date", "ticker", "date"),
    )

    id:     Mapped[int]   = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str]   = mapped_column(String(16), ForeignKey("tickers.symbol", ondelete="CASCADE"), nullable=False)
    date:   Mapped[str]   = mapped_column(String(12), nullable=False)   # "YYYY-MM-DD"
    open:   Mapped[Optional[float]] = mapped_column(Float)
    high:   Mapped[Optional[float]] = mapped_column(Float)
    low:    Mapped[Optional[float]] = mapped_column(Float)
    close:  Mapped[float]           = mapped_column(Float, nullable=False)
    volume: Mapped[Optional[float]] = mapped_column(Float)

    ticker_rel: "Ticker" = relationship("Ticker", back_populates="prices")


# ── Backtest runs ──────────────────────────────────────────────────────────────

class BacktestRun(Base):
    __tablename__ = "backtest_runs"

    id:            Mapped[str]            = mapped_column(String(36), primary_key=True,
                                                           default=lambda: str(uuid.uuid4()))
    strategy_name: Mapped[str]            = mapped_column(String(64), nullable=False)
    start_date:    Mapped[str]            = mapped_column(String(12))
    end_date:      Mapped[str]            = mapped_column(String(12))
    initial_capital:Mapped[float]         = mapped_column(Float)
    commission_pct: Mapped[float]         = mapped_column(Float, default=0.0015)
    slippage_pct:   Mapped[float]         = mapped_column(Float, default=0.0005)
    tickers:        Mapped[Optional[str]] = mapped_column(Text)   # JSON list
    strategy_params:Mapped[Optional[str]] = mapped_column(Text)   # JSON dict
    performance:    Mapped[Optional[str]] = mapped_column(Text)   # JSON dict
    status:         Mapped[str]           = mapped_column(String(20), default="completed")
    created_at:     Mapped[datetime]      = mapped_column(DateTime, server_default=func.now())

    # Persisted metrics (denormalised for quick queries)
    sharpe:      Mapped[Optional[float]] = mapped_column(Float)
    cagr:        Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown:Mapped[Optional[float]] = mapped_column(Float)
    n_trades:    Mapped[Optional[int]]   = mapped_column(Integer)


# ── Optimisation results ───────────────────────────────────────────────────────

class OptimisationResult(Base):
    __tablename__ = "optimisation_results"

    id:          Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy:    Mapped[str]  = mapped_column(String(64))
    metric:      Mapped[str]  = mapped_column(String(32))
    best_params: Mapped[str]  = mapped_column(Text)    # JSON
    best_value:  Mapped[float]= mapped_column(Float)
    all_results: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    created_at:  Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
