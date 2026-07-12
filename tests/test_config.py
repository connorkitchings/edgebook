"""Tests for configuration module."""

import pytest
from pydantic import ValidationError

from edgebook.core.config import DEV_SECRET_KEY, MIN_SECRET_KEY_LENGTH, Settings


def test_default_settings():
    """Test default values of the settings object."""
    settings = Settings()
    assert settings.PROJECT_NAME == "Edgebook"
    assert settings.ENV == "development"
    assert settings.DEBUG is True
    assert settings.PORT == 8000
    assert settings.HOST == "127.0.0.1"


def test_settings_env_override(monkeypatch):
    """Test that environment variables override default settings."""
    monkeypatch.setenv("PROJECT_NAME", "TestEdgebook")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/override")
    monkeypatch.setenv("PORT", "9000")

    settings = Settings()
    assert settings.PROJECT_NAME == "TestEdgebook"
    assert settings.DATABASE_URL == "postgresql://localhost/override"
    assert settings.PORT == 9000


def test_dev_env_allows_default_secret(monkeypatch):
    """Development environment must accept the placeholder secret."""
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("SECRET_KEY", DEV_SECRET_KEY)

    settings = Settings()

    assert settings.ENV == "development"
    assert settings.SECRET_KEY == DEV_SECRET_KEY


def test_production_rejects_default_secret(monkeypatch):
    """Production must reject the documented placeholder secret."""
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRET_KEY", DEV_SECRET_KEY)

    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings()


def test_production_rejects_empty_secret(monkeypatch):
    """Production must reject an unset or empty secret."""
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "")

    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings()


def test_production_rejects_short_secret(monkeypatch):
    """Production must reject a secret below the minimum length."""
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "too-short")

    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings()


def test_production_accepts_strong_secret(monkeypatch):
    """Production must accept a sufficiently long, non-default secret."""
    strong_key = "x" * MIN_SECRET_KEY_LENGTH
    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRET_KEY", strong_key)

    settings = Settings()

    assert settings.ENV == "production"
    assert settings.SECRET_KEY == strong_key
