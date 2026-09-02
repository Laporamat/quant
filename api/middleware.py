"""api/middleware.py – CORS, logging, error-handling middleware."""
from __future__ import annotations
import logging
import time
import traceback
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api")


def register_middleware(app: FastAPI) -> None:
    """Attach all middleware to the FastAPI app."""

    # ── CORS ──────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request timing ────────────────────────
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next: Callable) -> Response:
        t0 = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - t0
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        logger.debug(
            "%s %s → %d (%.3fs)",
            request.method, request.url.path,
            response.status_code, elapsed,
        )
        return response

    # ── Global exception handler ──────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "Unhandled exception on %s %s:\n%s",
            request.method, request.url.path,
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "detail": str(exc),
                "path":   str(request.url.path),
            },
        )
