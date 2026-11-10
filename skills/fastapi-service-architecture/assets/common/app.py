"""Application factory.

Every deployable in the repo builds its app through `create_app()`, then mounts
whichever routers that deployable owns. That is what lets one source tree ship as
a single API today and as N independently scaled services tomorrow without the
routes changing at all.
"""

import logging
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version
from typing import AsyncIterator

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.database import engine
from common.errors import register_exception_handlers
from common.settings import get_settings

logger = logging.getLogger(__name__)


def _package_version(distribution: str) -> str:
    try:
        return version(distribution)
    except PackageNotFoundError:
        return "0.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup before the yield, shutdown after.

    This replaces `@app.on_event("startup"/"shutdown")`, which is deprecated.
    Beyond being current, lifespan lets startup hand objects to shutdown through
    ordinary local variables, and it runs in tests when you enter the app as a
    context manager - `on_event` handlers silently do not.
    """
    settings = get_settings()
    logger.info("starting %s in %s", settings.app_name, settings.environment)
    yield
    # Return pooled connections before the process exits, otherwise the database
    # holds them until its own idle timeout fires.
    await engine.dispose()


health_router = APIRouter(tags=["health"])


@health_router.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    """Liveness only. Deliberately does not touch the database: if Postgres blips,
    you want the orchestrator to keep the pod and let requests fail, not to
    restart every replica at once. Put database checks on a separate /ready."""
    return {"status": "ok"}


def create_app(
    *,
    title: str | None = None,
    description: str = "",
    distribution: str = "service",
    **fastapi_kwargs,
) -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=title or settings.app_name,
        description=description,
        version=_package_version(distribution),
        lifespan=lifespan,
        # Interactive docs are an information-disclosure surface in production.
        # Keep them on everywhere else - the schema is the contract.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        **fastapi_kwargs,
    )

    # "*" plus credentials is not a valid CORS combination: a browser refuses a
    # wildcard origin on a credentialed request, so this silently breaks auth in
    # exactly the environment you cannot debug from. Enumerate origins in prod.
    allow_credentials = "*" not in settings.allowed_origins
    if settings.is_production and not allow_credentials:
        raise RuntimeError(
            "allowed_origins must list explicit origins in staging/production."
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(health_router)
    return app
