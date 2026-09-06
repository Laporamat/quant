"""api/middleware.py – CORS, logging, error-handling, security headers middleware."""
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

# Public paths that don't require auth headers (auth checks are per-route)
_PUBLIC_PREFIXES = [
    "/health", "/docs", "/redoc", "/openapi.json",
    "/auth/login", "/auth/register", "/auth/refresh", "/auth/providers",
    "/data/", "/stats/", "/indicators/", "/strategies/", "/backtest/",
    "/optimize/", "/daytrade/", "/trade/", "/ai/",
]


def register_middleware(app: FastAPI) -> None:
    """Attach all middleware to the FastAPI app."""

    # ── CORS — tightened for production ───────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:8080",
                       "http://127.0.0.1:5173"],  # explicit, not wildcard *
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token",
                       "X-Requested-With", "Accept"],
        expose_headers=["X-Process-Time", "X-Request-ID"],
    )

    # ── Security headers + request ID ─────────────────────────────────────────
    @app.middleware("http")
    async def security_headers(request: Request, call_next: Callable) -> Response:
        import secrets as _sec
        req_id   = _sec.token_hex(8)
        t0       = time.perf_counter()
        response = await call_next(request)
        elapsed  = time.perf_counter() - t0

        response.headers["X-Process-Time"]            = f"{elapsed:.4f}"
        response.headers["X-Request-ID"]              = req_id
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"]    = "nosniff"
        # Clickjacking protection
        response.headers["X-Frame-Options"]           = "DENY"
        # XSS filter (legacy browsers)
        response.headers["X-XSS-Protection"]          = "1; mode=block"
        # HSTS (HTTPS only in production)
        # response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        # Referrer
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        # Permissions policy
        response.headers["Permissions-Policy"]        = "geolocation=(), microphone=(), camera=()"
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.openai.com https://api.anthropic.com; "
        )

        logger.debug("%s %s → %d (%.3fs) [%s]",
                     request.method, request.url.path,
                     response.status_code, elapsed, req_id)
        return response

    # ── Rate limiter setup ─────────────────────────────────────────────────────
    try:
        from slowapi import Limiter, _rate_limit_exceeded_handler
        from slowapi.errors import RateLimitExceeded
        from slowapi.util import get_remote_address

        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    except ImportError:
        logger.warning("slowapi not installed — rate limiting disabled")

    # ── Global exception handler ───────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("Unhandled exception on %s %s:\n%s",
                     request.method, request.url.path, traceback.format_exc())
        # Don't leak internal errors in production
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error",
                     "detail": "An unexpected error occurred"},
        )
