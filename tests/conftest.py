"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.logging import reset_logging
from app.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Test settings that never touch the developer's real log directory."""
    return Settings(
        environment="test",
        log_level="DEBUG",
        log_format="json",
        log_dir=tmp_path / "logs",
        log_to_file=True,
    )


@pytest.fixture
def app(settings: Settings) -> Iterator[FastAPI]:
    """A FastAPI app built from the test settings."""
    reset_logging()
    yield create_app(settings)
    reset_logging()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """HTTP client bound to the test application."""
    with TestClient(app) as test_client:
        yield test_client
