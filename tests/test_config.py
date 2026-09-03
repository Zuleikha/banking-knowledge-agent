"""Configuration management tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_defaults_are_local_and_safe():
    settings = Settings(_env_file=None)
    assert settings.environment == "local"
    assert settings.is_production is False
    assert settings.port == 8000
    assert settings.log_level == "INFO"


def test_environment_variables_override_defaults(monkeypatch):
    monkeypatch.setenv("BKA_ENVIRONMENT", "production")
    monkeypatch.setenv("BKA_PORT", "9100")
    monkeypatch.setenv("BKA_LOG_FORMAT", "json")

    settings = Settings(_env_file=None)

    assert settings.environment == "production"
    assert settings.is_production is True
    assert settings.port == 9100
    assert settings.log_format == "json"


def test_invalid_port_is_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, port=70000)


def test_invalid_environment_is_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="staging")


def test_get_settings_is_cached():
    assert get_settings() is get_settings()


def test_settings_are_immutable():
    settings = Settings(_env_file=None)
    with pytest.raises(ValidationError):
        settings.port = 1234
