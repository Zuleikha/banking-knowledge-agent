"""Metrics endpoint (Stage 10, guide §20.33).

``GET /metrics`` returns the in-process counters and latency histograms as JSON.
They hold metric names and numbers only -- never a question, an identifier or
an answer -- and reset when the process restarts.

The endpoint is unauthenticated, like ``/health``. Who may read operational
numbers in a deployment is a Stage 13 question.

Not ``@traced``, for the reason every route handler is not (see
:mod:`app.core.tracing`); the request middleware records it instead.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.core.observability import get_metrics

router = APIRouter(tags=["observability"])


@router.get("/metrics", summary="In-process counters and latency histograms")
async def metrics() -> dict[str, Any]:
    """Report every counter and histogram collected since the process started."""
    return get_metrics().snapshot()
