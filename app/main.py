"""FastAPI application entry point.

Stage 1 wires only the foundation: configuration, structured logging, tracing
and a health endpoint. The agent, RAG pipeline, LLM abstraction and MCP tools
are added in later stages behind their own routers and services.

Run locally with::

    uvicorn app.main:app --reload
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.core.tracing import traced

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Log application startup and shutdown."""
    settings: Settings = app.state.settings
    logger.info(
        "application.startup",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
    yield
    logger.info("application.shutdown", service=settings.app_name)


@traced
def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Using a factory (rather than a module-level singleton only) keeps the app
    testable: tests can construct an instance with overridden settings.
    """
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Source-backed knowledge and support agent for a banking "
            "technology platform. All domain content is synthetic."
        ),
        lifespan=lifespan,
        debug=settings.debug,
    )
    app.state.settings = settings

    from app.api.routes import health

    app.include_router(health.router)
    return app


app = create_app()
