"""Tests for configuration module."""

from edgebook.core.config import Settings


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
