"""Shared FastAPI dependencies.

Settings are resolved from ``request.app.state`` rather than the cached
``get_settings()`` singleton, so the application factory stays the single
source of truth and tests can build an app with overridden configuration.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.core.config import Settings


def get_app_settings(request: Request) -> Settings:
    """Return the settings the running application was built with."""
    settings: Settings = request.app.state.settings
    return settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
