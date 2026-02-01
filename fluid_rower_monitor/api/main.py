from __future__ import annotations

import argparse
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from .broadcaster import get_broadcaster, BroadcastMode
from .middleware import add_cors
from .routers import router as base_router
from .routers.sessions import router as sessions_router
from .routers.config import router as config_router
from .routers.live import router as live_router


def create_app(mode: BroadcastMode = "production") -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup: start broadcaster
        broadcaster = get_broadcaster(mode=mode)
        await broadcaster.start()
        yield
        # Shutdown: stop broadcaster
        await broadcaster.stop()

    app = FastAPI(title="Fluid Rower Monitor API", version="0.1.0", lifespan=lifespan)

    # Middleware
    add_cors(app)

    # Routers
    app.include_router(sessions_router)
    app.include_router(config_router)
    app.include_router(live_router)

    return app


# Default to production mode; override with FRM_API_MODE=dev
_mode = os.environ.get("FRM_API_MODE", "production")
app = create_app(mode=_mode)  # type: ignore


def run(host: Optional[str] = None, port: Optional[int] = None, dev: bool = False) -> None:  # pragma: no cover
    """Convenience runner for `python -m fluid_rower_monitor.api` or entry point.

    Args:
        host: Host to bind to (default: 0.0.0.0)
        port: Port to bind to (default: 8000)
        dev: Use dev mode (synthetic data) vs production mode (real serial)
    """
    host = host or os.environ.get("FRM_API_HOST", "0.0.0.0")
    port = port or int(os.environ.get("FRM_API_PORT", "8000"))
    mode = "dev" if dev else "production"
    os.environ["FRM_API_MODE"] = mode

    import uvicorn

    print(f"🚀 Starting Fluid Rower Monitor API in {mode.upper()} mode")
    print(f"   Listening on http://{host}:{port}")
    print(f"   Docs: http://{host}:{port}/docs")
    if dev:
        print("   💡 Using synthetic data (pass --no-dev for real device)")

    uvicorn.run("fluid_rower_monitor.api.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description="Fluid Rower Monitor API")
    parser.add_argument("--host", default=None, help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=None, help="Port to bind to (default: 8000)")
    parser.add_argument("--dev", action="store_true", help="Use synthetic data (dev mode)")
    args = parser.parse_args()

    run(host=args.host, port=args.port, dev=args.dev)
