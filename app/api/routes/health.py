"""Health endpoint.

A pure liveness check: it answers "is this process alive and how is it
configured?" without touching any downstream system. Later stages add a
separate readiness check that probes the vector store and LLM provider.

Route handlers are intentionally not wrapped in ``@traced``: FastAPI resolves
handler annotations against the decorated function's module globals, which a
wrapper breaks. Request-level tracing is applied as middleware in Stage 10.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.dependencies import SettingsDep

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Payload returned by ``GET /health``."""

    status: str = Field(description="Overall service status.", examples=["ok"])
    service: str = Field(description="Human readable service name.")
    version: str = Field(description="Running application version.")
    environment: str = Field(description="Active environment profile.")


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health(settings: SettingsDep) -> HealthResponse:
    """Report that the service is running and how it is configured."""
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
