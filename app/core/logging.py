"""Structured logging configuration.

Uses ``structlog`` so every log line is a structured event rather than a
formatted string. This matters later: request IDs, retrieval latency, tool
calls and LLM latency (Stage 10) all become queryable fields instead of prose.

Logs are written to stdout and, when enabled, to a file on disk. Trace events
emitted by :mod:`app.core.tracing` go to a dedicated ``traces.log`` sink so
they never pollute the application log stream.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

import structlog

from app.core.config import Settings, get_settings

APP_LOG_FILENAME = "app.log"
TRACE_LOG_FILENAME = "traces.log"
TRACE_LOGGER_NAME = "bka.trace"

_MAX_LOG_BYTES = 5 * 1024 * 1024
_LOG_BACKUP_COUNT = 3

_configured = False


def _shared_processors() -> list[structlog.types.Processor]:
    """Return the structlog processors shared by every renderer."""
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def _build_file_handler(path: Path) -> logging.Handler:
    """Create a size-rotating file handler writing JSON lines to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=_MAX_LOG_BYTES,
        backupCount=_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=_shared_processors(),
        )
    )
    return handler


def configure_logging(settings: Settings | None = None) -> None:
    """Configure structlog and the stdlib logging bridge.

    Safe to call more than once; only the first call takes effect.
    """
    global _configured
    if _configured:
        return

    settings = settings or get_settings()
    level = getattr(logging, settings.log_level)

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if settings.log_format == "json"
        else structlog.dev.ConsoleRenderer(colors=False)
    )

    structlog.configure(
        processors=[
            *_shared_processors(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=_shared_processors(),
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(stream_handler)
    root.setLevel(level)

    trace_logger = logging.getLogger(TRACE_LOGGER_NAME)
    trace_logger.handlers.clear()
    trace_logger.setLevel(level)
    # Trace events are a dedicated sink, never mixed into the app stream.
    trace_logger.propagate = False

    if settings.log_to_file:
        root.addHandler(_build_file_handler(settings.log_dir / APP_LOG_FILENAME))
        trace_logger.addHandler(
            _build_file_handler(settings.log_dir / TRACE_LOG_FILENAME)
        )
    else:
        trace_logger.addHandler(logging.NullHandler())

    _configured = True


def reset_logging() -> None:
    """Tear down logging configuration. Intended for tests."""
    global _configured
    structlog.reset_defaults()
    logging.getLogger().handlers.clear()
    logging.getLogger(TRACE_LOGGER_NAME).handlers.clear()
    _configured = False


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger for ``name``."""
    logger: structlog.stdlib.BoundLogger = structlog.stdlib.get_logger(name)
    return logger
