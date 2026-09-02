"""database/crud.py – CRUD operations for all models."""
from __future__ import annotations
import json
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Ticker, Price, BacktestRun, OptimisationResult


# ── Tickers ────────────────────────────────────────────────────────────────────

async def get_ticker(db: AsyncSession, symbol: str) -> Optional[Ticker]:
    r = await db.execute(select(Ticker).where(Ticker.symbol == symbol))
    return r.scalar_one_or_none()


async def create_ticker(db: AsyncSession, **kwargs) -> Ticker:
    obj = Ticker(**kwargs)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def upsert_ticker(db: AsyncSession, symbol: str, **kwargs) -> Ticker:
    obj = await get_ticker(db, symbol)
    if obj is None:
        return await create_ticker(db, symbol=symbol, **kwargs)
    for k, v in kwargs.items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


# ── Prices ────────────────────────────────────────────────────────────────────

async def bulk_insert_prices(db: AsyncSession, rows: List[dict]) -> int:
    objs = [Price(**r) for r in rows]
    db.add_all(objs)
    await db.commit()
    return len(objs)


async def get_prices(
    db: AsyncSession, symbol: str, start: str, end: str
) -> List[Price]:
    r = await db.execute(
        select(Price)
        .where(Price.ticker == symbol, Price.date >= start, Price.date <= end)
        .order_by(Price.date)
    )
    return list(r.scalars().all())


# ── Backtest runs ──────────────────────────────────────────────────────────────

async def create_backtest_run(db: AsyncSession, **kwargs) -> BacktestRun:
    obj = BacktestRun(**kwargs)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_backtest_run(db: AsyncSession, run_id: str) -> Optional[BacktestRun]:
    r = await db.execute(select(BacktestRun).where(BacktestRun.id == run_id))
    return r.scalar_one_or_none()


async def list_backtest_runs(db: AsyncSession, limit: int = 50) -> List[BacktestRun]:
    r = await db.execute(
        select(BacktestRun).order_by(BacktestRun.created_at.desc()).limit(limit)
    )
    return list(r.scalars().all())


# ── Optimisation results ───────────────────────────────────────────────────────

async def create_optimisation_result(db: AsyncSession, **kwargs) -> OptimisationResult:
    obj = OptimisationResult(**kwargs)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj
