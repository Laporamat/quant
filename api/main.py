"""
api/main.py
FastAPI application entry point.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings, BASE_DIR
from api.middleware import register_middleware
from api.routers.data_router import router as data_router
from api.routers.stats_router import router as stats_router
from api.routers.indicators_router import router as indicators_router
from api.routers.strategy_router import router as strategy_router
from api.routers.backtest_router import router as backtest_router
from api.routers.optimize_router import router as optimize_router
from api.routers.daytrade_router import router as daytrade_router
from api.routers.trade_signal_router import router as trade_signal_router
from api.routers.ai_router import router as ai_router

logger = logging.getLogger("api")


# ── Startup / shutdown ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀  Quant Backend starting up (v%s)", settings.app_version)
    yield
    logger.info("🛑  Quant Backend shutting down")


# ── Application factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Quantitative Trading Backend — 20-year historical data analysis, "
            "technical indicators, stats, strategy backtesting, and optimisation."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    register_middleware(app)

    # ── Routers ──────────────────────────────
    app.include_router(data_router)
    app.include_router(stats_router)
    app.include_router(indicators_router)
    app.include_router(strategy_router)
    app.include_router(backtest_router)
    app.include_router(optimize_router)
    app.include_router(daytrade_router)
    app.include_router(trade_signal_router)
    app.include_router(ai_router)

    # ── Health / root ─────────────────────────
    @app.get("/", tags=["health"])
    async def root():
        return {"status": "ok", "app": settings.app_name, "version": settings.app_version}

    @app.get("/health", tags=["health"])
    async def health():
        return JSONResponse({"status": "healthy"})

    # ── Optional: serve built frontend at /ui ─────────────────────────────
    _frontend_dist = BASE_DIR / "frontend" / "dist"
    if _frontend_dist.exists():
        app.mount("/ui", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
        logger.info("Frontend dist found — serving at /ui")

    return app


app = create_app()
