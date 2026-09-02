"""
utils/logger.py
Structured JSON logging setup using structlog + standard logging.
"""
from __future__ import annotations
import logging
import logging.config
import sys
from pathlib import Path
from config import settings


def setup_logging() -> None:
    """Configure application-wide logging."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            } if settings.log_json else {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "plain": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "plain",
                "level": settings.log_level,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": settings.log_file,
                "maxBytes": 10 * 1024 * 1024,   # 10 MB
                "backupCount": 5,
                "formatter": "plain",
                "level": "DEBUG",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console", "file"],
        },
        "loggers": {
            "uvicorn":       {"level": "INFO",  "propagate": True},
            "uvicorn.error": {"level": "INFO",  "propagate": True},
            "uvicorn.access":{"level": "WARNING","propagate": True},
            "yfinance":      {"level": "WARNING","propagate": True},
            "httpx":         {"level": "WARNING","propagate": True},
        },
    }

    try:
        logging.config.dictConfig(LOGGING_CONFIG)
    except Exception:
        # Fallback basic config
        logging.basicConfig(
            level=settings.log_level,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            stream=sys.stdout,
        )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
