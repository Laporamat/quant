"""
main.py – Application entry point.
Run: python main.py  OR  uvicorn main:app
"""
from __future__ import annotations
import sys
import uvicorn
from utils.logger import setup_logging
from config import settings

# Configure logging before anything else
setup_logging()

# Import app (triggers all module imports)
from api.main import app  # noqa: E402 – must be after logging setup


def main() -> None:
    """Start the Quant Backend API server."""
    import argparse
    parser = argparse.ArgumentParser(description="Quant Backend")
    parser.add_argument("--host",    default=settings.host)
    parser.add_argument("--port",    type=int, default=settings.port)
    parser.add_argument("--workers", type=int, default=settings.workers)
    parser.add_argument("--reload",  action="store_true", default=settings.reload)
    parser.add_argument("--log-level", default=settings.log_level.lower())
    args = parser.parse_args()

    print(f"\n🚀  {settings.app_name} v{settings.app_version}")
    print(f"    API docs: http://{args.host}:{args.port}/docs")
    print(f"    ReDoc:    http://{args.host}:{args.port}/redoc\n")

    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        workers=args.workers if not args.reload else 1,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
