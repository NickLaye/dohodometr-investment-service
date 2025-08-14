from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from .core.config import get_settings
from .core.db import init_db
from .admin_api.routes import router as admin_router
from .admin_api.scheduler import start_scheduler


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Dohodometr Admin API")
    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])  # basic global limit
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(admin_router, prefix=settings.api_prefix)

    @app.on_event("startup")
    def _startup() -> None:
        init_db()
        if settings.run_scheduler:
            start_scheduler()

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


